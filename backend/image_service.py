import requests
import os
from dotenv import load_dotenv

# Load the secret keys from your .env file
load_dotenv()

class HuggingFaceService: 
    def __init__(self):
        # 🔒 Securely load the Pexels API key
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.search_url = "https://api.pexels.com/v1/search"

    def generate_image(self, voice_prompt: str) -> str:
        print(f"🔍 Searching Pexels for beautiful images of: '{voice_prompt}'...")
        
        headers = {
            "Authorization": self.pexels_api_key
        }
        params = {
            "query": voice_prompt,
            "per_page": 1
        }
        
        try:
            response = requests.get(self.search_url, headers=headers, params=params)
            data = response.json()
            
            # Check if Pexels found image results
            if "photos" in data and len(data["photos"]) > 0:
                # 🚀 Grab the high-quality image URL!
                photo_url = data["photos"][0]["src"]["large"]
                print(f"✅ Found Pexels Image! Passing direct URL to Telegram: {photo_url}")
                return photo_url
            else:
                print("⚠️ Pexels couldn't find an image for this specific prompt.")
                
        except Exception as e:
            print(f"🔥 System Error connecting to Pexels: {e}")
            
        # 🛟 Return the fallback placeholder if all else fails
        print("🛟 Using emergency fallback placeholder...")
        return "https://placehold.co/800x800/png?text=Image+Not+Found"