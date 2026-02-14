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

# 2. Setup Database (SQLite)
# Render uses a Linux file system, so we ensure the path is absolute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'posts.db')}"

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

# --- CRITICAL: CORS SETTINGS ---
# This allows your specific Vercel URL to talk to this Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "https://voice-social-poster-ng0v9x1lc-pragadeeswaran254s-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostCreate(BaseModel):
    content: str
    tone: str = "Professional"

# Initialize Gemini Client
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "AI Social Media API is Live 🚀"}

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
    Do not include any markdown formatting.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        response_text = response.text.strip()
        # Clean up any potential markdown backticks from AI response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
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

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), tone: str = Form("Professional")):
    if not client: return {"error": "API Key missing"}
    
    try:
        image_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Optimize image for faster API processing
        pil_image.thumbnail((800, 800)) 
        
        buffered = io.BytesIO()
        if pil_image.mode in ("RGBA", "P"): 
            pil_image = pil_image.convert("RGB")
        pil_image.save(buffered, format="JPEG")
        resized_image_bytes = buffered.getvalue()
        
        encoded_image = base64.b64encode(resized_image_bytes).decode('utf-8')
        
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
        
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=[prompt, pil_image]
        )
        
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        ai_content = json.loads(response_text)
        
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
        
        return new_post_entry

    except Exception as e:
        print(f"🔥 Vision Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))