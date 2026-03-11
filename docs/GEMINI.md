## **System Requirement: Local Voice-to-Text AI Assistant on Ubuntu**

### **Objective**

To develop a **fully local, offline-capable voice-to-text AI assistant** on **Ubuntu 20.04**, which allows the user to record speech, convert it into text, refine that text using a local AI model, and easily copy the final output—**without any paid services or cloud dependency**.

---

### **Key Functional Requirements**

1. **Voice Recording Interface**

   * A simple **trigger mechanism** (keyboard shortcut, command, or small GUI menu).
   * On activation, the system should:

     * Start audio recording from the microphone.
     * Allow stopping the recording manually.
   * Recorded audio should be stored temporarily in a local file.

2. **Speech-to-Text Conversion**

   * The recorded audio must be converted into text using a **local, open-source speech-to-text engine**.
   * No internet connection or paid API should be required.
   * The transcription should support **natural spoken language**.

3. **AI-Based Text Refinement**

   * The raw transcribed text should be passed to a **local AI model** running via **Ollama**.
   * The AI should:

     * Clean up grammar and sentence structure.
     * Convert spoken language into **clear, well-formatted written text**.
     * Optionally follow user-defined instructions (e.g., “make it formal”, “summarize”, “convert to notes”).

4. **Output & Copy Functionality**

   * The final AI-processed text should be:

     * Displayed clearly (terminal or lightweight GUI).
     * Automatically copied to the **system clipboard**, or
     * Provide a **copy button/command** for easy reuse in documents, emails, or code.

5. **System-Level Integration**

   * The system should work **system-wide** on Ubuntu:

     * Can be invoked from anywhere (hotkey / tray / command).
     * Lightweight and fast startup.
   * Python-based implementation is preferred.

---

### **Technical Constraints**

* **Operating System:** Ubuntu 20.04
* **Language:** Python
* **AI Model:** Local Ollama models (e.g., LLaMA / Mistral variants)
* **Speech-to-Text:** Fully open-source, local engine
* **Cost:** Zero (no paid APIs, subscriptions, or cloud services)
* **Privacy:** All data remains on the local machine

---

### **Non-Functional Requirements**

* Easy to extend (prompt tuning, different models).
* Modular design (audio → transcription → AI processing → output).
* Reusable for future automation (notes, reports, emails).
* Clear documentation and reproducible setup.

---

### **Expectation from Existing Solutions**

* Prefer **already available open-source projects on GitHub** that:

  * Support local speech-to-text.
  * Can integrate with Ollama or local LLMs.
* If not available as a single system, provide guidance to **combine existing open-source components** into one workflow.

As initial idea read @idea.md file