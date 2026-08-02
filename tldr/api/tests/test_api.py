from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tldr_api.main import app

client = TestClient(app)

FAKE_DOCS = [
    {
        "_id": "ai/2025-09-29#3",
        "title": "Apple's Veritas chatbot is reportedly an employee-only test",
        "url": "https://www.theverge.com/news/787046/apples-veritas-siri-ai-chatbot",
        "category": "ai",
        "date": "2025-09-29",
        "section": "Headlines & Launches",
        "source_host": "theverge.com",
        "raw_markdown": "Apple's Veritas chatbot is reportedly an employee-only test. "
        * 5,
        "score": 0.87,
    },
    {
        "_id": "ai/2025-09-29#5",
        "title": "DeepSeek-V3.1-Terminus launches with improved tool use",
        "url": "https://venturebeat.com/ai/deepseek",
        "category": "ai",
        "date": "2025-09-29",
        "section": "Headlines & Launches",
        "source_host": "venturebeat.com",
        "raw_markdown": "DeepSeek-V3.1-Terminus launches with improved agentic tool use.",
        "score": 0.81,
    },
]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("tldr_api.main.get_collection")
def test_search_returns_results(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = FAKE_DOCS

    resp = client.get("/api/search", params={"q": "apple chatbot"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "apple chatbot"
    assert body["count"] == 2
    assert body["results"][0]["id"] == "ai/2025-09-29#3"
    assert body["results"][0]["score"] == 0.87
    assert body["results"][0]["category"] == "ai"


@patch("tldr_api.main.get_collection")
def test_search_snippet_is_truncated(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = FAKE_DOCS

    resp = client.get("/api/search", params={"q": "apple"})

    snippet = resp.json()["results"][0]["snippet"]
    assert len(snippet) <= 221  # SNIPPET_LEN + ellipsis
    assert snippet.endswith("…")


@patch("tldr_api.main.get_collection")
def test_search_short_body_not_truncated(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = FAKE_DOCS

    resp = client.get("/api/search", params={"q": "deepseek"})

    snippet = resp.json()["results"][1]["snippet"]
    assert snippet == FAKE_DOCS[1]["raw_markdown"]
    assert not snippet.endswith("…")


def test_search_requires_query_param():
    resp = client.get("/api/search")
    assert resp.status_code == 422


def test_search_rejects_blank_query():
    resp = client.get("/api/search", params={"q": "   "})
    assert resp.status_code == 400


@patch("tldr_api.main.get_collection")
def test_search_passes_category_filter(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = []

    client.get("/api/search", params={"q": "test", "category": "infosec"})

    pipeline = mock_get_collection.return_value.aggregate.call_args[0][0]
    vector_stage = pipeline[0]["$vectorSearch"]
    assert vector_stage["filter"] == {"category": "infosec"}


@patch("tldr_api.main.get_collection")
def test_search_omits_filter_when_no_category(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = []

    client.get("/api/search", params={"q": "test"})

    pipeline = mock_get_collection.return_value.aggregate.call_args[0][0]
    vector_stage = pipeline[0]["$vectorSearch"]
    assert "filter" not in vector_stage


@patch("tldr_api.main.get_collection")
def test_search_respects_limit(mock_get_collection):
    mock_get_collection.return_value.aggregate.return_value = []

    client.get("/api/search", params={"q": "test", "limit": 5})

    pipeline = mock_get_collection.return_value.aggregate.call_args[0][0]
    vector_stage = pipeline[0]["$vectorSearch"]
    assert vector_stage["limit"] == 5
    assert vector_stage["numCandidates"] == 50


@pytest.mark.parametrize("limit", [0, 51, -1])
@patch("tldr_api.main.get_collection")
def test_search_limit_out_of_range_rejected(mock_get_collection, limit):
    resp = client.get("/api/search", params={"q": "test", "limit": limit})
    assert resp.status_code == 422


@patch("tldr_api.main.get_collection")
def test_search_backend_error_returns_502(mock_get_collection):
    from pymongo.errors import PyMongoError

    mock_get_collection.return_value.aggregate.side_effect = PyMongoError("index not ready")

    resp = client.get("/api/search", params={"q": "test"})
    assert resp.status_code == 502
