# Specification: Interactive Evening Review Extension for `voice_to_refinedtext`

## 1. Issue Statement & Objective
The current system successfully captures audio via the `Ctrl+Alt+V` hotkey, processes it through an audio-to-text pipeline, refines it using a local model, and pastes the final text into the active cursor window. 

While highly efficient for real-time dictation, it lacks structural orchestration for multi-step reflective tasks like daily logging. If the user returns from the office at the end of the day and forgets to manually create, open, and organize an Obsidian daily note, the tool cannot assist.

**Objective:** Introduce an interactive, automated "Evening Review" workflow that sequentially prompts the user for distinct daily milestones (Focus Word, Achievements, Tomorrow's Priorities, and Wellness/PTSD Logs). It must write these directly to local Obsidian Markdown files based on user prompts without breaking, altering, or delaying standard daytime text-injection functionality.

---

## 2. Initial Broad Solution
To introduce this feature without modifying the core functionality of the daytime tool, we will use a **State-Driven Routing Pattern**. 

A lightweight runtime file (`/tmp/review_state.json`) acts as an environment switch. 
* **Normal Mode:** If the state file does not exist, `Ctrl+Alt+V` functions exactly as it does now (transcribing, refining, and pasting into the active text cursor).
* **Interview Mode:** When the user initiates an evening review, the state file is created. The hotkey pipeline intercepts the refined text, appends it to the correct section of the Obsidian daily note, updates the state file tracker, and triggers a Linux desktop notification prompting the user for the next question.





[ Ctrl+Alt+V Hotkey Pressed ]
                            │
                            ▼
              [ Audio Capture & STT Pipeline ]
                            │
                            ▼
             [ Refinement via Local Ollama ]
                            │
                            ▼
              🧬 Is /tmp/review_state.json active?
                            / \
                          YES  NO
                          /     \
[ Route to Obsidian File Append ]  [ Default: Paste to Active Window ]
[ Advance State & Notify Next   ]

### Safety Guards for Existing Functionality:
* **Zero Hotkey Highjacking:** The global system shortcut entry point remains identical. 
* **Fail-Safe Fallback:** If the state file is absent, unreadable, or corrupted, the system instantly defaults to normal terminal/editor pasting.
* **Isolated Clipboard Execution:** During interview operations, text outputs pipe straight to append-streams on the hard drive, avoiding interference with active clipboards.

---

## 3. Configuration Specification
To ensure modularity and ease of maintenance, all target file paths, prompt messages, and output templates are externalized into a configuration JSON. This can be integrated into your existing configuration module or saved locally.

**File Location:** `config/review_config.json`
```json
{
  "vault_paths": {
    "base_vault": "/home/manoj/learning_vault",
    "daily_notes": "/home/manoj/learning_vault/My Daily Notes",
    "wellness_notes": "/home/manoj/learning_vault/My Daily Notes/Wellness"
  },
  "llm": {
    "provider": "ollama",
    "model_name": "qan2.5",
    "api_url": "http://localhost:11434/api/generate"
  },
  "review_steps": [
    {
      "step_id": 1,
      "section_name": "Focus Word",
      "prompt_notification": "Step 1: Speak today's core focus word or overarching theme.",
      "markdown_template": "### 📌 Focus Word: **{{text}}**\n"
    },
    {
      "step_id": 2,
      "section_name": "Achievements",
      "prompt_notification": "Step 2: What did you accomplish, build, or unblock today?",
      "markdown_template": "### 🛠️ Key Achievements & Progress\n{{text}}\n"
    },
    {
      "step_id": 3,
      "section_name": "Tomorrow's Priorities",
      "prompt_notification": "Step 3: What tasks or targets need immediate attention tomorrow?",
      "markdown_template": "### ⏳ Tomorrow's Priorities\n{{text}}\n"
    },
    {
      "step_id": 4,
      "section_name": "Wellness Log",
      "prompt_notification": "Step 4: Record any wellness or PTSD reflections. (Or skip if none).",
      "markdown_template": "### 🧠 Personal Reflection & Wellness Log\n* *Logged at {{timestamp}}*:\n{{text}}\n",
      "isolate_file": true
    }
  ]
}
4. Proposed Implementation Steps
Step 1: Create the Session Initializer Script
This script handles initialization when clicking the desktop application launcher. It calculates dates, ensures required vault paths are present, and schedules the initial prompt.

File Location: evening_review_start.py


import os
import json
from datetime import datetime

CONFIG_PATH = "config/review_config.json"
STATE_PATH = "/tmp/review_state.json"

def initialize_review():
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    # Verify directories exist
    os.makedirs(config["vault_paths"]["daily_notes"], exist_ok=True)
    os.makedirs(config["vault_paths"]["wellness_notes"], exist_ok=True)
    
    initial_state = {
        "active": True,
        "current_step_index": 0,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    with open(STATE_PATH, 'w') as f:
        json.dump(initial_state, f)
        
    # Trigger first notification using native Ubuntu notify-send
    first_step = config["review_steps"][0]
    os.system(f'notify-send "Evening Review Started" "{first_step["prompt_notification"]}" -i info')

if __name__ == "__main__":
    initialize_review()



Step 2: Inject State-Routing into the Post-Processing Pipeline
Modify the post-processing module inside your existing repository where the text from your local Ollama qan2.5 model is retrieved (right before it executes terminal injection).

Target Code Logic Insertion:

import os
import json
from datetime import datetime

STATE_PATH = "/tmp/review_state.json"
CONFIG_PATH = "config/review_config.json"

def handle_refined_text(refined_text):
    # GUARD: If state tracker file is missing, drop straight to default typing paste
    if not os.path.exists(STATE_PATH):
        execute_default_paste(refined_text)
        return

    with open(STATE_PATH, 'r') as f:
        state = json.load(f)
        
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    current_idx = state["current_step_index"]
    steps = config["review_steps"]
    current_step = steps[current_idx]
    
    today_str = state["date"]
    timestamp_str = datetime.now().strftime("%H:%M")
    
    # Parse template tags
    formatted_entry = current_step["markdown_template"].replace("{{text}}", refined_text).replace("{{timestamp}}", timestamp_str)
    
    # File Isolation Logic: Route sensitive wellness text away from work logs
    if current_step.get("isolate_file", False):
        target_file = os.path.join(config["vault_paths"]["wellness_notes"], f"{today_str}_Wellness.md")
    else:
        target_file = os.path.join(config["vault_paths"]["daily_notes"], f"{today_str}.md")
        
    # File write operations (append securely)
    with open(target_file, 'a') as f:
        f.write("\n" + formatted_entry)
        
    # State Engine Transition
    next_idx = current_idx + 1
    if next_idx < len(steps):
        state["current_step_index"] = next_idx
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f)
        # Notify user of next step execution requirement
        os.system(f'notify-send "Evening Review" "{steps[next_idx]["prompt_notification"]}"')
    else:
        # Tear down state file immediately upon final task cleanup
        os.remove(STATE_PATH)
        os.system('notify-send "Evening Review Complete" "All entry blocks successfully compiled into Obsidian."')

def execute_default_paste(text):
    # Your pre-existing text insertion implementation logic goes here
    pass



Step 3: Deploy the Desktop App Application Entry File
To enable a single-click setup when logging off your workspace, package the workflow initialization parameters as an Ubuntu desktop launcher.

File Location: ~/.local/share/applications/EveningReview.desktop


[Desktop Entry]
Version=1.0
Name=Evening Review Interview
Comment=Orchestrates structured step-by-step notes using local Ollama model pipelines
Exec=python3 /home/manoj/voice_to_refinedtext/evening_review_start.py
Icon=document-properties
Terminal=false
Type=Application
Categories=Utility;Development;