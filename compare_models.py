import requests
import json
import os
from langdetect import detect, DetectorFactory

# Ensure consistent results
DetectorFactory.seed = 0

def detect_lang(text):
    try:
        return detect(text)
    except:
        return "en"

# Load config for host
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
with open(config_path, "r") as f:
    config = json.load(f)
OLLAMA_HOST = config.get("OLLAMA_HOST", "http://localhost:11434")
TEMPERATURE = config.get("TEMPERATURE", 0.0)

models_to_test = ["qwen2.5:3b", "mashriram/sarvam-1:latest"]
test_cases = [
    "इसमें यह भी लिखें कि आपको बहुत एक जो प्रगति है उसको कंपोनेंट वाइस देनी है",
    "actually currently we have no web signer utility so your option is to create by own is a tough way and to purchase through the EM signer is a better way so I think being a designer I want to develop it by myself but if it is still tough then can you tell me the what is the costing of this purchasing of EM signer some idea actually"
]

# Load stop tokens once
prompts_dir = os.path.join(script_dir, "prompts")
stops_path = os.path.join(prompts_dir, "stops.json")
with open(stops_path, "r") as f:
    stops_data = json.load(f)

for model_name in models_to_test:
    print(f"\n{'='*20} Testing Model: {model_name} {'='*20}")
    
    # Resolve model folder
    model_subdir = model_name.replace("/", "_").replace(":", "_")
    model_path = os.path.join(prompts_dir, model_name)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, model_subdir)
    if not os.path.exists(model_path):
        model_path = os.path.join(prompts_dir, "default")

    for text in test_cases:
        lang = detect_lang(text)
        if lang not in ["hi", "en"]:
            lang = "en"
            
        # Read the prompt file
        prompt_file = os.path.join(model_path, f"{lang}.txt")
        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as f:
                prompt_template = f.read()
        else:
            prompt_template = "{text}"
            
        prompt = prompt_template.format(text=text)
        
        # Get stop tokens
        stop_tokens = stops_data.get(model_name, stops_data.get(model_subdir, stops_data["default"]))[lang]

        print(f"\n--- Raw Text ({lang}) ---")
        print(f"RAW: {text}")

        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": TEMPERATURE,
                    "top_p": 0.9,
                    "stop": stop_tokens
                },
                timeout=45
            )
            
            if response.status_code == 200:
                final_text = response.json().get("response", "").strip()
                
                # Apply same cleanup logic as main script
                prefixes_to_strip = [
                    "Professional English:", "Cleaned text:", "Refined text:",
                    "यहाँ सुधार हुआ पाठ है:", "शुद्ध रूप:", "संवाद:", "Raw:", "Output:",
                    "The professional version of the text is:", "Here is the refined text:"
                ]
                for prefix in prefixes_to_strip:
                    if final_text.lower().startswith(prefix.lower()):
                        final_text = final_text[len(prefix):].strip()
                if final_text.startswith('"') and final_text.endswith('"'):
                    final_text = final_text[1:-1].strip()
                    
                print(f"REFINED: {final_text}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to call Ollama: {e}")

print(f"\n{'='*50}")
print("Testing complete.")
