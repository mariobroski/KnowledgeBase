#!/usr/bin/env python3
"""
Aggregate results from smoke/operational, retrieval and quality evaluations.

Wejście (domyślnie):
 - eval/smoke_results.json (z backend/eval/smoke_eval.py)
 - eval/retrieval_scores.json (z backend/eval/run_retrieval_eval.py)
 - eval/quality_scores.json (z backend/eval/run_quality_eval.py)

Wyjście:
 - eval/aggregate_summary.json – agregaty per polityka
 - eval/aggregate_summary.csv – skrócona tabela per polityka

Przykład uruchomienia:
  python backend/eval/aggregate_results.py \
    --smoke eval/smoke_results.json \
    --retrieval eval/retrieval_scores.json \
    --quality eval/quality_scores.json \
    --out-json eval/aggregate_summary.json \
    --out-csv eval/aggregate_summary.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from typing import Any, Dict, List, Tuple


def _avg(vals: List[float]) -> float:
    return (sum(vals) / len(vals)) if vals else 0.0


def _percentile(vals: List[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    if len(s) == 1:
        return float(s[0])
    pos = (p / 100.0) * (len(s) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(s) - 1)
    frac = pos - lower
    return float(s[lower] * (1 - frac) + s[upper] * frac)


def load_json(path: str) -> Any:
    if not path or not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_smoke(smoke_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    per_policy: Dict[str, Dict[str, List[float]]] = {}
    for r in smoke_rows or []:
        pol = r.get('policy') or 'unknown'
        bucket = per_policy.setdefault(pol, {
            'search_time': [], 'generation_time': [], 'total_time': [],
            'tokens_used': [], 'cost': [], 'context_relevance': [], 'faithfulness': [],
        })
        for k in list(bucket.keys()):
            v = r.get(k)
            if isinstance(v, (int, float)):
                bucket[k].append(float(v))
    out: Dict[str, Dict[str, float]] = {}
    for pol, m in per_policy.items():
        out[pol] = {
            'search_time_avg': _avg(m['search_time']),
            'search_time_p50': _percentile(m['search_time'], 50),
            'search_time_p95': _percentile(m['search_time'], 95),
            'generation_time_avg': _avg(m['generation_time']),
            'generation_time_p50': _percentile(m['generation_time'], 50),
            'generation_time_p95': _percentile(m['generation_time'], 95),
            'total_time_avg': _avg(m['total_time']),
            'total_time_p50': _percentile(m['total_time'], 50),
            'total_time_p95': _percentile(m['total_time'], 95),
            'tokens_avg': _avg(m['tokens_used']),
            'cost_avg': _avg(m['cost']),
            'context_relevance_avg': _avg(m['context_relevance']),
            'faithfulness_avg': _avg(m['faithfulness']),
        }
    return out


def aggregate_retrieval(ret_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    # run_retrieval_eval.py zwraca metryki per qid. Tu liczymy średnią dla całego zbioru.
    ndcg = [float(r.get('ndcg@k', 0.0)) for r in ret_rows or []]
    rec = [float(r.get('recall@k', 0.0)) for r in ret_rows or []]
    mrr = [float(r.get('mrr@k', 0.0)) for r in ret_rows or []]
    return {
        'ndcg_avg': _avg(ndcg),
        'recall_avg': _avg(rec),
        'mrr_avg': _avg(mrr),
    }


def aggregate_quality(qual_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    per_policy: Dict[str, Dict[str, List[float]]] = {}
    for r in qual_rows or []:
        pol = r.get('policy') or 'unknown'
        bucket = per_policy.setdefault(pol, {
            'faithfulness': [], 'answer_relevance': [], 'context_precision': [], 'context_recall': [],
            'tokens_used': [], 'total_time': [],
        })
        for k in list(bucket.keys()):
            v = r.get(k)
            if isinstance(v, (int, float)):
                bucket[k].append(float(v))
    out: Dict[str, Dict[str, float]] = {}
    for pol, m in per_policy.items():
        out[pol] = {
            'faithfulness_avg': _avg(m['faithfulness']),
            'answer_relevance_avg': _avg(m['answer_relevance']),
            'context_precision_avg': _avg(m['context_precision']),
            'context_recall_avg': _avg(m['context_recall']),
            'tokens_avg': _avg(m['tokens_used']),
            'total_time_p50': _percentile(m['total_time'], 50),
            'total_time_p95': _percentile(m['total_time'], 95),
        }
    return out


def merge_aggregates(
    smoke: Dict[str, Dict[str, float]],
    quality: Dict[str, Dict[str, float]],
    retrieval: Dict[str, float],
) -> Dict[str, Any]:
    policies = sorted(set(list(smoke.keys()) + list(quality.keys())))
    merged: Dict[str, Any] = {'retrieval_overall': retrieval, 'policies': {}}
    for pol in policies:
        merged['policies'][pol] = {**smoke.get(pol, {}), **quality.get(pol, {})}
    return merged


def main() -> None:
    ap = argparse.ArgumentParser(description='Aggregate eval results (operational, retrieval, quality)')
    ap.add_argument('--smoke', default='eval/smoke_results.json')
    ap.add_argument('--retrieval', default='eval/retrieval_scores.json')
    ap.add_argument('--quality', default='eval/quality_scores.json')
    ap.add_argument('--out-json', default='eval/aggregate_summary.json')
    ap.add_argument('--out-csv', default='eval/aggregate_summary.csv')
    args = ap.parse_args()

    smoke_rows = load_json(args.smoke)
    ret_rows = load_json(args.retrieval)
    qual_rows = load_json(args.quality)

    smoke_agg = aggregate_smoke(smoke_rows if isinstance(smoke_rows, list) else [])
    ret_agg = aggregate_retrieval(ret_rows if isinstance(ret_rows, list) else [])
    qual_agg = aggregate_quality(qual_rows if isinstance(qual_rows, list) else [])

    merged = merge_aggregates(smoke_agg, qual_agg, ret_agg)

    os.makedirs(os.path.dirname(args.out_json) or '.', exist_ok=True)
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # CSV z najważniejszymi polami per polityka
    fields = [
        'policy',
        'search_time_p50', 'search_time_p95', 'total_time_p50', 'total_time_p95',
        'tokens_avg', 'cost_avg',
        'context_relevance_avg', 'faithfulness_avg',
        'answer_relevance_avg', 'context_precision_avg', 'context_recall_avg',
    ]
    with open(args.out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for pol, vals in merged['policies'].items():
            row = {k: vals.get(k, '') for k in fields}
            row['policy'] = pol
            writer.writerows([row])

    print(f"Zapisano agregaty: {args.out_json}, {args.out_csv}")


if __name__ == '__main__':
    main()

