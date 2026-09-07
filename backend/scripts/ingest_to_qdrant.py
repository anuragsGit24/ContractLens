from qdrant_client import QdrantClient

import sys
import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

QDRANT_URL = "https://d13e3e61-6ad5-4b0d-86f0-d0114d56c364.eu-central-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_API_KEY:
    print("QDRANT_API_KEY not found in environment. Please set it in your .env file.")
    sys.exit(1)

try:
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    collections = qdrant_client.get_collections()
    print("Qdrant connection successful. Collections:")
    print(collections)
except Exception as e:
    print("Failed to connect to Qdrant Cloud:", e)
    sys.exit(1)