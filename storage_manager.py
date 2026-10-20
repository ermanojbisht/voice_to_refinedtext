"""Unified Storage Manager & Garbage Cleaner for Voice Refiner and Audio to Ideas.

Handles:
- Centralized notes directory (MARKDOWN_PATH, default: ~/Documents/VoiceNotes)
- Dedicated Audio to Ideas output directory (~/Documents/VoiceNotes/AudioToIdeas)
- Internal cache isolation (~/.cache/voice_refiner/ without polluting source folders)
- Unique naming pattern: YYYYMMDD_HHMMSS_<stem>
- Metadata tracking (.meta.json)
- Automatic and on-demand cache / temporary file garbage collection
"""
import os
import re
import json
import time
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.is_file():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_notes_dir() -> Path:
    cfg = load_config()
    raw = cfg.get("MARKDOWN_PATH") or "~/Documents/VoiceNotes"
    p = Path(os.path.expanduser(raw)).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_audio_to_idea_output_dir() -> Path:
    p = get_notes_dir() / "AudioToIdeas"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cache_dir() -> Path:
    cache_base = Path(os.path.expanduser("~/.cache/voice_refiner"))
    cache_base.mkdir(parents=True, exist_ok=True)
    return cache_base


def sanitize_stem(text: str) -> str:
    cleaned = re.sub(r"[^\w\-_]", "_", text).strip("_")
    return cleaned[:32] if cleaned else "clip"


def generate_session_id(stem: str = "dictation") -> str:
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_stem = sanitize_stem(stem)
    return f"{now_str}_{clean_stem}"


def save_session_metadata(
    output_dir: Path,
    session_id: str,
    meta_dict: Dict[str, Any]
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / f"{session_id}.meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_dict, f, indent=2, ensure_ascii=False)
    return meta_path


def save_dictation_session(
    raw_text: str,
    refined_text: str,
    duration_s: float = 0.0,
    preset: str = "",
    goal: str = "",
    model: str = "",
    wav_path: Optional[str] = None,
    save_markdown: Optional[bool] = None
) -> Dict[str, Any]:
    cfg = load_config()
    should_save = cfg.get("SAVE_TO_MARKDOWN", True) if save_markdown is None else save_markdown
    notes_dir = get_notes_dir()
    session_id = generate_session_id("dictation")
    now_iso = datetime.datetime.now().isoformat()

    saved_files = {}

    # 1. Save Markdown Note if enabled
    if should_save:
        md_file = notes_dir / f"{session_id}.md"
        content = (
            f"# Dictation Note — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"> **Stage 1 (🎙 Preset)**: `{preset or 'default'}`  \n"
            f"> **Stage 2 (✨ Goal)**: `{goal or 'default'}`  \n"
            f"> **Duration**: `{duration_s:.1f}s` · **Words**: `{len(refined_text.split())}`\n\n"
            f"## ✨ Refined Output\n\n{refined_text}\n\n"
        )
        if raw_text and raw_text.strip() != refined_text.strip():
            content += f"## 🎙️ Raw Speech\n\n{raw_text}\n"
        
        md_file.write_text(content, encoding="utf-8")
        saved_files["refined_note"] = str(md_file)

    # 2. Save Raw Transcript file
    if raw_text:
        raw_file = notes_dir / f"{session_id}_raw.txt"
        raw_file.write_text(raw_text, encoding="utf-8")
        saved_files["raw_transcript"] = str(raw_file)

    # 3. Copy Audio if present and configured
    if wav_path and os.path.isfile(wav_path):
        audio_dir = notes_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        dest_wav = audio_dir / f"{session_id}.wav"
        try:
            shutil.copy2(wav_path, dest_wav)
            saved_files["audio"] = str(dest_wav)
        except Exception:
            pass

    # 4. Save metadata JSON
    meta = {
        "id": session_id,
        "created_at": now_iso,
        "source_type": "microphone",
        "duration_seconds": round(duration_s, 2),
        "word_count": len(refined_text.split()),
        "asr_preset": preset,
        "refinement_goal": goal,
        "model": model,
        "files": saved_files
    }
    meta_path = save_session_metadata(notes_dir, session_id, meta)
    saved_files["metadata"] = str(meta_path)

    return {"session_id": session_id, "files": saved_files}


def clean_garbage(retention_days: int = 7) -> Dict[str, Any]:
    """Cleans up stale cache chunks, temporary wav files, and old workspaces.
    
    Protects actual user output notes, transcripts, and final media files.
    """
    cutoff_time = time.time() - (retention_days * 86400)
    cleaned_bytes = 0
    removed_files = 0
    removed_dirs = 0

    # 1. Clean ~/.cache/voice_refiner
    cache_base = get_cache_dir()
    if cache_base.exists():
        for root, dirs, files in os.walk(cache_base, topdown=False):
            for f in files:
                fp = Path(root) / f
                try:
                    st = fp.stat()
                    if st.st_mtime < cutoff_time:
                        cleaned_bytes += st.st_size
                        fp.unlink(missing_ok=True)
                        removed_files += 1
                except Exception:
                    pass
            for d in dirs:
                dp = Path(root) / d
                try:
                    if not any(dp.iterdir()):
                        dp.rmdir()
                        removed_dirs += 1
                except Exception:
                    pass

    # 2. Clean temporary /tmp/.audio2idea-* directories
    tmp_path = Path("/tmp")
    for p in tmp_path.glob(".audio2idea-*"):
        try:
            st = p.stat()
            if st.st_mtime < cutoff_time:
                if p.is_dir():
                    size = sum(f.stat().st_size for f in p.glob("**/*") if f.is_file())
                    cleaned_bytes += size
                    shutil.rmtree(p, ignore_errors=True)
                    removed_dirs += 1
                else:
                    cleaned_bytes += st.st_size
                    p.unlink(missing_ok=True)
                    removed_files += 1
        except Exception:
            pass

    # 3. Clean legacy project-local .audio2idea caches if older than cutoff (or any .audio2idea in project)
    for p in SCRIPT_DIR.rglob(".audio2idea"):
        try:
            if p.is_dir():
                size = sum(f.stat().st_size for f in p.glob("**/*") if f.is_file())
                cleaned_bytes += size
                shutil.rmtree(p, ignore_errors=True)
                removed_dirs += 1
        except Exception:
            pass

    # 4. Clean stray legacy text/meta files in benchmarks/recordings
    benchmarks_dir = SCRIPT_DIR / "benchmarks" / "recordings"
    if benchmarks_dir.is_dir():
        for f in benchmarks_dir.glob("*"):
            if f.suffix in {".txt", ".json"} and not f.name.endswith(".wav"):
                try:
                    cleaned_bytes += f.stat().st_size
                    f.unlink(missing_ok=True)
                    removed_files += 1
                except Exception:
                    pass

    return {
        "ok": True,
        "removed_files": removed_files,
        "removed_dirs": removed_dirs,
        "freed_bytes": cleaned_bytes,
        "freed_mb": round(cleaned_bytes / (1024 * 1024), 2),
        "retention_days": retention_days
    }
