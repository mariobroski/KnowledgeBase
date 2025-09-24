#!/usr/bin/env python3
"""
Init job that prepares the stack automatically after `docker compose up`:
- seeds example articles (if DB empty)
- indexes fragments into Qdrant (if embedding service available)
- extracts facts from fragments and mirrors entities/relations into JanusGraph
- creates example users

Idempotent: safe to run multiple times.
"""

from __future__ import annotations

import os
import sys
import time
from typing import List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.database_models import Fragment as FragmentModel, Article as ArticleModel
from app.services.embedding_service import get_embedding_service
from app.services.fact_service import FactService
from app.services.janusgraph_service import janusgraph_service


def wait_for_janusgraph(timeout_sec: int = 120) -> None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            if janusgraph_service.is_connected():
                print("JanusGraph: connected ✔")
                return
        except Exception:
            pass
        print("Waiting for JanusGraph...")
        time.sleep(3)
    print("⚠ JanusGraph not reachable within timeout. Continuing without it.")


def seed_articles_if_needed() -> None:
    from simple_seed import create_sample_articles  # type: ignore
    db = SessionLocal()
    try:
        count = db.query(ArticleModel).count()
        if count == 0:
            print("Seeding sample articles...")
            create_sample_articles()
        else:
            print(f"Articles already present: {count} (skip seeding)")
    finally:
        db.close()


def index_fragments_in_qdrant() -> None:
    svc = get_embedding_service()
    if not svc.is_enabled:
        print("Embedding/Qdrant disabled or model unavailable – skipping vector index.")
        return
    db: Session = SessionLocal()
    try:
        fragments: List[FragmentModel] = db.query(FragmentModel).all()
        if not fragments:
            print("No fragments found – skipping vector index.")
            return
        payloads = []
        for fr in fragments:
            if not (fr.content and fr.content.strip()):
                continue
            payloads.append({
                "id": fr.id,
                "content": fr.content,
                "article_id": fr.article_id,
                "position": getattr(fr, "position", None),
                "indexed": bool(getattr(fr, "indexed", True)),
            })
        if not payloads:
            print("No eligible fragments to index.")
            return
        svc.upsert_fragments(payloads)
        print(f"Indexed {len(payloads)} fragments in Qdrant ✔")
    finally:
        db.close()


def extract_facts_and_update_graph() -> None:
    db: Session = SessionLocal()
    try:
        fragments: List[FragmentModel] = db.query(FragmentModel).all()
        if not fragments:
            print("No fragments found – skipping fact extraction.")
            return
        fs = FactService(db)
        total = 0
        for fr in fragments:
            created = fs.extract_facts_from_fragment(fr.id)
            total += len(created)
        print(f"Extracted {total} facts from {len(fragments)} fragments ✔")
    finally:
        db.close()


def create_users() -> None:
    try:
        from add_users import create_sample_users  # type: ignore
    except Exception:
        print("add_users import failed – skipping user creation.")
        return
    try:
        create_sample_users()
    except Exception as exc:
        print(f"User creation failed: {exc}")


def main() -> None:
    # 1) Ensure JanusGraph is up (best effort)
    wait_for_janusgraph()
    # 2) Seed minimal data (if empty)
    seed_articles_if_needed()
    # 3) Index fragments in Qdrant (if embeddings available)
    index_fragments_in_qdrant()
    # 4) Extract facts and mirror to JanusGraph
    extract_facts_and_update_graph()
    # 5) Create sample users
    create_users()
    print("Init completed ✔")


if __name__ == "__main__":
    main()

