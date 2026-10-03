import asyncio
from typing import List, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, SearchRequest
from neo4j import AsyncGraphDatabase
import numpy as np
from config import NEO4J_PASS, NEO4J_USER, qdrant, client, NEO4J_URI, driver, model
from neo4j import AsyncGraphDatabase
import time
from sentence_transformers import SentenceTransformer

# Choose optimized model (same as all-MiniLM-L6-v2)
MODEL_NAME = "sentence-transformers/paraphrase-MiniLM-L3-v2"

# Load ONNX-optimized model (quantization happens automatically with `export=True`)



async_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
# model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # small, fast, accurate


# Lightweight reranker (replace with cross-encoder if needed)
def rerank(query_embedding: List[float], docs: List[Tuple[str, List[float]]], top_k=3) -> List[str]:
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scores = [(doc[0], cosine_sim(query_embedding, doc[1])) for doc in docs]
    scores.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in scores[:top_k]]


async def query_qdrant(user_query: str, user_id: str) -> List[Tuple[str, List[float]]]:

    # Your code here


    start_emedding = time.perf_counter()
    embedding = model.encode(user_query, convert_to_numpy=True)


    end_embedding = time.perf_counter()
    start_qdrant = time.perf_counter()
    results = qdrant.search(
        collection_name="email_history",
        query_vector=embedding,
        limit=10,
    )
    end_qdrant = time.perf_counter()

    print(f"Elapsed time embedding: {end_embedding - start_emedding:.6f} seconds")
    print(f"Elapsed qdrant time: {end_qdrant - start_qdrant:.6f} seconds")
    return [(hit.payload["summary"], hit.vector) for hit in results]

async def query_qdrant_2(user_query: str, user_id: str) -> List[Tuple[str, List[float]]]:

    # Your code here


    start_emedding = time.perf_counter()
    embedding = model.encode(user_query, convert_to_numpy=True)


    end_embedding = time.perf_counter()
    start_qdrant = time.perf_counter()
    results = qdrant.search(
        collection_name="function_tools",
        query_vector=embedding,
        limit=10,
    )
    end_qdrant = time.perf_counter()

    print(f"Elapsed time embedding: {end_embedding - start_emedding:.6f} seconds for function tools")
    print(f"Elapsed qdrant time: {end_qdrant - start_qdrant:.6f} seconds for function tools")
    return [(hit.payload["label"], hit.vector) for hit in results]


async def query_neo4j(user_id: str) -> List[str]:
    async with async_driver.session() as session:
        result = await session.run(
            """
            MATCH (u:Person {user_id: $user_id})-[r]->(e)
            RETURN type(r) AS rel, e.name AS target LIMIT 10
            """,
            user_id=user_id
        )
        data = await result.values()
        return [f"{rel} -> {target}" for rel, target in data]


async def hybrid_retrieve(user_query: str, user_id) -> List[str]:
    # Run both tasks in parallel


    qdrant_task = query_qdrant(user_query, user_id)
    # neo4j_task = query_neo4j(user_id)
    qdrant_2_task = query_qdrant_2(user_query, user_id)

    qdrant_results, qdrant_2_results = await asyncio.gather(qdrant_task, qdrant_2_task)

    # qdrant_results = await query_qdrant(user_query, user_id)

    # Rerank Qdrant results using simple cosine scoring
    # top_vector_snippets = rerank(query_embedding, qdrant_results, top_k=3)

    # Combine both
    return qdrant_results + qdrant_2_results
