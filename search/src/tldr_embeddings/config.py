import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "tldr_search")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chunks")

# Path to the newsletter tree, relative to this package's root (search/).
# search/ is a sibling of tldr/ (the newsletter archive + mkdocs source) at
# the repo root, so ../tldr is the default.
DOCS_DIR = os.getenv("TLDR_DOCS_DIR", "../tldr")

VECTOR_INDEX_NAME = "tldr_vector_index"
TEXT_INDEX_NAME = "tldr_text_index"
EMBED_MODEL = "voyage-4"
QUERY_EMBED_MODEL = "voyage-4-lite"
