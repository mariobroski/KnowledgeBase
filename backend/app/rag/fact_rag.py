from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.db.database_models import Article as ArticleModel
from app.db.database_models import Fact as FactModel
from app.db.database_models import Fragment as FragmentModel
from app.rag.base import RAGPolicy
from app.rag.text_rag import _cosine_similarity, _get_embedder, _token_similarity  # reuse helperów
from app.services.llm_service import get_llm_service


class FactRAG(RAGPolicy):
    """Polityka FaktRAG z konfiguracją personalizowaną."""

    def __init__(self, config=None):
        super().__init__(config=config)

    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()

        effective_limit = limit or self.config.top_k_results
        candidate_pool = max(effective_limit, self.config.fact_rerank_top_n)

        facts_query = (
            db.query(FactModel)
            .join(FragmentModel)
            .join(ArticleModel)
            .filter(FactModel.status != "rejected")
            .order_by(FactModel.confidence.desc())
            .limit(candidate_pool)
        )
        facts_db: List[FactModel] = facts_query.all()

        embedder = _get_embedder(self.config.embedding_model)
        query_vector: Optional[np.ndarray] = None
        if embedder is not None:
            query_vector = np.array(embedder.encode(query), dtype=np.float32)

        scored_facts: List[Dict[str, Any]] = []
        for fact in facts_db:
            similarity = 0.0
            if query_vector is not None:
                similarity = _cosine_similarity(query_vector, np.array(embedder.encode(fact.content), dtype=np.float32))
            if similarity == 0.0:
                similarity = _token_similarity(query, fact.content)

            scored_facts.append({
                "id": fact.id,
                "content": fact.content,
                "confidence": round(fact.confidence or 0.0, 4),
                "similarity": round(similarity, 4),
                "source_fragment_id": fact.source_fragment_id,
                "article_title": (
                    fact.source_fragment.article.title
                    if fact.source_fragment and fact.source_fragment.article
                    else "Nieznany artykuł"
                ),
            })

        scored_facts.sort(key=lambda item: (item["similarity"], item["confidence"]), reverse=True)

        filtered_facts = [
            fact
            for fact in scored_facts
            if fact["similarity"] >= self.config.similarity_threshold
            and fact["confidence"] >= self.config.fact_confidence_threshold
        ]

        if not filtered_facts:
            filtered_facts = scored_facts[:effective_limit]
        else:
            filtered_facts = filtered_facts[:effective_limit]

        for index, fact in enumerate(filtered_facts, start=1):
            fact["rank"] = index

        elapsed_time = time.perf_counter() - start_time

        return {
            "query": query,
            "facts": filtered_facts,
            "elapsed_time": round(elapsed_time, 4),
            "total_candidates": len(scored_facts),
            "applied_settings": self.config.to_dict(),
        }

    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        start_time = time.perf_counter()
        facts = context.get("facts", [])

        if not facts:
            response = "Brak zweryfikowanych faktów pasujących do zapytania."
            elapsed = time.perf_counter() - start_time
            return {
                "response": response,
                "elapsed_time": round(elapsed, 4),
                "tokens_used": len(response.split()),
                "model": "no-facts",
                "temperature": self.config.temperature,
            }

        # Spróbuj użyć lokalnego LLM do odpowiedzi syntezującej fakty
        llm = get_llm_service()
        if llm.is_enabled:
            try:
                facts_bullets = [f"- ({f['similarity']:.0%}) {f['content']}" for f in facts[:8]]
                system = (
                    "Jesteś asystentem, który odpowiada, bazując wyłącznie na podanych faktach. "
                    "Nie dodawaj informacji spoza listy. Odpowiedz po polsku i dołącz krótki wykaz źródeł."
                )
                user = (
                    f"Pytanie: {query}\n\nFakty:\n" + "\n".join(facts_bullets) + "\n\nOdpowiedz zwięźle i wiernie faktom."
                )
                result = llm.generate(
                    prompt=user,
                    system=system,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.max_tokens, 600),
                )
                response = result.text or "Brak odpowiedzi."
                elapsed = time.perf_counter() - start_time
                tokens_used = (
                    int(result.usage.get("total_tokens"))
                    if isinstance(result.usage.get("total_tokens"), int)
                    else len(response.split())
                )
                return {
                    "response": response,
                    "elapsed_time": round(elapsed, 4),
                    "tokens_used": tokens_used,
                    "model": result.model,
                    "temperature": self.config.temperature,
                }
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("LLM generation failed (facts): %s", exc)

        # Fallback: wypisz fakty
        lines = [f"- ({fact['similarity']:.0%}) {fact['content']}" for fact in facts]
        response = "Kluczowe fakty:\n" + "\n".join(lines)
        response = response[: self.config.max_response_length]
        elapsed = time.perf_counter() - start_time
        tokens_used = len(response.split())

        return {
            "response": response,
            "elapsed_time": round(elapsed, 4),
            "tokens_used": tokens_used,
            "model": "facts-extractor",
            "temperature": self.config.temperature,
        }

    def get_justification(self, context: Any) -> Dict[str, Any]:
        return {
            "type": "facts",
            "facts": context.get("facts", []),
        }

    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        facts = context.get("facts", [])
        avg_similarity = (
            sum(fact.get("similarity", 0.0) for fact in facts) / len(facts)
            if facts else 0.0
        )
        avg_confidence = (
            sum(fact.get("confidence", 0.0) for fact in facts) / len(facts)
            if facts else 0.0
        )
        token_count = len(response.split())
        hallucination_score = max(0.0, 1.0 - min(avg_similarity, avg_confidence))
        faithfulness = min(1.0, min(avg_similarity, avg_confidence))

        return {
            "search_time": context.get("elapsed_time", 0.0),
            "generation_time": context.get("generation_time", 0.0),
            "total_time": context.get("elapsed_time", 0.0) + context.get("generation_time", 0.0),
            "tokens_used": token_count,
            "average_similarity": round(avg_similarity, 4),
            "average_confidence": round(avg_confidence, 4),
            "context_relevance": round(avg_similarity, 4),
            "hallucination_score": round(hallucination_score, 4),
            "faithfulness": round(faithfulness, 4),
            "cost": round(token_count * 0.000015, 6),
            "applied_settings": self.config.to_dict(),
            "result_count": len(facts),
        }
