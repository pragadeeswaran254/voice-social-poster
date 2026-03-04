from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai 
import os
from dotenv import load_dotenv
import json
import random
import requests
import re 

# --- Scheduler Imports ---
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

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

# --- 1. DATABASE SCHEMA ---
class PostDB(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) 
    content = Column(String, index=True)
    tone = Column(String)
    instagram_version = Column(Text)
    twitter_version = Column(Text)
    image_prompt = Column(String)     
    image_seed = Column(Integer)      
    is_upload = Column(Integer, default=0) 
    image_data = Column(Text, nullable=True) 
    scheduled_time = Column(String, nullable=True) 
    status = Column(String, default="Generated") 

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. SCHEDULER ENGINE (TELEGRAM & MOCK WEBHOOK AUTOMATION) ---
def check_scheduled_posts():
    db = SessionLocal() 
    try:
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M") 
        
        due_posts = db.query(PostDB).filter(
            PostDB.status == "Scheduled",
            PostDB.scheduled_time <= current_time
        ).all()

        for post in due_posts:
            print(f"[{current_time}] 🚀 Publishing Post ID {post.id}...")
            
            # Reconstruct the Image URL
            ignore_words = ["today", "went", "want", "just", "like", "with", "this", "that", "the", "and", "for", "from"]
            clean_content = re.sub(r'[^a-z ]', '', post.content.lower())
            words = clean_content.split()
            search_keywords = [w for w in words if len(w) > 2 and w not in ignore_words][:2]
            keywords_str = ",".join(search_keywords) if search_keywords else "social"
            
            image_url = f"https://loremflickr.com/800/800/{keywords_str}?lock={post.image_seed}"

            # --- CHANNEL A: Publish to Telegram ---
            BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
            CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
            
            if BOT_TOKEN and CHAT_ID:
                try:
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json={
                        "chat_id": CHAT_ID,
                        "photo": image_url
                    })
                    
                    text_message = f"🤖 *AI PUBLISH SUCCESS*\n\n📸 *Instagram:*\n{post.instagram_version}\n\n🐦 *Twitter:*\n{post.twitter_version}"
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                        "chat_id": CHAT_ID,
                        "text": text_message,
                        "parse_mode": "Markdown"
                    })
                    print("💬 Telegram Channel: SUCCESS")
                except Exception as e:
                    print(f"⚠️ Telegram Error: {e}")
            else:
                print("⚠️ Telegram keys missing!")

            # --- CHANNEL B: SEND TO MOCK WEBHOOK APP ---
            try:
                # We send the generated image and the instagram caption to port 8001
                requests.post("http://localhost:8001/webhook", json={
                    "image_url": image_url,
                    "caption": post.instagram_version
                })
                print("📱 Mock Webhook Channel: SUCCESS")
            except Exception as e:
                print(f"⚠️ Mock Webhook Error: {e}")
            # --------------------------------------------

            # Update database status so frontend shows "Published" badge
            post.status = "Published"
            db.commit()
            print("✅ Database Status Updated")
            
    except Exception as e:
        print(f"Scheduler Error: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(check_scheduled_posts, 'interval', minutes=1)
scheduler.start()

# --- 3. PYDANTIC MODELS ---
class PostCreate(BaseModel):
    user_id: str 
    content: str
    tone: str = "Professional"

class PostSchedule(BaseModel):
    scheduled_time: str

client = None
if api_key:
    client = genai.Client(api_key=api_key)

@app.get("/")
def read_root():
    return {"status": "AI Social Media API is Live 🚀"}

@app.get("/posts")
def get_posts(user_id: str = None): 
    db = SessionLocal()
    if not user_id:
        db.close()
        return []

    posts = db.query(PostDB).filter(PostDB.user_id == user_id).order_by(PostDB.id.desc()).all()
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
            model="gemini-2.5-flash", 
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
            user_id=post.user_id, 
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

@app.put("/posts/{post_id}/schedule")
def schedule_post(post_id: int, schedule_data: PostSchedule):
    db = SessionLocal()
    post = db.query(PostDB).filter(PostDB.id == post_id).first()
    
    if not post:
        db.close()
        raise HTTPException(status_code=404, detail="Post not found")
        
    post.scheduled_time = schedule_data.scheduled_time
    post.status = "Scheduled"
    
    db.commit()
    db.close()
    return {"message": "Post scheduled successfully!", "post_id": post_id, "scheduled_time": schedule_data.scheduled_time}