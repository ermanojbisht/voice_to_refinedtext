import os
import json
import re
import logging
import subprocess
from typing import Tuple, Set, Any, Optional
import requests
from langdetect import detect, DetectorFactory
from audio_to_idea.resources import legacy_inference

# Ensure consistent language detection
DetectorFactory.seed = 0

def load_config(script_dir):
    """Loads config.json or returns defaults."""
    config_path = os.path.join(script_dir, "config.json")
    default_config = {
        "GLOBAL_HOTKEY": "Ctrl+Space",
        "SAMPLE_RATE": 16000,
        "WHISPER_MODEL": "large-v3-turbo",
        "OLLAMA_MODELS": {
            "en": "qwen3.5:0.8b",
            "hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_TRANSLATE_MODELS": {
            "to_en": "qwen2.5:3b",
            "to_hi": "mashriram/sarvam-1:latest"
        },
        "OLLAMA_HOST": "http://localhost:11434",
        "SILENCE_THRESHOLD": 300,
        "SILENCE_DURATION": 2,
        "TEMPERATURE": 0.1,
        "MODE": "refine",  # Options: "refine", "translate"
        "LANGUAGE_MODE": "bilingual",  # Options: "bilingual", "pure_english", "pure_hindi", "roman_hinglish"
        "SAVE_TO_MARKDOWN": False,
        "MARKDOWN_PATH": "~/Documents/VoiceNotes",
        "DIRECT_TYPING": False,
        "FEATURES": {
            "start_end_sounds": True,
            "clipboard_output": True,
            "markdown_output": False,
            "direct_typing": False,
            "evening_review": True,
        }
    }
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                user_config = json.load(f)
                # Handle dictionary merge for nested configs
                for key in ["OLLAMA_MODELS", "OLLAMA_TRANSLATE_MODELS", "FEATURES"]:
                    if key in user_config and isinstance(user_config[key], dict):
                        default_config[key].update(user_config[key])
                        user_config.pop(key)
                
                # Merge remaining user config
                default_config.update(user_config)
                return default_config
            except:
                return default_config
    return default_config

def get_model_for_lang(config, lang):
    """Returns the correct model for the detected language in 'refine' mode."""
    models = config.get("OLLAMA_MODELS", {})
    return models.get(lang, config.get("OLLAMA_MODEL", "qwen2.5:3b"))

def get_translate_model(config, source_lang):
    """Returns the correct model for translation based on the target language."""
    target_key = "to_en" if source_lang == "hi" else "to_hi"
    trans_models = config.get("OLLAMA_TRANSLATE_MODELS", {})
    return trans_models.get(target_key, get_model_for_lang(config, source_lang))

# Unambiguous Hindi / Hinglish markers and grammar particles (strictly excluding English word collisions)
UNAMBIGUOUS_HINGLISH_WORDS = {
    'aaj', 'kal', 'kiya', 'karein', 'karna', 'karke', 'chahiye',
    'hona', 'hota', 'hoti', 'hote', 'sahab', 'kyunki', 'isliye', 'lekin',
    'magar', 'kuch', 'baat', 'apna', 'apni', 'apne', 'bhi', 'wala', 'wali',
    'wale', 'gaya', 'gayi', 'gaye', 'raha', 'rahi', 'rahe', 'dekh', 'dekha',
    'bhejo', 'bheja', 'diya', 'dijiye', 'karo', 'kariye', 'hain', 'tha',
    'thi', 'batao', 'boliye', 'bola', 'boli', 'baithak', 'nirikshan',
    'yojna', 'sadak', 'pariyojna', 'adhisashi', 'sahayak', 'mukhya'
}
COMMON_HINDI_PARTICLES = {'hai', 'aur', 'ho', 'ka', 'ke', 'ki', 'ko', 'se', 'ne', 'mein'}


def classify_speech_language(text: str) -> str:
    """Classifies speech transcript into linguistic categories:
    - 'pure_english': English speech without Hindi vocabulary.
    - 'pure_hindi': Devanagari Hindi text.
    - 'mixed_devanagari_hinglish': Devanagari script code-mixed with English technical terms.
    - 'roman_hinglish': Latin alphabet containing Hindi words/grammar.
    """
    if not text or not text.strip():
        return 'pure_english'

    devanagari_chars = len(re.findall(r'[\u0900-\u097f]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = devanagari_chars + latin_chars
    if total_chars == 0:
        return 'pure_english'

    if devanagari_chars > 0:
        if latin_chars == 0 or (devanagari_chars / total_chars > 0.85):
            return 'pure_hindi'
        return 'mixed_devanagari_hinglish'

    # Check for Roman Hinglish patterns in 100% Latin text
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', text)]
    if not words:
        return 'pure_english'

    unambiguous_count = sum(1 for w in words if w in UNAMBIGUOUS_HINGLISH_WORDS)
    particle_count = sum(1 for w in words if w in COMMON_HINDI_PARTICLES)

    if unambiguous_count >= 1 or particle_count >= 2:
        return 'roman_hinglish'

    return 'pure_english'


def detect_lang(text):
    """Detects primary language code: 'hi' or 'en'."""
    try:
        speech_class = classify_speech_language(text)
        if speech_class in ["pure_hindi", "mixed_devanagari_hinglish", "roman_hinglish"]:
            return "hi"
        return "en"
    except Exception:
        return "en"

def resolve_model_alias(model_name, config=None):
    """Return the short alias used as the prompts/ folder name for a model.

    Lookup order:
    1. model_aliases in config: if model_name is a value, return the matching key.
    2. model_aliases in config: if model_name is already a key, return it as-is.
    3. Auto-generate: take the last path component, strip the :tag suffix,
       replace non-alphanumeric chars with _, lowercase, trim to 40 chars.

    This is the single source of truth for folder resolution so callers never
    need to manually sanitise model names.
    """
    if config:
        aliases = config.get("model_aliases", {})
        for alias, full_name in aliases.items():
            if full_name == model_name:
                return alias
        if model_name in aliases:
            return model_name
    # Auto-generate a short folder name from the model string
    name = model_name.split("/")[-1]          # last path segment
    name = name.split(":")[0]                  # drop :tag
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return name[:40]


def ensure_model_prompts(script_dir, model_name, config=None):
    """Create a prompts/<alias>/ folder for a model if one does not yet exist.

    Copies the four template files from prompts/default/ as a starting point,
    then adds a default stop-token entry to stops.json.  Safe to call every
    time settings are saved — it is a no-op when the folder already exists.

    Returns the alias string that was used as the folder name.
    """
    import shutil
    alias = resolve_model_alias(model_name, config)
    prompts_dir = os.path.join(script_dir, "prompts")
    model_dir   = os.path.join(prompts_dir, alias)

    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        default_dir = os.path.join(prompts_dir, "default")
        for fname in (
            "en.txt", "hi.txt", "translate_en.txt", "translate_hi.txt",
            "bilingual.txt", "pure_english.txt", "pure_hindi.txt", "roman_hinglish.txt"
        ):
            src = os.path.join(default_dir, fname)
            dst = os.path.join(model_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            else:
                with open(dst, "w", encoding="utf-8") as fh:
                    fh.write("{text}\n")

    # Ensure stops.json has an entry for this alias
    stops_path = os.path.join(prompts_dir, "stops.json")
    try:
        with open(stops_path, "r", encoding="utf-8") as fh:
            stops = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        stops = {}
    if alias not in stops:
        default_stops = stops.get("default", {"hi": ["\n\n"], "en": ["\n\n"]})
        stops[alias] = {"hi": list(default_stops.get("hi", ["\n\n"])),
                        "en": list(default_stops.get("en", ["\n\n"]))}
        with open(stops_path, "w", encoding="utf-8") as fh:
            json.dump(stops, fh, ensure_ascii=False, indent=4)

    return alias


def build_granular_prompt(raw_text: str, goal_spec: dict, detected_lang: str = "en") -> str:
    """Assembles an LLM refinement prompt dynamically from 4 orthogonal dimensions:
    - target_lang: pure_english | pure_hindi | bilingual | roman_hinglish | same_as_input
    - intent: clean_paragraph | concise_summary | ideas_actions
    - acronyms: preserve_latin | devanagari_phonetic
    - action: refine_only | translate_and_refine
    """
    intent = goal_spec.get("intent", "clean_paragraph")
    target_lang = goal_spec.get("target_lang", "bilingual")
    acronym_policy = goal_spec.get("acronyms", "preserve_latin")
    action_mode = goal_spec.get("action", "refine_only")

    # 1. Document Intent Block
    if intent == "clean_paragraph":
        intent_rule = "Clean the transcript into clear, fluent, and well-structured professional paragraphs. Fix grammar and punctuation while removing verbal fillers and false starts."
    elif intent == "concise_summary":
        intent_rule = "Synthesize the transcript into a high-level executive summary: 1 brief overview paragraph followed by 2-4 concise bullet points highlighting key decisions and facts. If the transcript is conversational or brief without complex decisions, simply summarize what was stated without fabricating extra details."
    elif intent == "ideas_actions":
        intent_rule = "Extract concrete actionable tasks, decisions, and follow-ups. Format clearly with [Action Item], [Responsible Role/Person], and [Status/Timeline] where mentioned. If no explicit actionable tasks or deadlines were mentioned, state the core message and indicate 'No explicit action items mentioned' without fabricating fake engineering tasks or fictional deadlines."
    else:
        intent_rule = "Clean and refine the transcript into professional documentation."

    # 2. Target Language & Script Block
    if target_lang == "pure_english":
        lang_rule = "Write exclusively in professional ENGLISH (Latin script). Translate any Hindi or Hinglish speech into polished English."
    elif target_lang == "pure_hindi":
        lang_rule = "Write in formal, polished administrative HINDI (Devanagari script). Translate any English speech into formal Hindi."
    elif target_lang == "bilingual":
        lang_rule = "Maintain the natural bilingual flow: use Devanagari script for Hindi sentences and English Latin script for technical phrases and official nouns. Do NOT force-translate."
    elif target_lang == "roman_hinglish":
        lang_rule = (
            "CRITICAL SCRIPT REQUIREMENT:\n"
            "Write EXCLUSIVELY in LATIN SCRIPT (A-Z, English alphabet) in natural conversational Roman Hinglish (WhatsApp/Slack style).\n"
            "DO NOT use Devanagari script under any circumstances. Transliterate any Hindi words phonetically into Roman English characters."
        )
    else:  # same_as_input
        lang_rule = "Preserve the original language and script of the speaker. Do not translate across languages."

    # 3. Acronym & Technical Terminology Policy Block
    if acronym_policy == "preserve_latin":
        acronym_rule = (
            "PRESERVE TECHNICAL TERMS & ACRONYMS IN ENGLISH LATIN SCRIPT:\n"
            "Keep technical engineering terminology, departmental abbreviations, units, and software terms "
            "(e.g. EE, AE, JE, NIT, MB, RCC, M35, RA Bill, SOR, Server, Pipeline, Status, Site Visit, Concreting, Tender, BOQ) "
            "strictly in ENGLISH (Latin script). Do NOT invent awkward or archaic translations for established terms."
        )
    else:
        acronym_rule = "Write terms in the primary target script."

    # 4. Strict Contract & Truthfulness Block
    contract = (
        "STRICT CONSTRAINTS:\n"
        "- Base all statements strictly and exclusively on the input transcription.\n"
        "- Do NOT invent imaginary tasks, projects, roles, deadlines, risks, or advice not present in the transcription.\n"
        "- Preserve all factual numbers, dates, monetary amounts, and negative assertions.\n"
        "- Do NOT add conversational greetings ('Here is the...', 'Sure!'), intros, or conclusions.\n"
        "- Return ONLY the refined output text directly, without markdown code block backticks."
    )

    return f"{intent_rule}\n\n{lang_rule}\n\n{acronym_rule}\n\n{contract}\n\nSPEECH TRANSCRIPTION:\n{raw_text}\n\nREFINED OUTPUT:"


def get_prompt_and_stops(script_dir, model_name, text, lang, mode="refine", config=None):
    """Resolve the correct prompt template and stop tokens for a model and mode.

    Resolution order for prompt templates:
    1. Direct mode file check: e.g. bilingual.txt, pure_english.txt, roman_hinglish.txt
    2. Prefixed check: <mode>_<lang>.txt (e.g. translate_hi.txt).
    3. Lang fallback: <lang>.txt (e.g. en.txt, hi.txt).
    4. Dynamic 4D granular prompt assembly if mode is configured in REFINEMENT_GOALS.
    5. Fallback to raw '{text}'.
    """
    prompts_dir  = os.path.join(script_dir, "prompts")
    alias        = resolve_model_alias(model_name, config)
    model_subdir = model_name.replace("/", "_").replace(":", "_")

    search_dirs = []
    for candidate in (alias, model_subdir, "default"):
        path = os.path.join(prompts_dir, candidate)
        if os.path.exists(path) and path not in search_dirs:
            search_dirs.append(path)

    # 1. Direct mode/goal file check: e.g. clean_bilingual -> bilingual.txt
    prompt_template = None
    mode_candidates = [mode]
    goal_map = {
        "clean_bilingual": "bilingual",
        "official_english": "pure_english",
        "official_hindi": "pure_hindi",
        "concise_summary": "concise_summary",
        "ideas_actions": "ideas_actions",
        "roman_hinglish": "roman_hinglish",
    }
    if mode in goal_map and goal_map[mode] not in mode_candidates:
        mode_candidates.append(goal_map[mode])

    for m_cand in mode_candidates:
        named_mode_file = f"{m_cand}.txt"
        for sdir in search_dirs:
            candidate_path = os.path.join(sdir, named_mode_file)
            if os.path.exists(candidate_path):
                with open(candidate_path, "r", encoding="utf-8") as fh:
                    prompt_template = fh.read()
                break
        if prompt_template is not None:
            break

    # 2. Prefixed mode file check: e.g. translate_hi.txt
    if prompt_template is None and mode != "refine":
        prefixed_file = f"{mode}_{lang}.txt"
        for sdir in search_dirs:
            candidate_path = os.path.join(sdir, prefixed_file)
            if os.path.exists(candidate_path):
                with open(candidate_path, "r", encoding="utf-8") as fh:
                    prompt_template = fh.read()
                break

    # 3. Lang fallback check: e.g. en.txt or hi.txt
    if prompt_template is None:
        lang_file = f"{lang}.txt"
        for sdir in search_dirs:
            candidate_path = os.path.join(sdir, lang_file)
            if os.path.exists(candidate_path):
                with open(candidate_path, "r", encoding="utf-8") as fh:
                    prompt_template = fh.read()
                break

    if prompt_template is None:
        goals = (config or {}).get("REFINEMENT_GOALS", {})
        if mode in goals:
            prompt = build_granular_prompt(text, goals[mode], detected_lang=lang)
        else:
            prompt = text
    else:
        prompt = prompt_template.format(text=text)

    stops_path  = os.path.join(prompts_dir, "stops.json")
    stop_tokens = []

    if os.path.exists(stops_path):
        try:
            with open(stops_path, "r", encoding="utf-8") as fh:
                stops_data = json.load(fh)
            stop_tokens = (
                stops_data.get(model_name)
                or stops_data.get(alias)
                or stops_data.get(model_subdir)
                or stops_data.get("default", {})
            ).get(lang, [])
        except Exception:
            stop_tokens = []

    return prompt, stop_tokens

@legacy_inference
def call_ollama(host, model, prompt, stop_tokens, temperature=0.1, timeout=120, keep_alive="5m"):
    """Sends a request to Ollama and handles timeouts/errors."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "top_p": 0.9,
            "stop": stop_tokens
        }
        if keep_alive is not None:
            payload["keep_alive"] = str(keep_alive).strip()

        response = requests.post(
            f"{host}/api/generate",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}

def get_logger(name, log_file=None):
    """Return a named logger. Adds a FileHandler the first time log_file is provided.

    Call pattern:
        # at module level (no file yet):
        _logger = utils.get_logger("tray")
        # at startup when log path is known:
        utils.get_logger("tray", log_file="/path/to/review_debug.log")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger already configured — add file handler if newly provided
        if log_file and not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.addHandler(fh)
        return logger

    fmt = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def clean_response(text):
    """Strips <think> tags, markdown code blocks, prefixes, and surrounding quotes."""
    if not text:
        return ""

    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    # Strip markdown code blocks if wrapped
    text = re.sub(r'^```(?:text|markdown)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Strip conversational LLM introductory preambles (e.g. "Here's the revised text...", "Here is the polished...")
    text = re.sub(r'^(?:Here(?:\'s|\s+is)\s+[^\n]+[:\n]\s*)+', '', text, flags=re.IGNORECASE)

    prefixes_to_strip = [
        "Professional English:", "Cleaned text:", "Refined text:",
        "Refined English:", "Refined Hindi:",
        "Refined speech transcription:", "Refined transcription:",
        "I have refined the input speech transcription as follows:",
        "Sure! Here is the refined text:", "Here is the refined text:",
        "Here's the refined text:",
        "यहाँ सुधार हुआ पाठ है:", "शुद्ध रूप:", "संवाद:", "Raw:", "Output:",
        "The professional version of the text is:",
        "Correct and cleaned transcription:", "Correct and cleaned text:",
        "Correct and cleaned:", "यहाँ सुधार के लिए पाठ है:"
    ]

    for prefix in prefixes_to_strip:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()

    return text.strip()


# ── Global Hotkey Utilities ───────────────────────────────────────────────────

def get_global_hotkey(config: Optional[dict] = None, script_dir: Optional[str] = None) -> str:
    """Returns the configured global recording hotkey in display format (e.g. 'Ctrl+Space')."""
    if config is not None:
        raw = config.get("GLOBAL_HOTKEY")
        if raw:
            return format_hotkey_display(str(raw))
    if script_dir:
        cfg = load_config(script_dir)
        raw = cfg.get("GLOBAL_HOTKEY")
        if raw:
            return format_hotkey_display(str(raw))
    return "Ctrl+Space"


def format_hotkey_display(hotkey_str: str) -> str:
    """Canonical display string for hotkeys (e.g. 'Ctrl+Space', 'Ctrl+Alt+V')."""
    if not hotkey_str:
        return "Ctrl+Space"
    parts = re.findall(r'<([^>]+)>|([^+\s<>]+)', str(hotkey_str))
    tokens = [m[0].lower() if m[0] else m[1].lower() for m in parts if m[0] or m[1]]
    
    display_mods = []
    main_key = ""
    for tok in tokens:
        if tok in ("ctrl", "control", "primary"):
            if "Ctrl" not in display_mods:
                display_mods.append("Ctrl")
        elif tok == "alt":
            if "Alt" not in display_mods:
                display_mods.append("Alt")
        elif tok == "shift":
            if "Shift" not in display_mods:
                display_mods.append("Shift")
        elif tok in ("super", "win", "cmd"):
            if "Super" not in display_mods:
                display_mods.append("Super")
        elif tok in ("space", "spacebar"):
            main_key = "Space"
        elif tok in ("enter", "return"):
            main_key = "Enter"
        elif tok in ("esc", "escape"):
            main_key = "Esc"
        elif tok == "tab":
            main_key = "Tab"
        else:
            main_key = tok.upper() if len(tok) == 1 else tok.capitalize()
    
    if not main_key:
        main_key = "Space"
    if not display_mods:
        display_mods = ["Ctrl"]
    return "+".join(display_mods + [main_key])


def format_hotkey_gnome(hotkey_str: str) -> str:
    """Formats hotkey into GNOME custom keybinding syntax (e.g. '<Control>space', '<Control><Alt>v')."""
    parts = re.findall(r'<([^>]+)>|([^+\s<>]+)', str(hotkey_str))
    tokens = [m[0].lower() if m[0] else m[1].lower() for m in parts if m[0] or m[1]]
    gnome_mods = []
    main_key = ""
    for tok in tokens:
        if tok in ("ctrl", "control", "primary"):
            if "<Control>" not in gnome_mods:
                gnome_mods.append("<Control>")
        elif tok == "alt":
            if "<Alt>" not in gnome_mods:
                gnome_mods.append("<Alt>")
        elif tok == "shift":
            if "<Shift>" not in gnome_mods:
                gnome_mods.append("<Shift>")
        elif tok in ("super", "win", "cmd"):
            if "<Super>" not in gnome_mods:
                gnome_mods.append("<Super>")
        elif tok in ("space", "spacebar"):
            main_key = "space"
        elif tok in ("enter", "return"):
            main_key = "Return"
        elif tok in ("esc", "escape"):
            main_key = "Escape"
        elif tok == "tab":
            main_key = "Tab"
        else:
            main_key = tok.lower()

    if not main_key:
        main_key = "space"
    if not gnome_mods:
        gnome_mods = ["<Control>"]
    return "".join(gnome_mods) + main_key


def parse_hotkey(hotkey_str: str) -> Tuple[Set[str], Any]:
    """
    Parses a hotkey string into:
        (required_modifiers, trigger_key)
    where required_modifiers is a set of modifier group names: {'ctrl', 'alt', 'shift', 'super'}
    and trigger_key is either a pynput Key (e.g. Key.space) or a lowercase string char (e.g. 'v').
    """
    try:
        from pynput import keyboard
    except ImportError:
        keyboard = None

    parts = re.findall(r'<([^>]+)>|([^+\s<>]+)', str(hotkey_str))
    tokens = [m[0].lower() if m[0] else m[1].lower() for m in parts if m[0] or m[1]]
    modifiers = set()
    trigger_key = None

    for tok in tokens:
        if tok in ("ctrl", "control", "primary"):
            modifiers.add("ctrl")
        elif tok == "alt":
            modifiers.add("alt")
        elif tok == "shift":
            modifiers.add("shift")
        elif tok in ("super", "win", "cmd"):
            modifiers.add("super")
        elif tok in ("space", "spacebar"):
            trigger_key = getattr(keyboard.Key, "space", "space") if keyboard else "space"
        elif tok in ("enter", "return"):
            trigger_key = getattr(keyboard.Key, "enter", "enter") if keyboard else "enter"
        elif tok in ("esc", "escape"):
            trigger_key = getattr(keyboard.Key, "esc", "esc") if keyboard else "esc"
        elif tok == "tab":
            trigger_key = getattr(keyboard.Key, "tab", "tab") if keyboard else "tab"
        elif len(tok) == 1:
            trigger_key = tok.lower()
        elif keyboard and hasattr(keyboard.Key, tok):
            trigger_key = getattr(keyboard.Key, tok)
        else:
            trigger_key = tok.lower()

    if trigger_key is None:
        trigger_key = getattr(keyboard.Key, "space", "space") if keyboard else "space"
    if not modifiers:
        modifiers.add("ctrl")

    return modifiers, trigger_key


def is_modifier_key(key: Any) -> bool:
    """Returns True if the given pynput key is a modifier key."""
    try:
        from pynput import keyboard
        return key in (
            keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
            keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
        )
    except (ImportError, AttributeError):
        return False


def matches_hotkey(pressed_keys: Set[Any], current_key: Any, required_modifiers: Set[str], trigger_key: Any) -> bool:
    """Checks whether the currently pressed key and held modifiers match the target hotkey."""
    try:
        from pynput import keyboard
    except ImportError:
        return False

    # 1. Match trigger key
    if isinstance(trigger_key, keyboard.Key):
        if current_key != trigger_key:
            return False
    elif isinstance(trigger_key, str):
        c = getattr(current_key, "char", None)
        if not c or c.lower() != trigger_key.lower():
            return False
    else:
        if current_key != trigger_key:
            return False

    # 2. Check held modifier groups
    mod_groups = {
        "ctrl": (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r),
        "alt": (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r),
        "shift": (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r),
        "super": (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r),
    }

    for grp, keys in mod_groups.items():
        is_held = any(k in pressed_keys for k in keys)
        should_be_held = grp in required_modifiers
        if is_held != should_be_held:
            return False

    return True


def sync_system_hotkey(hotkey_str: str) -> bool:
    """
    If running under GNOME, automatically updates the 'VoiceToAI' custom keybinding
    in org.gnome.settings-daemon.plugins.media-keys to match hotkey_str.
    Returns True if successfully synchronized.
    """
    gnome_binding = format_hotkey_gnome(hotkey_str)
    try:
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True, text=True, timeout=2
        )
        if res.returncode != 0:
            return False

        paths = re.findall(r"'/org/gnome/[^']+'", res.stdout)
        target_path = None
        for p in paths:
            clean_p = p.strip("'")
            schema = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{clean_p}"
            name_res = subprocess.run(["gsettings", "get", schema, "name"], capture_output=True, text=True, timeout=1)
            cmd_res = subprocess.run(["gsettings", "get", schema, "command"], capture_output=True, text=True, timeout=1)
            name_val = name_res.stdout.strip("' \n")
            cmd_val = cmd_res.stdout.strip("' \n")
            if name_val == "VoiceToAI" or "tray_app.py" in cmd_val or "voice_to_ai_clipboard.py" in cmd_val:
                target_path = clean_p
                break

        if target_path:
            schema = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{target_path}"
            subprocess.run(["gsettings", "set", schema, "binding", gnome_binding], timeout=2)
            logging.info(f"Synchronized GNOME shortcut at {target_path} to {gnome_binding}")
            return True
    except Exception as e:
        logging.debug(f"GNOME shortcut sync skipped: {e}")
    return False

