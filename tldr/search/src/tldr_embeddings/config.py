import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "tldr_search")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "chunks")

# Path to the newsletter tree, relative to this package's root (tldr/search/).
# search/ is a sibling of the category directories (ai/, tech/, ...) inside tldr/,
# so the parent directory is the newsletter tree itself.
DOCS_DIR = os.getenv("TLDR_DOCS_DIR", "..")

VECTOR_INDEX_NAME = "tldr_vector_index"
TEXT_INDEX_NAME = "tldr_text_index"
EMBED_MODEL = "voyage-4"
QUERY_EMBED_MODEL = "voyage-4-lite"
