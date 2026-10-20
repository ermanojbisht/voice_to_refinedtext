### How to Inspect and Switch Between Versions

  • To see a summary of all files changed compared to the original main branch:
    git diff --stat main..after_hany_new_update

  • To inspect the exact line-by-line diff against the original:
    git diff main..after_hany_new_update

  • To switch back to the original untouched version:
    git checkout main

  • To return to this feature branch with all new capabilities:
    git checkout after_hany_new_update







 ### Verification Across All 7 System Pillars

   Component                         | Tested Functionality                                                                                               | Status
  -----------------------------------|--------------------------------------------------------------------------------------------------------------------|--------------------------------
   1. Normal Mic Dictation           | Pressing the global hotkey (Ctrl+Space), mic capture, audio quality gate, audio chimes (start.oga/end.oga), 3-     | ✅ Fully Replicated & Verified
                                     | portion acoustic LangID check, user preset preservation (no silent swaps), non-blocking notify-send desktop        |
                                     | advisory, and clipboard auto-copy (xclip).                                                                         |
   2. PWD Terminology Normalizer     | Pre-LLM phonetics (EE and JE, DFO office, culvert widening, earthwork quantity) normalizing spoken distortions     | ✅ Fully Replicated & Verified
                                     | before prompt assembly.                                                                                            |
   3. Audio-to-Ideas Web Studio      | File upload, batch queue management, audio scrubbing player, manifest persistence, live progress tracking (stage:  | ✅ Fully Replicated & Verified
                                     | acoustic_analysis), queue card suggestion badges ([💡 Suggested: Smart Bilingual]), and editable transcript        |
                                     | revisions.                                                                                                         |
   4. Refiner Dashboard              | Visual status aura, live polling via /api/refiner/status, raw speech toggle, history list, suggestion banner, and  | ✅ Fully Replicated & Verified
                                     | 🔁 Re-process with {suggested_preset} one-click re-run.                                                            |
   5. Evening Review Studio          | Session initialization, daily streak tracking, 6-step prompt guidance, live mic dictation, site audio attachments  | ✅ Fully Replicated & Verified
                                     | (.wav, .mp3, .m4a), staged clips inline editing, acoustic suggestion alerts, and Obsidian note compilation.        |
   6. Decoupled Preset & Goal Matrix | Independent selection of Stage 1 ASR Preset (speech decoder) and Stage 2 Refinement Goal (LLM prompt/model         | ✅ Fully Replicated & Verified
                                     | selection) with full backward compatibility.                                                                       |
   7. Global Hotkey Management       | Single-source-of-truth configuration via config.json without hardcoding (Ctrl+Space).                              | ✅ Fully Replicated & Verified
  ──────
  ### Test Suite Execution
  • 191 unit and integration tests passed (0 failures, 12 skipped, 8 warnings in 36.20s).
  • End-to-end integration script passed across all 7 operational workflows without error.





1. Normal Mic Dictation
2. PWD Terminology Normalizer
3. Audio-to-Ideas Web Studio
4. Refiner Dashboard
5. Evening Review Studio 












can you explain how prompting is done , logic behind

