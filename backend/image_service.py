import requests
import uuid
import os
from dotenv import load_dotenv

# Load the secret keys from your .env file
load_dotenv()

class HuggingFaceService: 
    def __init__(self):
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.unsplash_url = "https://api.unsplash.com/search/photos"
        self.wiki_url = "https://en.wikipedia.org/w/api.php"

    def get_wikipedia_image(self, query: str):
        print(f"🏛️ Asking Wikipedia for an official image of: '{query}'...")
        # Wikipedia requires a User-Agent so they know who is using their free API
        headers = {"User-Agent": "SocialFlowAI/1.0 (College Project)"}
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": 1,
            "prop": "pageimages",
            "piprop": "original"
        }
        
        try:
            response = requests.get(self.wiki_url, headers=headers, params=params)
            data = response.json()
            
            # Navigate through Wikipedia's JSON response to find the image URL
            pages = data.get("query", {}).get("pages", {})
            if pages:
                first_page = list(pages.values())[0]
                if "original" in first_page:
                    image_url = first_page["original"]["source"]
                    print(f"✅ Wikipedia found a match: {first_page.get('title')}")
                    return image_url
        except Exception as e:
            print(f"⚠️ Wikipedia search failed: {e}")
            
        print("⚠️ No official Wikipedia image found.")
        return None

    def generate_image(self, voice_prompt: str) -> str:
        print(f"🔍 Starting Image Search Engine for: '{voice_prompt}'")
        
        # STEP 1: Try Wikipedia first for landmarks!
        photo_url = self.get_wikipedia_image(voice_prompt)
        
        # STEP 2: If Wikipedia fails, fall back to Unsplash
        if not photo_url:
            print(f"📸 Falling back to Unsplash for: '{voice_prompt}'...")
            
            # Notice: We removed the "empty space" filter so it stops returning cats!
            unsplash_params = {
                "query": voice_prompt,
                "client_id": self.unsplash_key,
                "per_page": 1,
                "orientation": "squarish"
            }
            
            try:
                response = requests.get(self.unsplash_url, params=unsplash_params)
                data = response.json()
                
                if response.status_code == 200 and data.get('results'):
                    photo_url = data['results'][0]['urls']['regular']
                    print("✅ Found Unsplash photo!")
                else:
                    print("⚠️ Unsplash also failed. Using a tech fallback.")
                    photo_url = "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2"
            except Exception as e:
                print(f"🔥 Unsplash API Error: {e}")
                photo_url = "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2"

        # STEP 3: Download whatever photo we found and save it locally
        try:
            img_data = requests.get(photo_url).content
            filename = f"generated_{uuid.uuid4().hex[:8]}.jpg"
            save_path = os.path.join("static", filename)
            
            os.makedirs("static", exist_ok=True)
            
            with open(save_path, "wb") as file:
                file.write(img_data)
                
            print(f"✅ Image successfully saved at: {save_path}")
            return f"http://localhost:8000/static/{filename}"
            
        except Exception as e:
            print(f"🔥 Final System Error saving image: {e}")
            # The ultimate safety net
            return "https://loremflickr.com/800/800/technology"