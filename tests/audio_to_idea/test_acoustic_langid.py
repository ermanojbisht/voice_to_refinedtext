import os
import pytest
import numpy as np
from audio_to_idea.asr.acoustic_langid import AcousticLanguageDetector, get_acoustic_suggestion

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECORDINGS_DIR = os.path.join(SCRIPT_DIR, "benchmarks", "recordings")

def test_detect_pure_english():
    wav_path = os.path.join(RECORDINGS_DIR, "script1.wav")
    if not os.path.isfile(wav_path):
        pytest.skip("script1.wav not found")
        
    detector = AcousticLanguageDetector.get_instance()
    res = detector.detect(wav_path)
    assert res["ok"] is True
    assert res["detected_mode"] == "pure_english"
    assert res["avg_english_score"] > 0.80
    assert len(res["slices"]) == 3
    
    # Check suggestion logic
    sug_for_en = get_acoustic_suggestion(res, "instant_english")
    assert sug_for_en is None  # Compatible
    
    sug_for_hi = get_acoustic_suggestion(res, "instant_hindi")
    assert sug_for_hi is not None
    assert sug_for_hi["is_mismatch"] is True
    assert sug_for_hi["suggested_preset"] == "instant_english"

def test_detect_pure_hindi():
    wav_path = os.path.join(RECORDINGS_DIR, "script3.wav")
    if not os.path.isfile(wav_path):
        pytest.skip("script3.wav not found")
        
    detector = AcousticLanguageDetector.get_instance()
    res = detector.detect(wav_path)
    assert res["ok"] is True
    assert res["detected_mode"] == "pure_hindi"
    assert res["avg_hindi_score"] > 0.60
    
    # Check suggestion logic
    sug_for_en = get_acoustic_suggestion(res, "instant_english")
    assert sug_for_en is not None
    assert sug_for_en["is_mismatch"] is True
    assert sug_for_en["suggested_preset"] == "instant_hindi"
    
    # smart_bilingual has zero warning
    sug_for_bil = get_acoustic_suggestion(res, "smart_bilingual")
    assert sug_for_bil is None

def test_detect_mixed_bilingual():
    wav_path = os.path.join(RECORDINGS_DIR, "script5.wav")
    if not os.path.isfile(wav_path):
        pytest.skip("script5.wav not found")
        
    detector = AcousticLanguageDetector.get_instance()
    res = detector.detect(wav_path)
    assert res["ok"] is True
    assert res["detected_mode"] == "mixed_bilingual"
    
    sug = get_acoustic_suggestion(res, "instant_english")
    assert sug is not None
    assert sug["is_mismatch"] is True
    assert sug["suggested_preset"] == "smart_bilingual"

def test_short_audio_graceful_handling():
    detector = AcousticLanguageDetector.get_instance()
    # 0.1s silence
    tiny_audio = np.zeros(1600, dtype=np.float32)
    res = detector.detect(tiny_audio)
    assert res["ok"] is True
    assert res["detected_mode"] == "pure_english"
