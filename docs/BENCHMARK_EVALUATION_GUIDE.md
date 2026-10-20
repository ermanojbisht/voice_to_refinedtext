# 🏛️ PWD Voice Refiner — Benchmark Evaluation Guide & Matrix Specification

This document provides the standard procedure for conducting comprehensive multi-scenario speech testing across all 10 departmental benchmark scripts.

---

## 📁 Directory Architecture

```text
benchmarks/
├── scripts/                         # 10 canonical paragraph scripts
│   ├── script1.txt                  # System Governance & Documentation Pipeline
│   ├── script2.txt                  # Bridge Structural Inspection & M35 Testing
│   ├── script3.txt                  # Administrative Directive & Fiscal Audit
│   ├── script4.txt                  # Hill Road Drainage & Retaining Wall Quality
│   ├── script5.txt                  # Typical Site Visit Hinglish & Raft Concreting
│   ├── script6.txt                  # Dotted Abbreviations (e.e., j.e., m.b., r.a. bill)
│   ├── script7.txt                  # Roman Hinglish Tender Evaluation Memo
│   ├── script8.txt                  # Casual Speech with Fillers (matlab, you know)
│   ├── script9.txt                  # Forest Clearance & Land Hindrance Dictation
│   └── script10.txt                 # Financial Audit, BOQ Variations & Security Deposit
├── recordings/                      # Drop your recorded WAV / MP3 files here
│   ├── script1.wav (or script1.mp3)
│   ├── script2.wav ...
│   └── script10.wav
├── matrix_specs.json                # Codal rules, mandatory terms & forbidden tokens
├── benchmark_evaluator.py           # Automated evaluation runner & scorecard engine
└── BENCHMARK_REPORT.md              # Auto-generated executive comparison report
```

---

## 🎙️ Recording Instructions (Using Audacity or Any Mic)

1. Open **Audacity** (or your preferred sound recorder / phone voice recorder).
2. Set recording format to **Mono, 16 kHz or 44.1 kHz, 16-bit PCM** (or save as `.mp3` / `.wav`).
3. Read the designated script from [`benchmarks/scripts/`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts) in your natural speaking pace.
4. Export the file into [`benchmarks/recordings/`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/recordings) using the matching name:
   - `script1.wav` or `script1.mp3`
   - `script2.wav` or `script2.mp3`
   - ... up to `script10.wav` or `script10.mp3`

> [!NOTE]
> If you have not recorded audio for a script yet, [`benchmark_evaluator.py`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/benchmark_evaluator.py) automatically uses the text file as a dry-run input so you can test LLM refinement immediately!

---

## 🚀 How to Run the Benchmark Evaluator

Run all scripts across all modes:
```bash
.venv/bin/python benchmarks/benchmark_evaluator.py
```

Run a specific script only (e.g. `script1` or `script6`):
```bash
.venv/bin/python benchmarks/benchmark_evaluator.py script1
```

The evaluator will execute every script against the configured language modes, check for hallucinations and language purity, and update [`benchmarks/BENCHMARK_REPORT.md`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/BENCHMARK_REPORT.md).

---

## ⚖️ "Justified" Decision Logic Explained

When evaluating outputs, the system checks whether the output is **expected as per the active configuration**:

| Mode | Spoken Speech | Justified Behavior | Codal Violation / Bug |
| :--- | :--- | :--- | :--- |
| **`bilingual`** | Pure English (`script1`, `script2`) | 100% English. Proper civil terms (`M35`, `load test`). Zero Hindi translation. | Any Devanagari translation or invented acronyms `(IAR), (SUS)`. |
| **`bilingual`** | Pure Hindi (`script3`, `script4`) | 100% Formal Devanagari Hindi. Zero English translation. | Outputting English text or introductory preambles. |
| **`bilingual`** | Mixed Hinglish (`script5`, `script7`) | Natural technical code-switching (Latin for engineering words, Devanagari for grammar). | Forcing English words into Devanagari or translating Hindi verbs to English. |
| **`pure_english`** | Any Language | 100% English. If spoken in Hindi/Hinglish, translates to formal official English. | Untranslated Hindi words; grammar breakdown. |
| **`pure_hindi`** | Any Language | 100% Formal Hindi (Devanagari script), keeping technical acronyms in English. | Echoing English sentences without Hindi formulation. |
| **`translate`** | English | Professional Hindi translation. | English echoed back. |
| **`translate`** | Hindi | Professional English translation. | Hindi echoed back. |

---

## 📜 Complete Text of All 10 Benchmark Scripts

### Script 1: System Governance & Documentation Pipeline ([`script1.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script1.txt))
> *"This consideration I believe it would be more appropriate to have the system automatically updated and update the manual to ensure it is always current. While reviewing the technical guidelines, we noticed that several procedural references are outdated and require immediate revision. The software engineering team should automate the documentation pipeline so that whenever a new release is deployed, all user guides and engineering manuals synchronize without requiring manual intervention."*

