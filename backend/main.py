from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai 
import os
from dotenv import load_dotenv
import json
import random

# --- Database Imports ---
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'posts.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 1. UPDATED DATABASE SCHEMA ---
class PostDB(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # <--- NEW: Links post to specific user
    content = Column(String, index=True)
    tone = Column(String)
    instagram_version = Column(Text)
    twitter_version = Column(Text)
    image_prompt = Column(String)     
    image_seed = Column(Integer)      
    is_upload = Column(Integer, default=0) 
    image_data = Column(Text, nullable=True) 

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. UPDATED PYDANTIC MODEL ---
class PostCreate(BaseModel):
    user_id: str # <--- NEW: Frontend must send the user's ID
    content: str
    tone: str = "Professional"

client = None
if api_key:
    client = genai.Client(api_key=api_key)


@app.get("/")
def read_root():
    return {"status": "AI Social Media API is Live 🚀"}

# --- 3. UPDATED GET ROUTE (FILTER BY USER) ---
@app.get("/posts")
def get_posts(user_id: str = None): # FastAPI automatically looks for ?user_id= in the URL
    db = SessionLocal()
    
    # If a user is not logged in, return a blank feed immediately
    if not user_id:
        db.close()
        return []

    # STRICT FILTER: Only pull data where the user_id perfectly matches
    posts = db.query(PostDB).filter(PostDB.user_id == user_id).order_by(PostDB.id.desc()).all()
    
    db.close()
    return posts

# --- 4. UPDATED POST ROUTE (SAVE USER ID) ---
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
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        ai_content = json.loads(response_text)

        db = SessionLocal()
        new_post_entry = PostDB(
            user_id=post.user_id, # <--- NEW: Save who created this!
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