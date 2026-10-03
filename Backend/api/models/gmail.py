from pydantic import BaseModel

class TokenData(BaseModel):
    email: str
    access_token: str
    refresh_token: str


class GmailCredsPayload(BaseModel):
    email: str
    access_token: str
    refresh_token: str
    token_expiry: str
    scopes: list[str]
