"""Chunk newsletter markdown and upsert into MongoDB Atlas.

Usage:
    python -m tldr_embeddings.load --recent 7          # pilot: last 7 issues/category
    python -m tldr_embeddings.load --all               # full corpus
    python -m tldr_embeddings.load --recent 7 --dry-run  # chunk only, skip Mongo
    python -m tldr_embeddings.load --all --reset       # wipe collection, then full reload
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tldr_embeddings.chunker import chunk_dict, dedup_global, parse_file
from tldr_embeddings.config import DOCS_DIR


def find_files(docs_dir: Path, recent: int | None) -> list[Path]:
    """All newsletter files, optionally restricted to the most recent N
    issues per category (by filename date). Deliberately not a wall-clock
    day cutoff — the archive job runs on its own schedule and may lag
    "today" by weeks, which would silently select zero files."""
    categories = sorted(p for p in docs_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    files: list[Path] = []
    for cat in categories:
        cat_files = sorted(cat.glob("[0-9]*.md"))
        if recent is not None:
            cat_files = cat_files[-recent:]
        files.extend(cat_files)
    return files


def run(docs_dir: Path, recent: int | None, dry_run: bool, reset: bool = False) -> int:
    if not docs_dir.is_dir():
        print(f"error: docs dir not found: {docs_dir}", file=sys.stderr)
        return 1

    files = find_files(docs_dir, recent)
    if not files:
        print("no matching newsletter files found", file=sys.stderr)
        return 1

    chunks = []
    for f in files:
        chunks.extend(parse_file(f))
    chunks = dedup_global(chunks)

    by_cat: dict[str, int] = {}
    for c in chunks:
        by_cat[c.category] = by_cat.get(c.category, 0) + 1

    print(f"files scanned: {len(files)}")
    print(f"chunks produced: {len(chunks)}")
    print(f"by category: {by_cat}")

    if dry_run:
        print("dry run — skipping Mongo upsert")
        return 0

    from pymongo import UpdateOne

    from tldr_embeddings.db import get_collection

    collection = get_collection()

    if reset:
        deleted = collection.delete_many({})
        print(f"reset: deleted {deleted.deleted_count} existing documents")

    ops = [
        UpdateOne({"_id": c.id}, {"$set": chunk_dict(c)}, upsert=True) for c in chunks
    ]
    if ops:
        result = collection.bulk_write(ops, ordered=False)
        print(f"upserted: {result.upserted_count}  modified: {result.modified_count}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", default=DOCS_DIR, help="path to the tldr newsletter markdown tree")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--recent", type=int, help="only the last N issues per category (pilot mode)")
    group.add_argument("--all", action="store_true", help="load the full corpus")
    ap.add_argument("--dry-run", action="store_true", help="chunk only, do not write to MongoDB")
    ap.add_argument(
        "--reset",
        action="store_true",
        help="delete all existing documents before loading (only valid with --all)",
    )
    args = ap.parse_args()

    if args.reset and not args.all:
        print("error: --reset requires --all", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[2]
    docs_dir = (root / args.docs).resolve()
    recent = None if args.all else args.recent
    return run(docs_dir, recent, args.dry_run, args.reset)


if __name__ == "__main__":
    raise SystemExit(main())
