import json
import time
from pathlib import Path
import storage_manager


def test_storage_manager_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_manager, "CONFIG_PATH", tmp_path / "config.json")
    notes = storage_manager.get_notes_dir()
    audio_idea_out = storage_manager.get_audio_to_idea_output_dir()
    cache_dir = storage_manager.get_cache_dir()

    assert notes.exists()
    assert audio_idea_out.exists()
    assert cache_dir.exists()
    assert audio_idea_out.parent == notes


def test_save_dictation_session(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_manager, "CONFIG_PATH", tmp_path / "config.json")
    notes_dir = tmp_path / "TestNotes"
    (tmp_path / "config.json").write_text(json.dumps({
        "MARKDOWN_PATH": str(notes_dir),
        "SAVE_TO_MARKDOWN": True
    }), encoding="utf-8")

    res = storage_manager.save_dictation_session(
        raw_text="Hello world speech test",
        refined_text="Hello, world. Speech test.",
        duration_s=4.5,
        preset="instant_english",
        goal="official_english",
        model="qwen2.5:3b"
    )

    session_id = res["session_id"]
    files = res["files"]

    assert Path(files["refined_note"]).is_file()
    assert Path(files["raw_transcript"]).is_file()
    assert Path(files["metadata"]).is_file()

    meta = json.loads(Path(files["metadata"]).read_text(encoding="utf-8"))
    assert meta["id"] == session_id
    assert meta["asr_preset"] == "instant_english"
    assert meta["refinement_goal"] == "official_english"
    assert meta["duration_seconds"] == 4.5


def test_clean_garbage(tmp_path, monkeypatch):
    cache_base = tmp_path / "cache"
    cache_base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(storage_manager, "get_cache_dir", lambda: cache_base)

    old_file = cache_base / "old_chunk.wav"
    old_file.write_bytes(b"0" * 1024)
    old_mtime = time.time() - (10 * 86400)
    import os
    os.utime(old_file, (old_mtime, old_mtime))

    new_file = cache_base / "fresh_chunk.wav"
    new_file.write_bytes(b"0" * 512)

    stats = storage_manager.clean_garbage(retention_days=7)
    assert stats["ok"] is True
    assert not old_file.exists()
    assert new_file.exists()
    assert stats["freed_bytes"] >= 1024
