import certifi
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

from tldr_embeddings.config import (
    COLLECTION_NAME,
    DB_NAME,
    EMBED_MODEL,
    MONGODB_URI,
    QUERY_EMBED_MODEL,
    TEXT_INDEX_NAME,
    VECTOR_INDEX_NAME,
)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise RuntimeError("MONGODB_URI is not set (check .env)")
        # Explicit certifi bundle -- macOS's default trust store intermittently
        # fails the Atlas TLS handshake with the system OpenSSL build.
        _client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    return _client


def get_db() -> Database:
    return get_client()[DB_NAME]


def get_collection() -> Collection:
    return get_db()[COLLECTION_NAME]


VECTOR_INDEX_DEFINITION = {
    "fields": [
        {"type": "autoEmbed", "modality": "text", "path": "raw_markdown", "model": EMBED_MODEL},
        {"type": "filter", "path": "category"},
        {"type": "filter", "path": "date"},
        {"type": "filter", "path": "year_month"},
        {"type": "filter", "path": "section"},
        {"type": "filter", "path": "source_host"},
    ]
}

TEXT_INDEX_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "title": {"type": "string"},
            "raw_markdown": {"type": "string"},
        },
    }
}


def create_vector_index() -> dict:
    """Create the autoEmbed vector index. Idempotent — 'already exists' is
    treated as success, matching the kbase pattern."""
    result = {"vector": False, "vector_error": None}
    try:
        model = SearchIndexModel(
            definition=VECTOR_INDEX_DEFINITION, name=VECTOR_INDEX_NAME, type="vectorSearch"
        )
        get_collection().create_search_index(model=model)
        result["vector"] = True
    except OperationFailure as e:
        if "already exists" in str(e).lower():
            result["vector"] = True
        else:
            result["vector_error"] = str(e)
    return result


def create_text_index() -> dict:
    """Create the full-text index for the hybrid ($rankFusion) search path.

    Not created by default: M0 caps a cluster at 3 search/vector indexes
    total, and this shared cluster already has 2 in use by humana-it-kbase.
    Adding this index requires either dropping one of those, or moving to
    M10+. Call explicitly once that headroom exists.
    """
    result = {"text": False, "text_error": None}
    try:
        model = SearchIndexModel(definition=TEXT_INDEX_DEFINITION, name=TEXT_INDEX_NAME)
        get_collection().create_search_index(model=model)
        result["text"] = True
    except OperationFailure as e:
        if "already exists" in str(e).lower():
            result["text"] = True
        else:
            result["text_error"] = str(e)
    return result


def create_search_indexes() -> dict:
    """Create both indexes. Only safe when the cluster has 2 free slots."""
    return {**create_vector_index(), **create_text_index()}