▸ Thought for 8s
  Prompting employs a two-tiered architecture. The first tier uses pre-defined, model-specific templates, serving as a foundation. The second tier dynamically assembles a granular prompt...
  The prompting system in AI Voice Refiner uses a Two-Tier Architecture:

  1. Tier 1: Static Model-Specific Overrides (hand-tuned templates in prompts/<model>/<mode>.txt)
  2. Tier 2: The 4D Modular "Lego" Engine (utils.build_granular_prompt())

  Here is a comprehensive breakdown of how prompts are resolved, assembled, and protected against hallucinations.
  ──────
  ### 1. High-Level Prompt Resolution Pipeline
  When you speak, the text flows through the resolution logic in utils.get_prompt_and_stops():
  ┌──────────────────────────────────────────┐   ┌────────────────────────────────┐   ┌───────────────────────────────┐
  │                                          │   │                                │   │                               │
  │  Raw Speech Transcription + Active Goal  │   │       C -- "File Found"        │   │      C -- "No File Found"     │
  │                                          │   │                                │   │                               │
  └─────────────────────┬────────────────────┘   └────────────────┬───────────────┘   └───────────────┬───────────────┘
                        │                                         │                                   │
                        ▼                                         ▼                                   ▼
  ┌──────────────────────────────────────────┐   ┌────────────────────────────────┐   ┌───────────────────────────────┐
  │                                          │   │                                │   │                               │
  │        1. Model Alias Resolution         │   │     Format Static Template     │   │ 2. Assemble 4D Modular Prompt │
  │                                          │   │                                │   │                               │
  │     (qwen2_5, llama3_hindi, default)     │   │ template.format(text=raw_text) │   │ utils.build_granular_prompt() │
  │                                          │   │                                │   │                               │
  └─────────────────────┬────────────────────┘   └────────────────┬───────────────┘   └───────────────┬───────────────┘
                        │                                         │                                   │
                        ▼                                         ▼                                   │
  ┌──────────────────────────────────────────┐   ┌────────────────────────────────┐                   │
  │                                          │   │                                │                   │
  │       C{"Check Custom Prompt File?       │   │  3. Attach Model Stop Tokens   │                   │
  │                                          │   │                                │◄──────────────────┘
  │ e.g. prompts/default/ideas_actions.txt"} │   │   (from prompts/stops.json)    │
  │                                          │   │                                │
  └──────────────────────────────────────────┘   └────────────────┬───────────────┘
                                                                  │
                                                                  │
  ┌──────────────────────────────────────────┐                    │
  │                                          │                    │
  │         Send to Local Ollama LLM         │◄───────────────────┘
  │                                          │
  └──────────────────────────────────────────┘
  ──────
  ### 2. The Logic Behind the 4 Orthogonal Dimensions

  Instead of writing dozens of fragile prompt combinations, any document requirement is decomposed into 4 independent dimensions defined in config.json under REFINEMENT_GOALS:

   Dimension                        | Options                                                  | Engineering Purpose
  ----------------------------------|----------------------------------------------------------|-------------------------------------------------------------------------------------------
   1. Target Language (target_lang) | pure_english, pure_hindi, bilingual, roman_hinglish,     | Enforces output language and script (e.g. Latin English, Devanagari Hindi, or WhatsApp-
                                    | same_as_input                                            | style Roman Hinglish).
   2. Document Intent (intent)      | clean_paragraph, concise_summary, ideas_actions          | Dictates document structure: narrative paragraphs, executive bullets, or task matrices.
   3. Acronym Policy (acronyms)     | preserve_latin, devanagari_phonetic                      | Protects codal civil engineering terms (EE, AE, JE, NIT, MB, RCC, SOR) from being
                                    |                                                          | translated into awkward or corrupted words.
   4. Action Mode (action)          | refine_only, translate_and_refine                        | Decides whether the model should only fix grammar or perform cross-lingual translation.
  ──────
  ### 3. Modular "Lego" Prompt Construction

  In utils.build_granular_prompt(), these 4 dimensions are dynamically stacked into four distinct prompt blocks:

    ┌───────────────────────────────────────────────────────────┐
    │ 1. Intent Block (e.g. Extract tasks & responsible roles)   │
    ├───────────────────────────────────────────────────────────┤
    │ 2. Language & Script Block (e.g. Keep speaker's language) │
    ├───────────────────────────────────────────────────────────┤
    │ 3. Acronym & Terminology Policy (e.g. Keep EE, MB in Latin)│
    ├───────────────────────────────────────────────────────────┤
    │ 4. Strict Groundedness Contract (Zero-Hallucination Rule) │
    ├───────────────────────────────────────────────────────────┤
    │ SPEECH TRANSCRIPTION:                                     │
    │ {raw_text}                                                │
    │                                                           │
    │ REFINED OUTPUT:                                           │
    └───────────────────────────────────────────────────────────┘
  #### Why This Works Better Than Monolithic Prompts:

  • If you change the Document Intent from a paragraph to ideas_actions, the terminology rules and script constraints stay intact.
  • If you switch the Target Language from English to Hindi, the task extraction instructions remain unchanged.
  ──────
  ### 4. Model Selection Logic (Matching Prompt to Model Capabilities)

  The engine in engine.py:413-433 intelligently routes prompts based on the model's strengths:
  ┌──────────────────────────────────────────────────┐   ┌──────────────────────────────────────┐
  │                                                  │   │                                      │
  │           Active Goal / 4D Attributes            ├──►│ B{"Is Target Language Pure Hindi?"}  │
  │                                                  │   │                                      │
  └──────────────────────────────────────────────────┘   └──────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐   ┌──────────────────────────────────────┐
  │                                                  │   │                                      │
  │                                                  │   │     SL-Lexicons/Llama-3-Hindi-8B     │
  │                                                  │   │                                      │
  │    B -- "Yes (Official Administrative Hindi)"    ├──►│   • Rich formal Devanagari grammar   │
  │                                                  │   │                                      │
  │                                                  │   │    • High administrative fluency     │
  │                                                  │   │                                      │
  └──────────────────────────────────────────────────┘   └──────────────────────────────────────┘


  ┌──────────────────────────────────────────────────┐   ┌──────────────────────────────────────┐
  │                                                  │   │                                      │
  │                                                  │   │              Qwen2.5-3B              │
  │                                                  │   │                                      │
  │                                                  │   │        • Fast (<0.8s latency)        │
  │ B -- "No (Bilingual, English, or Ideas/Actions)" ├──►│                                      │
  │                                                  │   │   • Superior instruction following   │
  │                                                  │   │                                      │
  │                                                  │   │ • Highly factual / low hallucination │
  │                                                  │   │                                      │
  └──────────────────────────────────────────────────┘   └──────────────────────────────────────┘

  • Qwen 2.5 (3B) is the default for ideas_actions, concise_summary, and bilingual transcription because small instruction-tuned models follow strict negative constraints exceptionally
  well without inventing creative stories.
  • Llama 3 Hindi (8B) is reserved for pure formal administrative Hindi translation where native linguistic nuance is paramount.
  ──────
  ### 5. Why Hallucinations Occur & The "Parenthetical Priming Trap"

  In LLM prompt engineering, small language models suffer from creative completion if given unconstrained section headers.

  #### The Flawed Prompt Pattern (What caused the bridge hallucination):

    Extract Action Items (e.g. EE, AE, JE) with stated deadlines.
    List Blockers (e.g. forest clearance, utility shifting, weather).

  When fed general speech like "Typing in Hindi gives better quality", the LLM saw no tasks in the input. Because the prompt lacked an explicit instruction on what to do when no tasks are
  mentioned, the model assumed the parenthetical examples were mandatory facts and hallucinated:

  • Task: Obtain SOR for bridge (JE)
  • Blocker: Forest clearance & utility shifting

  #### The Grounded Solution (Negative Constraint Pattern):

    STRICT GROUNDEDNESS & ZERO-HALLUCINATION RULES:
    1. Base all output STRICTLY AND ONLY on the provided transcription.
    2. DO NOT invent, assume, or fabricate any tasks, roles, or deadlines not explicitly mentioned.
    3. If the transcription does NOT contain any actionable tasks (conversational speech, general opinion):
       - Key Message: <factual summary of what was actually said>
       - Action Items: None mentioned in transcript.
       NEVER fabricate fictional civil works, roles, or deadlines.
  With this negative constraint in place:

  • Speech with tasks → Extracted cleanly.
  • General conversational speech → Truthfully reports "Action Items: None mentioned in transcript".
  ──────
  ### 6. Post-Processing & Normalization
  Once the LLM generates a response, utils.clean_response() and pwd_helper.normalizer execute automated cleanup:

  1. Stop Token Truncation: Strips prompt remnants or conversational tags defined in stops.json.
  2. Markdown Code Fence Stripping: Removes backticks (```) so the output is ready to paste directly into documents.
  3. Departmental Acronym Capitalization: Corrects cases like ee → EE, nit → NIT, mb → MB.









so how to use skill ? what those keys means --scripts script1 --goals official_english,clean_bilingual

  ### 🛠 How to Use the asr-role-evaluator Skill & Command Breakdown
  The skill allows you or an AI agent to run targeted quality audits whenever you tweak an ASR model, prompt, or role. You don't have to test all 10 audio files or wait minutes—you can
  test exactly what you need.
  ──────
  ### 1. What the Command Flags Mean

  Take this command as an example:
    .venv/bin/python benchmarks/unified_benchmark.py --scripts script1 --goals official_english,clean_bilingual

  #### --scripts script1
  • What it means: Specifies which recorded audio file from benchmarks/recordings/ to evaluate.
  • Available choices: Any script from script1 to script10:
      • script1: English Technical Speech (System & Manual Governance)
      • script2: English Engineering Inspection (Bridge bearings, M35 grade, load test)
      • script3: Formal Administrative Hindi (Chief Engineer directive to Executive Engineers)
      • script4: Hill Road Engineering in Hindi (Tarring, widening, landslides)
      • script5: Code-Mixed Site Speech (Hinglish: site visit, bridge foundation, EE, JE, MB)
      • script6: Abbreviations Heavy Speech (MB, NIT, SOR, culvert)
      • script7: Conversational Hinglish (Tender review, earnest money deposit)
      • script8 to script10: Extended site & measurement cases.
  • Multiple scripts: You can pass a comma-separated list like --scripts script1,script3,script5 or omit it to run all representative files.
  ──────
  #### --goals official_english,clean_bilingual
  • What it means: Specifies which Refinement Roles / 4D Goals to run the transcript through.
  • Available choices:
      1. official_english:
          • 4D Spec: Target = pure_english | Intent = clean_paragraph | Acronyms = preserve_latin | Action = translate_and_refine.
          • What it tests: Does it translate Hindi into formal administrative English while keeping PWD terms?
      2. official_hindi:
          • 4D Spec: Target = pure_hindi | Intent = clean_paragraph | Acronyms = preserve_latin | Action = translate_and_refine.
          • What it tests: Does it translate English into formal Devanagari Hindi using Llama-3 Hindi without infinite loops?
      3. clean_bilingual:
          • 4D Spec: Target = bilingual | Intent = clean_paragraph | Acronyms = preserve_latin | Action = refine_only.
          • What it tests: Does it maintain natural code-mixing without force-translating?
      4. concise_summary:
          • 4D Spec: Target = same_as_input | Intent = concise_summary | Action = refine_only.
          • What it tests: Does it generate a 1-paragraph overview + 3-5 bullet points?
      5. ideas_actions:
          • 4D Spec: Target = same_as_input | Intent = ideas_actions | Action = refine_only.
          • What it tests: Does it extract [Action Item], [Responsible Role], and [Timeline]?
      6. roman_hinglish:
          • 4D Spec: Target = roman_hinglish | Intent = clean_paragraph | Action = refine_only.
          • What it tests: Does it write 100% in Latin script (WhatsApp style) with 0 Devanagari characters?

  ──────
  #### Optional Extra Flags

  • --asrs instant_english,smart_bilingual: Test specific ASR models instead of auto-pairing.
  • --force-asr: Re-transcribe from raw .wav audio instead of using the cache.
  • --dry-run: Run in 0.01 seconds without calling Ollama (validates audio files, regex rules, and specifications).
  ──────
  ### 2. How to Use the Skill (Step-by-Step Scenarios)
  #### Scenario A: You changed a Prompt in prompts/ or utils.py and want to verify you didn't break anything
  Run a quick 2-script regression check:

    .venv/bin/python benchmarks/unified_benchmark.py --scripts script1,script5 --goals official_english,clean_bilingual

  • What it tells you:
      • ✅ JUSTIFIED: Your prompt change is good! All numbers, dates, and PWD terms are preserved.
      • ❌ 2 ISSUES: Shows exactly what broke (e.g. "Missing mandatory technical term: 'M35'" or "Devanagari leaked into English memo").

  ──────
  #### Scenario B: You want to test if a new local LLM model works for Hindi
  1. Update config.json's OLLAMA_MODELS.hi to your new model.
  2. Run the test against a Hindi directive:
    .venv/bin/python benchmarks/unified_benchmark.py --scripts script3 --goals official_hindi
  • What it checks:
      • Does the model generate proper Hindi grammar?
      • Does it keep civil terms like EE, JE, MB?
      • Did it finish in under 12 seconds without token repetition loops?
  ──────
  #### Scenario C: Asking the AI Agent to Use the Skill

  Because this is registered as an Antigravity Skill in .agents/skills/asr-role-evaluator/SKILL.md, you can simply ask me in plain English:

  │ "Evaluate how script5 performs when converted to action items."
  │ or
  │ "Check if our Roman Hinglish prompt leaks Devanagari characters on script7."
  I will automatically invoke the skill, run the assertion engine, and present the pass/fail scorecard and latency metrics directly to you!

