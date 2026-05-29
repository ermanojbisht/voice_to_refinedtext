# Model Evaluation System

A tool for comparing two AI language models on voice transcription tasks, automatically finding the best prompts for each model, and telling you which model to use for English vs. Hindi.

---

## Table of Contents

1. [What This System Does](#1-what-this-system-does)
2. [Folder Structure](#2-folder-structure)
3. [Before You Start — Prerequisites](#3-before-you-start--prerequisites)
4. [Basic Usage — Comparing Two Models](#4-basic-usage--comparing-two-models)
5. [All Command Options](#5-all-command-options)
6. [Understanding the Output](#6-understanding-the-output)
7. [Understanding Results — What the Scores Mean](#7-understanding-results--what-the-scores-mean)
8. [Adding a New Model to Test](#8-adding-a-new-model-to-test)
9. [Adding Stop Tokens for a New Model](#9-adding-stop-tokens-for-a-new-model)
10. [Deploying the Winning Model](#10-deploying-the-winning-model)
11. [How Prompt Refinement Works (and Its Limits)](#11-how-prompt-refinement-works-and-its-limits)
12. [The Test Battery — What Gets Tested](#12-the-test-battery--what-gets-tested)
13. [Adding New Test Cases](#13-adding-new-test-cases)
14. [Troubleshooting](#14-troubleshooting)
15. [Lessons Learned from Testing](#15-lessons-learned-from-testing)

---

## 1. What This System Does

In plain English: **two AI models enter a competition, a judge scores their answers, and a coach tries to improve how each model is instructed. The best result wins.**

### The problem this solves

The voice-to-text app (AI Voice Refiner) uses a language model to clean up raw speech transcriptions — removing filler words like "uh" and "um", fixing grammar, and optionally translating between Hindi and English. But no single model is great at everything:

- Small English-focused models (like `qwen2.5:3b`) handle English very well but struggle with Hindi.
- Hindi-specialized models (like `llama3-hindi-8b`) handle Hindi beautifully but can be inconsistent on English.

This system gives you a **scientific, repeatable way to measure** which model performs better, and for which language, so you can configure the main app to use the right model for each task.

### What happens during a run

1. **Both models take the same 10 voice transcription tests** — a mix of English, Hindi, Hinglish (mixed), and translation tasks.
2. **A judge model scores each answer** from 0 to 10 and decides pass or fail.
3. **If a model fails or scores weakly**, a refiner model rewrites the model's instructions (called a "prompt") to try to fix the failure.
4. **This refine-and-retest loop repeats** up to 3 times (or however many iterations you choose).
5. **The best result across all iterations is kept.** If refinement makes things worse, the system automatically rolls back to the better version.
6. At the end, a report shows **three categories**: Overall, English-only, and Hindi-only — with a winner in each.

### Why three categories?

Because a model can win overall (more tests passed in total) but still lose on Hindi specifically. If you care about Hindi quality, you want to know the Hindi winner separately. The main app can be configured to use **different models for English and Hindi**, so knowing both winners is useful.

---

## 2. Folder Structure

```
model_eval/
├── eval.py                          — the main script (run this)
├── test_battery.json                — the 10 test cases
├── README.md                        — this file
├── prompts/
│   ├── default/                     — baseline prompts (never edit these directly)
│   │   ├── en.txt                   — English refinement prompt template
│   │   ├── hi.txt                   — Hindi refinement prompt template
│   │   ├── translate_en.txt         — Hindi→English translation prompt
│   │   └── translate_hi.txt         — English→Hindi translation prompt
│   ├── stops.json                   — stop tokens (one entry per model alias)
│   ├── qwen2_5/                     — auto-created: tuned prompts for qwen2.5
│   │   ├── en.txt
│   │   ├── hi.txt
│   │   ├── translate_en.txt
│   │   └── translate_hi.txt
│   └── llama3_hindi_8b_q5_km_gguf/ — auto-created: tuned prompts for llama3-hindi
│       └── ...
└── results/                         — one JSON file saved per eval run
    └── eval_20250528_143012_qwen2_5_vs_llama3_hindi_8b_q5_km_gguf.json
```

### What each file does

| File / Folder | What it is |
|---|---|
| `eval.py` | The brain of the system. Run this to start a comparison. |
| `test_battery.json` | A list of 10 test cases: each has an input (raw speech), criteria for what a good output looks like, and patterns to look for or avoid. |
| `prompts/default/` | The starting-point instructions for all models. These are never modified — they are copied fresh at the start of each run. |
| `prompts/default/en.txt` | Instructions for cleaning up English speech. Tells the model to remove "uh", "um", etc. |
| `prompts/default/hi.txt` | Same but written in Hindi, for cleaning up Hindi speech. |
| `prompts/default/translate_en.txt` | Instructions for translating Hindi speech into English. |
| `prompts/default/translate_hi.txt` | Instructions for translating English speech into Hindi. |
| `prompts/stops.json` | Stop tokens — signals that tell each model "stop generating here". One entry per model alias. |
| `prompts/qwen2_5/` | Auto-created folder containing prompts that were tuned specifically for `qwen2.5` during a run. |
| `prompts/llama3_hindi_8b_q5_km_gguf/` | Same, auto-created for the llama3-hindi model. |
| `results/` | Every completed run saves a detailed JSON file here with all scores, reasons, and the final report. |

> **Note:** The `prompts/<alias>/` folders are **reset to the default prompts at the start of every run**. This is intentional — each run starts from a clean slate so that a bad previous run cannot poison the next one.

---

## 3. Before You Start — Prerequisites

### Ollama must be running

The models are served by Ollama, a local AI model runner. Start it with:

```bash
ollama serve
```

Or check if it is already running:

```bash
curl http://localhost:11434
# Should return: Ollama is running
```

### Models must be downloaded

Before you can test a model, it must already be pulled to your machine:

```bash
ollama pull qwen2.5:3b
ollama pull SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest
```

Check what you have downloaded:

```bash
ollama list
```

### Python dependencies

The script uses `utils.py` from the parent folder (`voice_to_refinedtext/`). No extra install is needed beyond what the main app already uses. Run from the project root:

```bash
# From inside voice_to_refinedtext/
python model_eval/eval.py --help
```

---

## 4. Basic Usage — Comparing Two Models

### The standard command

```bash
python model_eval/eval.py \
  --model-a qwen2.5:3b \
  --model-b SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest \
  --iterations 3
```

### What each part means

| Part | Meaning |
|---|---|
| `python model_eval/eval.py` | Run the evaluation script |
| `--model-a qwen2.5:3b` | The first model to test (use its exact Ollama name) |
| `--model-b SL-Lexicons/...` | The second model to test |
| `--iterations 3` | Try up to 3 rounds of prompt refinement per model |

### What happens while it runs (step by step)

1. The script prints a header showing both model names, the judge, and the refiner.
2. It resets the prompt folders for both models to fresh copies from `default/`.
3. **Model A is evaluated first:**
   - All 10 tests are run through Model A.
   - Each output is checked against hard rules (does it contain forbidden phrases? Is it empty?).
   - A judge model scores the output 0–10 and says pass or fail.
   - If any tests fail or score poorly, a refiner rewrites the instructions and reruns.
   - This repeats up to 3 times.
4. **Model B is evaluated the same way.**
5. A final report compares both models across 3 categories and recommends what to deploy.
6. Results are saved to `model_eval/results/eval_<timestamp>.json`.

The whole run typically takes **5–20 minutes** depending on model sizes and the number of iterations.

---

## 5. All Command Options

```
python model_eval/eval.py [options]
```

| Option | Default | Description |
|---|---|---|
| `--model-a` | *(required)* | First model name exactly as shown in `ollama list` |
| `--model-b` | *(required)* | Second model name |
| `--iterations` | `3` | Max rounds of refinement per model. Use 5 for deeper testing. |
| `--judge` | English model from `config.json` | Which model evaluates outputs. Needs to be reliable at English reasoning. |
| `--refiner` | Same as judge | Which model rewrites failing prompts. Bigger = better. |
| `--pass-threshold` | `0.80` | A model needs to pass at least this fraction of tests to be considered "good enough". `0.80` means 8 out of 10. |
| `--temperature` | `0.1` | How random the tested model's outputs are. `0.0` = always the same answer, `1.0` = very random. The judge always uses `0.0`. |
| `--host` | From `config.json` | Ollama server address. Change this if Ollama runs on a different machine or port. |
| `--battery` | `model_eval/test_battery.json` | Path to a custom test file if you want to use your own tests. |
| `--output-dir` | `model_eval/results/` | Where to save the result JSON. |

### Example 1: Quick test (1 iteration, fast)

Use this to get a rough idea without waiting for refinement cycles.

```bash
python model_eval/eval.py \
  --model-a qwen2.5:3b \
  --model-b SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest \
  --iterations 1
```

### Example 2: Standard comparison (3 iterations, default)

The normal way to run a comparison.

```bash
python model_eval/eval.py \
  --model-a qwen2.5:3b \
  --model-b SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest \
  --iterations 3
```

### Example 3: Deep comparison with a better refiner

Use a larger model as the refiner to get higher-quality prompt improvements. This is especially useful when the default refiner keeps failing to fix the same test.

```bash
python model_eval/eval.py \
  --model-a qwen2.5:3b \
  --model-b SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest \
  --iterations 5 \
  --refiner qwen2.5:7b
```

---

## 6. Understanding the Output

Here is an annotated walkthrough of what you see in the terminal.

### Header block

```
==============================================================
MODEL EVALUATION SYSTEM
==============================================================
  Model A  : qwen2.5:3b
  Model B  : SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest
  Tests    : 10
  Threshold: 80%  |  Max iterations: 3
  Judge    : qwen2.5:3b
  Refiner  : qwen2.5:3b
  Host     : http://localhost:11434

  Prompt folders: qwen2_5/  llama3_hindi_8b_q5_km_gguf/
```

This confirms the setup before anything runs. Check here that the model names look correct and Ollama is the right address.

### Per-test results (inside each iteration)

```
  Iteration 1/3
    [✓] en_01 (en/refine) score=9/10  There are issues in the data enclosure...
    [✗] hi_01 (hi/refine) score=0/10  [HARD FAIL] Fail pattern found in output: 'मतलब'
    [✓] en_02 (en/refine) score=8/10  Go to web.php routes and add a GET route...
```

- **`[✓]`** — this test passed (score is high enough and no fail patterns found)
- **`[✗]`** — this test failed
- **`score=9/10`** — how well the model did on this test (0 to 10)
- **`(en/refine)`** — the language and mode of this test
- The text at the end is a short preview of the model's actual output

### Pass rate summary (after each iteration)

```
  Pass rate : 9/10 = 90%  Avg score: 8.3/10  Best so far: 90%
  Weak tests: ['hi_02'] (score < 8)
```

- **`9/10 = 90%`** — 9 out of 10 tests passed
- **`Avg score: 8.3/10`** — the mean score across all 10 tests
- **`Best so far: 90%`** — the highest pass rate achieved across all iterations so far
- **`Weak tests`** — tests that technically passed (not a hard failure) but scored below 8 — these also trigger refinement

### Refinement messages

```
  Refining prompts for 2 test(s) (1 failure(s), 1 weak test(s))...
    [refine] updated hi/refine prompt → prompts/qwen2_5/hi.txt
    [warn] refiner wrote banned phrase 'here is' into en/translate prompt — keeping current
```

- **`[refine] updated hi/refine prompt`** — the refiner successfully rewrote the Hindi instructions. The new version is saved to disk and will be used in the next iteration.
- **`[warn] refiner wrote banned phrase 'here is'`** — the refiner produced a bad prompt (one containing phrases that cause the model to echo labels into its output). The system rejected it and kept the current prompt. This is a safety check.

### Rollback message

```
  [rollback] Last iteration regressed — restoring best prompts (90% avg 8.3)
```

> **This is a safety net, not an error.** It means the last refinement round actually made things *worse*, so the system automatically goes back to the best version it found earlier. The final result shown is from the best iteration, not the last one.

### Final report table

```
==================================================================
FINAL REPORT — 3-CATEGORY BREAKDOWN
==================================================================

  Category      Tests   qwen2_5             llama3_hindi_8b_q    Winner
  ────────────  ──────  ──────────────────  ──────────────────  ────────────────────
  Overall       10      90% avg 8.3         80% avg 7.1         qwen2_5
  English       7       100% avg 9.1        71% avg 6.8         qwen2_5
  Hindi         3       67% avg 5.2         100% avg 9.4        llama3_hindi_8b_q5_km_gguf

  Per-test detail (best iteration per model):
  Test             Group   qwen2_5       llama3_hi
  ────────────── ──────  ────────────  ────────────
  en_01            en      ✓  9/10        ✓  8/10
  en_02            en      ✓  9/10        ✓  7/10
  hi_01            hi      ✗  0/10        ✓ 10/10
```

- The table shows pass rate and average score for each model in each category.
- The **Winner** column names the alias of the winning model.
- The per-test detail shows every individual test with the score and pass/fail for each model.

### Deployment instructions

```
  Deployment / Recommendation:
    [Single model for everything] Use 'qwen2.5:3b'
      Copy model_eval/prompts/qwen2_5/ → prompts/qwen2_5/
    [English-only model (OLLAMA_MODELS.en)] Use 'qwen2.5:3b'
      Copy model_eval/prompts/qwen2_5/ → prompts/qwen2_5/
    [Hindi-only model  (OLLAMA_MODELS.hi)] Use 'SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest'
      Copy model_eval/prompts/llama3_hindi_8b_q5_km_gguf/ → prompts/llama3_hindi_8b_q5_km_gguf/
    Verify prompts/stops.json has entries for both aliases after copying.
    Restart the main app (or tray icon).
```

This tells you exactly what to do to put the winning model into production. See [Section 10](#10-deploying-the-winning-model) for the full step-by-step.

---

## 7. Understanding Results — What the Scores Mean

### The score (0–10)

| Score | Meaning |
|---|---|
| **0** | Hard failure — the model produced no output, repeated the instructions back, said "please provide the input text", or its output contained a forbidden phrase. |
| **1–5** | Poor quality — the model tried but failed significantly: wrong language, key information missing, filler words not removed. |
| **6–7** | Acceptable but has issues — most of the content is correct but something is off (awkward phrasing, one filler word remaining, minor meaning loss). |
| **8–9** | Good — only minor imperfections. The output is usable in production. |
| **10** | Perfect — the output meets every criterion exactly. |

### Pass vs. fail

A test is marked **pass** when:
- No hard failures (no forbidden phrases, no empty output, no refusal)
- The judge scores it high enough

A test is marked **fail** when any of these happen:
- The output is empty
- The output contains a phrase from `fail_patterns` (e.g. the word "मतलब" in a Hindi test)
- The model said something like "please provide the input" instead of actually doing the task
- The judge scored it too low

### Pass rate vs. average score — why both matter

**Pass rate** tells you how *reliable* a model is. A model with 90% pass rate fails only 1 test in 10 — that is acceptable for production.

**Average score** tells you *how well* it passes. Two models can both pass 9/10 tests, but one might score 10/10 on every passing test while the other scores 6/10 — barely passing each time.

Always look at both numbers together. A 90% pass rate with a 9.5 average is excellent. A 90% pass rate with a 6.1 average suggests the model is barely scraping by.

### Why a model can win overall but lose on Hindi

The overall score is calculated across all 10 tests. There are 7 English tests and only 3 Hindi tests. A model that aces English (7/7) but fails all Hindi tests (0/3) still gets 70% overall — which is not far behind a model that gets 90% overall. But for Hindi use cases, the first model is useless. That is why the Hindi category is reported separately.

---

## 8. Adding a New Model to Test

### Step 1: Download the model

```bash
ollama pull your-new-model-name:tag
```

Confirm it downloaded:

```bash
ollama list
```

### Step 2: Run the evaluation

Use your new model as `--model-b` (compare it against the current best):

```bash
python model_eval/eval.py \
  --model-a qwen2.5:3b \
  --model-b your-new-model-name:tag \
  --iterations 3
```

### Step 3: The system auto-creates a prompt folder

At the start of the run, the script creates `model_eval/prompts/<alias>/` with copies of the default prompts. The alias is the model name simplified — for example:
- `your-new-model-name:tag` becomes `your_new_model_name`

You do not need to create this folder yourself.

### Step 4: Add stop tokens

This is the most important manual step. See [Section 9](#9-adding-stop-tokens-for-a-new-model) for a full explanation. In short: open `model_eval/prompts/stops.json` and add an entry for the new model's alias.

### Step 5: Check the results

Open the most recent file in `model_eval/results/` — it is a JSON file you can open in any text editor. The scores, reasons, and per-test details are all there.

---

## 9. Adding Stop Tokens for a New Model

This is the most confusing part of the system. Take your time with this section.

### What is a stop token?

When an AI model generates text, it does not know when to stop unless you tell it. A **stop token** is a signal — a word or phrase — that tells the model: "stop generating here, your answer is complete."

Without stop tokens, models tend to keep rambling after giving the answer. For example, a model might produce:

```
Remind me to check the server logs at 5 PM

INPUT TEXT:
your next voice input here...
```

The model answered correctly on the first line, but then kept going and started a new "conversation" with itself. Stop tokens prevent this by telling it to halt after the first blank line.

### Why do different models need different stop tokens?

Different models were trained differently and recognize different signals as "end of response". Some models stop cleanly at `\n\n` (two newlines = a blank line). Others respond to `INPUT TEXT:` or `REFINED TEXT:` because those labels appear in the prompt template.

### How the alias is calculated

The alias is the simplified version of the model name used as the folder name. The rules are:
1. Take the last part after any `/` in the name
2. Remove the `:tag` part
3. Replace any special characters (`.`, `-`, spaces) with underscores `_`
4. Lowercase everything

Examples:
- `qwen2.5:3b` → alias is `qwen2_5`
- `SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest` → alias is `llama3_hindi_8b_q5_km_gguf`
- `mistral:7b` → alias is `mistral`

### Adding the entry to stops.json

Open `model_eval/prompts/stops.json` and add an entry. Here is the template:

```json
"your_model_alias": {
    "hi": ["इनपुट पाठ:", "आउटपुट:", "\n\n"],
    "en": ["INPUT TEXT:", "REFINED TEXT:", "\n\n"]
}
```

These stop tokens match the labels used in the default prompt templates, so they work for most models out of the box.

### Complete stops.json example

```json
{
    "default": {
        "en": ["INPUT TEXT:", "REFINED TEXT:", "\n\n"],
        "hi": ["इनपुट पाठ:", "आउटपुट:", "\n\n"]
    },
    "qwen2_5": {
        "hi": ["इनपुट पाठ:", "आउटपुट:", "\n\n"],
        "en": ["INPUT TEXT:", "REFINED TEXT:", "\n\n"]
    },
    "llama3_hindi_8b_q5_km_gguf": {
        "hi": ["इनपुट पाठ:", "आउटपुट:", "\n\n"],
        "en": ["INPUT TEXT:", "REFINED TEXT:", "\n\n"]
    },
    "your_model_alias": {
        "hi": ["इनपुट पाठ:", "आउटपुट:", "\n\n"],
        "en": ["INPUT TEXT:", "REFINED TEXT:", "\n\n"]
    }
}
```

### When to adjust stop tokens

Start with the default template above. After running the eval, check the outputs in the results JSON:

- **Output is cut off too early** (missing words at the end) → the stop token is triggering too soon. Try using only `"\n\n"` and removing the label-based stops.
- **Output keeps going for many lines** (the model is rambling) → the stop token is not working. Try adding `"\n"` (single newline) as the first stop token, before `"\n\n"`.

---

## 10. Deploying the Winning Model

After the eval completes, the terminal prints clear deployment instructions. Here is what each step means and how to do it.

### Full example

Imagine the eval recommends:
- English: use `qwen2.5:3b` (alias: `qwen2_5`)
- Hindi: use `SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest` (alias: `llama3_hindi_8b_q5_km_gguf`)

#### Step 1: Copy the tuned prompt folders

The eval stores the best prompts it found in `model_eval/prompts/<alias>/`. Copy these to the main app's `prompts/` folder so the main app can use them.

```bash
# Copy qwen2_5 prompts to the main app
cp -r model_eval/prompts/qwen2_5/ prompts/qwen2_5/

# Copy llama3-hindi prompts to the main app
cp -r model_eval/prompts/llama3_hindi_8b_q5_km_gguf/ prompts/llama3_hindi_8b_q5_km_gguf/
```

#### Step 2: Update stops.json in the main prompts folder

The main app has its own `prompts/stops.json` (separate from `model_eval/prompts/stops.json`). Make sure both model aliases are listed there.

Open `prompts/stops.json` (in the root project folder, not inside model_eval/) and add entries for any new models you are deploying, using the same format from Section 9.

#### Step 3: Update config.json

Open `config.json` in the root project folder and update the `OLLAMA_MODELS` entries:

```json
{
    "OLLAMA_MODELS": {
        "en": "qwen2.5:3b",
        "hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    },
    "OLLAMA_TRANSLATE_MODELS": {
        "to_en": "qwen2.5:3b",
        "to_hi": "SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest"
    }
}
```

Set `"en"` to the English winner's full Ollama model name, and `"hi"` to the Hindi winner's full name.

#### Step 4: Restart the tray app

Right-click the tray icon and choose Quit (or Restart). The app will load the updated config and start using the new models.

```bash
# Or restart from the terminal
python tray_app.py
```

---

## 11. How Prompt Refinement Works (and Its Limits)

### What the refiner does

When a model fails a test, the refiner is given:
- The current prompt (the instructions the model was using)
- The failing test case (what input was given)
- The model's bad output
- The judge's reason for failing it

The refiner then **rewrites the prompt** to try to prevent that specific failure from happening again. It is like a coach watching a player fail and then giving them more specific instructions.

### Why a bigger refiner is better

A small model used as the refiner (like `qwen2.5:3b`) sometimes writes bad prompts — prompts that contain the very phrases they are supposed to prevent, or prompts that drop the required `{text}` placeholder. When this happens, the system rejects the new prompt and keeps the old one. This means small refiners often produce no improvement at all.

A larger model (like `qwen2.5:7b` or `qwen3.5:9b`) understands the task better and produces higher-quality prompt rewrites. Use `--refiner qwen2.5:7b` or larger when you want serious refinement.

> **Real finding:** Using `qwen3.5:9b` as the refiner was the first time the llama3-hindi model achieved 100% on all tests. The default refiner (`qwen2.5:3b`) had never managed to fix the same failures.

### Why refinement sometimes makes things worse (and how rollback saves you)

Prompt refinement is not magic. Sometimes the refiner adds an instruction that accidentally makes a previously-passing test fail. For example, it might make the Hindi prompt so strict about removing filler words that it starts removing important content words too.

The rollback mechanism protects you from this. After every iteration, the system compares the current results to the best results seen so far. If the latest iteration was worse, it **automatically restores the prompts from the best iteration** before saving and reporting.

You will see this in the terminal as:
```
  [rollback] Last iteration regressed — restoring best prompts (90% avg 8.3)
```

This is normal and expected behavior — not an error.

### What prompts CANNOT fix: model capability ceilings

Every model has a ceiling — a level of quality it simply cannot exceed, no matter how well-written the prompt is.

**Real example:** `qwen2.5:3b` consistently fails to remove the Hindi filler word "मतलब" from Hindi text, even when the prompt explicitly says: *"Remove this word: मतलब"*. The model reads the instruction, acknowledges it understands, and then includes "मतलब" in the output anyway. This is not a prompt problem — it is a model limitation.

When you see the same test fail across all 3 iterations, with the refiner unable to fix it, you have likely hit the model's ceiling. At that point:
- Accept that this model is not suitable for that task
- Try a different (usually larger or language-specialized) model
- For Hindi specifically, switch to a Hindi-trained model

There is no benefit to running more iterations when the model has a hard capability ceiling.

---

## 12. The Test Battery — What Gets Tested

The 10 tests cover the main real-world scenarios the voice app encounters.

### English tests (en_01 to en_04)

| Test ID | What it tests |
|---|---|
| `en_01` | A rambling technical bug report with filler words ("uh", "that that", "i think"). The model must clean it up and preserve the technical detail (decimal places). |
| `en_02` | A short voice command with a technical file reference (`web.php`). Must remove "uh" and "okay" without touching the technical terms. |
| `en_03` | A task list dictated by voice with three items buried in filler ("so", "um", "like", "okay so that's it"). All three tasks must survive the cleanup. |
| `en_04` | A single short sentence with one filler word ("um") and a specific time ("five pm"). Tests that the model does not over-engineer a simple input. |

### Hindi tests (hi_01, hi_02)

| Test ID | What it tests |
|---|---|
| `hi_01` | A Hindi meeting note with "मतलब" (a common Hindi filler meaning "I mean"), "uh", and a repeated word ("वो वो"). The output must be clean Devanagari Hindi with the meeting decision intact. This is the hardest test for small English-focused models. |
| `hi_02` | A short personal task note starting with "यार" (informal Hindi for "hey man/friend") and containing "uh". Both informal words must be removed; both tasks (bank visit, electricity bill) must be preserved. |

### Hinglish tests (hinglish_01, hinglish_02)

Hinglish is the natural mix of Hindi and English that many Indian speakers use. The model sees a mix like "yeh wala function mein kuch issue hai" and must clean it up.

| Test ID | What it tests |
|---|---|
| `hinglish_01` | A code review note mixing Hindi filler ("basically", "like") with English technical terms (function, return value). Must remove fillers while preserving the technical meaning. |
| `hinglish_02` | A deadline instruction in Hinglish with two tasks and a time reference ("kal tak" = by tomorrow). The model must extract both tasks AND preserve the deadline — a word like "tomorrow" must appear in the output. |

> **Note:** Hinglish tests use the English prompt (`lang: en`) because the primary language of the instruction style is English-adjacent. The model is not asked to choose a language — it just cleans up whatever it receives.

### Translation tests

| Test ID | What it tests |
|---|---|
| `translate_hi_01` | Translate a Hindi meeting decision into professional English. The output must be English-only (no Devanagari) with accurate meaning (meeting, next phase, two weeks, resources). |
| `translate_en_01` | Translate an English technical sentence (deployment pipeline failure) into Hindi. The output must be proper Devanagari — not garbage transliteration like "पाइलाइच" for "pipeline". The system has a hard rule that catches Latin characters mixed into Devanagari output. |

### Pass keywords and fail patterns

Each test has two lists that help the judge:

- **`pass_keywords`** — words that should appear in a correct output. At least one of these should be present if the model understood the task. Example: for `en_03`, the pass keywords are `["call", "review", "deploy"]` — if none of these appear, the three tasks were likely dropped.

- **`fail_patterns`** — words or phrases that must NOT appear in a passing output. Example: `"मतलब"` in `hi_01`, or `"Here is"` in any test (because that means the model started its reply with a label instead of the content).

The system checks fail patterns programmatically (in code, not by the AI judge) — this prevents the judge from hallucinating a pass when a forbidden word is clearly present.

---

## 13. Adding New Test Cases

### JSON structure

Each test case in `test_battery.json` follows this format:

```json
{
  "id": "en_05",
  "mode": "refine",
  "lang": "en",
  "description": "English: voice memo with a price quote",
  "input": "uh yeah so tell the client the price is like uh two fifty per month okay",
  "criteria": [
    "removes fillers (uh, yeah, like, okay, so)",
    "price preserved ($250 or 250)",
    "output is a single clean sentence",
    "no added labels or preamble"
  ],
  "pass_keywords": ["250", "month"],
  "fail_patterns": ["uh", "yeah so", "like", "Here is", "Please provide"]
}
```

### What each field means

| Field | Required | Description |
|---|---|---|
| `id` | Yes | A unique identifier. Use `en_05`, `hi_03`, `hinglish_03`, etc. to follow the naming pattern. |
| `mode` | Yes | `"refine"` for cleanup tasks, `"translate"` for translation tasks. |
| `lang` | Yes | `"en"` for English and Hinglish inputs, `"hi"` for Hindi inputs. |
| `description` | Yes | One sentence describing the test for humans and for the judge. Be specific. |
| `input` | Yes | The raw "voice transcription" text — exactly as a speech recognition system would produce it, with fillers and all. |
| `criteria` | Yes | A list of what a correct output must satisfy. These are shown to the judge model. Be concrete — "preserves price ($250)" is better than "preserves important information". |
| `pass_keywords` | Yes | Words that must appear in a good output. Choose words that are genuinely distinctive — not common words that might appear by accident. |
| `fail_patterns` | Yes | Words or phrases that absolutely must NOT appear. Include filler words from the input, and common bad-output markers like "Here is" and "Please provide". |

### Rules for good tests

- **`pass_keywords` should be distinctive** — choose words from the input that a good model will naturally keep. Avoid very common words like "the" or "and".
- **`fail_patterns` should catch clear failures** — if a filler word appears in the output, it is definitely a failure. Add it. But do not add words that might legitimately appear (e.g. do not add "meeting" as a fail pattern for a test about a meeting).
- **Criteria should be checkable** — "professional tone" is vague. "No filler words (uh, um, like)" is checkable.
- **One test per concept** — do not try to test too many things in one case. If you want to test deadline preservation AND task extraction, those can be separate tests.

---

## 14. Troubleshooting

### "Model not found" or connection error

The model name you passed is not recognized by Ollama. Fix:

```bash
ollama list           # See what is available
ollama pull model:tag # Pull the missing model
```

Make sure the name you pass to `--model-a` or `--model-b` matches exactly what `ollama list` shows.

### "Timeout after 120s"

A model took too long to respond on a single test. This usually means:
- The model is very large and your machine is slow to run it
- Ollama is still loading the model weights for the first time

What to do:
- Wait for the first run to finish (Ollama caches the model in RAM for subsequent calls)
- Try a smaller judge model: `--judge qwen2.5:3b`
- If the *tested* model is slow, there is not much to do — that model may not be practical on your hardware

### "Refiner timeout"

The refiner gets 300 seconds (5 minutes) per call, which is already generous. If it times out, the refiner call is skipped and the current prompt is kept. To fix:
- Use a smaller refiner: `--refiner qwen2.5:3b` instead of a large model
- Or accept that this iteration's refinement is skipped

### Results vary a lot between runs

AI models have some randomness built in. A temperature of 0.1 (the default for tested models) means results are mostly consistent but not perfectly identical. The judge always uses 0.0 (fully deterministic).

To minimize variance:
```bash
python model_eval/eval.py ... --temperature 0.0
```

But note: even at 0.0, you may get slightly different results across runs due to Ollama's internal batching. Some variance (1–2 tests flipping) is normal. Consistent failures across 3+ runs are a real signal.

### "[warn] refiner wrote banned phrase 'here is'"

The refiner is not good enough at following instructions. It keeps writing banned phrases like "Here is the improved prompt:" into the prompts, which the system rejects.

Fix:
```bash
python model_eval/eval.py ... --refiner qwen2.5:7b
# or
python model_eval/eval.py ... --refiner qwen3.5:9b
```

A larger refiner is much better at following the strict rules.

### "No prompt changes" / refinement never happens

If the refiner produces no valid updates across all iterations, the prompts stay at the default. Check:
1. Is the refiner model too small? Try a 7b+ model.
2. Is the failing test actually fixable by prompt changes? (Or is it a model ceiling?)
3. Check the `[warn]` messages in the terminal — they explain exactly why each refinement was rejected.

### Both models fail the same test

When both Model A and Model B fail the same test consistently, even after refinement, that test is likely exposing a **model capability ceiling** — something neither of these models can do. Your options:
- Accept the limitation and find a different, larger model
- Remove that test from the battery if it is not critical to your use case
- Switch to a model that specializes in that language or task

### hi_01 always fails for qwen2.5

This is a **known and documented limitation**. The word "मतलब" is extremely common in Hindi speech, and `qwen2.5:3b` does not reliably remove it even when explicitly instructed to. This is not a prompt engineering problem — the model simply cannot do it consistently at this size.

**Solution:** Use `llama3-hindi-8b` for Hindi tasks. It handles "मतलब" correctly and achieves 100% on Hindi tests.

---

## 15. Lessons Learned from Testing

These are real findings from actual evaluation runs, documented here so you do not have to rediscover them.

### Model performance profiles

**`qwen2.5:3b` — excellent for English, poor for Hindi**
- English pass rate: 100% consistently
- Hindi pass rate: 67% — `hi_01` always fails due to the "मतलब" ceiling
- Very fast inference
- Not suitable as its own refiner (too small, writes banned phrases)

**`SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest` — excellent for Hindi, inconsistent for English**
- Hindi pass rate: 100%
- English pass rate: 71%–100% (varies by run, averages around 85%)
- Slower inference due to larger size
- Good at following complex Hindi instructions

### Refiner findings

- Using `qwen2.5:3b` as its own refiner rarely produces improvements. It often writes banned phrases into the prompts, causing every refinement to be silently rejected.
- Using `qwen3.5:9b` as the refiner was the first time the llama3-hindi model achieved a perfect 100% on all 10 tests. The improvement was significant and immediate.
- The rollback mechanism has prevented bad outcomes many times — later iterations that introduced regressions were automatically rolled back without any manual intervention needed.

### Technical findings

- **Devanagari word-boundary matching** requires special handling. Python's `\b` (word boundary) only works with ASCII characters. Unicode patterns (Hindi words) fall back to plain substring matching in the code, which is the correct behavior.
- **Latin characters mixed with Devanagari** in translation output is a reliable signal of transliteration garbage (e.g., the model transliterating "pipeline" as "पाइलाइच" instead of using the accepted Hindi term "पाइपलाइन"). The hard rule that detects this is one of the most useful safety checks.

### Recommendation from testing

**Use a dual-model setup:**

| Language | Model |
|---|---|
| English (and Hinglish) | `qwen2.5:3b` |
| Hindi | `SL-Lexicons/llama3-hindi-8b-q5_km.gguf:latest` |

This gives you 100% English and 100% Hindi rather than one model that mediocrely handles both. The main app (`config.json`) already supports this dual-model configuration via `OLLAMA_MODELS.en` and `OLLAMA_MODELS.hi`.

---

*Last updated: May 2026. Run eval again after adding new test cases or pulling new model versions.*
