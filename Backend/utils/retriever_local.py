import asyncio
from main import get_embedding_model
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
import numpy as np
from config import NEO4J_PASS, NEO4J_USER, NEO4J_URI, driver  # modelremoved cloud qdrant client import
import time

# from text_message import send_text_message, auto_send_email

# Initialize local Qdrant client (replace cloud qdrant with this)
local_qdrant = QdrantClient(host="localhost", port=6333, prefer_grpc=False)




# Lightweight reranker (replace with cross-encoder if needed)
def rerank(query_embedding: List[float], docs: List[Tuple[str, List[float]]], top_k=3) -> List[str]:
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scores = [(doc[0], cosine_sim(query_embedding, doc[1])) for doc in docs]
    scores.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in scores[:top_k]]


import asyncio

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from typing import List, Tuple, Any
import asyncio
import time

router = APIRouter()

# Assuming you already have these initialized somewhere:
# local_qdrant = QdrantClient(...)
# driver = AsyncGraphDatabase.driver(...)
# tool_dict = {...}

# ----------------------------
# Request / Response Models
# ----------------------------
class QdrantRequest(BaseModel):
    user_query: List[float]  # assuming already an embedding vector
    user_id: str

class Neo4jRequest(BaseModel):
    user_id: str

class HybridRequest(BaseModel):
    user_query: str
    user_id: str

# ----------------------------
# Core Functions (unchanged)
# ----------------------------
async def query_qdrant(user_query, user_id: str) -> List[Tuple[str, str, str]]:
    def search_qdrant():
        return local_qdrant.search(
            collection_name="email_history",
            query_vector=user_query,
            limit=10,
        )

    start_qdrant = time.perf_counter()
    results = await asyncio.to_thread(search_qdrant)
    end_qdrant = time.perf_counter()

    print(f"Elapsed qdrant time: {end_qdrant - start_qdrant:.6f} seconds")
    return [(hit.payload["summary"], hit.payload["user_email"], hit.payload["recipient_email"]) for hit in results]


async def query_qdrant_2(user_query, user_id: str) -> List[Any]:
    count = local_qdrant.count(
        collection_name="function_tools",
        exact=True
    ).count
    print(f"count : {count}")

    def search_qdrant():
        return local_qdrant.search(
            collection_name="function_tools",
            query_vector=user_query,
            limit=5,
        )

    start_qdrant = time.perf_counter()
    results = await asyncio.to_thread(search_qdrant)
    end_qdrant = time.perf_counter()

    for res in results:
        print(f"ID: {res.id}, cosine similarity: {res.score}, {res.payload.get('label')}")

    print(f"Elapsed qdrant time: {end_qdrant - start_qdrant:.6f} seconds for function_tools")

    retrieved = [(hit.payload.get("label", "[no label]"), hit.vector) for hit in results]
    return retrieved


async def query_neo4j(user_id: str) -> List[str]:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (u:Person {user_id: $user_id})-[r]->(e)
            RETURN type(r) AS rel, e.name AS target LIMIT 10
            """,
            user_id=user_id
        )
        data = await result.values()
        return [f"{rel} -> {target}" for rel, target in data]


async def hybrid_retrieve(user_query: str, user_id: str) -> List[Any]:
    start_model_load = time.perf_counter()
    model = get_embedding_model()
    print(f"Model instance id: {id(model)}")
    end_model_load = time.perf_counter()
    print(f"time to load {end_model_load - start_model_load}")
    print("[RETRIEVER] Using model in PID", __import__("os").getpid())
    start_embedding = time.perf_counter()
    embedding =  embedding = model.encode(user_query, normalize_embeddings=True, convert_to_numpy=True)
    end_embedding = time.perf_counter()
    print(f"Elapsed embedding time: {end_embedding - start_embedding:.6f} seconds")
    start_hybrid = time.perf_counter()
    qdrant_task = query_qdrant(embedding, user_id)
    qdrant_2_task = query_qdrant_2(embedding, user_id)
    qdrant_results, qdrant_2_results = await asyncio.gather(qdrant_task, qdrant_2_task)
    end_hybrid = time.perf_counter()
    print(f"Elapsed hybrid time: {end_hybrid - start_hybrid:.6f} seconds")
    return [qdrant_results, qdrant_2_results]

# ----------------------------
# FastAPI Endpoints
# ----------------------------
@router.post("/query_qdrant")
async def query_qdrant_endpoint(req: QdrantRequest):
    results = await query_qdrant(req.user_query, req.user_id)
    return {"results": results}

@router.post("/query_qdrant_2")
async def query_qdrant_2_endpoint(req: QdrantRequest):
    results = await query_qdrant_2(req.user_query, req.user_id)
    return {"results": results}

@router.post("/query_neo4j")
async def query_neo4j_endpoint(req: Neo4jRequest):
    results = await query_neo4j(req.user_id)
    return {"results": results}

@router.post("/hybrid_retrieve")
async def hybrid_retrieve_endpoint(req: HybridRequest):
    results = await hybrid_retrieve(req.user_query, req.user_id)
    return {"results": results}
