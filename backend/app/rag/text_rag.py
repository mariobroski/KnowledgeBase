from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.db.database_models import Article as ArticleModel
from app.db.database_models import Fragment as FragmentModel
from app.rag.base import RAGPolicy
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service

try:  # pragma: no cover - w środowisku bez sentence-transformers użyjemy fallbacku
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


_EMBEDDER_CACHE: Dict[str, "SentenceTransformer"] = {}


def _get_embedder(model_name: str) -> Optional["SentenceTransformer"]:
    if SentenceTransformer is None:
        return None
    if model_name not in _EMBEDDER_CACHE:
        try:
            _EMBEDDER_CACHE[model_name] = SentenceTransformer(model_name)
        except Exception:  # pragma: no cover
            return None
    return _EMBEDDER_CACHE[model_name]


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) or 1e-10
    return float(np.dot(vec_a, vec_b) / denom)


def _token_similarity(query: str, content: str) -> float:
    query_tokens = {token for token in query.lower().split() if len(token) > 2}
    content_tokens = {token for token in content.lower().split() if len(token) > 2}
    if not query_tokens or not content_tokens:
        return 0.0
    return len(query_tokens & content_tokens) / len(query_tokens | content_tokens)


class TextRAG(RAGPolicy):
    """Implementacja polityki TekstRAG uwzględniająca personalizację ustawień."""

    def __init__(self, config=None):
        super().__init__(config=config)

    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()

        effective_limit = limit or self.config.top_k_results

        embedding_service = get_embedding_service()
        fragments_result: List[Dict[str, Any]]
        total_candidates = 0

        if embedding_service.is_enabled:
            try:
                search_hits = embedding_service.search(query, limit=max(effective_limit, self.config.text_rerank_top_n))
                fragment_ids = [hit["fragment_id"] for hit in search_hits]
                if fragment_ids:
                    db_fragments = (
                        db.query(FragmentModel)
                        .options()
                        .filter(FragmentModel.id.in_(fragment_ids))
                        .all()
                    )
                    fragment_map = {fragment.id: fragment for fragment in db_fragments}
                    fragments_result = []
                    for rank, hit in enumerate(search_hits, start=1):
                        fragment = fragment_map.get(hit["fragment_id"])
                        if not fragment:
                            continue
                        fragments_result.append(
                            {
                                "id": fragment.id,
                                "article_id": fragment.article_id,
                                "article_title": fragment.article.title if fragment.article else "Nieznany artykuł",
                                "similarity": round(hit["score"], 4),
                                "position": fragment.position,
                                "content": fragment.content,
                                "rank": rank,
                            }
                        )
                    fragments_result = fragments_result[:effective_limit]
                    total_candidates = len(search_hits)
                else:
                    fragments_result = []
            except Exception as exc:  # pragma: no cover - fallback
                logger = logging.getLogger(__name__)
                logger.warning("Błąd podczas wyszukiwania w Qdrant: %s", exc)
                fragments_result = []
        else:
            fragments_result = []

        if not fragments_result:
            fragments_result = self._fallback_fragment_search(db, query, effective_limit)
            total_candidates = len(fragments_result)

        elapsed_time = time.perf_counter() - start_time

        return {
            "query": query,
            "fragments": fragments_result,
            "elapsed_time": round(elapsed_time, 4),
            "total_candidates": total_candidates,
            "applied_settings": self.config.to_dict(),
        }

    def _fallback_fragment_search(self, db: Session, query: str, limit: int) -> List[Dict[str, Any]]:
        candidate_pool = max(limit, self.config.text_rerank_top_n)
        fragments_db: List[FragmentModel] = (
            db.query(FragmentModel)
            .join(ArticleModel)
            .filter(FragmentModel.indexed.is_(True))
            .limit(candidate_pool)
            .all()
        )

        embedder = _get_embedder(self.config.embedding_model)
        query_vector: Optional[np.ndarray] = None
        if embedder is not None:
            try:
                query_vector = np.array(embedder.encode(query), dtype=np.float32)
            except Exception:
                query_vector = None

        scored_fragments: List[Dict[str, Any]] = []
        for fragment in fragments_db:
            similarity = 0.0
            if query_vector is not None and fragment.embedding:
                try:
                    fragment_vector = np.asarray(fragment.embedding, dtype=np.float32)
                    if fragment_vector.ndim == 1 and fragment_vector.size == query_vector.size:
                        similarity = _cosine_similarity(query_vector, fragment_vector)
                except Exception:
                    similarity = 0.0
            if similarity == 0.0:
                similarity = _token_similarity(query, fragment.content or "")

            scored_fragments.append(
                {
                    "id": fragment.id,
                    "article_id": fragment.article_id,
                    "article_title": fragment.article.title if fragment.article else "Nieznany artykuł",
                    "similarity": round(similarity, 4),
                    "position": fragment.position,
                    "content": fragment.content,
                }
            )

        scored_fragments.sort(key=lambda item: item["similarity"], reverse=True)

        filtered_fragments = [
            fragment for fragment in scored_fragments
            if fragment["similarity"] >= self.config.similarity_threshold
        ]

        if not filtered_fragments:
            filtered_fragments = scored_fragments[:limit]
        else:
            filtered_fragments = filtered_fragments[:limit]

        for index, fragment in enumerate(filtered_fragments, start=1):
            fragment["rank"] = index

        return filtered_fragments

    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        start_time = time.perf_counter()
        fragments = context.get("fragments", [])

        # Jeśli brak kontekstu — szybka odpowiedź informacyjna
        if not fragments:
            response = (
                "Nie znaleziono fragmentów wystarczająco dopasowanych do zapytania. "
                "Spróbuj zmienić progi podobieństwa lub sformułowanie pytania."
            )
            elapsed = time.perf_counter() - start_time
            return {
                "response": response,
                "elapsed_time": round(elapsed, 4),
                "tokens_used": len(response.split()),
                "model": "no-context",
                "temperature": self.config.temperature,
            }

        # Spróbuj użyć lokalnego LLM (Ollama) do odpowiedzi na podstawie kontekstu
        llm = get_llm_service()
        if llm.is_enabled:
            try:
                ctx_items = []
                for fr in fragments[:5]:
                    title = fr.get("article_title") or "Źródło"
                    pos = fr.get("position")
                    snippet = (fr.get("content") or "").strip().replace("\n", " ")
                    snippet = snippet[:400]
                    label = f"{title}, frag {pos}" if pos is not None else title
                    ctx_items.append(f"- [{label}] {snippet}")

                system = (
                    "Jesteś asystentem bazującym na kontekście. Odpowiadaj po polsku, "
                    "opierając się wyłącznie na dostarczonych fragmentach. Jeżeli brak danych, powiedz, że nie wiesz. "
                    "Dodawaj krótkie cytowania źródeł w nawiasach kwadratowych, np. [Tytuł, frag X]."
                )
                user = (
                    f"Pytanie: {query}\n\nKontekst:\n" + "\n".join(ctx_items) + "\n\nZwięźle odpowiedz, podając źródła."
                )
                result = llm.generate(
                    prompt=user,
                    system=system,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.max_tokens, 800),
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
            except Exception as exc:  # fallback do heurystyki
                logger = logging.getLogger(__name__)
                logger.warning("LLM generation failed, fallback to heuristic: %s", exc)

        # Fallback: prosta odpowiedź na bazie fragmentów
        highlighted = [fragment["content"] for fragment in fragments[:3] if fragment.get("content")]
        merged_context = " ".join(highlighted)
        merged_context = merged_context[: self.config.max_response_length]
        response = (
            "Najtrafniejsze fragmenty wskazują, że:\n" f"{merged_context}\n\n"
            "(Odpowiedź zestawiona na podstawie fragmentów o najwyższym podobieństwie.)"
        )
        elapsed = time.perf_counter() - start_time
        tokens_used = len(response.split())
        return {
            "response": response,
            "elapsed_time": round(elapsed, 4),
            "tokens_used": tokens_used,
            "model": self.config.embedding_model if SentenceTransformer else "keyword-matching",
            "temperature": self.config.temperature,
        }

    def get_justification(self, context: Any) -> Dict[str, Any]:
        return {
            "type": "text_fragments",
            "fragments": context.get("fragments", []),
        }

    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        fragments = context.get("fragments", [])
        avg_similarity = (
            sum(fragment.get("similarity", 0.0) for fragment in fragments) / len(fragments)
            if fragments else 0.0
        )
        token_count = len(response.split())
        hallucination_score = max(0.0, 1.0 - avg_similarity)
        faithfulness = min(1.0, avg_similarity)

        return {
            "search_time": context.get("elapsed_time", 0.0),
            "generation_time": context.get("generation_time", 0.0),
            "total_time": context.get("elapsed_time", 0.0) + context.get("generation_time", 0.0),
            "tokens_used": token_count,
            "average_similarity": round(avg_similarity, 4),
            "context_relevance": round(avg_similarity, 4),
            "hallucination_score": round(hallucination_score, 4),
            "faithfulness": round(faithfulness, 4),
            "cost": round(token_count * 0.00002, 6),
            "applied_settings": self.config.to_dict(),
            "result_count": len(fragments),
        }
