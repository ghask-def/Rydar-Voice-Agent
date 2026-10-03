# app/api/routes/token.py

import os
from fastapi import APIRouter, HTTPException, Request, Header
from api.models.tokens import TokenRequest, TokenResponse
from livekit import api

from dotenv import load_dotenv
from pathlib import Path
import uuid
from livekit.api import WebhookReceiver, TokenVerifier, DeleteRoomRequest
import json




env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

router = APIRouter()


@router.get('/getToken')
def getToken():
  unique_id = str(uuid.uuid4())
  participant_id = str(uuid.uuid4())  # Generate unique participant identity
  
  token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
    .with_identity(participant_id) \
    .with_name(f"user-{participant_id[:8]}") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room=unique_id,
    ))
  return {"token": token.to_jwt()}


token_verifier = TokenVerifier(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))

def get_livekit_api():
    return api.LiveKitAPI(os.getenv("LIVEKIT_URL"), api_key=os.getenv("LIVEKIT_API_KEY"), api_secret=os.getenv("LIVEKIT_API_SECRET"))

webhookReceiver = WebhookReceiver(token_verifier)

@router.post("/webhook")
async def sip_handler(ev: Request, authorization: str = Header(None)):
    body = await ev.body()
    print(body)
    print(authorization)
    body_str = body.decode("utf-8")

    event = webhookReceiver.receive(body_str, authorization)

    body_json = json.loads(body_str)
    room_name = body_json.get("room").get("name")
    print(body_json.get("room").get("name"))
    lkapi = get_livekit_api()
    if body_json.get("event") == "room_started":
      agent_name = "rydar-agent"
      response = await lkapi.agent_dispatch.create_dispatch(
          api.CreateAgentDispatchRequest(
              agent_name=agent_name,
              room=body_json.get("room").get("name"),
          )
      )
      print(f"Dispatched agent: {response}")
      return {"ok": True}
    elif body_json.get("event") == "participant_left":
      print(body_json.get("participant"))
      await lkapi.room.delete_room(DeleteRoomRequest(
        room=room_name,
      ))
    return {"ok": True}