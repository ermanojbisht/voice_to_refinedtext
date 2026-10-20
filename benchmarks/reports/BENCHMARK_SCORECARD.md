# 📊 Unified PWD Voice Refiner Benchmark Scorecard

**Execution Timestamp:** `2026-10-20 11:15:15`  
**Total Matrix Evaluations:** `192` | **✅ Justified:** `8` | **❌ Codal Violations:** `184`

---

## 📈 Executive Summary Matrix

| Script | Category | ASR Preset | Goal / Mode | Status | Compatibility | Latency | Issues Encountered |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 3.64s | Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer' |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 4.94s | Hallucinated numeric figures not in speech: 24.5 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `suboptimal` | 5.45s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'M35'; Missing mandatory technical term: 'bearings'; Missing mandatory technical term: 'load test' |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 4.03s | Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `viable_but_slower` | 3.27s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `official_hindi` | ❌ **Violation** | `fundamentally_invalid` | 1.81s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 6.76s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `suboptimal` | 3.26s | ⚠️ *Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 2.59s | Missing mandatory technical term: 'JE' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 2.29s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 3.83s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Hallucinated numeric figures not in speech: 12 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 3.59s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 3.15s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 2.85s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `suboptimal` | 4.17s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 3.35s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 3.98s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 2.03s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 3.42s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 2.95s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 2.78s | Missing mandatory technical term: 'highway maintenance' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 2.94s | Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Hallucinated numeric figures not in speech: 8, 15 |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 3.19s | Missing mandatory technical term: 'highway maintenance' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 3.21s | Missing mandatory technical term: 'highway maintenance' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 3.35s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 2.39s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 15 |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 3.76s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 15 |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 3.51s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `official_hindi` | ❌ **Violation** | `optimal` | 4.18s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `official_hindi` | ❌ **Violation** | `optimal` | 3.12s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `official_hindi` | ❌ **Violation** | `optimal` | 4.45s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `official_hindi` | ❌ **Violation** | `optimal` | 2.99s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 7 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `clean_bilingual` | ✅ **Justified** | `optimal` | 0.73s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `official_english` | ✅ **Justified** | `optimal` | 0.72s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `concise_summary` | ✅ **Justified** | `optimal` | 0.67s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.49s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'M35' |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `smart_bilingual` | `roman_hinglish` | ✅ **Justified** | `optimal` | 0.7s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `clean_bilingual` | ✅ **Justified** | `optimal` | 0.71s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.73s | Hallucinated numeric figures not in speech: 24.5 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `concise_summary` | ✅ **Justified** | `optimal` | 0.67s | None |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.44s | Unwanted Chinese / CJK characters detected; Missing mandatory technical term: 'M35'; Missing mandatory technical term: 'load test' |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.69s | Hallucinated numeric figures not in speech: 24.5 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `suboptimal` | 0.66s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 24 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `official_english` | ❌ **Violation** | `suboptimal` | 0.82s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `suboptimal` | 0.74s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `suboptimal` | 0.62s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `suboptimal` | 0.7s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.73s | Hallucinated numeric figures not in speech: 24 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.73s | Hallucinated numeric figures not in speech: 24 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.69s | Hallucinated numeric figures not in speech: 24 |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.45s | Missing mandatory technical term: 'M35' |
| **script2** (Bridge Structural Engineering & Quality Audit) | `pure_english` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.75s | Hallucinated numeric figures not in speech: 24 |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `viable_but_slower` | 0.77s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `official_english` | ❌ **Violation** | `viable_but_slower` | 0.73s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `viable_but_slower` | 0.79s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `viable_but_slower` | 0.72s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'; Hallucinated numeric figures not in speech: 7 |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `viable_but_slower` | 0.81s | ⚠️ *Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `fundamentally_invalid` | 0.54s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `official_english` | ❌ **Violation** | `fundamentally_invalid` | 0.33s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `concise_summary` | ❌ **Violation** | `fundamentally_invalid` | 0.74s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `ideas_actions` | ❌ **Violation** | `fundamentally_invalid` | 0.52s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `fundamentally_invalid` | 0.51s | ⚠️ *Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.*<br>Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.75s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.76s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 0.71s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.71s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.77s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `suboptimal` | 2.88s | ⚠️ *Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `official_english` | ❌ **Violation** | `suboptimal` | 0.7s | ⚠️ *Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `suboptimal` | 1.24s | ⚠️ *Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `suboptimal` | 1.23s | ⚠️ *Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.*<br>Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल' |
| **script4** (Hill Road Quality & Drainage Inspection) | `pure_hindi` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.7s | Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.7s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.76s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `concise_summary` | ✅ **Justified** | `optimal` | 0.58s | None |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.89s | Missing mandatory technical term: 'JE' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `smart_bilingual` | `roman_hinglish` | ✅ **Justified** | `optimal` | 0.66s | None |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.34s | Missing mandatory technical term: 'site visit'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.41s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.42s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.39s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 24 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.44s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.66s | Missing mandatory technical term: 'measurement book'; Hallucinated numeric figures not in speech: 11 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.67s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 15 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.66s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 15 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.65s | Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 11 |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.94s | Missing mandatory technical term: 'site visit' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'concreting' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 1.47s | Missing mandatory technical term: 'site visit' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.94s | Missing mandatory technical term: 'site visit' |
| **script5** (Typical Site Visit & Measurement Dictation) | `mixed_devanagari_hinglish` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.95s | Missing mandatory technical term: 'site visit' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.62s | Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `optimal` | 0.6s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.57s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.59s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.6s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `suboptimal` | 2.56s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `official_english` | ❌ **Violation** | `suboptimal` | 0.64s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `suboptimal` | 0.63s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `suboptimal` | 0.75s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `suboptimal` | 0.6s | ⚠️ *Hindi acoustic model transliterated English words into Devanagari characters.*<br>Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.64s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.59s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.59s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.34s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill' |
| **script6** (Spoken Dotted Abbreviations & Official Roles) | `pure_english` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.62s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 2.18s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `optimal` | 0.73s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.64s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.51s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.6s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.31s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 2.53s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.73s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 0.67s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.73s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10 |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.71s | Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.54s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'earnest money deposit' |
| **script7** (Roman Hinglish - Tender Evaluation Meeting) | `roman_hinglish` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.67s | Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.65s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.44s | Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Negation assertion ('not') was inverted or dropped |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.64s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.67s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.55s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.56s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.56s | Forbidden hallucination token detected: you know; Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 2.66s | Missing mandatory technical term: 'highway maintenance' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.7s | Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Negation assertion ('नहीं') was inverted or dropped |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 3.08s | Hallucinated numeric figures not in speech: 50 |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 2.4s | Missing mandatory technical term: 'highway maintenance' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.58s | Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.66s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.64s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.7s | Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.43s | Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice' |
| **script8** (Casual Speech with Verbal Hesitations & Fillers) | `roman_hinglish` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.63s | Missing mandatory technical term: 'show cause notice' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 2.84s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.73s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 2023 |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `optimal` | 0.73s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Negation assertion ('नहीं') was inverted or dropped |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 2.47s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.66s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.5s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.54s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.49s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 1.0s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.46s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 2.55s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.67s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 50; Negation assertion ('नहीं') was inverted or dropped |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 0.52s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 50 |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.57s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Negation assertion ('नहीं') was inverted or dropped |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.71s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.61s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.57s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.62s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script9** (Bilingual Land Clearance & Forest Hindrance) | `roman_hinglish` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.65s | Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `clean_bilingual` | ❌ **Violation** | `optimal` | 1.99s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `official_english` | ❌ **Violation** | `optimal` | 0.46s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `concise_summary` | ❌ **Violation** | `optimal` | 1.84s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10 |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `ideas_actions` | ❌ **Violation** | `optimal` | 1.74s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10 |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `smart_bilingual` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.54s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.81s | Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `official_english` | ❌ **Violation** | `optimal` | 0.86s | Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `concise_summary` | ❌ **Violation** | `optimal` | 0.6s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `ideas_actions` | ❌ **Violation** | `optimal` | 2.54s | Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 7, 14, 30 |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_english` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.75s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `clean_bilingual` | ❌ **Violation** | `optimal` | 3.29s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `official_english` | ❌ **Violation** | `optimal` | 0.83s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `concise_summary` | ❌ **Violation** | `optimal` | 0.68s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.74s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Hallucinated numeric figures not in speech: 7; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `instant_hindi` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.8s | Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Hallucinated numeric figures not in speech: 7; Negation assertion ('नहीं') was inverted or dropped |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `clean_bilingual` | ❌ **Violation** | `optimal` | 0.77s | Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `official_english` | ❌ **Violation** | `optimal` | 0.71s | Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `concise_summary` | ❌ **Violation** | `optimal` | 0.66s | Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `ideas_actions` | ❌ **Violation** | `optimal` | 0.86s | Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'security deposit' |
| **script10** (Financial Audit, Variations & Security Deposit) | `roman_hinglish` | `roman_hinglish` | `roman_hinglish` | ❌ **Violation** | `optimal` | 0.68s | Missing mandatory technical term: 'security deposit'; Hallucinated numeric figures not in speech: 10 |

---

## 📝 Detailed Input Speech vs Refined Document Logs

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.64s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer'

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
संरचना निरीक्षण के दौरान पुल की मुख्य स्पैनों और चेनेज 24.5 पर पियर कैप्स और एबटमेंट्स को विशेष रूप से जांचा गया। इसने M35 ग्रेड निर्दिष्टीकरण के अनुसार इन्हें मंजूरी दी। हालाँकि, पियर नंबर 3 पर एलास्टोमेरिक बेयरिंग्स माइनर लेटरल डिस्प्लेसमेंट का संकेत दे रही थीं, जिसके कारण उन्हें अगले ट्यूएसडे को आधिकारिक रूप से निर्धारित लोड टेस्ट से पहले पुनः समायोजित करना होगा।
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (4.94s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24.5

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
एक विशिष्ट संरचना निरीक्षण के दौरान, प्रमुख अभियंता, सहायक अभियंता और अन्य अधिकारी एक बहु-स्पैन ब्रिज पर मौजूद थे। इस घटना को 24.5 किलोमीटर के स्थिति निर्दिष्ट करने वाले पॉइंट पर आयोजित किया गया। 

निरीक्षण की जांच में यह पाया गया कि ब्रिज के peer caps और avatments M35 ब्रीड स्पेसिफिकेशन को पूरा करते हैं। हालाँकि, Pier Number Three पर electromeric bearings minor lateral displacement दिखाई दिए, जिसकी वजह से उन्हें लोड टेस्ट शेड्यूल्ड करने से पहले फिर से समायोजित करने की आवश्यकता है। इस प्रक्रिया में, ब्रिज को एक अधिक विश्वसनीय और सुरक्षित बनाने के उद्देश्य से लोड टेस्ट शेड्यूल्ड किया गया।
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (5.45s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'M35'; Missing mandatory technical term: 'bearings'; Missing mandatory technical term: 'load test'

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
एक विस्तृत मल्टी-स्पैन पुल का संरचनात्मक निरीक्षण एक महत्वपूर्ण कार्यवाई थी। इसमें एग्जीक्यूटिव इंजीनियर और असिस्टेंट इंजीनियर शामिल थे। इस दौरान, उन्होंने मल्टी-स्पैन पुल पर स्थित चेंज ट्वेंटी फोर पॉइंट फाइव का निरीक्षण किया। उनका उद्देश्य यह सत्यापित करना था कि पियर कैप्स और अवर्तमेंट कंपनी डिजाइनेटेड मथे फाइव ब्रेड स्पेसिफिकेशन को पूरा करते हैं। इसके अलावा, उन्होंने इलेक्ट्रोमेरी बेरिंग्स पर नंबर थ्री पियर पर विचार किया। यह ध्यान देने योग्य है कि माइनर लाटर डिस्प्ले मस्ट रिक्रेटेड जाना चाहिए, इससे पहले कि इसे आधिकारिक रूप से अगली बार टेस्टिंग के लिए शेड्यूल किया जाए।
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (4.03s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Executive Engineer'; Missing mandatory technical term: 'Assistant Engineer'

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
संरचना निरीक्षण के दौरान पुल की विस्तृत जांच की। चिनीस 24.5 पर स्थित मल्टी-स्पैन ब्रिज। मूल्यांकन के अनुसार, पीयर कैप्स और अवत्मेंट्स निर्दिष्ट एम 35 ग्रेड विशेषज्ञता को पूरा करते हैं। हालाँकि, पुल संख्या 3 पर एलास्टोमेरिक बेयरिंग माइनर लेटरल डिस्प्लेसमेंट दिखाती है और इसकी आधिकारिक लोड टेस्ट के पहले इसे फिर से समायोजित करना आवश्यक है। अगले मंगलवार को निर्धारित लोड टेस्ट के बाद यह पुनर्विचारित किया जाएगा।
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.27s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
पर्वतीय मार डामरी करने और चौड़ी करने के कार्य के स्थल पर निर्वहन जल निकासी नालियों का पता लगाया गया। इस दौरान, संबंधित ढलानों पर भूस्खलन रोकने हेतु RCC रिटेनिंग बॉल और ग्यावियन संदचनों को तेजी से प्रगति पर रखा गया।

साइग एविंता को निर्देश दिया गया था कि वे सब बेस की समतलता और सगनता की जांच रिपोर्ट अभिलम संकलित करें।
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (1.81s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
पोरवेट मार्गर डैम, उत्पत्ति स्थली नेक्स्ट के दौरान गेलनसी नोल्लोका सन्ट पेया। शेवता को नेर्ड धिये गैटेमिन्स कन्क्रीट बिचान्य स बास्की कुछ या शंटगशालापोर्ट अबलम स्लिट करें।
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (6.76s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान, जल निकासी नालियों का निर्माण संतोषजनक पाया गया। इसने सुनिश्चित किया है कि मार्ग पर जल निकासी को सुचारू रूप से किया जाए। इसके अतिरिक्त, आरसीसी रिटेनिंग मॉल और गैविन संरचनाओं का निर्माण तेजी से प्रगति पर है, जिससे भूस्खलन को संवेदनशील ढलानों पर रोका गया। यह सुनिश्चित करता है कि मार्ग के लिए एक सुरक्षित और विश्वसनीय निर्माण प्रक्रिया हो।

इसके अलावा, ब्रिटिमिनस कंक्रीट बिछाने से पहले, सब बेस की समतलता और सघनता पर जांच रिपोर्ट को अवलंबित करने का निर्देश दिया गया है। यह सुनिश्चित करता है कि मार्ग के आधार की गुणवत्ता उच्चतम स्तर पर रखी गई है, जिससे इसकी लम्बे समय तक स्थायित्व और विश्वसनीयता सुनिश्चित होती है।
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.26s)
- **Compatibility:** `suboptimal` — Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
निर्माण स्थलों के निकट जल निकासी नहरों का निर्माण संतोषजनक हुआ है। रेतीले मैदानों पर बाधाओं को रोकने के लिए आरसीसी रिटेनिंग बॉल और गायब संरचनाओं का निर्माण तेजी से प्रगति कर रहा है। विभिन्नता को निर्देश दिया गया है कि पहले सब बेस की समानता और स्थिरता की जांच रिपोर्ट सकलित करने के लिए bituminous concrete लगाने से पूर्व।
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.59s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
आज, हमने site visit किया, जहां पाया गया कि contractor ने bridge foundation का excavation work समाप्त कर लिया। इस मौके पर उपसित E.E. साहब और J.E. को निर्देश दिया गया था कि suttering की alignment और reinforcement steel की spacing को measurement book में तुरंत दर्ज करें। यदि कल मौसम अनुकूल नहीं रहता, तो 12 बजे से raft foundation की concreting शुरू होनी चाहिए।
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.29s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
साइट विजिट कराने वाला ठेकेदार ने पुल की स्थापना काम पूरा करने की घोषणा की। मॉकस्ट या जॉन्सट्रिंग अलेमेंट रेफोर्सिंग स्टील की स्पेसिफिकेशन बुक में ड्रम ड्रैगम ऑन कुल्टी राफ्ट फाउंडेशन पर कंक्रीट के निर्माण को छोटा कर दिया।
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.83s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Hallucinated numeric figures not in speech: 12

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
आज, हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क पूरा कर लिया। ई साहब और जेई को मौके पर उपस्थित होने की सलाह दी गई थी, जहां उन्हें शटरिंग के अलाइनमेंट और रेइन्फोर्समेंट स्टील की स्पेसिंग को तुरंत मेजरमेंट बुक में दर्ज करने का निर्देश दिया गया। यदि कल मौसम अनुकूल रहा, तो दोपहर 12 बजे से राफ्ट फाउंडेशन की कंक्रीटिंग शुरू होने की योजना बनाई गई थी।
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.59s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
आज हमने साइट विजिट की द्वारा पाया कि निर्माता ने ब्रिज फाउंडेशन के खुदाई काम पूरा कर लिया है। मौके पर उपस्थित अधिकारी और जूनियर इंजीनियरिंग एक्सपर्ट (जी.ई.ई.) को सैटिंग की अलाइनमेंट और रिफोर्सड स्टील की स्पेसिंग का मापन बुक में तुरंत दर्ज करने के लिए निर्देशित किया गया। यदि कल मौसम अनुकूल रहता है, तो दोपहर 2 बजे रात्रि फाउंडेशन की सीमेंटिंग शुरू कर दी जाएगी।
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.15s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
ई और जे ने कुलवेर्ट विंडिंग कार्य के लिए एमबी बढ़ाना प्रमाणित किया। उन्होंने रिवाइज्ड एसओआर आइटम के साथ दरों को भी चेक किया। ठेकेदार ने तीसरे आरई बिल, हिंडरेंस रजिस्टर और मैटेरियल टेस्ट सर्टिफिकेट्स के साथ प्रस्तुत किए। तकनीकी वेटिंग के बाद, विभाग शुक्रवार दोपहर तक बचे हुए रोड पैकेज के लिए नई एनआईटी जारी करेगा।
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.85s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
ई और जे ने कुलवेर्ट व्हाइट इंक की दरों को रिवीज्ड एसओआर आइटम से मिलाकर एमबी बढ़ाने का पुष्टि किया। ठेकेदार ने तीसरी पहुंच और हिंडरेंस रजिस्टर, मैटेरियल टेस्ट सर्टिफिकेट्स के साथ सबमिट किए। विभागीय तकनीकी जांच पूरा करने के बाद, दिवासियों ने शेष रोड पैकेज के लिए नया एनआईटी जारी करेगा।
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (4.17s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
ई एंड जे ने कल्बर्ट व्हाइटिंग और क्रस्ट की मी इनक्रीस को वरिफाई करना शुरू कर दिया। उन्होंने रेट्स के साथ पुनरावृत्ति की, ताकि यह सबमिट होने के लिए तैयार हो। इसके बाद, वे एक एलोन विथ हिन्द्रेंस रजिस्टर और मेटेर टेस्ट सर्टिफिकेट जारी करना चाहते थे, जो प्रॉपर्टी तकनीकल वेटिंग के बाद होता। इसके बाद, डिवीजन ने फ्रेश ने इट को रिमिंग रोड पैकेज के लिए तैयार करना शुरू कर दिया, जिसे उन्होंने सोमवार की शाम तक पूरा करने का लक्ष्य रखा।
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.35s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
ई ई और जे ने कंसल्टिंग वायरिंग कार्य के लिए एमबी में वृद्धि का सत्यापन किया। उन्होंने रिवाइज्ड एसओआर आइटम से दरों को पुनः जांचा है। ठेकेदार ने तीसरे आरई बिल, हिंटरेंस रजिस्टर और मैटेरियल टेस्ट सर्टिफिकेट्स के साथ सबमिट किया। तकनीकी वेटिंग के पूर्णतः सत्यापन के बाद, विभाग शुक्रवार दोपहर तक शेष रोड पैकेज के लिए नया एनआईटी जारी करेगा।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.98s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
कल, 10 बजे, डिविजन आफिस में टेंडर रिवीलेशन कमिटी का आयोजन होना है। इस बैठक में, अस्टेड लिए साहब को विभिन्न प्रतियोगिताओं के लिए समानीकृत कथन और तकनीकी आवश्यकताओं की एक संक्षिप्त फ़ाइल तैयार करनी चाहिए। यह फाइल उन निर्माणकर्ताओं को शामिल नहीं करेगी, जिनका प्रवर्तक मानदंडों के अनुसार गुणवत्ता मानकों को पूरा नहीं करता। इसके अतिरिक्त, ऐसी स्थितियों में भी विशेष ध्यान देना चाहिए जहां निवेशकों की धनराशि जमा करने की आवश्यकता होती है।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.03s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
सहबोल्क की तुलनात्मक विवरण या तकनीकी बिट्स सारांश में ऑफिस टेंडर रेवोल्यूशन कमेटी के शेड्यूल को प्रस्तुत करना। इस सम्मेलन में, जोक्ट क्वालीफाइंग क्राइटेरिया पूरा करते हुए, नेक मनी डिपॉजिट रिलीज फाइल सबमिट करें।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.42s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
सुबह दस बजे, टेंडर रिवोल्यूशन कमेटी को डिवीजन ऑफिस में शेड्यूल किया गया है। ऑस्ट्रेलिया साहब के लिए आवश्यक है कि वे बोलकर, उन्होंने तैयार रखें, जिसमें कांट्रैक्टर्स क्वालीफाइंग क्राइटेरिया मीट नहीं कर रहे हैं, उनकी अनलेस मनी डिपॉजिट रिलीज करने की फाइल। इसके अलावा, उन्हें एक अलग से समरी फाइल सबमिट करनी होगी, जिसमें कम्पेरेटिव स्टेटमेंट और टेक्निकल बिट्स शामिल होंगे।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.95s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
कल सुबह दस बजे विभागीय कार्यालय में टेंडर रिवीजन कमिटी की शेड्यूल होनी है। अस्त्रिड नियात सहबा को बोलकर तुलनात्मक कथन और तकनीकी वस्तुओं की संक्षिप्त विवरण फाइल पूर्व-तैयार रखने की आवश्यकता होगी। जिन ठेकेदारों ने गुणवत्ता मानदंडों को पूरा नहीं किया, उन्हें जब तक धन जमा रिलीज करने की फ़ाइल अलग से जमा करनी पड़ेगी।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.78s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
मीटिंग में हमने स्पष्ट रूप से चर्चा की थी कि हाईवे रखरखाव शेड्यूल देरी कर रहा है। ठेकेदार ने वादा किया था कि दो सप्ताहों के भीतर, 8 और 15 किमी. के बीच के सभी छिद्रों को पास करने का। लेकिन जमीनी स्थिति यह है कि श्रमिक नहीं मोबाइल हैं। इसलिए हमें तुरंत आधिकारिक नोटिस जारी करना चाहिए।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.94s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Hallucinated numeric figures not in speech: 8, 15

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
हाईवे रखरखाव कार्यक्रम की समयसीमा में देरी हो रही है। संविदाकार ने घोषणा की थी कि 8 और 15 किलोमीटर के बीच पोर्थोल्स को दो सप्ताहों के भीतर पूरा करेगा। हालांकि, जमीनी वास्तविकताओं में संविदाकार ने गतिविधियाँ शुरू नहीं कीं। इस परिस्थिति को देखते हुए, हमें तुरंत आधिकारिक सोस्कोर्ड अधिसूचना जारी करनी चाहिए।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.19s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
एक्चुअली मतलब मीटिंग में वे क्लियरली डिस्कस दैट यू नो हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड। कॉन्ट्रैक्टर प्रॉमिस दैट लाइक विदिन टू वीक्स ऑल पोर्ट होल बिट्वीन किलोमीटर एट एंड किलोमीटर फिफ्टीन विल बी पास्ट बैक्टीरियल ग्राउंड रियलिटी। यह लगता है कि लेबर मोबिलाइज नहीं हुई है, सो वे मस्ट इशू आन ऑफिशियल सोकोज नोटिस इमीडिएटली।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.21s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
मीटिंग में हमने स्पष्ट रूप से चर्चा की थी कि हाईवे रखरखाव शेड्यूल देरी से प्रभावित हो रहा है। ठेकेदार ने वादा किया था कि 2 सप्ताहों में किलोमीटर 8 और किलोमीटर 15 के बीच सभी रुकावट पूरी कर दी जाएगी। हालांकि, जमीनी स्थिति देखने पर लगता है कि श्रमिक विमोचित नहीं हो रहे हैं। इसलिए, हमें तुरंत आधिकारिक नोटिस जारी करना चाहिए।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.35s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
परियोजना कार्यों को निर्बाध रूप से आगे बढ़ाने के लिए, 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी गई थी। इस प्रक्रिया में, डिफरेंस ऑफिस और SDM साहब ने जॉइन किया, जहां उन्होंने एक सफल इफेक्शन कंडक्ट किया। हालाँकि, इलेक्रिकल पॉर्स और ड्रिंकिंग वाटर पाइपलाइन्स की यूटिटी सिफ्टिंग का इस्टिमेट अभी तक जल सस्तान से टापत नहीं हुआ है।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.39s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 15

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
स्थानीय ग्राहकों से मंजूरी अभी तक TFO कार्यालय में प्रतीक्षा कर रही है। रोड फॉर्मेशन कटिंग टेम्पररिली हार्ड करने वाली कार को लाइन 12:15 पर किया जाता है, SDM साहब सतन द्वारा, या प्रतिष्ठित बिजली खंभों और पेयजल पाइपलाइन्स शिफ्टिंग का अनुमान लगाया।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.76s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 15

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
फॉरेस्ट डिपार्टमेंट द्वारा अप्रूवल की आवश्यकता के कारण, टीफो ऑफिस में अभी तक इसे प्राप्त करने में विलंब होने पर चेन ने 12 से 15 तक रोड फॉर्मेशन कटिंग टेम्परेरी हार्ड कर दिया। इसके अलावा, रेवेन्यू डिपार्टमेंट और एसडीएम के साथ ज्वाइन इंस्पेक्शन कंडक्ट हो चुका है। हालांकि, इलेक्ट्रिकल पोल्स और ड्रिंकिंग वाटर पाइपलाइन्स की यूटिटी सेफ्टींग का एस्टीमेट अभी तक जल संस्थान से प्राप्त नहीं हुआ है।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.51s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
संचालन के लिए स्वीकृति अभी तक TFO कार्यालय में प्रतीक्षा कर रही है। यदि चीनी 12 से 15 तक रोड फॉर्मेशन कटिंग टेम्पररी रूप से बंद कर दी गई है, तो यह एक महत्वपूर्ण विकास कार्य पर असर डाल सकती है। इस्लिए, राजस्व विभाग और SDM श्री के साथ मिलकर निरीक्षण आयोजित किया गया था, लेकिन अभी तक जल संस्थान से बिजली पोलों और पीने के पाइपलाइन को UTT स्थानांतरित करने का अनुमान नहीं मिला है।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (4.18s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
अर्थवर्क कंपनी ने अपने मीजर्मेंट बुक वेरिफाय करने के पश्चात पाया है कि अर्थवर्क कॉंटिटी में कुछ वैरिशन है। यह स्पष्ट रूप से दिखता है कि इस वैरिशन ने एप्रूब्ट ब्योक्यू आइटम ब्योक्यू लिमिट से लगभग समान प्रतिशत अधिक है, जो एक महत्वपूर्ण अंतर दर्शाता है। यह मुद्दा कॉंट्रेक्टर द्वारा फाइनल बिल रिलीस करने पर गंभीरता से प्रभावित करेगा। इस वैरिशन की वजह से, पूर्ग रिव क्योटी डिपॉजिट रिफंड नहीं किया जाएगा, जो एक महत्वपूर्ण आर्थिक असर होगा।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (3.12s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
मापन पुस्तक स्वीकृति में आर्थिक मात्रा मैकेनिकल, जोप्ट बीओक्यू के लिए निर्धारित होती है। यह सीमाएं लंबाई और गहराई को शामिल करती हैं। ठेकेदार को अंतिम रूप से पुल परिवर्तित अनुमान या समय विस्तारण मंजूरी प्राप्त करने तक निर्माणाधीनता अवधि के दौरान लाभदायक रहकर नए शिकार जमा कर सकता है। इस अवधि के बाद, ठेकेदार को जमा रिफंड नहीं मिलेगा।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (4.45s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
साहिब ने मेजरमेंट बुक वेरीफाई करने के पश्चात पाया कि अर्थवर्क क्वांटिटी में लगभग सात फीसदी अधिक है, जो एप्रोप पीओक्यू आइटम बीओक्यू लिमिट से वेरिशन करता है। इस स्थिति में, कांट्रेक्टर को अपने निर्माण कार्यों के समापन से पहले रिवाइज एस्टीमेट और टाइम एक्सटेंशन अप्रूवल पाने की आवश्यकता होती है। यह अनिवार्य है कि इस तरह की मंजूरी प्राप्त करने से पहले। जब तक डिफेक्ट लायबिलिटी अवधि सफलतापूर्वक समाप्त नहीं हो जाती, तब तक सिक्योरिटी डिपॉजिट रिफंड नहीं किया जाएगा।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇮🇳 Official Hindi Directive` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `llama3-hindi-8b-q5_km.gguf:latest` (2.99s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 7

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
माप की पुस्तक सत्यापन करने के बाद, आप ने स्थिति में कुछ विविधता पाई है, जो स्वीकृत BOQ आइटम और BOQ सीमा से लगभग 7% अधिक है। अनुबंधक को अंतिम बिल रिलीज करने से पहले, उन्हें समायोजित अनुमान और समय विस्तार मंजूरी प्राप्त करनी चाहिए। जब तक दोष जिम्मेदारी अवधि सफलतापूर्वक पूरी नहीं होती, तब तक जमा रिफंड नहीं किया जाएगा।
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at chainage 24.5. The concrete code testing confirmed that both the pier caps and abutments comply with the designated M35 grade specification. However, it was noted that the elastomeric bearings on pier number 3 require minor lateral displacement adjustments before the load test scheduled for next Tuesday can be officially conducted.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `qwen2.5:3b` (0.72s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at chainage 24.5. The concrete code testing confirmed that both the pier caps and abutments meet the specified M35 grade specification. However, it was noted that the elastomeric bearings on pier number 3 require minor lateral displacement adjustments before the load test scheduled for next Tuesday can proceed officially.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage 24.5. The concrete code testing confirmed that the pier caps and abutments comply with the designated M35 grade specification. However, the elastomeric bearings on pier number 3 require minor lateral displacement calibration before the load test scheduled for next Tuesday can proceed.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `qwen2.5:3b` (0.49s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'M35'

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
[Action Item] Recalibrate elastomeric bearings on pier number 3 to ensure proper operation prior to the upcoming load test.
[Responsible Role/Person] Structural Engineer
[Status/Timeline] To be completed by Monday, as soon as available.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.946s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at chainage...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of the multi-span bridge at chainage 24.5. The concrete code testing confirmed that the pier caps and abutments comply with the designated M35 grade specification. However, the elastomeric bearings on pier number 3 need minor lateral displacement adjustments before the load test scheduled for next Tuesday can be officially conducted.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at site number twenty-four point five. The concrete code testing confirmed that both the peer caps and avatments meet the specified M35 breed specification. However, the electromeric bearings on Pier Number Three exhibited minor lateral displacement; therefore, they must be recalibrated before the load test scheduled for next Tuesday can proceed officially.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24.5

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at Span 24.5. The concrete code testing confirmed that both the piers' caps and armorings adhere to the M35 specification, however, it was noted that there is minor lateral displacement in Pier Number Three's electromeric bearings. These must be recalibrated before the load test scheduled for next Tuesday can proceed officially.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at change twenty four point five. The concrete code testing confirmed that the peer caps and avatments comply with the designated M35 breed specification, however, the electromeric bearings on Pier Number Three show minor lateral displacement which must be recalibrated before the load test scheduled for next Tuesday is officially conducted.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `qwen2.5:3b` (0.44s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Unwanted Chinese / CJK characters detected; Missing mandatory technical term: 'M35'; Missing mandatory technical term: 'load test'

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
[Action Item] Conduct site visit to pier number three for calibration of electromeric bearings.
[Responsible Role/Person] Assistant Engineer
[Status/Timeline] Immediate安排现场检查Pier Number Three以校准电磁轴承。
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.699s) | **Refiner Model:** `qwen2.5:3b` (0.69s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24.5

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at change t...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of the multi-span bridge at site number 24.5. The concrete code testing confirmed that the pier caps and avatars comply with the designated M35 breed specification, but the electromeric bearings on Pier Number Three show minor lateral displacement; they must be recalibrated before the load test scheduled for next Tuesday can officially proceed.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
The EE and AE conducted a detailed inspection of the multi-span bridge at 24-point span, confirming data from the company commissioned by Mathew Feeney Bridges for Space Specification Havers, Electric Bearings on Pier Number Three. The master board was recoded before the load test as per official schedule next scheduled thusly.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `qwen2.5:3b` (0.82s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
The Executive Engineer and Assistant Engineer conducted a detailed inspection of the multi-span bridge at 20-foot span concrete testing by DCT Capital Designated Mathew's Feadz Spaces Specification Harness, ILB Electromagnetic Bearings on Pier Number Three. The data caps and circumference company was confirmed by the test results from Amps & Volumes Company. Before the load test, this official schedule has been scheduled for next.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `qwen2.5:3b` (0.74s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
The Executive Engineer and Assistant Engineer conducted a detailed inspection of the multi-span bridge at 20 points for testing by the company designated as Mathew Feane Braces, Electric Bearings on Pier Number Three. The test data confirmed the PEC’s caps and circumference company design specifications, with the magnetic recorder re-recorded before the load test according to the official schedule next week.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `qwen2.5:3b` (0.62s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
The Executive Engineer and Assistant Engineer conducted a detailed structural inspection of the multi-span bridge at 20 for points concrete testing confirmed data from the company designated Mathew Feave Bridge Specification Havers, Electrical Bearings on Pier Number Three MSL displayed before the load test. Officially scheduled next thus.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.948s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'; Hallucinated numeric figures not in speech: 20

**Input Speech Transcription:**
> द एग्जीक्यूटिव इंजीनियर एंड असिस्टेंट इंजीनियर कंडक्टेड ए डिटेल स्ट्रक्चर इंस्पेक्शन ऑफ मल्टी स्पैन ब्रिज एट चेंज ट्वेंट...

**Refined Document Output:**
```text
The Executive Engineer and Assistant Engineer conducted a detailed inspection of the multi-span bridge at 20 points for concrete testing, confirming data from Caps & Alignment Company designed by Mr. Mathew Faebd Space Specifications, including Electrical Bearings on Pier Number Three with minor display master B recaptured before the load test according to the official schedule next week.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at Chinis on May 24. The concrete code testing confirmed that both the peer caps and avatars comply with the designated M35 grade specification. However, it was noted that the elastomeric bearing on pier number three requires minor lateral displacement correction before the load test scheduled for next Tuesday can be officially conducted.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed inspection of the multi-span bridge at Site Chinis on May 24. The concrete code testing confirmed that both the pier caps and abutments meet the designated M35 grade specification. However, it was noted that the elastomeric bearing on Pier Number 3 requires minor lateral displacement adjustments before the load test scheduled for next Tuesday can proceed officially.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `qwen2.5:3b` (0.69s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of multi-span bridge at Chinis on May 24. The concrete code testing confirmed that the pier caps and avatars comply with the designated M35 grade specification. However, the elastomeric bearing on pier number 3 showed minor lateral displacement requiring recalibration before the load test scheduled for next Tuesday is officially conducted.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `qwen2.5:3b` (0.45s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'M35'

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
[Action Item] Recalibrate elastomeric bearing on span number 3.
[Responsible Role/Person] AE (Assistant Engineer)
[Status/Timeline] To be done by Wednesday, to prepare for load test next Tuesday.
```

---

### script2: Bridge Structural Engineering & Quality Audit $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.586s) | **Refiner Model:** `qwen2.5:3b` (0.75s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> The executive engineer and assistant engineer conducted a detailed structure inspection of multi span bridge at chinis 2...

**Refined Document Output:**
```text
The executive engineer and assistant engineer conducted a detailed structure inspection of the multi-span bridge at Chinis on May 24. The concrete code testing confirmed that both the piers caps and avatars comply with the designated M35 grade specification. However, the elastomeric bearing on pier number 3 shows minor lateral displacement; it needs to be recalibrated before the load test scheduled for next Tuesday can proceed officially.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `qwen2.5:3b` (0.77s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
During the site inspection of dam reinforcement and widening on Mount Mar, joy was felt at observing the removal of water levels in reservoirs. RCC retaining walls and geotechnical reinforcements were progressing rapidly to prevent landslides caused by sediment flow. Instructions had been given to Sai Geventa that bitumen concrete should achieve a smooth and uniform surface with proper compaction as per the report compiled promptly.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
During the site inspection of the timber and dam reinforcement for Mount Mar, a sense of excitement was felt regarding the water infiltration outlets. RCC retaining walls and gully control structures are progressing rapidly to prevent erosion on the embankment surfaces. Instructions were given to Sigeventta to compile reports detailing the smoothness and compaction levels achieved through bituminous concrete placement.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `qwen2.5:3b` (0.79s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
During the site inspection for damming and chousing of Mount Malar's Dampir and Chouidi sections, water infiltration nodes have been identified. RCC retaining walls and gully control measures are progressing rapidly to prevent seepage on embankment slopes. Instructions were given to SAG EVITA to compile a report detailing the smoothness and compaction quality achieved with bituminous concrete placement.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `qwen2.5:3b` (0.72s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'; Hallucinated numeric figures not in speech: 7

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
During the site inspection for culvert and chowki installation of Nittany Maha, water infiltration outlets were observed. RCC retaining walls and gully traps are in progress to prevent erosion on embankment slopes. Instructions have been given to Sigh Evinta to compile a report detailing smoothness and compaction from bitumen concrete placement within 7 days.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (2.365s) | **Refiner Model:** `qwen2.5:3b` (0.81s)
- **Compatibility:** `viable_but_slower` — Whisper Turbo is viable but ~3x slower than instant_hindi with minor phonetic deviations.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> पर्वतिय मार के डामरी करण और चौडी करण के कार के स्थली नेक्षण के दौरान जल निकासी नालियों का निर्वाण संतोज जनक पाया गया है।...

**Refined Document Output:**
```text
During the site inspection for damming and chiseling operations in Parvatimai, we have experienced great satisfaction with the water intake structures. The reinforcement bars on the diversion channels are being protected by RCC retaining balls and gully liners at an accelerated pace. Instructions were given to Sai Vinanta that a comprehensive report should be compiled based on the smoothness and compaction data obtained from bituminous concrete placements.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `qwen2.5:3b` (0.54s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gave a concrete proposal for the construction work at her site and mentioned that she was looking to secure some or shantagshalaport assistance from someone.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `qwen2.5:3b` (0.33s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
Porvet marger damrik, and the origin story of Sunt Paya next involves a site visit. She provided concrete advice on some aspect related to construction work.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `qwen2.5:3b` (0.74s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gave technical details about the concrete batching plant construction process and mentioned that she would arrange a site visit soon to ensure everything is in place for the concreting work. No specific monetary amounts or dates were provided; only negative assertions regarding certain aspects of the project are preserved as per instructions.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `qwen2.5:3b` (0.52s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gave technical specifications for the concrete batching plant to be constructed at Sunt Paya site. Ensure all engineering terms and units are in English (Latin script).
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (2.669s) | **Refiner Model:** `qwen2.5:3b` (0.51s)
- **Compatibility:** `fundamentally_invalid` — Acoustic mismatch: Nemotron English acoustic model hallucinated phonetics on pure Hindi speech.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gaveta को nerd dhie gatemins concret bic...

**Refined Document Output:**
```text
Porvet marger damrik, origin stlie next ke dora gelncasi nolloca Sunt Paya. She gave a statement that she had gone to the site for concreting work and something or shantagshalaport ablm slitt car.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `qwen2.5:3b` (0.75s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
During the site inspection for the construction of culverts and widening on the highway, it was noted that water infiltration in the channels had been successfully mitigated. The use of ASR retention methods and gavyn structures is progressing rapidly to prevent erosion at vulnerable slopes. Guidelines have also been issued requiring a thorough assessment report based on the preliminary findings before proceeding with placing base concrete.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `qwen2.5:3b` (0.76s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
During the site inspection for the construction of water tanks in the sustainable drainage system, it was noted with satisfaction that the concrete placements were proceeding smoothly. The reinforcement and gavin structures are advancing rapidly to prevent erosion on sensitive slopes. Guidelines have been issued to ensure that prior to placing Britishmin cement, a report detailing the assessment of flatness and compaction quality must be submitted for approval.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
During the site inspection for dam reinforcement and widening on the Garvati river, concrete pourable forms were successfully produced. The RCC retaining walls are progressing rapidly to prevent erosion at sensitive slopes. Guidelines have been issued to ensure that prior to placing Britimins cementitious materials, a report of trial tests confirming flatness and cohesion of base material is approved.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
During the site inspection for the reinforcement and widening of the embankment on the high-pressure pipeline, concrete pour was successful. The retention method is effectively controlling erosion at risk areas with geavine structures advancing rapidly. Guidelines have been issued to check beforehand that all base flatness and compaction performance reports are in line before Britimins cement pouring.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.723s) | **Refiner Model:** `qwen2.5:3b` (0.77s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> गर्वतीय मार्ग के दामरीकरण और चौड़ीकरण के कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गय...

**Refined Document Output:**
```text
During the site inspection for the construction of culverts and widening on the pride route, it was noted that water infiltration in the drainage channels has been effectively managed. The ASCE Retaining Wall and Gavrin structures are progressing well to prevent erosion at sensitive slopes. Guidelines have also been issued to use Britannin concrete before conducting a trial report on the flatness and compaction of base materials.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `qwen2.5:3b` (2.88s)
- **Compatibility:** `suboptimal` — Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
मार्ग के दौरान, डाम्रिक्रन और चौधीक्रन के स्थायीण का प्रयोजन में जल निकासी लाइनों की स्थापना सफलता हुई। संवेदनशील धालन के रॉकने पर, बिटुमियन क्रोसने से पहले चढ़ाव और गिलास की प्रयोगशाळा जांच वितरण में इतिहास रखने की संकल्पना अब शुरू हुई। सायविभिन्ताको निर्देश दिए गए हैं, कि बिटुमियन क्रोसने से पहले चढ़ाव और गिलास की प्रयोगशाळा जांच में व्यापक निर्देशन करने की आवश्�ykत है।
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `suboptimal` — Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
During the construction phase of the road's drainage and culvert structures, significant progress has been made in achieving the desired water management. The application of RCC retaining walls for waterproofing is a key aspect that has progressed efficiently. Recommendations have also been provided to evaluate the effectiveness of bituminous concrete as an alternative material for certain base layers and sublayers based on preliminary testing results.
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `qwen2.5:3b` (1.24s)
- **Compatibility:** `suboptimal` — Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
Maarg ke daamrikran aur chaudikran ka sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank paaya gaya hai. Sanvednashil dhalaano par bhooskhalan rokne hetu RCC retaining ball aur gayaven sanrachanaon ka kaary teji se pragti par hai. Saiy vibhinnata ko nirdesh die gae hain ki bituminous concrete bichhaane se poorv sab base ki samtalta aur saglanta ki prayogashaala jaanch report abilambh sankalit karen.nan
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `qwen2.5:3b` (1.23s)
- **Compatibility:** `suboptimal` — Apex Hinglish converted Hindi to Roman script; subsequent Devanagari translation requires extra decoding.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
Maarg ke daamrikran aur chaudikran ka nirmaan santosh jank paaya gaya hai jal nikaasi naaliyon ke sthali nekshan ke dauraan. Sanvednashil dhalaano par bhooskhalan rokne hetu RCC retaining ball aur gayaven sanrachanaon ka kaary teji se pragti par hai. Saiy vibhinnata ko nirdesh die gae hain ki bituminous concrete bichhaane se poorv sab base ki samtalta aur saglanta ki prayogashaala jaanch report abilambh sankalit karen.nan
```

---

### script4: Hill Road Quality & Drainage Inspection $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.683s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'डामरीकरण'; Missing mandatory technical term: 'जल निकासी'; Missing mandatory technical term: 'रिटेनिंग वॉल'; Missing mandatory technical term: 'सहायक अभियंता'

**Input Speech Transcription:**
> Maarg ke daamrikran aur chaudikran ke kaary ke sthali nekshan ke dauraan jal nikaasi naaliyon ka nirmaan santosh jank pa...

**Refined Document Output:**
```text
In the construction of Maarg and Daamrikran, we have achieved a significant milestone with the completion of water tank structures. RCC retaining balls are being used extensively to prevent erosion on the Sanvednashil slope. The plan is now underway to evaluate the effectiveness of bituminous concrete in reducing initial stability issues and assessing its potential for future applications based on our findings.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
Today, we have received the site visit report indicating that the contractor has completed the excavation work for the bridge foundation. The appointed E.E. and J.E. were instructed to record the alignment of suttering and the spacing of reinforcement steel in the measurement book. If the weather remains unfavorable tomorrow, concrete pouring for the raft foundation will commence at 12 PM.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `qwen2.5:3b` (0.76s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
Today, we have received the site visit report indicating that the contractor has completed the excavation work for the bridge foundation. The respective Engineer-in-Charge (E.E.) and Junior Engineer (J.E.) were instructed to record the alignment of suttering and the spacing of reinforcement steel in the measurement book. If the weather remains unfavorable, concrete pouring for the raft foundation will commence at 12 PM tomorrow.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
- Site visit conducted today revealed that the contractor has completed the excavation work for bridge foundation. The EE and JE were instructed to record alignment of suttering and spacing of reinforcement steel in the measurement book. If weather remains unfavorable, concreting of raft foundation will commence at 12 PM tomorrow.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `qwen2.5:3b` (0.89s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
[Action Item] Measurement book entries for alignment and reinforcement steel spacing,
[Responsible Role/Person] Upisit E.E. & J.E.,
[Status/Timeline] Complete by next day if weather remains unsuitable, start concreting at 12 PM on the following day.  
[Action Item] Start raft foundation concreting,
[Responsible Role/Person] Site Visit,
[Status/Timeline] Begin at 12 PM on the following day.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.971s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ✅ Justified

**Input Speech Transcription:**
> आज हमने site visit के दोहान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है मौके पर उपसित...

**Refined Document Output:**
```text
Today, we received the site visit report stating that the contractor has completed the excavation work for the bridge foundation. The appointed EE and JE were instructed to record the alignment of suttering and the spacing of reinforcement steel in the measurement book. If it rains on Monday, concreting of the raft foundation should commence at 12 PM.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `qwen2.5:3b` (0.34s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'site visit'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
Contractor has completed the bridge foundation works. The mocksetting and alignment of reinforcement steel measurements are recorded in the document for the short duration concrete work related to the raft foundation.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `qwen2.5:3b` (0.41s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
The site visit by the contractor has confirmed that the bridge foundation works have been completed. The mock setting of alignment and reinforcement steel measurements are documented in the construction documentation, with concrete work for the short raft foundation having commenced.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `qwen2.5:3b` (0.42s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
The site visit with the contractor has confirmed that the bridge foundation works are now completed. The mock setting of alignment and reinforcement steel measurements have been recorded in the construction documentation for the raft foundation, which is currently undergoing concrete work.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `qwen2.5:3b` (0.39s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 24

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
[Action Item] Site visit to the contractor for bridge foundation work completion.
[Responsible Role/Person] AE
[Status/Timeline] Immediate action required, complete site visit within 24 hours.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.473s) | **Refiner Model:** `qwen2.5:3b` (0.44s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Site visite contractor ne bridge foundation work complete. Mockst or Johnsetring Alejment or reinforcement steel की spej...

**Refined Document Output:**
```text
The site visit with the contractor has confirmed that they have completed the bridge foundation work. The mock setting and alignment of the reinforcement steel is documented in the construction measurement book, noting a discrepancy regarding the concrete pouring for the short raft foundation.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Hallucinated numeric figures not in speech: 11

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
Today during the site visit, it was observed that the contractor had completed excavation work for the bridge foundation. The present sir and JE were instructed to immediately enter alignment of shoring and reinforcement steel spacing into the majoring book. If weather permits, concreting of raft foundation should commence from 11 AM onwards tomorrow afternoon.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 15

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
During the site visit today, it was observed that the contractor had completed excavation work for the bridge foundation. The present client and JE were instructed to immediately document the alignment of shoring and reinforcement steel in the major works book. If weather conditions permit, concrete pouring for the raft foundation should commence by 1:15 PM tomorrow afternoon.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
Today during the site visit, it was noted that the contractor has completed excavation work for the bridge foundation. The AE and JE were instructed to immediately enter alignment and reinforcement steel spacing into the Majoring Book. If weather permits by tomorrow noon, concrete pouring for the raft foundation should commence.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 15

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
Today, we have found out during the site visit that the contractor has completed excavation work for the bridge foundation. The present gentleman and JE are instructed to immediately enter alignment and reinforcement steel spacing into the Majoring Book. If weather permits tomorrow, concrete pouring of the raft foundation should commence by 1:15 PM.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.693s) | **Refiner Model:** `qwen2.5:3b` (0.65s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'concreting'; Hallucinated numeric figures not in speech: 11

**Input Speech Transcription:**
> आज हमने साइट विजिट के दौरान पाया कि कॉन्ट्रैक्टर ने ब्रिज फाउंडेशन का एक्सकेवेशन वर्क कम्प्लीट कर लिया है। मौके पर उपस्थ...

**Refined Document Output:**
```text
Today during the site visit, we found that the contractor has completed excavation work for the bridge foundation. The present client and I were instructed to immediately enter alignment and reinforcement steel spacing into the majoring book in the field notes. If weather permits tomorrow, concrete pouring for the raft foundation can start from 11 AM onwards.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `qwen2.5:3b` (0.94s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'site visit'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
Aaj hamne side visit ke dwaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Upasthit e saahab aur JEE ko nirdeshit kiya gaya ki satting ki alignment aur reinforcement steel ki spacing ko measurement book mein tūrantar darj karen. Yadi kal mausam anukool raha to do baar baarah baje se raṭ foundation ka concreting shūroo kar di jaegi.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'concreting'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
Today, we conducted a site visit where the contractor has completed the excavation work for the bridge's foundation. The supervising engineer and JEE were instructed to immediately enter in the measurement book the alignment of the supporting structure and the spacing of the reinforcement steel. If the weather remains favorable until tomorrow, concrete pouring will commence at least twice daily.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `qwen2.5:3b` (1.47s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'site visit'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke par upasthit e saahab aur JEE ko nirdeshit kiya gaya ki satting ki alignment aur reinforcement steel ki spacing ko measurement book mein turant darj karen. Yadi kal mausam anukool raha to do baar baarah baje se raat foundation ki concreting shuroo kar di jaegi.

Key Decisions and Facts:
- Bridge Foundation excavation work completed by the contractor.
- Upasthit e saahab and JEE instructed to immediately enter alignment of satting and spacing of reinforcement steel in measurement book.
- Concrete pouring for the raat foundation will commence within two days if the weather remains favorable.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `qwen2.5:3b` (0.94s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'site visit'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke par upasthit e saahab aur JEE ko nirdeshit kiya gaya ki satting ki alignment aur reinforcement steel ki spacing ko measurement book mein turant darj karen. Yadi kal mausam anukool raha to do baar baarah baje se raat foundation ki concreting shuroo kar di jaegi.
```

---

### script5: Typical Site Visit & Measurement Dictation $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.396s) | **Refiner Model:** `qwen2.5:3b` (0.95s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'site visit'

**Input Speech Transcription:**
> Aaj hamne side visit ke dvaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke p...

**Refined Document Output:**
```text
Aaj hamne side visit ke dwaan paaya ki contractor ne bridge foundation ka excavation work complete kar liya hai. Mauke par upasthit e saahab aur JEE ko nirdeshit kiya gaya ki satting ki alignment aur reinforcement steel ki spacing ko measurement book mein turtant darj karen. Yadi kal mausam anukool raha to do baar baarah baje se raat foundation ka concreting shuroo kar di jaegi.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `qwen2.5:3b` (0.62s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
The EE and JE verified the MB increase for culvert winding work and cross-checked the rates against the revised SOR item. The contractor has submitted the third RE bill along with a hindrance register and material test certificates. After proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
The E and JE verified the MB increase for the culvert winding work and cross-checked the rates against the revised SOR item. The contractor has submitted the third RE bill along with a hindrance register and material test certificates. Following proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `qwen2.5:3b` (0.6s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
The E and JE verified the MB increase for culvert winding work and cross-checked rates against the revised SOR item. The contractor has submitted the third RE bill along with a hindrance register and material test certificates. After proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item. The contractor has submitted the third RE bill along with the hindrance register and material test certificates. After proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.718s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item...

**Refined Document Output:**
```text
The E and JE verified the MB increase for the culvert winding work and cross-checked the rates with the revised SOR item. The contractor has submitted their third RE bill along with a hindrance register and material test certificates. After proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
E and JE verified the MB increase for the culvert white ink, cross-checked the rates against the revised SOR item. The contractor submitted the third arrival along with a hindrance register and material test certificates after proper technical wetting. Division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `qwen2.5:3b` (0.57s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
E and JE verified the MB increase for culvert white ink and cross-checked the rates against the revised SOR item. The contractor submitted their third arrival along with a hindrance register and material test certificates, after proper technical wetting. Division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `qwen2.5:3b` (0.59s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
E and JE verified the MB increase for the culvert white ink and cross-checked the rates with the revised SOR item. The contractor has submitted the third arrival along with the hindrance register and material test certificates after proper technical wetting. The division will issue a fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `qwen2.5:3b` (0.6s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
[E and JE verified the MB increase for the culvert white ink and cross-checked the rates with the revised SOR item. The contractor has submitted the third arrival along with the hindrance register and material test certificates after proper technical wetting. The division will issue the fresh NIT for the remaining road package by Friday afternoon.]
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.559s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> E and JE verified the MB increase for the culvert white ink and cross checked the rates with the revised SOR item. The c...

**Refined Document Output:**
```text
E and JE verified the MB increase for the culvert white ink and cross-checked the rates against the revised SOR item. The contractor has submitted their third arrival along with a hindrance register and material test certificates after proper technical wetting. Division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `qwen2.5:3b` (2.56s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
ईंड एंजीनियरिंग वेरिफ़िकेट कल्बर्ट वैटिंग और क्रस्ट डाउन सबमिट थर्द एवलएलोन, रिवाइज सो र आंतरिक टेस्ट सर्टिफ़िकेट के लिए मी इनक्रीस बॉट। हिन्द्रेंस रजिस्टर और मेटेर टेस्ट सर्टिफ़िकेट, प्रॉपर्ट टेक्निकल वेटिंग के बाद। डीवीजन विल इशु और फ्रेश एट फौड रोड पैकेज बाय-फ्राउंड, आंतरिक टेस्ट सर्टिफ़िकेट के लिए।
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `qwen2.5:3b` (0.64s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
The ANDY Verify for the Concreting of the Baltimore Whiteing and Crosses Rate with the Revision, SOWs submitted to the COTR along with the Hinduess Registrar's Test Certificate after Property Technical Inspection, Division Issue Report for Fresh Issues in the Remining Road Package BFD have been issued.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
Key decisions and facts from the transcript include:
- ENDE verified the concreting for the Carroll Whiteing & Crosses Rates with the revised tenders submitted to the court.
- The division will issue a third evaluation after property technical weighing, fresh issues were raised by FRIT for the remailing road package.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `qwen2.5:3b` (0.75s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
[Action Item] Verify concrete for the Carroll Whiteing & Crosses Rates with the revised tenders and submit to the third evaluation along with the Hindrance Registration and Material Test Certificate after property technical weighing, division will issue issues for the remaning road package batch dispatched ASAP. 

[Responsible Role/Person] Engineering Department

[Status/Timeline] Pending Response from Division
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.68s) | **Refiner Model:** `qwen2.5:3b` (0.6s)
- **Compatibility:** `suboptimal` — Hindi acoustic model transliterated English words into Devanagari characters.
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'; Missing mandatory technical term: 'NIT'

**Input Speech Transcription:**
> ई एंड जे वेरिफिकेट द मी इनक्रीस फॉर द कल्बर्ट व्हाइटिंग एंड क्रस्ट द रेट्स विथ द रिवाइज सो र इट्स द कॉटर हास एस सबमिट द ...

**Refined Document Output:**
```text
JW verifies the concrete for the Carroll Whiteing & Crossings with the review and tenders submitted to ASR. The third evaluation is done by the Hindrance Registrar and Material Test Certificate after property technical vetting, division issue report for fresh IT for the remining road package dispatched ASAP.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `qwen2.5:3b` (0.64s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
The e and j verified the MB increase for the convert wiring work and cross-checked the rates against the revised SOR item. The contractor has submitted the third RE bill along with the hintrance register and material test certificates. After a thorough technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `qwen2.5:3b` (0.59s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
The e and j verified the MB increase for the convert wiring work and cross-checked the rates against the revised SOR item. The contractor has submitted the third RE bill along with the interim register and material test certificates. Following a thorough technical review, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `qwen2.5:3b` (0.59s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
The e and j verified the MB increase for convert wiring work and cross-checked rates against the revised SOR item. The contractor submitted the third RE bill along with the hintrance register and material test certificates. After thorough technical vetting, the division will issue a fresh NIT for the remaining road package by Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `qwen2.5:3b` (0.34s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'MB'; Missing mandatory technical term: 'SOR'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
[Action Item] Issue the fresh NIT for the remaining road package,
[Responsible Role/Person] Division,
[Status/Timeline] By Friday afternoon.
```

---

### script6: Spoken Dotted Abbreviations & Official Roles $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.345s) | **Refiner Model:** `qwen2.5:3b` (0.62s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'JE'; Missing mandatory technical term: 'RA Bill'

**Input Speech Transcription:**
> The e and j e verified the MB increase for the convert wiring work and cross check the rates with the revised SOR item. ...

**Refined Document Output:**
```text
e and j verified the MB increase for the convert wiring work and cross-checked the rates against the revised SOR item. The contractor has submitted their third RE bill along with the hintrance register and material test certificates. After a proper technical vetting, the division will issue the fresh NIT for the remaining road package by Friday afternoon.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `qwen2.5:3b` (2.18s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
कल सुबार 10 बजे, डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करना होगा। अस्टेड लिए साहब को, बोल कर कमपेरिटे स्टेटमेंट और टेक्निकल वेट्स की समरी फाइल रखना होगा। जहाँ कॉंट्रेक्टर्स, जो कॉण्ट्रेक्ट के पकड़ मिलने के बजाय नहीं आये हैं, इमनस मनी डिपाजिट विलीस करना चाहेंगे।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
Last week at 10 AM, the tender review committee schedule was set for discussion with Assistant Leader. The Compliance Statement and Technical Warrants that were to be presented by contractors who have not attended Quality Assurance Meetings must also be submitted separately. Additionally, a hold money deposit warrant should be sent along with these documents.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
- The tender review committee schedule for yesterday afternoon at Division Office has been confirmed. The prepared comparison statement and technical weights are ready to be submitted by the ASTED LEESAB.
- There will be a separate submission of the retention money waiver application due to contractors who have not attended the quality meeting, which is also ready to be sent.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `qwen2.5:3b` (0.64s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
The tender review committee schedule for yesterday at 10 AM is with ASTED LEASEE. The comparative statement and technical weights report should be ready by the comparator team, which will not allow contractors who have not attended the quality meeting to participate in their meetings. A separate submission for this matter must also be submitted.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.535s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबार दस बजे डिविजन आफिस में टेंडर रिविलेशन कमिटी की सेडूल करनी है अस्टेड लिए साहब को बोल कर कमपेरिटे स्टेट्मेंट और ट...

**Refined Document Output:**
```text
Yesterday at 10 AM, the Tender Review Committee schedule was sent to Mr. Asstd Liasb for him to prepare a comparison statement and technical weights as well which are ready for contractors who haven't attended the meeting yet. Additionally, separate submissions were also submitted regarding their non-payment deposit requests.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
The office Tender Revolution Committee has scheduled a meeting for the comparison of statements and summary of technical bits. This includes discussions on RNI (Rural Infrastructure), JOCT (Joint Operating Control Team) qualification criteria, as well as the submission of documents including money deposit release files. These submissions are necessary to facilitate further progress in relevant projects.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `qwen2.5:3b` (0.51s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
The office tender revolution committee has scheduled a meeting to review the comparative statements and technical summaries for the upcoming project. Additionally, there is an agenda item regarding the submission of qualification criteria documents and the filing of the required monetary deposit. It is important that these items are submitted in time.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `qwen2.5:3b` (0.6s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
The Office Tender Revolution Committee has scheduled a meeting for the comparison of statements and technical bits. The focus is on NIT, RCC M35, RA Bill, SOR, Server, Pipeline status, Site Visit, Concreting, Tender BOQ, and Kid money deposit release file submission criteria as per Joct qualifying standards.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `qwen2.5:3b` (0.31s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
Office Tender Revolution Committee schedule in Sahbolk Comparative Statement or Technical Bits Summary fight RNI, JOCT Qualifying Criteria Meet Neck Money Deposit Release File Submit Kid.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.459s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Office tender revolution committee schedule in Sahbolk comparative statement or technical bits sumry fighting rni, Joct ...

**Refined Document Output:**
```text
The office tender revolution committee has a scheduled meeting on the subject of comparing statements and summarizing technical bits from Sahbolk. There will also be a discussion about qualification criteria for the fight against RNI (RBI National ID). Additionally, there's an item regarding submitting a kid file along with a deposit release document.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `qwen2.5:3b` (2.53s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
कल सुबह दस बजे, डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करना होगा। ऑस्ट्रेलिया साहब को, बोलकर के जवाब में, कम्पेरेटिव स्टेटमेंट और टेक्निकल बिट्स की समरी फाइल रखना होगा। जो कांट्रैक्टर्स क्वालीफायंग क्राडेटेरिया मीट नहीं कर रहे हैं, उनके अनलेस मनी देखित डिपोजिट रिलीज करने की फाइल भी अलग से सबमिट की जाए।
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
Yesterday morning at 10 AM, the Divison Office is scheduled to hold a Tender Revolution Committee meeting. The Australian representative must brief the Competent Statement and Technical Bits document, which has been prepared for contractors who have not passed the Qualification Character Meeting. Additionally, separate submissions should be submitted for those contractors whose preliminary assessments indicate they are unable to attend the qualification character meeting.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
The tender revolution committee schedule is to be finalized by 10 AM today at the division office. The Australian representative will present a qualified contractors statement and technical bits ready for review, which has been submitted by companies not meeting qualification criteria. Additionally, an alternate submission of the assessment results for those who did not qualify must also be sent in separately.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
The tender revolution committee meeting is scheduled for 10 AM today at the division office. The Australian representative needs to brief on the competitive statement and technical bits that are ready for submission by bidders who have not qualified during the pre-qualification meetings. Additionally, an alert should be sent out via email regarding the late submissions from those whose alternate documents need to be released now.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> कल सुबह दस बजे डिवीजन ऑफिस में टेंडर रिवोल्यूशन कमेटी की शेड्यूल करनी है। ऑस्ट्रेलिया साहब को बोलकर कम्पेरेटिव स्टेटमेंट...

**Refined Document Output:**
```text
Today at 10 AM, the tender revolution committee meeting is scheduled in the DevOps office. The Australian representative needs to brief on the competitive statement and technical bits that are ready for contractors who haven't qualified yet. Additionally, separate submissions need to be sent for those contractors whose offline deposits have not been released yet.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
Tender revisions committee ke schedule kal subah das baaje mein karnay ka kam hai. Astrid niyat saahab ko comparative statement aur technical goods ke summary file prakar ready rakha jaega. Jo contractors qualifying criteria nahi meet kar rahe hain, unke money deposit ki release ka file bhi alag se submit ho jayegi.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `qwen2.5:3b` (0.54s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
On the morning of das, a tender revisions committee schedule will be prepared at the division office. Astrid niyat saahab is expected to prepare comparative statements and summaries for technical goods. Additionally, files detailing overdue payments for contractors who have not met the qualifying criteria must also be submitted separately.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
Kal subah division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko comparative statement aur technical goods ki summary file ready rakhna hoga. Contractors qualifying criteria meet nahi kar rahe hain, unka money deposit release ka file bhi alag se submit ki jayega.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
Kal subah division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko comparative statement aur technical goods ki summary file ready rakhani hogi. Jo contractors qualifying criteria meet nahin kar rahe hain, unka money deposit release ki file bhi alag se submit ki jae.
```

---

### script7: Roman Hinglish - Tender Evaluation Meeting $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.363s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'Assistant Engineer'; Missing mandatory technical term: 'earnest money deposit'

**Input Speech Transcription:**
> Kal subah das baje division office mein tender revisions committee ki schedule karni hai. Astrid niyat saahab ko bolkar ...

**Refined Document Output:**
```text
Tender revisions committee ka schedule kal subah das mein hai division office mein. Astrid niyat saahab comparative statement aur technical goods summary file ko saath hi ready karni hoga. Jo contractors qualifying criteria nahi meet kar rahe hain, unka money deposit ki release ke liye bhi separate file submit hona chahiye.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
Actually, in the meeting, it was clearly discussed that the highway maintenance schedule has been delayed. The contractor had promised to address all potholes between km 8 and km 15 within two weeks. However, ground reality indicates that labor mobilization is not taking place as scheduled. Therefore, we must issue an official notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `qwen2.5:3b` (0.65s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
In the meeting, it was clearly discussed that the highway maintenance schedule has been delayed. The contractor had promised to address all potholes between km 8 and km 15 within two weeks. However, in reality, labor mobilization is not taking place as expected. Therefore, we must issue an official notice immediately to ensure compliance with the scheduled work.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
The meeting discussed the delayed highway maintenance schedule with potholes to be repaired between km 8 and km 15 by the contractor within two weeks. However, upon inspection, it was found that labor mobilization has not occurred as promised. Therefore, an official notice must be issued immediately to address this issue promptly.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `qwen2.5:3b` (0.44s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Negation assertion ('not') was inverted or dropped

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
[Action Item] Issue a formal notice to the contractor regarding the delayed pothole repair schedule between km 8 and km 15.
[Responsible Role/Person] Project Manager
[Status/Timeline] Immediate issuance
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (0.698s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, in meeting we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contr...

**Refined Document Output:**
```text
In the meeting, it was clearly discussed that the highway maintenance schedule has been delayed. The contractor promised to address all potholes between km 8 and km 15 within two weeks. However, in reality, labor mobilization hasn't happened yet. So we need to issue an official notice immediately right away.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `qwen2.5:3b` (0.64s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
Actually, during our meeting it was clearly discussed that you are aware the highway maintenance schedule is getting delayed. The contractor has promised that all portholes between kilometer eight and fifteen will be completed within two weeks; however, in reality, they have not mobilized as per their promise. Therefore, we must issue an official SOC cord notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
In our meeting, it was clearly discussed that the highway maintenance schedule is delayed. The contractor has promised that all portholes between kilometers eight and fifteen will be completed within two weeks; however, based on current ground realities, they have not mobilized as expected. Therefore, we must issue an official SOC (Statement of Claim) notice immediately to ensure compliance with our expectations.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `qwen2.5:3b` (0.55s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
The meeting clearly discussed that the highway maintenance schedule is delayed. The contractor promised that all portals between kilometer eight and fifteen would be completed within two weeks; however, in actuality, the ground reality shows they have not mobilized as expected. Therefore, we must issue an official SOC cord notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `qwen2.5:3b` (0.56s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
Actually, during our meeting, you mentioned that the highway maintenance schedule is delayed. The contractor has promised that all portholes between kilometer eight and fifteen will be completed within two weeks, but in reality, they have not mobilized yet. Therefore, we must issue an official SOC cord notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.536s) | **Refiner Model:** `qwen2.5:3b` (0.56s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Forbidden hallucination token detected: you know; Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually, meeting we clearly discuss that you know the highway maintains schedule is getting delayed, the contractor pro...

**Refined Document Output:**
```text
Actually, during our meeting, you know, the highway maintenance schedule is getting delayed. The contractor promised that all portholes between kilometer eight and fifteen would be completed within two weeks, but in reality, they haven't mobilized yet. So we need to issue an official SOC cord notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `qwen2.5:3b` (2.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
एक्चुअली मतलब में, डिटयू नो हाईवे मेंटेन शेड्यूल के लिए वी क्लियरली डिस्कस किया गया। कॉन्ट्रैक्टर प्रॉमिस था, द विदिन टू वीक्स ऑल पोर्ट होल बिट्वीन किलोमीटर एट एंड किलोमीटर फिफ्तीन विल। बी पास्ट बैक्टीरियल ग्राउंड रियलिटी देखकर, लेबर मोबिलाइज हुई नहीं था। सो कि वी मस्ट इशू आन ऑफिशियल सोकोज नोटिस इमीडिएटली पेदर राहने।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
At the actual meeting, I clearly discussed with You that the ducting schedule for this gate has been delayed and the contractor promised to have it installed within a fortnight between kilometer one and kilometer fifty. It seems unlikely that labor mobilization has taken place; therefore, I must inform you immediately about issuing an official notice of non-compliance.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `qwen2.5:3b` (3.08s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Hallucinated numeric figures not in speech: 50

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
एक्चुअली मतलब मतलब, मतलब मीटिंग में डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, कॉन्ट्रैक्टर प्रॉमिस वीक्स ऑल पोर्ट होल बिट्वीन किलोमीटर एट एंड किलोमीटर फिफ्तीन विल बी पास्ट बैक्टीरियल ग्राउंड रियलिटी देखकर लगता है कि लेबर मोबिलाइज नहीं हुई है, सो वी मस्ट इशू आन ऑफिशियल सोकोज नोटिस इमीडिएतली।

KEY POINTS:
- The highway maintenance schedule for this gate is delayed.
- The contractor promises to have the port hole filled within a week between kilometer and 50, but based on bacterial ground reality it seems labor mobilization has not happened yet.
- V must issue an official stop work notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `qwen2.5:3b` (2.4s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
एक्चुअली मतलब मीटिंग में डिस्कस करने पर, यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड हुई है। कॉन्ट्रैक्टर प्रॉमिस दैट लाइक विदिन टू वीक्स ऑल पोर्ट होल बिट्वीन किलोमीटर एट एंड किलोमीटर फिफ्तीन विल। बैच्यांस रेलिज मोबिलाइज नहीं हुई है, सो वी मस्ट इशू आन ऑफिशियल सोकोज नोटिस इमीडिएतली।
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.712s) | **Refiner Model:** `qwen2.5:3b` (0.58s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> एक्चुअली मतलब मीटिंग में वी क्लियरली डिस्कस दैट यू नो द हाईवे मेंटेन शेड्यूल इस गेटिंग डिलेड, द कॉन्ट्रैक्टर प्रॉमिस दैट...

**Refined Document Output:**
```text
At the actual meeting, I clearly discussed with DU about scheduling this gate delay. The contractor promised like a week to the port hole between kilometer and fifty-two bypass back bacterial ground reality suggests that mobilization has not happened yet. So, V needs to issue an official notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
In the actual meeting, it was clearly discussed that the highway maintenance schedule is being delayed. The contractor has promised to complete work between kilometer 8 and kilometer 15 within two weeks. However, upon inspection on site, it appears that labor mobilization has not taken place as expected. Therefore, we must issue an official so cause notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `qwen2.5:3b` (0.64s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
During the meeting, it was clearly discussed that the highway maintenance schedule is being delayed. The contractor has promised to complete work between kilometer 8 and kilometer 15 within two weeks. However, upon inspection on site, it appears that labor mobilization has not occurred as expected. Therefore, we must issue an official stop-work notice immediately.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `qwen2.5:3b` (0.7s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
During the MATLAB meeting, it was clearly discussed that the highway maintenance schedule is delayed. The contractor promised that all work between kilometer 8 and kilometer 15 will be completed within two weeks. However, upon ground reality inspection, it appears that labor mobilization has not occurred as expected. Therefore, an official stop notice must be issued immediately to ensure compliance with the scheduled timeline.
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `qwen2.5:3b` (0.43s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'highway maintenance'; Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
[Action Item] Issue a formal Notice of Delay to the Contractor regarding the hold between kilometer 8 and kilometer 15.
[Responsible Role/Person] Project Manager
[Status/Timeline] Immediate issuance
```

---

### script8: Casual Speech with Verbal Hesitations & Fillers $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.357s) | **Refiner Model:** `qwen2.5:3b` (0.63s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'show cause notice'

**Input Speech Transcription:**
> Actually matlab meeting mein we clearly discuss that you know the highway maintenance schedule is getting delayed. The c...

**Refined Document Output:**
```text
In the meeting, it was clearly discussed that the highway maintenance schedule is getting delayed. The contractor promised that work will be completed between kilometer 8 and kilometer 15 within two weeks. However, on-site reality shows that labor mobilization hasn't happened yet. So we must issue an official stop-work notice immediately to ensure progress.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `qwen2.5:3b` (2.84s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
पॉर्स के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस ने 12 से 15 तक रोड फॉर्मिशन कटिंग टेप्री में हाल्ट कर दिया है। इस पर रेबिन्यू डिपार्टमेंट और संचार सदन (SDM) से सहयोग हुआ जोएंड इसिफेक्शन कंडेक्ट हो चुका था। पॉर्स और ड्रिमिंग वाटर पायपलाइन्स की सिफ्टिंग के महत्त्वपूर्ण अभिन्नता को जल सस्तान से टापट करने पर भी इंजीनियरिंग सेकुणद लगभग अभी तक है।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 2023

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
The approved hold on the pending approval for PORS at DFF office has been extended until January 15, 2023. Coordination with SDM and members of the Reinforcement Department has already taken place to conduct the road forming concrete works. However, estimates for electrical porting and drinking water pipelines have not yet been finalized based on utility tender quotations.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `qwen2.5:3b` (0.73s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
Paring the speech transcript into a high-level executive summary:

- The approval for Pors ke liye saapling panding vaned DFF office has been halted from March 12 to 15. Engineering and SDM have conducted an inspection, but electrical porrs and drinking water pipelines' utility testing is yet to be completed by the site maintenance department.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `qwen2.5:3b` (2.47s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस 12 से 15 में रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी गई है, रेबिन्यू डिपार्टमेंट और SDM साहब के साथ इसिफेक्शन कंडेक्ट हो चुकी है। लेकिन इलेक्रिकल पॉर्स और ड्रिमिंग वाटर पायप्स की यूटिटी सिफ्टिंग का इस्टिमेट अभी तक जल संशोधन से टापत हुआ नहीं है।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.559s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> पॉरस के लिए से अप्रूबल इस्टिल पैंडिंग विद दीएफो आफिस इसलिए चेनिस 12 से 15 तक रोड फॉर्मिशन कटिंग टेंप्रेरिली हाल्ट कर दी ...

**Refined Document Output:**
```text
For the PORs and drinking water pipelines, preliminary estimates have been conducted by DFF office till November 12-15. The Engineering Department along with the SDM has already carried out the inspection, but the electrical PORs and drinking water pipeline utilities’ suitability testing hasn’t been finalized yet due to budget constraints.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `qwen2.5:3b` (0.5s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
Forest client's approval for the project remains pending with the TFO office. Therefore, temporary hold is in place on road formation cutting until further notice from the revenue department or SDM Sahb Satan regarding the installation of electrical poles and drinking water pipeline shifting estimates.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `qwen2.5:3b` (0.54s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
The Forest client's approval for the project remains pending with the TFO office. In the interim, road formation cutting is temporarily halted due to revenue department approvals and SDM Sahb Satan conducting work related to electrical pole installation or water pipeline shifts. The estimates for these activities are still being finalized.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `qwen2.5:3b` (0.49s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
Key decisions and facts:

- Forest clients approval for the project remains pending with TFO office.
- Road formation cutting is temporarily halted due to revenue department's involvement.
- Electrical pole installation or drinking water pipeline shift estimates are being prepared by SDM Sahb Satan.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `qwen2.5:3b` (1.0s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
[Action Item] Obtain Forest clients' approval from TFO office.
[Responsible Role/Person] Project Manager
[Status/Timeline] Pending, awaiting response

[Action Item] Conduct road formation cutting temporarily until Forest clients' approval is obtained.
[Responsible Role/Person] Site Engineer
[Status/Timeline] In progress, pending approval for continuation

[Action Item] Estimate for ho chucken electrical poles or drinking water pipeline shifting.
[Responsible Role/Person] Cost Estimator
[Status/Timeline] Pending, awaiting response from Forest clients
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.526s) | **Refiner Model:** `qwen2.5:3b` (0.46s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Forest clients approval is still pending with the TFO office, is lin is twelve fifteen to road formation cutting tempora...

**Refined Document Output:**
```text
Forest client's approval for the project still needs to be finalized with the TFO office. For now, road formation cutting is temporarily halted due to revenue department approvals or SDM Sahb Satan conducting the electrical poles and drinking water pipeline shifts' estimates.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `qwen2.5:3b` (2.55s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
Forrest के लिए अप्रूवल, यह स्टेला पेंडिंग विथ द टीफो ऑफिस, इसके चेन रोड फॉर्मेशन कटिंग टेम्परेरी हार्ड कर दी गई है। रेवेन्यू डिपार्टमेंट और सडीएम साहब के साथ जोइन इंस्पेक्शन कंडक्ट हुआ है, लेकिन एलेक्ट्रिकल पोल्स और ड्रिमिंग वाटर पायपलाइन्ज की यूटिटी सेफ्टींग का अस्तेमेट अभी तक सुधार संस्थान से मिलकर प्राप्त नहीं हुआ है।
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `qwen2.5:3b` (0.67s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 50; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
For the approval of Forest, this steel pendulum with the Teflon® coating has been hardened from 12 to 50 degrees. The Revenue Department and S.D.M have conducted a joint inspection, but estimates for electrical poles and drinking water pipelines' safety inspections are yet to be received from the local utility company.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `qwen2.5:3b` (0.52s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
For Forest, the approved PPE for TWelve to Fifty road forming hardening is in place. Revenue Department and SMD have conducted joint inspection, but electrical poles and drinking water pipelines' utility testing has not yet been received from Utility Company.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Hallucinated numeric figures not in speech: 12, 50

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
Forrest for approval with the TFE office, this steel pendulum from 12 to 50 degree road forming casting temperature has been set. Revenue department and S&D partner's inspection is conducted, but electrical poles and drinking water pipelines' utility safety assessment hasn't arrived yet from Utility company.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.694s) | **Refiner Model:** `qwen2.5:3b` (0.57s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'SDM'; Missing mandatory technical term: 'utility shifting'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> फॉरेस्ट के लिए अप्रूवल इस स्टिल पेंडिंग विथ द टीफो ऑफिस, इसलिए चेन इस ट्वेल्व से फिफ्टीन तक रोड फॉर्मेशन कटिंग टेम्परेरी...

**Refined Document Output:**
```text
For the approval, road forming temperature for the project at Forest has been set between twelve and fifty degrees Celsius. The Revenue Department and SMD have conducted a joint inspection, but estimates for electrical poles and drinking water pipelines' suitability testing are yet to be received from the utility company.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
For the purpose of force-ke lie approval, it is still pending with the TFO office. Road formation cutting in Chinese will be temporarily halted from 12 to 15 for a period. Joint inspection has been conducted by the Revenue department and SDM saahab, but estimates regarding the shifting of electrical poles and drinking water pipeline have not yet arrived from the construction site.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `qwen2.5:3b` (0.61s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
The approval for the force lies pending with the TFO office. Road formation cutting has been temporarily halted from 12 to 15 Chinese until further notice. Joint inspections conducted by the Revenue Department and SDM have yet to receive a quotation estimate from the utility service provider regarding the relocation of electrical poles and the drinking water pipeline.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `qwen2.5:3b` (0.57s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
Force Ke Lie Approval is still pending with the TFO office. Road formation cutting in Islie Chinese 12-15 has been temporarily halted by Revenue department and SDM Sahab for joint inspection, but estimates for shifting of electrical poles and drinking water pipeline have not yet arrived from the utility station.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `qwen2.5:3b` (0.62s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
Force ke lie approval is still pending with the TFO office. Road formation cutting in Islie Chinese from 12 to 15 will be temporarily halted. Revenue department and SDM saahab have scheduled a joint inspection, but no estimate for shifting of electrical poles and drinking water pipeline has been received from the construction site yet.
```

---

### script9: Bilingual Land Clearance & Forest Hindrance $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.373s) | **Refiner Model:** `qwen2.5:3b` (0.65s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'DFO'; Missing mandatory technical term: 'forest clearance'; Missing mandatory technical term: 'utility shifting'

**Input Speech Transcription:**
> Force ke lie approval is still pending with the TFO office. Islie Chinese 12 se 15 tak road formation cutting temporaril...

**Refined Document Output:**
```text
The approval for the force is still pending with the TFO office. Road formation cutting in Chinese area will be temporarily halted from 12 to 15 PM. A joint inspection by the revenue department and SDM saahab has been scheduled, but estimates for shifting electrical poles and drinking water pipeline have not yet come in from the construction site.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🌐 Bilingual Field Note` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `qwen2.5:3b` (1.99s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
इस बुक में मीजरमेंट पर हुई वेरिफाय के बाद, अर्थवर्क कॉंटिटी में कुछ वैरिशन होकर एप्रूब्ट बिल्यू आइटम से लगभग पारसेंट अधिक हैं। इसलिए, कॉंट्रेक्टर को फाडनल बिल रिलीस करने से पहुँचा जाने पर यह रिव क्योटी डिपॉजिट रिफंड होने में प्रतिबद्धि नहीं होगी।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇬🇧 Official English Memo` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `qwen2.5:3b` (0.46s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
After the verification of the master budget, it was noted that there are some variances in the project estimate within the contract limits. This will prevent a refund deposit from being credited to the final bill release for the contractor.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `📋 Executive Summary` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `qwen2.5:3b` (1.84s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
इस आपने मीजर्मेंट बुक वेरिफाय करने पर से पता चला कि अर्थवर्क कॉंटिटी में कुछ वैरिशन हैं, जो एप्रूब्ट ब्योक्यू आइटम से लगभग 10% अधिक हैं। इस कारण, कॉन्ट्रेक्टर को फाएनल बिल रिलीस करने से पहले रिव क्योटी डिपोजिट रिफंड नहीं हुआ।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💡 Action Items & Tasks` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `qwen2.5:3b` (1.74s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
इमेज मेंबर्स बुक प्रदान के बाद पाया गया है कि अर्थवर्क कोंटिटी में कुछ वैरिशन है, जो एप्रूब्ट ब्योक्यू आइटम से लगभग 10% अधिक है। इस कारण, कंट्रेक्टर को फाइनल बिल रिलीस करने से पहले रिव क्योटी डिपोजिट रिफंड नहीं हुआ।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💬 Conversational Roman Hinglish` (ASR: `smart_bilingual`)
- **ASR Preset:** `smart_bilingual` (1.352s) | **Refiner Model:** `qwen2.5:3b` (0.54s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 10; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> इस आपने मीजर्मेंट बुक वेरिफाय करने के बाद पाया की अर्थवर्क कॉंटिटी में कुछ वैरिशन है जो एप्रूब्ट ब्योक्यू आइटम ब्योक्यू ...

**Refined Document Output:**
```text
After the verification of the mastermangement book, it appears that there are some variances in the work quantity within the project budget which exceed about 10% of the approved tender items. This will prevent the contractor from releasing the final bill and deposit refund.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🌐 Bilingual Field Note` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `qwen2.5:3b` (0.81s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
Verify the measurement book for arithmetic quantities and check the Jopt BOQ (Job Order Bill of Quantities). Ensure that all Q limits are adhered to, as well as Lgb Sat percent accuracy. The contractor will be finalizing their revised estimate or time extension approval from competent authorities without any liability period if they successfully complete the new project within the stipulated timeline. In such a case, there would also be no need for a deposit refund neck.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇬🇧 Official English Memo` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `qwen2.5:3b` (0.86s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
Verify the measurement book for accurate quantities and review the Bill of Quantities (BOQ) to ensure that all Jopt limits are adhered to. The contractor will be granted final release with a revised estimate or time extension approval by competent authorities, thereby avoiding any potential legal liability period if they successfully complete the new project within the stipulated timeframe. Additionally, this decision ensures that the site visit and concreting activities can proceed without delay, allowing for the timely refund of the outstanding deposit.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `📋 Executive Summary` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `qwen2.5:3b` (0.6s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
Key decisions and facts from the transcript include:
- Verification of measurement quantities is required for Jopt BOQ.
- Limits set by Lgb Sat percent are to be adhered to.
- The contractor will receive a revised estimate or time extension approval from competent authorities, without liability period if successfully completing new works with no deposit refund due.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💡 Action Items & Tasks` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `qwen2.5:3b` (2.54s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'; Hallucinated numeric figures not in speech: 7, 14, 30

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
[Action Item] Verify measurement book arithmetic quantities and check the Jopt BOQ for discrepancies.
[Responsible Role/Person] Engineering Department
[Status/Timeline] Immediate

[Action Item] Ensure all limits are adhered to as per Lgb Sat percent agreement.
[Responsible Role/Person] Contract Management Team
[Status/Timeline] Immediate

[Action Item] Obtain final revised estimate or time extension approval from competent authorities if necessary.
[Responsible Role/Person] Legal Department and Project Manager
[Status/Timeline] Within 7 days of receipt of revised estimates.

[Action Item] Ensure successful completion of the project within the new deadline, without incurring liability period penalties.
[Responsible Role/Person] Project Management Team
[Status/Timeline] Within 30 days after obtaining final approval

[Action Item] Arrange for a site visit to confirm progress and address any remaining issues.
[Responsible Role/Person] Site Supervisor
[Status/Timeline] Within 14 days of receiving revised estimates.

[Action Item] Prepare and submit tender documents, including BOQ (Bill of Quantities).
[Responsible Role/Person] Tendering Team
[Status/Timeline] Within 2 weeks after site visit confirmation

[Action Item] Negotiate with the contractor for final deposit refund or extension.
[Responsible Role/Person] Finance Department
[Status/Timeline] Within 14 days of successful completion and receipt of all approvals.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_english`)
- **ASR Preset:** `instant_english` (0.565s) | **Refiner Model:** `qwen2.5:3b` (0.75s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'security deposit'; Missing mandatory technical term: 'defect liability'

**Input Speech Transcription:**
> Measurement book verify arth quantity mechan, Jopt BOQ It'm Q limits, Lgb Sat percent addict. Contractor को final will r...

**Refined Document Output:**
```text
To ensure accuracy and clarity in the measurement book verification for quantities related to Jopt BOQ (Job Order Purchase Bill), it's crucial that all limits are adhered to. The contractor will be released from their revised estimate or time extension approval by competent authorities, which must successfully complete the project within the stipulated period without any liability issues. If they fail to do so, a new killing deposit refund may be required.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🌐 Bilingual Field Note` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `qwen2.5:3b` (3.29s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
साहब द्वारा मेजरमेंट बुक पर वेरीफाई किया गया है, जहाँ अर्थवर्क क्वांटिटी में कुछ वेरिशन दिखाए रखे गए हैं। ये वेरि�शन पीओक्यू आइटम बीओक्यू से लगभग सात परसेंट का मुल्य अधिक हैं। कांट्रेक्टर को फाइनल बिल के रिलीज करने से पहले, रिवाइज एस्टीमेट और टाम एक्सटेंशन अप्रॉवल को जुड़ाए गए अथॉरिटी से पहुंचना आवश्यक है। डिफेक्ट लायबिलिटी पीरियोड कम्प्लीट नहीं होने से, सिक्योरिटी डिपोजिट रिफंड नहीं किया जाएगा।
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇬🇧 Official English Memo` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `qwen2.5:3b` (0.83s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
After the major book verification, it was noted that there were some variances in the quantity of the architectural drawings (ARQ) which exceeded approximately seven percent compared to the approved P.O.Q. limit. It is mandatory for the contractor to obtain final bill approval from the competent authority before releasing the Final Estimate and team extension approvals. Until the defect liability period has been successfully completed, no security deposit refund will be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `📋 Executive Summary` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `qwen2.5:3b` (0.68s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
The major book verifications revealed some variances in the project's engineering quantities that exceed about seven percent of the approved APROPO BOP quantity. Final bill release can only proceed after obtaining approval from the competent authority for re-estimation and time extension. Until the defect liability period is successfully completed, security deposit refunds cannot be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💡 Action Items & Tasks` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `qwen2.5:3b` (0.74s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Hallucinated numeric figures not in speech: 7; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
The project manager has found some variances in the construction quantity within the budget estimate, which exceed about 7% of the approved Apropos POQ items. Before releasing the final bill to the contractor, it is mandatory for the revision estimator and team extension approver to approve the estimation. Until the defect liability period completes successfully, no security deposit will be refunded.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💬 Conversational Roman Hinglish` (ASR: `instant_hindi`)
- **ASR Preset:** `instant_hindi` (0.818s) | **Refiner Model:** `qwen2.5:3b` (0.8s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'measurement book'; Missing mandatory technical term: 'BOQ'; Hallucinated numeric figures not in speech: 7; Negation assertion ('नहीं') was inverted or dropped

**Input Speech Transcription:**
> साहब ने मेजरमेंट बुक वेरीफाई करने के बाद पाया कि अर्थवर्क क्वांटिटी में कुछ वेरिशन है जो एप्रोप पीओक्यू आइटम बीओक्यू लिम...

**Refined Document Output:**
```text
After the major book verification, it was found that there are some variances in the quantity of the engineering work order (EWO) which exceed about 7% of the approved PPO quantities. Before releasing the final bill to the contractor, a review and approval from the competent authority for revised estimate and time extension is mandatory. Until the defect liability period completes successfully, no security deposit refund will be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🌐 Bilingual Field Note` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.77s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
After verifying the measurement book, it was found that there is a variation in the arthabhar quantity within the approved BOQ item, exceeding by less than one percent of the BOQ limit. It is pending for final bill release from the contractor, which requires prior revised estimate and time extension approval from competent authorities. Until the defect liability period successfully concludes, no refund on deposit will be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `🇬🇧 Official English Memo` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.71s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
After verifying the measurement book, it was found that there are variations in the arthabhar quantity compared to the approved BOQ items, with excess exceeding a slight percentage of one percent. The final bill release from the contractor is pending approval by the competent authority after receiving prior revised estimates and time extension approvals. Until the defect liability period successfully concludes, no refund on deposits will be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `📋 Executive Summary` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.66s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
The measurement book verification revealed variations in the arthabhar quantity compared to the approved BOQ items, with these exceeding by at least 1% of the BOQ limit. The contractor is required to obtain final bill release approval from competent authorities after receiving the revised estimate and time extension. Until the defect liability period successfully concludes, no deposit refund will be made.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💡 Action Items & Tasks` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.86s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'EE'; Missing mandatory technical term: 'security deposit'

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item, BOQ limit se lagabhag saat percent adhik hai. Contactor ko final bill release karne se poorv revised estimate aur time extension approval competent authority se lena anivaary hai. Jab tak defect liability period successfully complete nahin hota, tab tak deposit refund nahin kiya jaega.
```

---

### script10: Financial Audit, Variations & Security Deposit $\times$ `💬 Conversational Roman Hinglish` (ASR: `roman_hinglish`)
- **ASR Preset:** `roman_hinglish` (0.616s) | **Refiner Model:** `qwen2.5:3b` (0.68s)
- **Compatibility:** `optimal` 
- **Status:** ❌ Codal Violations: Missing mandatory technical term: 'security deposit'; Hallucinated numeric figures not in speech: 10

**Input Speech Transcription:**
> Is aapne measurement book verify karne ke baad paaya ki arthabhar quantity mein kuchh variation hai jo approved BOQ item...

**Refined Document Output:**
```text
After verifying the measurement book, it was found that there is a variation in the arthabhar quantity compared to the approved BOQ item, which exceeds by about 10% of the BOQ limit. The final bill release from the contractor now requires prior approval from the competent authority. Until the defect liability period successfully completes, no refund on deposit will be given.
```

---

