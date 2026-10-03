import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct
import random

from config import qdrant

COLLECTION_EMAIL_HISTORY = "email_history"
COLLECTION_FUNCTION_TOOLS = "function_tools"
DISTANCE = models.Distance.COSINE

VECTOR_SIZE = 384

# Connect to local Qdrant
local_client = QdrantClient(
  host="localhost",
  port=6333,
  prefer_grpc=False
)

# Recreate email_history collection locally
print(f"Recreating collection '{COLLECTION_EMAIL_HISTORY}' locally...")
local_client.recreate_collection(
  collection_name=COLLECTION_EMAIL_HISTORY,
  vectors_config=models.VectorParams(
    size=VECTOR_SIZE,
    distance=DISTANCE
  )
)

# Download points from cloud for email_history
print("Downloading points from cloud for email_history...")
points, _ = qdrant.scroll(

  collection_name=COLLECTION_EMAIL_HISTORY,
  limit=5,
  with_vectors=True,
  with_payload=True
)

if not points:
  print(f"No points found in cloud collection '{COLLECTION_EMAIL_HISTORY}'.")
else:
  formatted_points = [
    PointStruct(id=p.id, vector=p.vector, payload=p.payload)
    for p in points
  ]
  print(f"Uploading {len(formatted_points)} points to local '{COLLECTION_EMAIL_HISTORY}'...")
  local_client.upsert(collection_name=COLLECTION_EMAIL_HISTORY, points=formatted_points)

# Create function_tools collection locally
print(f"Recreating collection '{COLLECTION_FUNCTION_TOOLS}' locally...")
local_client.recreate_collection(

  collection_name=COLLECTION_FUNCTION_TOOLS,
  vectors_config=models.VectorParams(
    size=VECTOR_SIZE,
    distance=DISTANCE
  )
)

print("Downloading points from cloud for function_tools...")
points, _ = qdrant.scroll(
  collection_name=COLLECTION_FUNCTION_TOOLS,
  limit=40,
  with_vectors=True,
  with_payload=True
)

formatted_points = [
  PointStruct(id=p.id, vector=p.vector, payload=p.payload)
  for p in points
]
print(f"Uploading {len(formatted_points)} points to local '{COLLECTION_FUNCTION_TOOLS}'...")
local_client.upsert(collection_name=COLLECTION_FUNCTION_TOOLS, points=formatted_points)

print("Done. Your local Qdrant DB is ready with both collections.")
