#!/usr/bin/env python3
"""Trenuje model ML do wyboru polityki RAG na podstawie zapytań użytkowników.

Wymaga scikit-learn + joblib. Dane treningowe pobierane są z tabeli SearchQuery
– zakładamy, że pole `policy` przechowuje typ użytej polityki.

Przykład:
    python backend/eval/train_policy_router.py --out models/policy_router.joblib \
        --min-per-class 5
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.db.database import SessionLocal  # type: ignore
from app.db.database_models import SearchQuery as SearchQueryModel  # type: ignore


def load_training_data(session, min_per_class: int) -> Tuple[List[str], List[str]]:
    rows: List[SearchQueryModel] = (
        session.query(SearchQueryModel)
        .filter(SearchQueryModel.policy.isnot(None))
        .all()
    )

    queries: List[str] = []
    policies: List[str] = []

    for row in rows:
        query = (row.query or "").strip()
        policy = (row.policy or "").strip().lower()
        if not query or not policy:
            continue
        queries.append(query)
        policies.append(policy)

    if not queries:
        raise ValueError("Brak danych treningowych (tabela search_queries jest pusta)")

    # Sprawdź klasy – odfiltruj te, które mają zbyt mało przykładów
    filtered_queries: List[str] = []
    filtered_policies: List[str] = []
    for policy in sorted(set(policies)):
        indices = [i for i, p in enumerate(policies) if p == policy]
        if len(indices) < min_per_class:
            continue
        for idx in indices:
            filtered_queries.append(queries[idx])
            filtered_policies.append(policies[idx])

    if not filtered_queries:
        raise ValueError(
            "Za mało danych na klasę – zwiększ ilość zapytań lub obniż próg min-per-class"
        )

    return filtered_queries, filtered_policies


def train_model(queries: List[str], policies: List[str]) -> dict:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)
    X = vectorizer.fit_transform(queries)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(policies)

    clf = LogisticRegression(max_iter=2000, multi_class="auto")
    clf.fit(X, y)

    return {
        "vectorizer": vectorizer,
        "model": clf,
        "label_encoder": label_encoder,
        "labels": list(label_encoder.classes_),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ML policy router")
    parser.add_argument("--out", required=True, help="Ścieżka do zapisu modelu (joblib)")
    parser.add_argument("--min-per-class", type=int, default=5, help="Minimalna liczba przykładów na klasę")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        queries, policies = load_training_data(session, min_per_class=args.min_per_class)
    finally:
        session.close()

    payload = train_model(queries, policies)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, out_path)
    print(f"Zapisano model ML policy routera do {out_path}")


if __name__ == "__main__":
    main()
