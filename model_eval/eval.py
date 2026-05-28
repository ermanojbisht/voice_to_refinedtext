#!/usr/bin/env python3
"""
Model comparison and iterative prompt refinement system.

Usage:
    python model_eval/eval.py --model-a qwen2.5:3b --model-b SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest
    python model_eval/eval.py --model-a qwen2.5:3b --model-b qwen3.5:0.8b --iterations 4 --judge qwen2.5:3b

Flow per model:
  1. Run all 10 battery tests with current prompts.
  2. LLM judge scores each output against criteria.
  3. If pass_rate >= threshold → done (early exit).
  4. LLM refiner rewrites prompts for failing (lang, mode) groups.
  5. Repeat up to --iterations times.

Results are saved to model_eval/results/eval_<timestamp>.json.
Winning model's tuned prompts live in model_eval/prompts/<alias>/.
To deploy: copy that folder to ../prompts/<alias>/ and restart the main app.
"""

import os
import sys
import json
import re
import argparse
import datetime

# Allow importing utils from the parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils  # noqa: E402  (import after sys.path manipulation)

EVAL_DIR    = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(EVAL_DIR, "prompts")
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
BATTERY_PATH = os.path.join(EVAL_DIR, "test_battery.json")
PASS_THRESHOLD_DEFAULT = 0.80
MAX_ITERATIONS_DEFAULT = 3
MIN_SCORE_FOR_REFINEMENT = 8   # tests scoring below this trigger refinement even if "passing"


# ---------------------------------------------------------------------------
# Prompt resolution (eval-local, mirrors utils but rooted at EVAL_DIR)
# ---------------------------------------------------------------------------

