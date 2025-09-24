#!/usr/bin/env python3
"""
Ingest (RAGBench-like) corpora into the local system.

Wczytuje dokumenty z pliku JSONL/JSON i dodaje do bazy jako `articles`.
Treść jest automatycznie segmentowana (ArticleService), a fragmenty
opcjonalnie indeksowane do Qdrant (EmbeddingService, jeśli dostępny).

Wejście (elastyczne):
 - JSONL (po jednym rekordzie na linię) lub pojedynczy plik JSON
 - Pola:  id (domyślnie "id"), tytuł (domyślnie "title"), treść (domyślnie "context", fallback "text")

Przykład:
  python backend/eval/ingest_ragbench.py \
    --input data/finqa.jsonl \
    --domain finance \
    --id-field id --title-field title --text-field context \
    --output-map id_map_finqa.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, Iterable, List

# Upewnij się, że `backend/` jest na ścieżce modułów
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.db.database import SessionLocal  # type: ignore
from app.services.article_service import ArticleService  # type: ignore


def _iter_json(input_path: str) -> Iterable[Dict[str, Any]]:
    if input_path.endswith(".jsonl") or input_path.endswith(".ndjson"):
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            elif isinstance(data, dict):
                # Pojedynczy obiekt
                yield data
            else:
                raise ValueError("Nieobsługiwany format pliku JSON")


def ingest(
    input_path: str,
    domain: str,
    id_field: str = "id",
    title_field: str = "title",
    text_field: str = "context",
    output_map: str | None = None,
) -> None:
    db = SessionLocal()
    service = ArticleService(db)

    id_map: List[Dict[str, Any]] = []

    total = 0
    created = 0
    for rec in _iter_json(input_path):
        total += 1
        src_id = rec.get(id_field)
        title = (rec.get(title_field) or rec.get("doc_title") or f"doc_{total}")
        text = rec.get(text_field) or rec.get("text") or rec.get("document")
        if not isinstance(text, str) or not text.strip():
            continue

        art = service.create_article(
            title=str(title)[:255],
            content=str(text),
            file_content=None,
            filename=None,
            author_id=None,
            tags=[domain] if domain else None,
        )
        id_map.append({"source_id": src_id, "article_id": art.id, "title": art.title})
        created += 1

    if output_map:
        os.makedirs(os.path.dirname(output_map) or ".", exist_ok=True)
        with open(output_map, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source_id", "article_id", "title"])
            writer.writeheader()
            writer.writerows(id_map)

    print(f"Przetworzono rekordów: {total}; utworzono artykułów: {created}")
    if output_map:
        print(f"Zapisano mapowanie ID: {output_map}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest RAGBench-like corpora into local system")
    ap.add_argument("--input", required=True, help="Ścieżka do pliku JSON/JSONL")
    ap.add_argument("--domain", default="generic", help="Etykieta domeny/tag artykułu")
    ap.add_argument("--id-field", default="id")
    ap.add_argument("--title-field", default="title")
    ap.add_argument("--text-field", default="context")
    ap.add_argument("--output-map", default="id_map.csv")
    args = ap.parse_args()

    ingest(
        input_path=args.input,
        domain=args.domain,
        id_field=args.id_field,
        title_field=args.title_field,
        text_field=args.text_field,
        output_map=args.output_map,
    )


if __name__ == "__main__":
    main()

