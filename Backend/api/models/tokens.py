from pydantic import BaseModel

class TokenRequest(BaseModel):
    identity: str
    room: str

class TokenResponse(BaseModel):
    token: str