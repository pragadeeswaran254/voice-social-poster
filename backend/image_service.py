import requests
import os
from dotenv import load_dotenv

# Load the secret keys from your .env file
load_dotenv()

class HuggingFaceService: 
    def __init__(self):
        # 🔒 Securely load the Google API keys
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx = os.getenv("GOOGLE_CX")
        self.search_url = "https://www.googleapis.com/customsearch/v1"

    def generate_image(self, voice_prompt: str) -> str:
        print(f"🔍 Searching Google Images for: '{voice_prompt}'...")
        
        params = {
            "q": voice_prompt,
            "key": self.google_api_key,
            "cx": self.google_cx,
            "searchType": "image",
            "num": 1
        }
        
        try:
            response = requests.get(self.search_url, params=params)
            data = response.json()
            
            # Check if Google found image results
            if "items" in data:
                # 🚀 VERCEL FIX: Just grab the direct public URL from Google!
                photo_url = data["items"][0]["link"]
                print(f"✅ Found Google Image! Passing direct URL to Telegram...")
                
                # Return the public link directly so Telegram can download it.
                return photo_url
            else:
                print("⚠️ Google couldn't find an image for this.")
                
        except Exception as e:
            print(f"🔥 System Error connecting to Google: {e}")
            
        # 🛟 Return a public URL for the fallback too!
        print("🛟 Using emergency fallback image...")
        return "https://loremflickr.com/800/800/technology"