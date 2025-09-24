#!/usr/bin/env python3
"""
Smoke-test /api/search (lub warstwę usług) dla zestawu zapytań.

Uruchamia polityki: text, facts, graph, hybrid i zapisuje wyniki (CSV/JSON).
Można wskazać plik z zapytaniami (po jednym na linię) lub pojedyncze zapytanie.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, Iterable, List

# Ścieżka do backend/
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.db.database import SessionLocal  # type: ignore
from app.services.search_service import SearchService  # type: ignore


def _iter_queries(path: str | None, q: str | None) -> Iterable[str]:
    if q:
        yield q
        return
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def run_smoke(
    queries: Iterable[str],
    policies: List[str],
    limit: int,
    out_csv: str | None,
    out_json: str | None,
) -> None:
    db = SessionLocal()
    service = SearchService(db)

    rows: List[Dict[str, Any]] = []

    for query in queries:
        for policy in policies:
            try:
                result = service.search(query=query, policy_type=policy, params={"limit": limit})
                metrics = result.get("metrics", {})
                row = {
                    "query": query,
                    "policy": policy,
                    "search_time": metrics.get("search_time"),
                    "generation_time": metrics.get("generation_time"),
                    "total_time": metrics.get("total_time"),
                    "tokens_used": metrics.get("tokens_used"),
                    "cost": metrics.get("cost"),
                    "context_relevance": metrics.get("context_relevance"),
                    "faithfulness": metrics.get("faithfulness"),
                    "result_count": metrics.get("result_count"),
                }
                rows.append(row)
                print(json.dumps({"ok": True, **row}, ensure_ascii=False))
            except Exception as exc:
                print(json.dumps({"ok": False, "query": query, "policy": policy, "error": str(exc)}))

    if out_csv:
        os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "query",
                    "policy",
                    "search_time",
                    "generation_time",
                    "total_time",
                    "tokens_used",
                    "cost",
                    "context_relevance",
                    "faithfulness",
                    "result_count",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    if out_json:
        os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser(description="Smoke eval for /api/search policies")
    ap.add_argument("--queries-file", help="Plik z zapytaniami (po jednym na linię)")
    ap.add_argument("--query", help="Pojedyncze zapytanie (nadpisuje plik)")
    ap.add_argument("--policies", nargs="*", default=["text", "facts", "graph", "hybrid"], help="Polityki do uruchomienia")
    ap.add_argument("--limit", type=int, default=5, help="Limit wyników")
    ap.add_argument("--out-csv", default="eval/smoke_results.csv")
    ap.add_argument("--out-json", default="eval/smoke_results.json")
    args = ap.parse_args()

    queries = list(_iter_queries(args.queries_file, args.query))
    if not queries:
        print("Brak zapytań. Użyj --query lub --queries-file.")
        sys.exit(1)

    run_smoke(queries, args.policies, args.limit, args.out_csv, args.out_json)


if __name__ == "__main__":
    main()

