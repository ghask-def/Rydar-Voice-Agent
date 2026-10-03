
from supabase import create_client
from openai import OpenAI
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
import openai
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Set your OpenAI key for cheap LLMs like gpt-3.5-turbo
openai.api_key = os.getenv("OPENAI_API_KEY")

# Neo4j setup
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# QDrant setup
QDRANT_URL = os.getenv("QDRANT_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_KEY")
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supa = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ensure QDrant collection exists
client = OpenAI()

model = None

USER_ID = "JohnDoe"
NAME = "John Doe"


creds = Credentials(
    token=ACCESS_TOKEN,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

def update_creds():
    global creds
    cred = Credentials(
        token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    creds = cred
    print(f"credentials being saved: {creds}")
    print(NAME)
    return cred

def refresh_tokens():
    global creds
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    ACCESS_TOKEN = creds.token
    update_creds()
    return creds.token


