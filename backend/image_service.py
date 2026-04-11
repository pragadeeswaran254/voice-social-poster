import requests
import uuid
import os
from dotenv import load_dotenv

# Load the secret keys from your .env file
load_dotenv()

class HuggingFaceService: 
    # We keep this class name the same so your main.py file doesn't break!
    def __init__(self):
        # 🔒 Securely grab the Unsplash key from the .env file
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.api_url = "https://api.unsplash.com/search/photos"

    def generate_image(self, voice_prompt: str) -> str:
        print(f"🔍 Searching Unsplash for a real photo for: '{voice_prompt}'...")
        
        # THE FIX: We use a universal filter to get all types of places (urban, nature, indoor) but block selfies
        smart_query = f"{voice_prompt} background location empty space"
        
        # 1. Ask Unsplash to search for the photo
        params = {
            "query": smart_query,
            "client_id": self.access_key,
            "per_page": 1,
            "orientation": "squarish" # Perfect square for Instagram!
        }
        
        try:
            response = requests.get(self.api_url, params=params)
            data = response.json()
            
            # Check if Unsplash successfully found a matching photo
            if response.status_code == 200 and data.get('results'):
                # Grab the high-resolution URL from the Unsplash results
                photo_url = data['results'][0]['urls']['regular']
                print("✅ Found Unsplash photo! Downloading it locally...")
            else:
                print("⚠️ Unsplash couldn't find an exact match. Using a tech fallback.")
                photo_url = "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2"
            
            # 2. Download the physical image file to your computer
            img_data = requests.get(photo_url).content
            filename = f"unsplash_{uuid.uuid4().hex[:8]}.jpg"
            save_path = os.path.join("static", filename)
            
            os.makedirs("static", exist_ok=True)
            
            with open(save_path, "wb") as file:
                file.write(img_data)
                
            print(f"✅ Image successfully saved at: {save_path}")
            
            # 3. Return the local URL for your React frontend and Database
            return f"http://localhost:8000/static/{filename}"
                
        except Exception as e:
            print(f"🔥 System Error: {e}")
            # Ultimate safety net: If the Wi-Fi drops, use a reliable dummy image
            fallback_data = requests.get("https://loremflickr.com/800/800/technology").content
            filename = f"fallback_{uuid.uuid4().hex[:8]}.jpg"
            save_path = os.path.join("static", filename)
            with open(save_path, "wb") as file:
                file.write(fallback_data)
            return f"http://localhost:8000/static/{filename}"