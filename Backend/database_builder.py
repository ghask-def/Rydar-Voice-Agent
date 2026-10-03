from supabase import create_client
from openai import OpenAI
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
import openai
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
from services.gmail_service import scrape_user_gmail, process_emails, sample_sent_emails_and_store
from services.supabase_services import store_email_creds
from utils.utils import email_creds_exist_for_user
from utils.retriever_local import hybrid_retrieve, query_qdrant_2
import asyncio
import time
from config import model
from uuid import uuid4
from config import supa, qdrant
from agents.function_tools import TOOL_LIST

def user_creds_exist(user_id: str) -> bool:
    """
    Check if Gmail credentials already exist for the given user_id and provider.
    """
    response = supa.table("users") \
        .select("user_id") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    return len(response.data) > 0

def user_email_creds_exist(user_id: str) -> bool:
    """
    Check if Gmail credentials already exist for the given user_id and provider.
    """
    response = supa.table("users") \
        .select("user_id") \
        .eq("user_id", user_id) \
        .limit(1) \
        .execute()

    return len(response.data) > 0

def add_user_to_supabase(user_id: str, full_name: str):
    data = {
        "user_id": user_id,
        "full_name": full_name
    }

    try:
        response = supa.table("users").insert(data).execute()
        if response.status_code == 201:
            print("User added successfully.")
        else:
            print("Insert returned status:", response.status_code, response.data)
    except Exception as e:
        print("Error inserting user:", str(e))

def add_user_email_to_supabase(user_id: str, full_name: str):
    data = {
        "user_id": user_id,
        "email": full_name,
        "provider": "google",
        "access_token": os.getenv("ACCESS_TOKEN"),
        "refresh_token": os.getenv("REFRESH_TOKEN")
    }

    try:
        response = supa.table("email_credentials").insert(data).execute()
        if response.status_code == 201:
            print("User added successfully.")
        else:
            print("Insert returned status:", response.status_code, response.data)
    except Exception as e:
        print("Error inserting user:", str(e))

async def test_function_tool_retrieval():
    query = "Can you create an email for me"

    embedded_query = model.encode(query, convert_to_numpy = True)
    functions = await query_qdrant_2(query, "JohnDoe")

    print(f"The resulting functions are: {functions}")

    return functions




from qdrant_client.http.models import PointStruct, VectorParams, Distance
from services.neo4j_graph_services import extract_neo4j_relations
from transformers import AutoTokenizer
from qdrant_client import QdrantClient, models
from text_message import send_text_message, auto_send_email



def add_custom_email_to_qdrant():

    text = "John Doe asked "

    collection_name="email_history"
    summary = """ On August 1, 2025 (Yesterday), John Melton thanked John Doe (the user) for doing 
        an electrical inspection service and he is wondering when he will get a 
        

        """
    embedding = model.encode(summary, convert_to_numpy=True)
    
    qdrant.upsert(
    points=[
        PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "user_id": "JohnDoe",
                "email_id": "email_id",
                "label": "email_thing",
                "user_email": "john.doe@example.com",
                "recipient_email": "client@example.com",
                "summary": summary
            }
        )
    ]
    )

def add_function_tools_to_qdrant():

    COLLECTION_NAME="function_tools"
    seen = set()

    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    x = 0
    for tool in TOOL_LIST:
        if not tool.__doc__ or not tool.__name__:
            continue
        print(tool.__doc__)
        print(tool.__name__)

        x = x+1
        identifier = (tool.__name__, tool.__doc__ or "")
        
        if identifier not in seen:
            seen.add(identifier)
        else:
            continue

        qdrant_id = str(uuid4())

        embedding = model.encode(tool.__doc__, convert_to_numpy=True)

        
        # Store in QDrant
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=qdrant_id,
                    vector=embedding,
                    payload={
                        "label": tool.__name__,
                        "description": tool.__doc__
                    }
                )
            ]
        )
    print(x)



asyncio.run(test_function_tool_retrieval())