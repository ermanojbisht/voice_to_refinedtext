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

