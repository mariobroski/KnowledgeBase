#!/usr/bin/env python3
"""
Ocena jakości odpowiedzi (faithfulness, answer_relevance, context_precision/recall).

Skrypt próbuje użyć biblioteki RAGAS, jeśli jest dostępna i poprawnie
skonfigurowany jest dostawca LLM (np. OpenAI). W przeciwnym razie stosuje
proste proxy oparte na pokryciu słów kluczowych i dopasowaniach fragmentów.

Wejście:
 - queries: TSV (id\tquestion) lub JSONL ([{"id","question"}])
 - policies: list[a] polityk do uruchomienia (text|facts|graph|hybrid)
 - limit: top‑k

Wyjście:
 - JSON z per‑zapytanie metrykami i agregatami per politykę
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, Iterable, List, Tuple

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.db.database import SessionLocal  # type: ignore
from app.services.search_service import SearchService  # type: ignore


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


def _simple_faithfulness(answer: str, contexts: List[str]) -> float:
    """Proxy zgodności: pokrycie lematycznych słów kluczowych odpowiedzi w kontekście."""
    import re
    tokens = {t for t in re.findall(r"\w+", answer.lower()) if len(t) > 3}
    if not tokens:
        return 0.0
    ctx = " \n ".join(contexts).lower()
    covered = sum(1 for t in tokens if t in ctx)
    return covered / max(1, len(tokens))


def _extract_context_strings(policy: str, context: Dict[str, Any]) -> List[str]:
    if policy == 'text':
        return [fr.get('content') or '' for fr in context.get('fragments', [])]
    if policy == 'facts':
        return [f.get('content') or '' for f in context.get('facts', [])]
    if policy == 'graph':
        parts = []
        for p in context.get('paths', [])[:5]:
            nodes = [n.get('name') for n in p.get('nodes', [])]
            rels = [f"{r.get('source')} --[{r.get('type')}]--> {r.get('target')}" for r in p.get('relations', [])]
            parts.append(" -> ".join(nodes) + (" | " + "; ".join(rels) if rels else ''))
        return parts
    if policy == 'hybrid':
        items = context.get('fused', [])
        out = []
        for it in items:
            t = it.get('type')
            p = it.get('payload', {})
            if t == 'text':
                out.append(p.get('content') or '')
            elif t == 'fact':
                out.append(p.get('content') or '')
            elif t == 'graph':
                nodes = [n.get('name') for n in p.get('nodes', [])]
                out.append(" -> ".join(nodes))
        return out
    return []


def try_ragas_eval(samples: List[Dict[str, Any]]) -> List[Dict[str, float]]:
    """Próba uruchomienia RAGAS; w razie braku – zwrot pustych metryk."""
    try:
        # Lazy import, aby nie wywracać skryptu, jeśli ragas nie jest zainstalowany
        from ragas.metrics import faithfulness, answer_relevance, context_precision, context_recall  # type: ignore
        from ragas import evaluate  # type: ignore
        import pandas as pd  # type: ignore

        rows = []
        for s in samples:
            rows.append({
                'question': s['question'],
                'answer': s['answer'],
                'contexts': s['contexts'],
                # 'ground_truths': s.get('ground_truths', [])  # opcjonalne
            })
        df = pd.DataFrame(rows)
        result = evaluate(df, metrics=[faithfulness, answer_relevance, context_precision, context_recall])
        # result.scores to dict metric->list
        out: List[Dict[str, float]] = []
        for i in range(len(df)):
            out.append({m: float(scores[i]) for m, scores in result.scores.items()})
        return out
    except Exception:
        return [{} for _ in samples]


def main() -> None:
    ap = argparse.ArgumentParser(description='Quality eval (RAGAS if available, else proxy)')
    ap.add_argument('--queries', required=True, help='Plik zapytań (TSV id\tquestion lub JSONL)')
    ap.add_argument('--policies', nargs='*', default=['text', 'facts', 'graph', 'hybrid'])
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--out', default='eval/quality_scores.json')
    args = ap.parse_args()

    queries = load_queries(args.queries)
    db = SessionLocal()
    service = SearchService(db)

    per_query: List[Dict[str, Any]] = []

    for qid, question in queries:
        for policy in args.policies:
            res = service.search(query=question, policy_type=policy, params={'limit': args.limit})
            answer = res.get('response') or ''
            context = res.get('context', {})
            ctx_strings = _extract_context_strings(policy, context)

            samples = [{'question': question, 'answer': answer, 'contexts': ctx_strings}]
            ragas_scores = try_ragas_eval(samples)[0]

            if not ragas_scores:
                # Proxy faithfulness
                ragas_scores = {'faithfulness': _simple_faithfulness(answer, ctx_strings)}

            row = {
                'qid': qid,
                'policy': policy,
                'answer_len': len(answer.split()),
                'faithfulness': float(ragas_scores.get('faithfulness', 0.0)),
                'answer_relevance': float(ragas_scores.get('answer_relevance', 0.0)) if ragas_scores.get('answer_relevance') is not None else None,
                'context_precision': float(ragas_scores.get('context_precision', 0.0)) if ragas_scores.get('context_precision') is not None else None,
                'context_recall': float(ragas_scores.get('context_recall', 0.0)) if ragas_scores.get('context_recall') is not None else None,
                'tokens_used': res.get('metrics', {}).get('tokens_used'),
                'total_time': res.get('metrics', {}).get('total_time'),
            }
            per_query.append(row)
            print(json.dumps({'qid': qid, **{k: v for k, v in row.items() if k not in ('qid',)}}, ensure_ascii=False))

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(per_query, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()

