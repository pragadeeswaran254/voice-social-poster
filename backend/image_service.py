import requests
import uuid
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
        
        # 🚀 The ultimate, restriction-free search parameters
        params = {
            "q": voice_prompt,
            "key": self.google_api_key,
            "cx": self.google_cx,
            "searchType": "image",
            "num": 1
            # Notice we completely removed "safe", "gl", and "imgSize" to stop it from rejecting good images!
        }
        
        try:
            response = requests.get(self.search_url, params=params)
            data = response.json()
            
            # Check if Google found image results
            if "items" in data:
                # Grab the direct image link from the first result
                photo_url = data["items"][0]["link"]
                print("✅ Found Google Image! Downloading it locally...")
                
                # Download the physical image to your computer
                img_data = requests.get(photo_url).content
                filename = f"google_{uuid.uuid4().hex[:8]}.jpg"
                save_path = os.path.join("static", filename)
                
                # Ensure the static folder exists
                os.makedirs("static", exist_ok=True)
                
                with open(save_path, "wb") as file:
                    file.write(img_data)
                    
                print(f"✅ Image successfully saved at: {save_path}")
                return f"http://localhost:8000/static/{filename}"
            else:
                print("⚠️ Google couldn't find an image for this within the allowed domains.")
                
        except Exception as e:
            print(f"🔥 System Error connecting to Google: {e}")
            
        # 🛟 Ultimate safety net if the internet drops or Google API fails
        print("🛟 Using emergency fallback image...")
        fallback_data = requests.get("https://loremflickr.com/800/800/technology").content
        filename = f"fallback_{uuid.uuid4().hex[:8]}.jpg"
        save_path = os.path.join("static", filename)
        
        os.makedirs("static", exist_ok=True)
        
        with open(save_path, "wb") as file:
            file.write(fallback_data)
            
        return f"http://localhost:8000/static/{filename}"