# main.py
from fastapi import FastAPI
import os
from dotenv import load_dotenv
load_dotenv()



from firebase_admin import initialize_app, credentials, get_app
import firebase_admin
from sentence_transformers import SentenceTransformer



app = FastAPI()
model = None

@app.on_event("startup")
async def startup_event():
    global model
    print("[Startup] Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"Model instance id: {id(model)}")
    _ = model.encode("warm up", normalize_embeddings=True)
    _ = model.encode("warm up", normalize_embeddings = True)
    print("[RETRIEVER] Using model in PID", __import__("os").getpid())

    print("[Startup] Model loaded and warmed up.")
print(f"Model instance id: {id(model)}")

def get_embedding_model():
    global model
    if model is None:
        raise RuntimeError("Embedding model not initialized yet")
    return model

from api.routes import livekitToken as token
from api.routes import gmail_endpoints
from api.routes import session_endpoints

app.include_router(token.router, prefix="/token")
app.include_router(session_endpoints.router)

# app.include_router(websocket_server.router)
app.include_router(gmail_endpoints.router, prefix = "/auth")

from utils import retriever_local as retriever

app.include_router(retriever.router)

# Firebase Admin Initialization
try:
    app = get_app()
except ValueError:
    cred = credentials.Certificate("firebase-service-account.json")
    initialize_app(cred)
