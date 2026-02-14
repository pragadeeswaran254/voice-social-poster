from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Fallback if .env fails
    api_key = "AIzaSyD4P4MCiR8bapzUMtYv-uPVnJTn_eL0vcg"

print(f"Connecting with key ending in... {api_key[-4:]}")

try:
    client = genai.Client(api_key=api_key)
    print("\n✅ SUCCESS! Here are your available models:\n")

    for m in client.models.list():
        # We only want models that can write text (generateContent)
        if "generateContent" in m.supported_actions:
            print(f"MODEL NAME: {m.name}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")