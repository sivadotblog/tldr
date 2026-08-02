import certifi
from pymongo import MongoClient
from pymongo.collection import Collection

from tldr_api.config import COLLECTION_NAME, DB_NAME, MONGODB_URI

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


def get_collection() -> Collection:
    return get_client()[DB_NAME][COLLECTION_NAME]
