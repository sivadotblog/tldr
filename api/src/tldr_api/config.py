import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "tldr_search")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chunks")

VECTOR_INDEX_NAME = "tldr_vector_index"
QUERY_EMBED_MODEL = "voyage-4-lite"

# Astro dev server default port.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4321").split(",")
