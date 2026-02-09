"""
Quick script to list available Gemini models and verify the configured model exists.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("🔍 Fetching available Gemini models...\n")

# List all available models
models = genai.list_models()

print("=" * 80)
print("AVAILABLE GEMINI MODELS")
print("=" * 80)

generate_content_models = []
for model in models:
    if 'generateContent' in model.supported_generation_methods:
        generate_content_models.append(model.name)
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description[:100]}...")
        print()

print("=" * 80)
print(f"Total models supporting generateContent: {len(generate_content_models)}")
print("=" * 80)

# Check configured models
smart_model = os.getenv("GEMINI_SMART_MODEL", "gemini-2.0-flash-exp")
fast_model = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")

print("\n🔧 CONFIGURED MODELS:")
print(f"   SMART: {smart_model}")
print(f"   FAST:  {fast_model}")

print("\n✅ VALIDATION:")
smart_full = f"models/{smart_model}"
fast_full = f"models/{fast_model}"

if smart_full in generate_content_models:
    print(f"   ✅ Smart model '{smart_model}' is VALID")
else:
    print(f"   ❌ Smart model '{smart_model}' is INVALID")
    print(f"   💡 Suggested alternatives:")
    for m in generate_content_models[:5]:
        print(f"      - {m.replace('models/', '')}")

if fast_full in generate_content_models:
    print(f"   ✅ Fast model '{fast_model}' is VALID")
else:
    print(f"   ❌ Fast model '{fast_model}' is INVALID")
    print(f"   💡 Suggested alternatives:")
    for m in generate_content_models[:5]:
        print(f"      - {m.replace('models/', '')}")
