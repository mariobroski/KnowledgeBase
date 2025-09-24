from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple


def dcg(relevances: Sequence[float]) -> float:
    return sum((rel / math.log2(idx + 2) for idx, rel in enumerate(relevances)))


def ndcg_at_k(retrieved: Sequence[str], relevant: Dict[str, float], k: int) -> float:
    k = min(k, len(retrieved))
    if k == 0:
        return 0.0
    rels = [relevant.get(doc_id, 0.0) for doc_id in retrieved[:k]]
    ideal = sorted(relevant.values(), reverse=True)[:k]
    dcg_val = dcg(rels)
    idcg_val = dcg(ideal) if ideal else 0.0
    return (dcg_val / idcg_val) if idcg_val > 0 else 0.0


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    if not rel_set:
        return 0.0
    hit = sum(1 for doc_id in retrieved[:k] if doc_id in rel_set)
    return hit / len(rel_set)


def mrr_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    for idx, doc_id in enumerate(retrieved[:k], start=1):
        if doc_id in rel_set:
            return 1.0 / idx
    return 0.0


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return float(s[idx])

