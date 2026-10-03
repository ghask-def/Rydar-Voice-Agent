

# router = APIRouter()

# executor = ThreadPoolExecutor(max_workers=2)

# # @router.post("/google")
# # async def start_google_auth():
# #     # Replace this with your actual iOS client ID
# #     client_id = os.getenv("GOOGLE_CLIENT_ID")
# #     redirect_uri = "com.haskell.frontend:/google-callback"

# #     scopes = [
# #         "https://www.googleapis.com/auth/gmail.modify",
# #         # "https://www.googleapis.com/auth/userinfo.email"
# #     ]
# #     scope_param = urllib.parse.quote(" ".join(scopes))
# #     auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=https://www.googleapis.com/auth/gmail.modify%20https://www.googleapis.com/auth/userinfo.email&access_type=offline&prompt=consent"
# #     print(auth_url)

# #     return {"oauth_url": auth_url}

import os
from fastapi import APIRouter, Request, Body, Query
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urlencode
import requests
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from typing import Optional, List
from config import supa
import aiohttp

from utils.utils import run_email_pipeline  # Update this import to match your project

router = APIRouter()
executor = ThreadPoolExecutor()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email"
]

class GmailCredentials(BaseModel):
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    scopes: Optional[List[str]] = None

# class IDTokenRequest(BaseModel):
#     id_token: str

@router.post("/google")
def generate_oauth_url():
    """
    Accepts Firebase ID token and returns the Google OAuth URL for Web OAuth flow.
    """
    # Optional: verify Firebase ID token here using Firebase Admin SDK
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"oauth_url": oauth_url}


@router.get("/google/callback")
def google_oauth_callback(request: Request):
    """
    Handles the redirect from Google's OAuth flow with an authorization code.
    Exchanges the code for access/refresh tokens and returns a redirect to the app.
    """
    code = request.query_params.get("code")
    if not code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(token_url, data=data)
    if not token_response.ok:
        return JSONResponse(status_code=400, content={"error": "Token exchange failed"})

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # Get user's email using access token
    userinfo_res = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if not userinfo_res.ok:
        return JSONResponse(status_code=400, content={"error": "Failed to get user info"})

    email = userinfo_res.json().get("email")

    # Bundle credentials and run pipeline in the background
    creds = {
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "scopes": SCOPES
    }

    executor.submit(run_email_pipeline, creds)

    # Return something simple for now; frontend is not using this redirect content
    return RedirectResponse(url="com.haskell.frontend:/oauth-success")


@router.post("/google/store")
def store_user_tokens(creds: GmailCredentials):
    """
    Stores user credentials after successful OAuth flow.
    """
    print("received creds")
    executor.submit(run_email_pipeline, creds)

    return {"status": "success"}


class GmailStatusResponse(BaseModel):
    connected: bool
    email: str | None = None


@router.get("/google/status", response_model=GmailStatusResponse)
async def check_gmail_status(user_id: str = Query(...)):
    # 1. Fetch from Supabase table
    result = supa.table("email_credentials").select("email, refresh_token").eq("user_id", user_id).single().execute()

    if result.data is None or "refresh_token" not in result.data:
        return {"connected": False}

    email = result.data["email"]
    refresh_token = result.data["refresh_token"]

    # 2. Try refreshing access token from Google
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=payload) as resp:
            token_response = await resp.json()

            if resp.status != 200 or "access_token" not in token_response:
                print(f"Invalid refresh token for user {user_id}: {token_response}")
                return {"connected": False}

            new_access_token = token_response["access_token"]

    # 3. Update access_token in Supabase
    supa.table("email_credentials").update({"access_token": new_access_token}).eq("user_id", user_id).execute()

    # 4. Return status
    return {
        "connected": True,
        "email": email
    }