#!/usr/bin/env python3
"""
TRACe-like evaluation adapter.

Łączy wyniki systemu per zapytanie z etykietami referencyjnymi (adherence,
completeness, utilization, relevance) i liczy agregaty per polityka.

Wejście:
 - --system: JSON z wierszami per zapytanie (output z run_quality_eval.py lub smoke_eval.py)
   Wymagane pola: qid, policy (text|facts|graph|hybrid). Pozostałe pomijane.
 - --labels: JSONL z wierszami o polach: id, adherence (0/1), completeness (0..1), utilization (0..1)
   Nazwy pól można zmienić parametrami CLI.

Wyjście:
 - JSON z agregatami TRACe per polityka.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List


def load_system(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        raise ValueError('Oczekiwano listy rekordów w pliku systemowym')


def load_labels(path: str, id_field: str, adh_field: str, comp_field: str, util_field: str) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            qid = str(rec.get(id_field))
            if not qid:
                continue
            adh = float(rec.get(adh_field)) if rec.get(adh_field) is not None else None
            comp = float(rec.get(comp_field)) if rec.get(comp_field) is not None else None
            util = float(rec.get(util_field)) if rec.get(util_field) is not None else None
            out[qid] = {}
            if adh is not None:
                out[qid]['adherence'] = adh
            if comp is not None:
                out[qid]['completeness'] = comp
            if util is not None:
                out[qid]['utilization'] = util
    return out


def avg(vals: List[float]) -> float:
    return (sum(vals) / len(vals)) if vals else 0.0


def evaluate(system_rows: List[Dict[str, Any]], labels: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    per_policy: Dict[str, Dict[str, List[float]]] = {}
    for r in system_rows:
        qid = str(r.get('qid'))
        pol = str(r.get('policy', 'unknown'))
        if qid not in labels:
            continue
        bucket = per_policy.setdefault(pol, {
            'adherence': [], 'completeness': [], 'utilization': []
        })
        lab = labels[qid]
        for k in ('adherence', 'completeness', 'utilization'):
            v = lab.get(k)
            if isinstance(v, (int, float)):
                bucket[k].append(float(v))
    out: Dict[str, Any] = {}
    for pol, m in per_policy.items():
        out[pol] = {
            'adherence_avg': avg(m['adherence']),
            'completeness_avg': avg(m['completeness']),
            'utilization_avg': avg(m['utilization']),
            'count': len(m['adherence']),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description='TRACe adapter – agregaty per polityka')
    ap.add_argument('--system', required=True, help='JSON wyników systemu (run_quality_eval lub smoke_eval)')
    ap.add_argument('--labels', required=True, help='JSONL etykiet TRACe (id + adherence/completeness/utilization)')
    ap.add_argument('--id-field', default='id')
    ap.add_argument('--adh-field', default='adherence')
    ap.add_argument('--comp-field', default='completeness')
    ap.add_argument('--util-field', default='utilization')
    ap.add_argument('--out', default='eval/trace_aggregates.json')
    args = ap.parse_args()

    sys_rows = load_system(args.system)
    labels = load_labels(args.labels, args.id_field, args.adh_field, args.comp_field, args.util_field)
    agg = evaluate(sys_rows, labels)

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
    print(f'Zapisano agregaty TRACe: {args.out}')


if __name__ == '__main__':
    main()

