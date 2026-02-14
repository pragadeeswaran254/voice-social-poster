from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai 
import os
from dotenv import load_dotenv
import json
import random
import io
import base64
from PIL import Image

# --- Database Imports ---
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY not found in .env file!")

# 2. Setup Database (SQLite)
DATABASE_URL = "sqlite:///./posts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the SQL Table
class PostDB(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    tone = Column(String)
    instagram_version = Column(Text)
    twitter_version = Column(Text)
    image_prompt = Column(String)     
    image_seed = Column(Integer)      
    is_upload = Column(Integer, default=0) 
    image_data = Column(Text, nullable=True) 

# Create the tables
Base.metadata.create_all(bind=engine)

# 3. Setup App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostCreate(BaseModel):
    content: str
    tone: str = "Professional"

# Initialize Client
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# --- API ENDPOINTS ---

@app.get("/posts")
def get_posts():
    db = SessionLocal()
    posts = db.query(PostDB).all()
    db.close()
    return posts

@app.post("/posts")
def create_post(post: PostCreate):
    if not client: return {"error": "API Key missing"}

    prompt = f"""
    You are an expert social media manager. 
    Write an Instagram caption and a Twitter post about: "{post.content}"
    
    CRITICAL INSTRUCTION: You MUST write these posts in a {post.tone} tone of voice!
    
    Return the response strictly in JSON format exactly like this:
    {{
      "instagram_version": "your caption here",
      "twitter_version": "your tweet here"
    }}
    Do not include any markdown formatting like ```json.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:-3]
        elif response_text.startswith("```"): response_text = response_text[3:-3]
        
        ai_content = json.loads(response_text)

        db = SessionLocal()
        new_post_entry = PostDB(
            content=post.content,
            tone=post.tone,
            instagram_version=ai_content.get("instagram_version", ""),
            twitter_version=ai_content.get("twitter_version", ""),
            image_prompt=post.content,
            image_seed=random.randint(100000, 999999),
            is_upload=0 
        )
        db.add(new_post_entry)
        db.commit()
        db.refresh(new_post_entry)
        db.close()
        return new_post_entry

    except Exception as e:
        print(f"🔥 AI Error: {e}")
        return {"instagram_version": f"Error: {str(e)}", "twitter_version": "Please try again."}

# --- OPTIMIZED IMAGE UPLOAD ENDPOINT ---
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), tone: str = Form("Professional")):
    if not client: return {"error": "API Key missing"}
    
    print(f"📸 Receiving image... Tone: {tone}")
    
    try:
        # 1. Read the image file
        image_bytes = await file.read()
        
        # 2. OPEN & RESIZE IMAGE (The Fix!)
        # We shrink the image to max 800px so it sends faster
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.thumbnail((800, 800)) 
        
        # 3. Convert Resized Image to Bytes for Base64 (Storage)
        buffered = io.BytesIO()
        # Convert to RGB to handle PNGs with transparency
        if pil_image.mode in ("RGBA", "P"): 
            pil_image = pil_image.convert("RGB")
        pil_image.save(buffered, format="JPEG")
        resized_image_bytes = buffered.getvalue()
        
        encoded_image = base64.b64encode(resized_image_bytes).decode('utf-8')
        
        # 4. Prepare Prompt
        prompt = f"""
        Look at this image. You are a social media expert.
        Write an amazing Instagram caption and a Twitter post for this image.
        
        The tone should be: {tone}.
        
        Return the response strictly in JSON format exactly like this:
        {{
          "instagram_version": "your caption here",
          "twitter_version": "your tweet here"
        }}
        Do not include any markdown formatting.
        """
        
        # 5. Call Gemini with RESIZED Image
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=[prompt, pil_image]
        )
        
        response_text = response.text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:-3]
        elif response_text.startswith("```"): response_text = response_text[3:-3]
        
        ai_content = json.loads(response_text)
        
        # 6. Save to Database
        db = SessionLocal()
        new_post_entry = PostDB(
            content="[Image Upload]",
            tone=tone,
            instagram_version=ai_content.get("instagram_version", ""),
            twitter_version=ai_content.get("twitter_version", ""),
            image_prompt="uploaded",
            image_seed=0,
            is_upload=1,
            image_data=encoded_image 
        )
        db.add(new_post_entry)
        db.commit()
        db.refresh(new_post_entry)
        db.close()
        
        print("✅ Success! Image processed.")
        return new_post_entry

    except Exception as e:
        print(f"🔥 Vision Error: {e}")
        # Return a 500 error so frontend knows it failed
        raise HTTPException(status_code=500, detail=str(e))