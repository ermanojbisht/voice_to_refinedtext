import os
import utils

# Load config for host
script_dir = os.path.dirname(os.path.abspath(__file__))
config = utils.load_config(script_dir)
OLLAMA_HOST = config.get("OLLAMA_HOST", "http://localhost:11434")
TEMPERATURE = config.get("TEMPERATURE", 0.0)

models_to_test = ["qwen2.5:3b", "qwen3.5:0.8b"]
test_cases = [
    "there are some issues i thought that that in some length it shows uh value beyond the  point zero zero zero something six or seven place it should be limited only up to three  because it's a data enclosure so maximum place should be three places and it should be for  every data i think consistent one thing second thing i need total of the rows field which are  countable in data table but those fields should be shown at top of the column not at the bottom  or we may so this informer data in another way on top of data table so that user not to go  at the town he may see the data at top so what is your take  is  Thank you very much."
]

for model_name in models_to_test:
    print(f"\n{'='*20} Testing Model: {model_name} {'='*20}")
    
    for text in test_cases:
        lang = utils.detect_lang(text)
        print(f"\n--- Raw Text ({lang}) ---")
        print(f"RAW: {text}")

        # Resolve prompt and stops
        prompt, stop_tokens = utils.get_prompt_and_stops(script_dir, model_name, text, lang)

        # Call Ollama
        response_json = utils.call_ollama(OLLAMA_HOST, model_name, prompt, stop_tokens, TEMPERATURE)

        if "error" in response_json:
            print(f"❌ Failed to call Ollama: {response_json['error']}")
        else:
            final_text = utils.clean_response(response_json.get("response", ""))
            print(f"REFINED: {final_text}")

print(f"\n{'='*50}")
print("Testing complete.")
