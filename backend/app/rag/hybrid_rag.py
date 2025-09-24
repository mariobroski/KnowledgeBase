from __future__ import annotations

from typing import Any, Dict, List, Optional

import math

from sqlalchemy.orm import Session

from app.rag.base import RAGPolicy
from app.rag.settings import RAGSettings
from app.rag.text_rag import TextRAG
from app.rag.fact_rag import FactRAG
from app.rag.graph_rag import GraphRAG
from app.services.llm_service import get_llm_service


def _minmax(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if math.isclose(vmin, vmax):
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


class HybridRAG(RAGPolicy):
    """Polityka hybrydowa: łączy wyniki TextRAG, FactRAG i GraphRAG.

    Fuzja późna (late fusion) z normalizacją min–max i wagami z konfiguracji.
    """

    def __init__(self, config: Optional[RAGSettings] = None) -> None:
        super().__init__(config=config)
        self._text = TextRAG(config=self.config)
        self._facts = FactRAG(config=self.config)
        self._graph = GraphRAG(config=self.config)

    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        k = limit or self.config.top_k_results

        text_ctx = self._text.search(query, db, limit=max(k, self.config.text_rerank_top_n))
        fact_ctx = self._facts.search(query, db, limit=max(k, self.config.fact_rerank_top_n))
        graph_ctx = self._graph.search(query, db, limit=max(k, self.config.graph_max_paths))

        text_items = [
            {
                "type": "text",
                "score_raw": float(fr.get("similarity", 0.0)),
                "payload": fr,
            }
            for fr in text_ctx.get("fragments", [])
        ]

        fact_items = [
            {
                "type": "fact",
                "score_raw": float(min(f.get("similarity", 0.0), f.get("confidence", 0.0))),
                "payload": f,
            }
            for f in fact_ctx.get("facts", [])
        ]

        graph_items = [
            {
                "type": "graph",
                "score_raw": float(p.get("score", 0.0)),
                "payload": p,
            }
            for p in graph_ctx.get("paths", [])
        ]

        # Normalizacja min–max w obrębie każdego typu
        def _norm(items: List[Dict[str, Any]]) -> None:
            scores = _minmax([i["score_raw"] for i in items])
            for i, s in zip(items, scores):
                i["score_norm"] = s

        _norm(text_items)
        _norm(fact_items)
        _norm(graph_items)

        wt, wf, wg = (
            float(self.config.fusion_w_text),
            float(self.config.fusion_w_facts),
            float(self.config.fusion_w_graph),
        )

        fused: List[Dict[str, Any]] = []
        for it in text_items:
            fused.append({
                "score": wt * it.get("score_norm", 0.0),
                "type": it["type"],
                "payload": it["payload"],
            })
        for it in fact_items:
            fused.append({
                "score": wf * it.get("score_norm", 0.0),
                "type": it["type"],
                "payload": it["payload"],
            })
        for it in graph_items:
            fused.append({
                "score": wg * it.get("score_norm", 0.0),
                "type": it["type"],
                "payload": it["payload"],
            })

        fused.sort(key=lambda x: x["score"], reverse=True)
        fused = fused[:k]

        return {
            "query": query,
            "fused": fused,
            "components": {
                "text": text_ctx,
                "facts": fact_ctx,
                "graph": graph_ctx,
            },
        }

    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        llm = get_llm_service()
        fused = context.get("fused", [])
        if not fused:
            return {
                "response": "Brak kontekstu do odpowiedzi.",
                "elapsed_time": 0.0,
                "tokens_used": 0,
                "model": "no-context",
                "temperature": self.config.temperature,
            }

        # Zbuduj zwięzły kontekst mieszany
        lines: List[str] = []
        for item in fused[:8]:
            t = item["type"]
            p = item["payload"]
            if t == "text":
                title = p.get("article_title") or "Źródło"
                pos = p.get("position")
                snippet = (p.get("content") or "").replace("\n", " ")[:300]
                label = f"{title}, frag {pos}" if pos is not None else title
                lines.append(f"[FRAG] {label}: {snippet}")
            elif t == "fact":
                lines.append(f"[FAKT] ({p.get('similarity',0):.0%}/{p.get('confidence',0):.0%}) {p.get('content','')}")
            else:
                nodes = [n.get("name") for n in p.get("nodes", [])]
                lines.append(f"[GRAF] Ścieżka: {' -> '.join(nodes)}")

        system = (
            "Odpowiadaj wyłącznie na podstawie kontekstu. Dodawaj krótkie cytowania lub wskazania ścieżek."
        )
        user = f"Pytanie: {query}\n\nKontekst:\n" + "\n".join(lines) + "\n\nZwięźle odpowiedz."

        if llm.is_enabled:
            try:
                result = llm.generate(
                    prompt=user,
                    system=system,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.max_tokens, 700),
                )
                text = result.text or "Brak odpowiedzi."
                tokens = (
                    int(result.usage.get("total_tokens"))
                    if isinstance(result.usage.get("total_tokens"), int)
                    else len(text.split())
                )
                return {
                    "response": text,
                    "elapsed_time": 0.0,
                    "tokens_used": tokens,
                    "model": result.model,
                    "temperature": self.config.temperature,
                }
            except Exception:
                pass
        # Fallback
        text = "\n".join(lines)[: self.config.max_response_length]
        return {
            "response": text,
            "elapsed_time": 0.0,
            "tokens_used": len(text.split()),
            "model": "hybrid-fallback",
            "temperature": self.config.temperature,
        }

    def get_justification(self, context: Any) -> Dict[str, Any]:
        return {"type": "hybrid", "items": context.get("fused", [])}

    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        fused = context.get("fused", [])
        avg_score = sum(i.get("score", 0.0) for i in fused) / len(fused) if fused else 0.0
        token_count = len(response.split())
        faithfulness = min(1.0, avg_score)
        return {
            "tokens_used": token_count,
            "fused_count": len(fused),
            "avg_fused_score": round(avg_score, 4),
            "faithfulness": round(faithfulness, 4),
            "applied_settings": self.config.to_dict(),
        }

