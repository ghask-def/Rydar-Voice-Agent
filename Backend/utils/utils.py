

# def verify_firebase_token(authorization: str = Header(...)):
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Missing Bearer token")
#     id_token = authorization.split(" ")[1]
#     try:
#         decoded = auth.verify_id_token(id_token)
#         return decoded["uid"]
#     except:
#         raise HTTPException(status_code=401, detail="Invalid Firebase token")


from supabase import create_client, Client
import os

# Set up Supabase client (reuse this in your app)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception(f"Missing URL or key: {SUPABASE_URL}, {SUPABASE_KEY}")
supabase: Client = create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

def email_creds_exist_for_user(user_id: str, provider: str = "google") -> bool:
    """
    Check if Gmail credentials already exist for the given user_id and provider.
    """
    response = supabase.table("email_creds") \
        .select("user_id") \
        .eq("user_id", user_id) \
        .eq("provider", provider) \
        .limit(1) \
        .execute()

    return len(response.data) > 0

# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List
import os

from services.gmail_service import scrape_user_gmail, process_emails, sample_sent_emails_and_store

executor = ThreadPoolExecutor(max_workers=2)  # You can adjust this

class TokenData(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    scopes: Optional[List[str]] = None

def run_email_pipeline(data: TokenData):
    try:
        print("starting email pipeline")
        # sample_sent_emails_and_store(user_id=data.user_id, user_email=data.email,access_token=data.access_token,refresh_token=data.refresh_token, scopes=data.scopes)
        email_threads = scrape_user_gmail(user_id=data.user_id, user_email=data.email,access_token=data.access_token,refresh_token=data.refresh_token, scopes=data.scopes)
        process_emails(data.email, email_threads, data.access_token, data.user_id)
        print("Email pipeline completed")
    except Exception as e:
        print("Error in email pipeline:", e)


