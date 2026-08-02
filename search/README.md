# tldr-embeddings

Chunks the TLDR newsletter archive (`../../tldr/`) into one document per
story and upserts into MongoDB Atlas, where `autoEmbed` handles vectorization
via Voyage AI — no local embedding model.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # or reuse tldr-search/.venv
pip install -e .
cp .env.example .env   # fill in MONGODB_URI
```

## Usage

```bash
# Pilot: most recent 7 issues per category (~35 files, ~470 chunks)
python -m tldr_embeddings.load --recent 7 --dry-run   # chunk only, no Mongo write
python -m tldr_embeddings.load --recent 7             # chunk + upsert

# Full corpus (~18,300 chunks)
python -m tldr_embeddings.load --all
```

`--recent N` selects the last N issues per category *by filename date*, not
a wall-clock day cutoff — the archive job runs on its own schedule and may
lag "today," which would otherwise silently select zero files.

Upserts are keyed on a deterministic `_id` (`{category}/{date}#{ordinal}`),
so re-running the loader over the same newsletters is idempotent.

## Creating search indexes

One-time, after the collection has documents (Atlas needs the collection to
exist first):

```python
from tldr_embeddings.db import create_search_indexes
create_search_indexes()
```

## Tests

```bash
pytest -q
```

50 tests, all against real fixture newsletters (`tests/fixtures/`) — no
mocked markdown. Covers footer/masthead exclusion, sponsor and self-promo
filtering, emoji/whitespace normalization, URL tracking-param stripping, and
idempotency.

See `docs/superpowers/specs/2026-08-01-tldr-search-design.md` (repo root)
for the full design.
