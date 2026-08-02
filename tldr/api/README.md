# tldr-api

Plain FastAPI service over the `tldr_search.chunks` collection. One real
endpoint: `GET /api/search`. Vector search only — Atlas `$vectorSearch` with
`autoEmbed`, so this service never computes an embedding itself; the query
text is passed straight through and Voyage AI embeds it server-side.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # or reuse tldr-search/.venv
pip install -e .
cp .env.example .env   # fill in MONGODB_URI
```

## Run

```bash
uvicorn tldr_api.main:app --reload --port 8000
```

- `GET /health` → `{"status": "ok"}`
- `GET /api/search?q=deepseek&limit=10&category=ai` → ranked results
- `GET /docs` → interactive Swagger UI

## Tests

```bash
pytest -q
```

13 tests, all against a mocked collection (`unittest.mock.patch` on
`get_collection`) — no live Atlas cluster required to run them. Covers
health, result shaping, snippet truncation, category filtering, limit
validation, and backend-error handling (502 on `PyMongoError`).