### Script 2: Bridge Engineering & Structural Inspection ([`script2.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script2.txt))
> *"The Executive Engineer and Assistant Engineer conducted a detailed structural inspection of the multi-span bridge at chainage twenty-four point five. The concrete core testing confirmed that the pier caps and abutments comply with the designated M35 grade specifications. However, the elastomeric bearings on pier number three show minor lateral displacement and must be recalibrated before the load test is officially scheduled next Tuesday."*

### Script 3: Administrative Directive & Fiscal Audit ([`script3.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script3.txt))
> *"मुख्य अभियंता महोदय ने मंडल के सभी अधिशासी अभियंताओं को सख्त निर्देश जारी किए हैं कि वित्तीय वर्ष की समाप्ति से पूर्व सभी अवशेष देयकों का सत्यापन अनिवार्य रूप से पूर्ण कर लिया जाए। निर्माण कार्यों की प्रगति में अनावश्यक विलंब करने वाले ठेकेदारों के विरुद्ध अनुबंध की शर्तों के अनुसार दंडात्मक कार्रवाई प्रस्तावित की जाए। आगामी सोमवार को आहूत समीक्षा बैठक में सभी खंडों की अद्यतन प्रगति रिपोर्ट प्रस्तुत करना सुनिश्चित करें।"*

### Script 4: Hill Road Quality & Drainage Inspection ([`script4.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script4.txt))
> *"पर्वतीय मार्ग के डामरीकरण और चौड़ीकरण कार्य के स्थलीय निरीक्षण के दौरान जल निकासी नालियों का निर्माण संतोषजनक पाया गया। संवेदनशील ढलानों पर भूस्खलन रोकने हेतु आरसीसी रिटेनिंग वॉल और गेबियन संरचनाओं का कार्य तेजी से प्रगति पर है। सहायक अभियंता को निर्देश दिए गए हैं कि बिटुमिनस कंक्रीट बिछाने से पूर्व सब-बेस की समतलता और सघनता की प्रयोगशाला जांच रिपोर्ट अविलंब संकलित करें।"*

### Script 5: Typical Site Visit Hinglish & Raft Concreting ([`script5.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script5.txt))
> *"आज हमने site visit के दौरान पाया कि contractor ने bridge foundation का excavation work complete कर लिया है। मौके पर उपस्थित EE साहब और JE को निर्देशित किया गया कि shuttering की alignment और reinforcement steel की spacing को measurement book में तुरंत दर्ज करें। यदि कल मौसम अनुकूल रहा, तो दोपहर बारह बजे से raft foundation की concreting शुरू कर दी जाएगी।"*

### Script 6: Dotted Abbreviations (e.e., j.e., m.b., r.a. bill, s.o.r., n.i.t.) ([`script6.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script6.txt))
> *"The e.e. and j.e. verified the m.b. entries for the culvert widening work and cross-checked the rates with the revised s.o.r. items. The contractor has submitted the third r.a. bill along with the hindrance register and material test certificates. After proper technical vetting, the division will issue the fresh n.i.t. for the remaining road package by Friday afternoon."*

### Script 7: Roman Hinglish Tender Evaluation Memo ([`script7.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script7.txt))
> *"Kal subah 10 baje division office mein tender evaluation committee ki meeting schedule karni hai. Assistant Engineer sahab ko bolkar comparative statement aur technical bids ki summary file ready rakhni hogi. Jo contractors qualifying criteria meet nahi kar rahe hain, unka earnest money deposit release karne ki file bhi alag se submit ki jaye."*

### Script 8: Casual Speech with Verbal Hesitations & Fillers ([`script8.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script8.txt))
> *"Uh actually matlab meeting mein we clearly discussed that, you know, the highway maintenance schedule is getting delayed. The contractor promised that, like, within two weeks all potholes between kilometer eight and kilometer fifteen will be patched. But actually ground reality dekh kar lagta hai ki labor mobilize nahi hui hai, so we must issue an official show cause notice immediately."*

### Script 9: Forest Clearance & Land Hindrance Dictation ([`script9.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script9.txt))
> *"Forest clearance approval is still pending with the DFO office, isliye chainage twelve se fifteen tak road formation cutting temporarily halt kar di gayi hai. Revenue department aur SDM sahab ke sath joint inspection conduct ho chuki hai, lekin electrical poles aur drinking water pipelines ki utility shifting ka estimate abhi tak jal sansthan se prapt nahi hua hai."*

### Script 10: Financial Audit, BOQ Variations & Security Deposit ([`script10.txt`](file:///media/manoj/datadisk_linux/pythonprojects/voice_to_refinedtext/benchmarks/scripts/script10.txt))
> *"EE sahab ne measurement book verify karne ke baad paya ki earthwork quantity mein kuch variations hain jo approved BOQ limit se lagbhag saat percent adhik hain. Contractor ko final bill release karne se purv revised estimate aur time extension approval competent authority se lena anivarya hai. Jab tak defect liability period successfully complete nahi hota, tab tak security deposit refund nahi kiya jayega."*
