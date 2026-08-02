"""Plain FastAPI service in front of the tldr_search.chunks collection.

One real endpoint: GET /api/search, which runs Atlas $vectorSearch with
autoEmbed handling both index-time and query-time embedding (Voyage AI) —
this service never computes an embedding itself.
"""

from __future__ import annotations

from pymongo.errors import PyMongoError

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tldr_api.config import CORS_ORIGINS, QUERY_EMBED_MODEL, VECTOR_INDEX_NAME
from tldr_api.db import get_collection

app = FastAPI(title="tldr-search API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class SearchResult(BaseModel):
    id: str
    title: str
    url: str
    category: str
    date: str
    section: str
    source_host: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]


SNIPPET_LEN = 220


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    category: str | None = Query(None, description="Filter to one category, e.g. 'ai'"),
) -> SearchResponse:
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="q must not be blank")

    vector_stage: dict = {
        "index": VECTOR_INDEX_NAME,
        "path": "raw_markdown",
        "query": q,
        "model": QUERY_EMBED_MODEL,
        "numCandidates": limit * 10,
        "limit": limit,
    }
    if category:
        vector_stage["filter"] = {"category": category}

    pipeline = [
        {"$vectorSearch": vector_stage},
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "url": 1,
                "category": 1,
                "date": 1,
                "section": 1,
                "source_host": 1,
                "raw_markdown": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    try:
        docs = list(get_collection().aggregate(pipeline))
    except PyMongoError as e:
        raise HTTPException(status_code=502, detail=f"search backend error: {e}") from e

    results = [
        SearchResult(
            id=d["_id"],
            title=d.get("title", ""),
            url=d.get("url", ""),
            category=d.get("category", ""),
            date=d.get("date", ""),
            section=d.get("section", ""),
            source_host=d.get("source_host", ""),
            snippet=_snippet(d.get("raw_markdown", "")),
            score=d.get("score", 0.0),
        )
        for d in docs
    ]
    return SearchResponse(query=q, count=len(results), results=results)


def _snippet(text: str) -> str:
    if len(text) <= SNIPPET_LEN:
        return text
    return text[:SNIPPET_LEN].rsplit(" ", 1)[0] + "…"
