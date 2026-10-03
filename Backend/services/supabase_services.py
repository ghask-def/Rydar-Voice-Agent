### File: services/supabase_services.py
from supabase import create_client
import os
from config import supa


def check_creds_exist(user_id: str) -> bool:
    response = supa.table("gmail_creds").select("*").eq("user_id", user_id).execute()
    return len(response.data) > 0

def store_email_creds(user_id: str, payload):
    data = {
        "user_id": user_id,
        "email": payload.email,
        "provider": "google",
        "access_token": payload.access_token,
        "refresh_token": payload.refresh_token,
        # "token_expiry": payload.token_expiry,
        "scopes": payload.scopes
    }
    supa.table("email_credentials").upsert(data).execute()

def store_emails_in_supabase(user_id: str, emails: list[dict]):
    rows = []
    for email in emails:
        row = {
            "user_id": user_id,
            "thread_id": email["thread_id"],
            "message_id": email["message_id"],
            "subject": email["subject"],
            "sender": email["from"],
            "recipient": email["to"],
            "snippet": email["snippet"],
            "body": email["body"],
            "received_at": email["date"]
        }
        rows.append(row)
    supa.table("emails").upsert(rows).execute()
