from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.db.database_models import Entity as EntityModel
from app.db.database_models import Relation as RelationModel


class GraphConsistencyService:
    """Proste kontrole spójności grafu wiedzy (SQL).

    Zwraca wykryte anomalie w formie raportu.
    """

    def __init__(self, db: Session):
        self.db = db

    def find_orphan_entities(self, limit: int = 100) -> List[Dict[str, Any]]:
        q = (
            self.db.query(EntityModel)
            .outerjoin(RelationModel, or_(
                RelationModel.source_entity_id == EntityModel.id,
                RelationModel.target_entity_id == EntityModel.id,
            ))
            .group_by(EntityModel.id)
            .having(func.count(RelationModel.id) == 0)
            .limit(limit)
        )
        rows = q.all()
        return [{"id": e.id, "name": e.name, "type": e.type} for e in rows]

    def find_edges_without_evidence(self, limit: int = 200) -> List[Dict[str, Any]]:
        # RelationModel.evidence_facts udostępnia listę powiązanych Factów
        relations = (
            self.db.query(RelationModel)
            .limit(limit * 2)
            .all()
        )
        out: List[Dict[str, Any]] = []
        for r in relations:
            evidence = getattr(r, 'evidence_facts', []) or []
            if len(evidence) == 0:
                out.append({
                    "id": r.id,
                    "source_entity_id": r.source_entity_id,
                    "target_entity_id": r.target_entity_id,
                    "relation_type": r.relation_type,
                    "weight": float(r.weight or 0.0),
                })
            if len(out) >= limit:
                break
        return out

    def find_type_issues(self, limit: int = 200) -> List[Dict[str, Any]]:
        # Bardzo prosta heurystyka: brak typu lub 'Unknown'
        rows = (
            self.db.query(EntityModel)
            .filter(or_(EntityModel.type.is_(None), EntityModel.type == '', EntityModel.type.ilike('%unknown%')))
            .limit(limit)
            .all()
        )
        return [{"id": e.id, "name": e.name, "type": e.type} for e in rows]

    def report(self, limits: Dict[str, int] | None = None) -> Dict[str, Any]:
        limits = limits or {}
        orphan_limit = int(limits.get("orphans", 100))
        edges_limit = int(limits.get("edges_no_evidence", 200))
        types_limit = int(limits.get("type_issues", 200))

        orphans = self.find_orphan_entities(limit=orphan_limit)
        edges_wo_evidence = self.find_edges_without_evidence(limit=edges_limit)
        type_issues = self.find_type_issues(limit=types_limit)
        communities = self._weakly_connected_components(limit=50)

        return {
            "summary": {
                "orphan_entities_count": len(orphans),
                "edges_without_evidence_count": len(edges_wo_evidence),
                "entities_with_type_issues_count": len(type_issues),
                "communities_count": len(communities),
            },
            "orphans": orphans,
            "edges_without_evidence": edges_wo_evidence,
            "entities_with_type_issues": type_issues,
            "communities_sample": communities,
        }

    def _weakly_connected_components(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Prosty podział na spójne składowe (mock społeczności)."""
        rels = self.db.query(RelationModel).limit(5000).all()
        parent: Dict[int, int] = {}

        def find(x: int) -> int:
            parent.setdefault(x, x)
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for r in rels:
            if r.source_entity_id and r.target_entity_id:
                union(int(r.source_entity_id), int(r.target_entity_id))

        # Grupuj po reprezentantach
        groups: Dict[int, List[int]] = {}
        for node in list(parent.keys()):
            root = find(node)
            groups.setdefault(root, []).append(node)

        # Zwróć kilka największych grup jako sample
        ordered = sorted(groups.values(), key=len, reverse=True)[:limit]
        return [{"size": len(g), "entity_ids": g[:20]} for g in ordered]