def get_eval_prompt(model_name, lang, mode, config=None):
    """Resolve prompt from model_eval/prompts/<alias>/ → default/.
    Returns (prompt_template_str, source_folder_name).
    """
    alias = utils.resolve_model_alias(model_name, config)
    prefix = f"{mode}_" if mode != "refine" else ""
    fname = f"{prefix}{lang}.txt"

    for candidate in (alias, "default"):
        folder = os.path.join(PROMPTS_DIR, candidate)
        path = os.path.join(folder, fname)
        fallback = os.path.join(folder, f"{lang}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read(), candidate
        if os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8") as fh:
                return fh.read(), candidate

    return "{text}", "hardcoded"


def get_eval_stops(model_name, lang, config=None):
    """Resolve stop tokens from model_eval/prompts/stops.json."""
    alias = utils.resolve_model_alias(model_name, config)
    stops_path = os.path.join(PROMPTS_DIR, "stops.json")
    if not os.path.exists(stops_path):
        return ["\n\n"]
    with open(stops_path, "r", encoding="utf-8") as fh:
        stops_data = json.load(fh)
    entry = (
        stops_data.get(model_name)
        or stops_data.get(alias)
        or stops_data.get("default", {})
    )
    return entry.get(lang, ["\n\n"])


def save_eval_prompt(model_name, lang, mode, prompt_text, config=None):
    """Write an updated prompt to model_eval/prompts/<alias>/."""
    alias = utils.resolve_model_alias(model_name, config)
    folder = os.path.join(PROMPTS_DIR, alias)
    os.makedirs(folder, exist_ok=True)
    prefix = f"{mode}_" if mode != "refine" else ""
    path = os.path.join(folder, f"{prefix}{lang}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(prompt_text)
    return path


def bootstrap_model_prompts(model_name, config=None):
    """Reset model_eval/prompts/<alias>/ to clean copies from default/.

    Always overwrites — each eval run starts from the same baseline so
    previous runs' (possibly degraded) refinements don't poison the next run.
    """
    import shutil
    alias = utils.resolve_model_alias(model_name, config)
    alias_dir   = os.path.join(PROMPTS_DIR, alias)
    default_dir = os.path.join(PROMPTS_DIR, "default")
    os.makedirs(alias_dir, exist_ok=True)
    for fname in ("en.txt", "hi.txt", "translate_en.txt", "translate_hi.txt"):
        src = os.path.join(default_dir, fname)
        dst = os.path.join(alias_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
    return alias


# ---------------------------------------------------------------------------
# Running models
# ---------------------------------------------------------------------------

def run_model(host, model_name, test, config, temperature):
    """Run one test case through the model. Returns (output_str, error_str)."""
    lang = test["lang"]
    mode = test["mode"]
    text = test["input"]

    prompt_template, _ = get_eval_prompt(model_name, lang, mode, config)
    try:
        prompt = prompt_template.format(text=text)
    except KeyError:
        prompt = prompt_template.replace("{text}", text)

    stop_tokens = get_eval_stops(model_name, lang, config)
    result = utils.call_ollama(host, model_name, prompt, stop_tokens, temperature)

    if "error" in result:
        return None, result["error"]

    raw = result.get("response", "")
    return utils.clean_response(raw), None


# ---------------------------------------------------------------------------
# Hard rule enforcement (runs BEFORE the LLM judge — these are never delegated)
# ---------------------------------------------------------------------------

# Phrases that indicate the model refused to process the input (refusal patterns)
# These are checked with word-boundary matching, case-insensitive.
_REFUSAL_FRAGMENTS = [
    "please provide the input",
    "please provide",
    "provide the input text",
    "i'll refine it",
    "i will refine it",
    "could you please provide",
    "can you provide",
    "please enter",
    "i need the input",
    # Hindi refusal / prompt-echo patterns
    "कृपया पेश करें",
    "कृपया प्रदान करें",
    "निम्नलिखित अंग्रेजी भाषा का अनुवाद",
    "अनुवाद कृपया",
    "कृपया इनपुट",
    "इनपुट पाठ दें",
]

# Characters used in Devanagari (Hindi) — for translation quality checks
_DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')
# Latin ASCII letters mixed into a Devanagari-only output = likely transliteration garbage
_LATIN_IN_DEVANAGARI_RE = re.compile(r'[\u0900-\u097F][a-zA-Z]|[a-zA-Z][\u0900-\u097F]')


def _pattern_in_output(pattern, output):
    """Word-boundary-aware pattern match (case-insensitive).

    For ASCII patterns: \b prevents false matches like 'here is' matching
    inside 'there is', or 'uh' matching inside 'although'.

    For Unicode/Devanagari patterns: Python's \b is ASCII-only and doesn't
    recognise non-ASCII word characters, so we fall back to plain substring
    match for any pattern that contains non-ASCII characters.
    """
    if any(ord(c) > 127 for c in pattern):
        # Unicode pattern — \b is unreliable; simple substring match
        return pattern.lower() in output.lower()
    try:
        return bool(re.search(r'\b' + re.escape(pattern), output, re.IGNORECASE))
    except re.error:
        return pattern.lower() in output.lower()


def check_hard_rules(output, test):
    """Programmatically enforce fail_patterns and detect model refusals/garbage.

    Returns (auto_fail: bool, reason: str).
    When auto_fail is True the test is failed immediately — the LLM judge is
    NOT called, eliminating judge hallucinations for clear-cut failures.

    Rules enforced:
      1. Empty output → fail
      2. Refusal fragments (English + Hindi) → fail
      3. fail_patterns with word-boundary matching → fail
      4. Translation-to-Hindi tests: Latin chars mixed with Devanagari → fail
         (catches transliteration garbage like 'डेटापाह्लीग', 'लीनियुम')
    """
    if not output or not output.strip():
        return True, "Model produced no output."

    # 1. Detect model refusal / prompt echo
    for fragment in _REFUSAL_FRAGMENTS:
        if _pattern_in_output(fragment, output):
            return True, f"Model refused or echoed prompt — output contains '{fragment}'."

    # 2. Check fail_patterns with word-boundary matching
    for pattern in test.get("fail_patterns", []):
        if _pattern_in_output(pattern, output):
            return True, f"Fail pattern found in output: '{pattern}'."

    # 3. Translation-to-Hindi test: detect Latin/Devanagari mixing (transliteration garbage)
    #    Only applies when the expected output language is Hindi (lang=hi, mode=translate)
    if test.get("lang") == "en" and test.get("mode") == "translate":
        devanagari_chars = len(_DEVANAGARI_RE.findall(output))
        if devanagari_chars > 10 and _LATIN_IN_DEVANAGARI_RE.search(output):
            return True, "Translation output mixes Latin and Devanagari characters — likely transliteration garbage."

    return False, ""


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

JUDGE_PROMPT_TEMPLATE = """\
You are evaluating an AI model's output on a voice transcription task.

TASK: {description}
ORIGINAL INPUT: {input}

EVALUATION CRITERIA:
{criteria}

PASS KEYWORDS (at least one should appear if the content is correct): {pass_keywords}
FAIL PATTERNS (none of these must appear in a passing output): {fail_patterns}

MODEL OUTPUT:
{output}

Evaluate whether the model output passes ALL criteria.
A output fails if ANY criterion is unmet OR if any fail_pattern appears in it.

Respond ONLY with valid JSON in exactly this format (no other text):
{{"pass": true, "score": 8, "reason": "one concise sentence explaining the verdict"}}

"pass" is true only if ALL criteria are met and no fail_patterns appear.
"score" is 0-10 (10 = perfect).
"""


def judge_output(host, judge_model, test, model_output):
    """Score a single test output. Hard rules are checked first (programmatically),
    then the LLM judge scores the content quality.
    Returns dict: {pass: bool, score: int, reason: str, hard_fail: bool}
    """
    if model_output is None:
        return {"pass": False, "score": 0, "reason": "Model returned an error — no output to judge.", "hard_fail": True}

    # Hard rules: checked by code, never by the LLM — catches refusals and fail_patterns
    auto_fail, hard_reason = check_hard_rules(model_output, test)
    if auto_fail:
        return {"pass": False, "score": 0, "reason": f"[HARD FAIL] {hard_reason}", "hard_fail": True}

    criteria_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(test["criteria"]))
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        description=test["description"],
        input=test["input"],
        criteria=criteria_text,
        pass_keywords=", ".join(test.get("pass_keywords", [])),
        fail_patterns=", ".join(test.get("fail_patterns", [])),
        output=model_output,
    )

    result = utils.call_ollama(host, judge_model, prompt, stop_tokens=[], temperature=0.0)
    if "error" in result:
        return {"pass": False, "score": 0, "reason": f"Judge error: {result['error']}"}

    raw = result.get("response", "")

    # Extract first {...} JSON block robustly
    match = re.search(r'\{[^{}]*"pass"[^{}]*\}', raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return {
                "pass":      bool(data.get("pass", False)),
                "score":     int(data.get("score", 0)),
                "reason":    str(data.get("reason", "")),
                "hard_fail": False,
            }
        except (json.JSONDecodeError, ValueError):
            pass

    # Heuristic fallback: look for true/false in raw text
    passed = "true" in raw.lower() and "false" not in raw.lower()
    return {
        "pass":      passed,
        "score":     5 if passed else 0,
        "reason":    f"(parse failed) raw: {raw[:120]}",
        "hard_fail": False,
    }


# ---------------------------------------------------------------------------
# LLM prompt refiner
# ---------------------------------------------------------------------------

REFINER_PROMPT_TEMPLATE = """\
You are a prompt engineer improving prompts for a voice transcription AI system.

CURRENT PROMPT TEMPLATE ({{text}} is replaced with actual voice input at runtime):
---
{current_prompt}
---

This prompt FAILED on the following test case:
  Description: {description}
  Voice input:  {input}
  Model output: {output}
  Judge reason: {reason}

CRITERIA that were NOT met:
{unmet_criteria}

Write an improved version of this prompt template that will fix these failures.
STRICT RULES for your response:
1. Keep the {{text}} placeholder exactly as written — do not remove or rename it.
2. Preserve the language of the prompt (Hindi prompts must stay in Hindi).
3. Output ONLY the new prompt template text. No explanations, no commentary.
4. CRITICAL — do NOT use any of these phrases anywhere in the improved prompt,
   because the model echoes them verbatim into its output and fails the test:
     "Here is"  |  "Here's"  |  "Please provide"  |  "Note:"  |  "Please note"
   Do not add "---" separator lines. Do not write example output sections.
"""

# Phrases the refiner must not write into prompt templates — if found, discard the refinement
_BAD_REFINER_PATTERNS = ["here is", "here's", "please provide", "please note", "note:", "---"]


def refine_prompts_for_model(host, refiner_model, model_name, failures, config):
    """For each (lang, mode) group of failures, ask the LLM to rewrite the prompt.
    Uses the worst-scoring failure as the driving example per group.
    Skips the group silently if {text} is missing from the result.
    """
    # Group failures by (lang, mode)
    groups: dict[tuple, list] = {}
    for f in failures:
        key = (f["lang"], f["mode"])
        groups.setdefault(key, []).append(f)

    for (lang, mode), group in groups.items():
        # Use the failure with the lowest score as the primary example
        worst = min(group, key=lambda r: r["verdict"]["score"])

        current_prompt, _ = get_eval_prompt(model_name, lang, mode, config)

        # Always show all criteria to the refiner — the judge already pinpointed the
        # specific issue in verdict["reason"], so the refiner has full context.
        unmet = "\n".join(f"  - {c}" for c in worst["test"]["criteria"])

        refiner_prompt = REFINER_PROMPT_TEMPLATE.format(
            current_prompt=current_prompt,
            description=worst["test"]["description"],
            input=worst["test"]["input"],
            output=worst["output"] or "(no output — model error)",
            reason=worst["verdict"]["reason"],
            unmet_criteria=unmet,
        )

        result = utils.call_ollama(
            host, refiner_model, refiner_prompt, stop_tokens=[], temperature=0.3
        )
        if "error" in result:
            print(f"    [warn] refiner error for {lang}/{mode}: {result['error']}")
            continue

        new_prompt = result.get("response", "").strip()

        # Validate: placeholder must be present
        if "{text}" not in new_prompt:
            print(f"    [warn] refiner dropped {{text}} for {lang}/{mode} — keeping current prompt")
            continue

        # Validate: refiner must not have introduced bad preamble phrases
        new_lower = new_prompt.lower()
        bad = next((p for p in _BAD_REFINER_PATTERNS if p in new_lower), None)
        if bad:
            print(f"    [warn] refiner wrote banned phrase '{bad}' into {lang}/{mode} prompt — keeping current")
            continue

        saved = save_eval_prompt(model_name, lang, mode, new_prompt, config)
        print(f"    [refine] updated {lang}/{mode} prompt → {os.path.relpath(saved, EVAL_DIR)}")


# ---------------------------------------------------------------------------
# Evaluation loop (per model)
# ---------------------------------------------------------------------------

def evaluate_model(host, model_name, battery, config, temperature,
                   judge_model, refiner_model, pass_threshold, max_iterations):
    """Run the full iterative evaluation loop for one model.
    Returns a result dict with per-test results and metadata.
    """
    alias = utils.resolve_model_alias(model_name, config)
    all_iterations = []

    print(f"\n  Model: {model_name}  (alias: {alias})")
    print(f"  {'─'*50}")

    final_pass_rate = 0.0
    iterations_run  = 0

    # Track best prompts seen across iterations so we restore the winner at end,
    # regardless of whether later refinements made things worse.
    best_pass_rate    = -1.0
    best_avg_score    = -1.0
    best_prompt_snap  = {}   # {(lang, mode): prompt_text}
    best_iter_results = []   # per-test results from the best iteration

    def _snapshot_prompts():
        snap = {}
        for lang, mode_key in [("en","refine"),("hi","refine"),("en","translate"),("hi","translate")]:
            text, _ = get_eval_prompt(model_name, lang, mode_key, config)
            snap[(lang, mode_key)] = text
        return snap

    def _restore_prompts(snap):
        for (lang, mode_key), text in snap.items():
            save_eval_prompt(model_name, lang, mode_key, text, config)

    for iteration in range(1, max_iterations + 1):
        iterations_run = iteration
        print(f"\n  Iteration {iteration}/{max_iterations}")

        iter_results = []
        for test in battery:
            output, error = run_model(host, model_name, test, config, temperature)
            verdict = judge_output(host, judge_model, test, output)

            result = {
                "test_id":   test["id"],
                "lang":      test["lang"],
                "mode":      test["mode"],
                "input":     test["input"],
                "output":    output,
                "error":     error,
                "verdict":   verdict,
                "test":      test,   # kept for refiner context; stripped before JSON save
            }
            iter_results.append(result)

            status = "✓" if verdict["pass"] else "✗"
            preview = (output or error or "—")[:60]
            print(f"    [{status}] {test['id']} ({test['lang']}/{test['mode']}) "
                  f"score={verdict['score']}/10  {preview}")

        passed = sum(1 for r in iter_results if r["verdict"]["pass"])
        final_pass_rate = passed / len(iter_results)
        avg_score = sum(r["verdict"]["score"] for r in iter_results) / len(iter_results)

        # Strip internal 'test' key before storing (it's in battery already)
        storable = [{k: v for k, v in r.items() if k != "test"} for r in iter_results]

        # Track best: update snapshot when this iteration beats the previous best
        if (final_pass_rate, avg_score) >= (best_pass_rate, best_avg_score):
            best_pass_rate    = final_pass_rate
            best_avg_score    = avg_score
            best_prompt_snap  = _snapshot_prompts()
            best_iter_results = storable  # snapshot per-test results of this iteration

        # Classify tests needing work:
        #   failures = hard fail (pass=False)
        #   weak     = passed but scored below MIN_SCORE_FOR_REFINEMENT
        failures   = [r for r in iter_results if not r["verdict"]["pass"]]
        weak       = [r for r in iter_results
                      if r["verdict"]["pass"] and r["verdict"]["score"] < MIN_SCORE_FOR_REFINEMENT]
        needs_work = failures + weak

        print(f"\n  Pass rate : {passed}/{len(iter_results)} = {final_pass_rate:.0%}  "
              f"Avg score: {avg_score:.1f}/10  Best so far: {best_pass_rate:.0%}")
        if weak:
            print(f"  Weak tests: {[r['test_id'] for r in weak]} (score < {MIN_SCORE_FOR_REFINEMENT})")
        all_iterations.append({
            "iteration":  iteration,
            "pass_rate":  final_pass_rate,
            "avg_score":  avg_score,
            "results":    storable,
        })

        # Early exit only when threshold met AND no weak tests remain
        if final_pass_rate >= pass_threshold and not needs_work:
            print(f"  ✓ All tests passing with score {MIN_SCORE_FOR_REFINEMENT}+. Done.")
            break

        if iteration < max_iterations:
            if needs_work:
                label = f"{len(failures)} failure(s), {len(weak)} weak test(s)"
                print(f"\n  Refining prompts for {len(needs_work)} test(s) ({label})...")
                refine_prompts_for_model(host, refiner_model, model_name, needs_work, config)
            else:
                # pass_rate below threshold but nothing to refine (shouldn't happen, but guard it)
                print(f"  No tests to refine — threshold not met but no failures or weak tests detected.")

    # Restore the best prompts seen during this run (rollback if last iteration regressed)
    if best_prompt_snap and (final_pass_rate, avg_score) < (best_pass_rate, best_avg_score):
        print(f"\n  [rollback] Last iteration regressed — restoring best prompts "
              f"({best_pass_rate:.0%} avg {best_avg_score:.1f})")
        _restore_prompts(best_prompt_snap)
        final_pass_rate = best_pass_rate
    elif best_prompt_snap:
        # Still write the best snapshot so the file on disk matches the best iteration
        _restore_prompts(best_prompt_snap)

    # Snapshot final prompt file contents (from disk after rollback if any)
    final_prompts = {}
    for (lang, mode_key, fname) in [
        ("en", "refine",    "en.txt"),
        ("hi", "refine",    "hi.txt"),
        ("en", "translate", "translate_en.txt"),
        ("hi", "translate", "translate_hi.txt"),
    ]:
        template, _ = get_eval_prompt(model_name, lang, mode_key, config)
        final_prompts[fname] = template

    return {
        "model":              model_name,
        "alias":              alias,
        "final_pass_rate":    best_pass_rate,    # report best, not last
        "final_avg_score":    best_avg_score,    # avg score of the best iteration
        "best_iter_results":  best_iter_results, # per-test results of the best iteration
        "iterations_run":     iterations_run,
        "passed_threshold":   best_pass_rate >= pass_threshold,
        "all_iterations":     all_iterations,
        "final_prompts":      final_prompts,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

# Tests grouped by the language prompt they exercise.
# "en" group = tests using the en.txt / translate_en.txt prompt  (lang=en)
# "hi" group = tests using the hi.txt / translate_hi.txt prompt  (lang=hi)
_EN_TEST_IDS = {"en_01", "en_02", "en_03", "en_04", "hinglish_01", "hinglish_02", "translate_en_01"}
_HI_TEST_IDS = {"hi_01", "hi_02", "translate_hi_01"}


def _category_stats(result_map, test_ids):
    """Return (pass_rate, avg_score, pass_count, total) for a subset of tests."""
    subset = [r for tid, r in result_map.items() if tid in test_ids]
    if not subset:
        return 0.0, 0.0, 0, 0
    passed    = sum(1 for r in subset if r["verdict"]["pass"])
    avg       = sum(r["verdict"]["score"] for r in subset) / len(subset)
    return passed / len(subset), avg, passed, len(subset)


def _category_winner(rate_a, avg_a, rate_b, avg_b, alias_a, alias_b):
    """Return (winner_alias, loser_alias, margin_str)."""
    if rate_a != rate_b:
        if rate_a > rate_b:
            return alias_a, alias_b, f"{rate_a:.0%} vs {rate_b:.0%}"
        return alias_b, alias_a, f"{rate_b:.0%} vs {rate_a:.0%}"
    # Tie on pass rate — use avg score as tiebreaker
    if avg_a != avg_b:
        if avg_a > avg_b:
            return alias_a, alias_b, f"tied {rate_a:.0%}, avg {avg_a:.1f} vs {avg_b:.1f}"
        return alias_b, alias_a, f"tied {rate_b:.0%}, avg {avg_b:.1f} vs {avg_a:.1f}"
    return "TIE", "TIE", f"tied {rate_a:.0%}, avg {avg_a:.1f}"


def generate_report(result_a, result_b, args):
    """Compare two evaluation results across three categories and produce a report dict."""

    def best_map(result):
        """Per-test results from the best-scoring iteration (not necessarily the last)."""
        rows = result.get("best_iter_results") or result["all_iterations"][-1]["results"]
        return {r["test_id"]: r for r in rows}

    map_a   = best_map(result_a)
    map_b   = best_map(result_b)
    alias_a = result_a["alias"]
    alias_b = result_b["alias"]

    # ── Overall ──────────────────────────────────────────────────────────────
    rate_a_all = result_a["final_pass_rate"]
    rate_b_all = result_b["final_pass_rate"]
    avg_a_all  = result_a.get("final_avg_score", 0.0)
    avg_b_all  = result_b.get("final_avg_score", 0.0)
    ov_win, ov_lose, ov_margin = _category_winner(
        rate_a_all, avg_a_all, rate_b_all, avg_b_all, alias_a, alias_b)

    # ── English category ─────────────────────────────────────────────────────
    rate_a_en, avg_a_en, pass_a_en, tot_en = _category_stats(map_a, _EN_TEST_IDS)
    rate_b_en, avg_b_en, pass_b_en, _      = _category_stats(map_b, _EN_TEST_IDS)
    en_win, en_lose, en_margin = _category_winner(
        rate_a_en, avg_a_en, rate_b_en, avg_b_en, alias_a, alias_b)

    # ── Hindi category ───────────────────────────────────────────────────────
    rate_a_hi, avg_a_hi, pass_a_hi, tot_hi = _category_stats(map_a, _HI_TEST_IDS)
    rate_b_hi, avg_b_hi, pass_b_hi, _      = _category_stats(map_b, _HI_TEST_IDS)
    hi_win, hi_lose, hi_margin = _category_winner(
        rate_a_hi, avg_a_hi, rate_b_hi, avg_b_hi, alias_a, alias_b)

    # ── Per-test breakdown ────────────────────────────────────────────────────
    per_test = []
    all_tids = [r["test_id"] for r in (result_a.get("best_iter_results") or result_a["all_iterations"][-1]["results"])]
    for tid in all_tids:
        ra = map_a.get(tid, {})
        rb = map_b.get(tid, {})
        lang_group = "en" if tid in _EN_TEST_IDS else "hi"
        per_test.append({
            "test_id":    tid,
            "lang_group": lang_group,
            "score_a":    ra.get("verdict", {}).get("score", 0),
            "score_b":    rb.get("verdict", {}).get("score", 0),
            "pass_a":     ra.get("verdict", {}).get("pass", False),
            "pass_b":     rb.get("verdict", {}).get("pass", False),
            "reason_a":   ra.get("verdict", {}).get("reason", ""),
            "reason_b":   rb.get("verdict", {}).get("reason", ""),
        })

    # ── Deployment instructions (3 scenarios) ────────────────────────────────
    def _deploy(winner_alias, winner_model, scenario):
        if winner_alias == "TIE":
            return [f"[{scenario}] Both models tied — keep the lighter/faster one."]
        return [
            f"[{scenario}] Use '{winner_model}'",
            f"  Copy model_eval/prompts/{winner_alias}/ → prompts/{winner_alias}/",
        ]

    ov_win_model  = result_a["model"] if ov_win == alias_a else result_b["model"]
    en_win_model  = result_a["model"] if en_win == alias_a else result_b["model"]
    hi_win_model  = result_a["model"] if hi_win == alias_a else result_b["model"]

    deployment = (
        _deploy(ov_win, ov_win_model,  "Single model for everything") +
        _deploy(en_win, en_win_model,  "English-only model (OLLAMA_MODELS.en)") +
        _deploy(hi_win, hi_win_model,  "Hindi-only model  (OLLAMA_MODELS.hi)") +
        ["Verify prompts/stops.json has entries for both aliases after copying.",
         "Restart the main app (or tray icon)."]
    )

    categories = {
        "overall": {
            "winner": ov_win, "margin": ov_margin,
            f"{alias_a}_pass_rate": rate_a_all, f"{alias_a}_avg_score": avg_a_all,
            f"{alias_b}_pass_rate": rate_b_all, f"{alias_b}_avg_score": avg_b_all,
        },
        "english": {
            "winner": en_win, "margin": en_margin, "test_count": tot_en,
            f"{alias_a}_pass_rate": rate_a_en, f"{alias_a}_avg_score": avg_a_en,
            f"{alias_b}_pass_rate": rate_b_en, f"{alias_b}_avg_score": avg_b_en,
        },
        "hindi": {
            "winner": hi_win, "margin": hi_margin, "test_count": tot_hi,
            f"{alias_a}_pass_rate": rate_a_hi, f"{alias_a}_avg_score": avg_a_hi,
            f"{alias_b}_pass_rate": rate_b_hi, f"{alias_b}_avg_score": avg_b_hi,
        },
    }

    return {
        "run_timestamp":   datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {
            "judge_model":    args.judge,
            "refiner_model":  args.refiner,
            "pass_threshold": args.pass_threshold,
            "max_iterations": args.iterations,
            "temperature":    args.temperature,
        },
        "model_a":             result_a,
        "model_b":             result_b,
        "categories":          categories,
        "per_test_comparison": per_test,
        "deployment_instructions": deployment,
    }


def print_summary(report):
    alias_a = report["model_a"]["alias"]
    alias_b = report["model_b"]["alias"]
    cats    = report["categories"]

    col_a = alias_a[:18]
    col_b = alias_b[:18]

    print(f"\n{'='*66}")
    print("FINAL REPORT — 3-CATEGORY BREAKDOWN")
    print(f"{'='*66}")

    # ── Category table ────────────────────────────────────────────────────────
    print(f"\n  {'Category':<12}  {'Tests':<6}  {col_a:<18}  {col_b:<18}  Winner")
    print(f"  {'─'*12}  {'─'*6}  {'─'*18}  {'─'*18}  {'─'*20}")

    def _row(label, cat_key, test_ids):
        c = cats[cat_key]
        n = c.get("test_count", len(test_ids))
        ra = c[f"{alias_a}_pass_rate"]
        rb = c[f"{alias_b}_pass_rate"]
        sa = c[f"{alias_a}_avg_score"]
        sb = c[f"{alias_b}_avg_score"]
        cell_a = f"{ra:.0%} avg {sa:.1f}"
        cell_b = f"{rb:.0%} avg {sb:.1f}"
        w = c["winner"]
        print(f"  {label:<12}  {n:<6}  {cell_a:<18}  {cell_b:<18}  {w}")

    _row("Overall",  "overall", _EN_TEST_IDS | _HI_TEST_IDS)
    _row("English",  "english", _EN_TEST_IDS)
    _row("Hindi",    "hindi",   _HI_TEST_IDS)

    # ── Per-test breakdown ────────────────────────────────────────────────────
    print(f"\n  Per-test detail (best iteration per model):")
    print(f"  {'Test':<16} {'Group':<6}  {col_a[:12]:<12}  {col_b[:12]:<12}")
    print(f"  {'─'*16} {'─'*6}  {'─'*12}  {'─'*12}")

    last_group = None
    for t in report["per_test_comparison"]:
        if t["lang_group"] != last_group:
            last_group = t["lang_group"]
        a_mark = "✓" if t["pass_a"] else "✗"
        b_mark = "✓" if t["pass_b"] else "✗"
        print(f"  {t['test_id']:<16} {t['lang_group']:<6}  "
              f"{a_mark} {t['score_a']:>2}/10        "
              f"{b_mark} {t['score_b']:>2}/10")

    # ── Recommendation ────────────────────────────────────────────────────────
    print(f"\n  Deployment / Recommendation:")
    for step in report["deployment_instructions"]:
        print(f"    {step}")

    # ── Warnings ─────────────────────────────────────────────────────────────
    if (not report["model_a"]["passed_threshold"] and
            not report["model_b"]["passed_threshold"]):
        thr = report["config"]["pass_threshold"]
        print(f"\n  ⚠  Neither model reached the {thr:.0%} overall threshold.")
        print("     Try --iterations 5 or test a different model.")

    print(f"{'='*66}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compare two Ollama models on voice transcription tasks with iterative prompt refinement.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--model-a",        required=True,  help="First model name (as registered in Ollama)")
    parser.add_argument("--model-b",        required=True,  help="Second model name")
    parser.add_argument("--iterations",     type=int,   default=MAX_ITERATIONS_DEFAULT,
                        help=f"Max prompt refinement iterations per model (default: {MAX_ITERATIONS_DEFAULT})")
    parser.add_argument("--pass-threshold", type=float, default=PASS_THRESHOLD_DEFAULT,
                        help=f"Pass rate (0–1) to consider a model effective (default: {PASS_THRESHOLD_DEFAULT})")
    parser.add_argument("--judge",          default=None,
                        help="Ollama model used as judge/evaluator (default: OLLAMA_MODELS.en from config.json)")
    parser.add_argument("--refiner",        default=None,
                        help="Ollama model used for prompt refinement (default: same as judge)")
    parser.add_argument("--host",           default=None,
                        help="Ollama host URL (default: OLLAMA_HOST from config.json)")
    parser.add_argument("--temperature",    type=float, default=0.1,
                        help="Temperature for model-under-test calls (default: 0.1; judge always uses 0.0)")
    parser.add_argument("--battery",        default=BATTERY_PATH,
                        help=f"Path to test_battery.json (default: {BATTERY_PATH})")
    parser.add_argument("--output-dir",     default=RESULTS_DIR,
                        help=f"Directory for result JSON files (default: {RESULTS_DIR})")
    args = parser.parse_args()

    # Load config from parent directory
    parent_dir = os.path.dirname(EVAL_DIR)
    config = utils.load_config(parent_dir)

    # Apply CLI overrides
    host           = args.host    or config.get("OLLAMA_HOST", "http://localhost:11434")
    judge_model    = args.judge   or config.get("OLLAMA_MODELS", {}).get("en", "qwen2.5:3b")
    refiner_model  = args.refiner or judge_model

    # Patch args so generate_report can read them
    args.judge   = judge_model
    args.refiner = refiner_model

    # Load test battery
    with open(args.battery, "r", encoding="utf-8") as fh:
        battery = json.load(fh)

    print(f"\n{'='*62}")
    print("MODEL EVALUATION SYSTEM")
    print(f"{'='*62}")
    print(f"  Model A  : {args.model_a}")
    print(f"  Model B  : {args.model_b}")
    print(f"  Tests    : {len(battery)}")
    print(f"  Threshold: {args.pass_threshold:.0%}  |  Max iterations: {args.iterations}")
    print(f"  Judge    : {judge_model}")
    print(f"  Refiner  : {refiner_model}")
    print(f"  Host     : {host}")

    # Bootstrap prompt folders (creates model_eval/prompts/<alias>/ from default/)
    alias_a = bootstrap_model_prompts(args.model_a, config)
    alias_b = bootstrap_model_prompts(args.model_b, config)
    print(f"\n  Prompt folders: {alias_a}/  {alias_b}/")

    # Run evaluation loops sequentially (avoids Ollama contention)
    print(f"\n{'─'*62}")
    print("EVALUATING MODEL A")
    result_a = evaluate_model(
        host, args.model_a, battery, config, args.temperature,
        judge_model, refiner_model, args.pass_threshold, args.iterations,
    )

    print(f"\n{'─'*62}")
    print("EVALUATING MODEL B")
    result_b = evaluate_model(
        host, args.model_b, battery, config, args.temperature,
        judge_model, refiner_model, args.pass_threshold, args.iterations,
    )

    # Generate and print report
    report = generate_report(result_a, result_b, args)
    print_summary(report)

    # Save results JSON
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = os.path.join(
        args.output_dir,
        f"eval_{timestamp}_{alias_a}_vs_{alias_b}.json",
    )
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"  Results saved → {os.path.relpath(result_path)}")


if __name__ == "__main__":
    main()
