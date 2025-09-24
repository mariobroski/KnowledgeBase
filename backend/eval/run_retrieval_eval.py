#!/usr/bin/env python3
"""
Ocena retrievalu (nDCG@k, Recall@k, MRR@k) na podstawie zapytań i qrels.

Wejście:
 - queries: TSV (id\tquestion) lub JSONL ([{"id","question"}]).
 - qrels: TSV (qid\tdocid\trel) – rel>0 traktowane jako relevant.
 - id_map: CSV (source_id,article_id,...) – mapuje docid z qrels do article_id w systemie.

Uruchamia politykę `text` (TextRAG), pobiera top‑k fragmentów, sprowadza do poziomu article_id
i liczy metryki na podstawie mapowania docid→article_id.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Tuple

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.db.database import SessionLocal  # type: ignore
from app.services.search_service import SearchService  # type: ignore
from backend.eval.metrics_utils import ndcg_at_k, recall_at_k, mrr_at_k  # type: ignore


def load_queries(path: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    if path.endswith('.jsonl') or path.endswith('.ndjson'):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                qid = str(rec.get('id') or rec.get('qid'))
                q = str(rec.get('question') or rec.get('query'))
                if qid and q:
                    out.append((qid, q))
    else:
        with open(path, 'r', encoding='utf-8') as f:
            for row in f:
                row = row.strip()
                if not row:
                    continue
                parts = row.split('\t')
                if len(parts) >= 2:
                    out.append((parts[0], parts[1]))
    return out


def load_qrels(path: str) -> Dict[str, Dict[str, float]]:
    qrels: Dict[str, Dict[str, float]] = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 3:
                # dopuszczalny format qid docid rel
                parts = line.split()
            if len(parts) < 3:
                continue
            qid, docid, rel = parts[0], parts[1], float(parts[2])
            if rel <= 0:
                continue
            qrels.setdefault(qid, {})[docid] = rel
    return qrels


def load_id_map(path: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = str(row.get('source_id'))
            aid = str(row.get('article_id'))
            if sid and aid:
                mapping[sid] = aid
    return mapping


def main() -> None:
    ap = argparse.ArgumentParser(description='Retrieval eval for TextRAG')
    ap.add_argument('--queries', required=True, help='Plik zapytań (TSV id\tquestion lub JSONL)')
    ap.add_argument('--qrels', required=True, help='Plik qrels (TSV qid\tdocid\trel)')
    ap.add_argument('--id-map', required=True, help='CSV mapowania source_id→article_id')
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--out', default='eval/retrieval_scores.json')
    args = ap.parse_args()

    queries = load_queries(args.queries)
    qrels = load_qrels(args.qrels)
    id_map = load_id_map(args.id_map)

    db = SessionLocal()
    service = SearchService(db)

    scores: List[Dict[str, Any]] = []

    for qid, question in queries:
        rel_docs = qrels.get(qid, {})
        if not rel_docs:
            continue
        try:
            res = service.search(query=question, policy_type='text', params={'limit': args.k})
            fragments = res.get('context', {}).get('fragments', [])
            retrieved_articles = []
            for fr in fragments:
                aid = str(fr.get('article_id'))
                if aid:
                    retrieved_articles.append(aid)
            # Zamapuj qrels docid → article_id
            relevant_article_ids = {id_map.get(docid) for docid in rel_docs.keys() if id_map.get(docid)}
            # nDCG, Recall, MRR
            ndcg = ndcg_at_k(retrieved_articles, {aid: 1.0 for aid in relevant_article_ids}, args.k)
            rec = recall_at_k(retrieved_articles, relevant_article_ids, args.k)
            mrr = mrr_at_k(retrieved_articles, relevant_article_ids, args.k)
            scores.append({
                'qid': qid,
                'ndcg@k': ndcg,
                'recall@k': rec,
                'mrr@k': mrr,
                'retrieved': retrieved_articles,
                'relevant': list(relevant_article_ids),
            })
            print(json.dumps({'qid': qid, 'ndcg@k': ndcg, 'recall@k': rec, 'mrr@k': mrr}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({'qid': qid, 'error': str(exc)}))

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()

