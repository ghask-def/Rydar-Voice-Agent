from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.session_utils import create_user_session, retrieve_gmail_creds

router = APIRouter()

class UserIDPayload(BaseModel):
    user_id: str

@router.post("/user/id")
async def receive_user_id(payload: UserIDPayload):
    user_id = payload.user_id
    # Here you can store the user_id in DB or session or whatever you need
    print(f"Received Firebase user ID: {user_id}")
    
    # Example: just return a confirmation message
    create_user_session(user_id)
    retrieve_gmail_creds(user_id)
    return {"message": f"User ID {user_id} received successfully"}
