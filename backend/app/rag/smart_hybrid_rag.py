"""
SmartHybridRAG - Inteligentny HybridRAG z selektorem kosztów i wydajności
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.rag.base import RAGPolicy
from app.rag.settings import RAGSettings
from app.rag.text_rag import TextRAG
from app.rag.fact_rag import FactRAG
from app.rag.graph_rag import GraphRAG
from app.rag.hybrid_rag import HybridRAG
from app.services.llm_service import get_llm_service
from app.services.smart_rag_selector import SmartRAGSelector, RAGType
import logging

logger = logging.getLogger(__name__)

class SmartHybridRAG(RAGPolicy):
    """Inteligentny HybridRAG z selektorem kosztów i wydajności.
    
    Automatycznie wybiera optymalny typ RAG na podstawie:
    - Analizy zapytania
    - Ograniczeń kosztowych
    - Profili wydajności
    - Metryk jakości
    """

    def __init__(self, config: Optional[RAGSettings] = None) -> None:
        super().__init__(config=config)
        self._text = TextRAG(config=self.config)
        self._facts = FactRAG(config=self.config)
        self._graph = GraphRAG(config=self.config)
        self._hybrid = HybridRAG(config=self.config)
        self._selector = SmartRAGSelector()
        
        # Ustawienia inteligentnego wyboru
        self.auto_select = True
        self.budget_limit = None  # None = brak ograniczeń
        self.quality_threshold = 0.7  # Minimalna jakość wymagana
        self.fallback_to_hybrid = True  # Fallback do HybridRAG jeśli inne zawiodą

    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        """Wyszukiwanie z inteligentnym wyborem strategii RAG"""
        k = limit or self.config.top_k_results
        
        # Analiza zapytania i wybór optymalnej strategii
        if self.auto_select:
            selected_rag, decision_details = self._selector.select_optimal_rag(
                query, budget_limit=self.budget_limit
            )
            logger.info(f"Wybrano {selected_rag.value} dla zapytania: {query[:50]}...")
        else:
            # Użyj HybridRAG jako domyślnego
            selected_rag = RAGType.HYBRID
            decision_details = {"selected_rag": "hybrid", "reasoning": "Manual selection"}
        
        # Wykonaj wyszukiwanie wybraną strategią
        start_time = time.time()
        try:
            if selected_rag == RAGType.TEXT:
                context = self._text.search(query, db, limit=k)
                context["selected_strategy"] = "text"
            elif selected_rag == RAGType.FACTS:
                context = self._facts.search(query, db, limit=k)
                context["selected_strategy"] = "facts"
            elif selected_rag == RAGType.GRAPH:
                context = self._graph.search(query, db, limit=k)
                context["selected_strategy"] = "graph"
            else:  # HYBRID
                context = self._hybrid.search(query, db, limit=k)
                context["selected_strategy"] = "hybrid"
            
            search_time = time.time() - start_time
            context["search_time"] = search_time
            context["decision_details"] = decision_details
            
            # Sprawdź jakość wyników
            quality_score = self._assess_result_quality(context, query)
            context["quality_score"] = quality_score
            
            # Jeśli jakość jest niska i mamy fallback, spróbuj HybridRAG
            if (quality_score < self.quality_threshold and 
                selected_rag != RAGType.HYBRID and 
                self.fallback_to_hybrid):
                
                logger.warning(f"Jakość wyników niska ({quality_score:.3f}), próba fallback do HybridRAG")
                fallback_context = self._hybrid.search(query, db, limit=k)
                fallback_quality = self._assess_result_quality(fallback_context, query)
                
                if fallback_quality > quality_score:
                    logger.info(f"Fallback do HybridRAG poprawił jakość: {fallback_quality:.3f}")
                    fallback_context["selected_strategy"] = "hybrid_fallback"
                    fallback_context["search_time"] = time.time() - start_time
                    fallback_context["decision_details"] = decision_details
                    fallback_context["quality_score"] = fallback_quality
                    return fallback_context
                else:
                    logger.info("Fallback nie poprawił jakości, używamy oryginalnych wyników")
            
            return context
            
        except Exception as e:
            logger.error(f"Błąd w wyszukiwaniu {selected_rag.value}: {e}")
            
            # Fallback do HybridRAG w przypadku błędu
            if selected_rag != RAGType.HYBRID and self.fallback_to_hybrid:
                logger.info("Próba fallback do HybridRAG po błędzie")
                try:
                    fallback_context = self._hybrid.search(query, db, limit=k)
                    fallback_context["selected_strategy"] = "hybrid_error_fallback"
                    fallback_context["search_time"] = time.time() - start_time
                    fallback_context["decision_details"] = decision_details
                    fallback_context["error"] = str(e)
                    return fallback_context
                except Exception as fallback_error:
                    logger.error(f"Fallback również zawiódł: {fallback_error}")
            
            # Zwróć pusty kontekst w przypadku całkowitego błędu
            return {
                "query": query,
                "selected_strategy": "error",
                "search_time": time.time() - start_time,
                "error": str(e),
                "quality_score": 0.0
            }

    def _assess_result_quality(self, context: Dict[str, Any], query: str) -> float:
        """Ocenia jakość wyników wyszukiwania"""
        quality_factors = []
        
        # Sprawdź liczbę wyników
        total_results = 0
        if "fragments" in context:
            total_results += len(context["fragments"])
        if "facts" in context:
            total_results += len(context["facts"])
        if "paths" in context:
            total_results += len(context["paths"])
        if "fused" in context:
            total_results += len(context["fused"])
        
        # Jakość na podstawie liczby wyników
        if total_results == 0:
            quality_factors.append(0.0)
        elif total_results >= 5:
            quality_factors.append(1.0)
        else:
            quality_factors.append(total_results / 5.0)
        
        # Jakość na podstawie podobieństwa/confidence
        similarity_scores = []
        if "fragments" in context:
            for frag in context["fragments"]:
                if "similarity" in frag:
                    similarity_scores.append(frag["similarity"])
        if "facts" in context:
            for fact in context["facts"]:
                if "similarity" in fact:
                    similarity_scores.append(fact["similarity"])
                if "confidence" in fact:
                    similarity_scores.append(fact["confidence"])
        
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            quality_factors.append(avg_similarity)
        else:
            quality_factors.append(0.5)  # Neutralna jakość
        
        # Jakość na podstawie długości kontekstu
        context_length = 0
        if "fragments" in context:
            for frag in context["fragments"]:
                if "content" in frag:
                    context_length += len(frag["content"])
        if "facts" in context:
            for fact in context["facts"]:
                if "content" in fact:
                    context_length += len(fact["content"])
        
        if context_length > 0:
            # Im więcej kontekstu, tym lepiej (do pewnego limitu)
            context_quality = min(1.0, context_length / 2000.0)
            quality_factors.append(context_quality)
        else:
            quality_factors.append(0.0)
        
        # Średnia ważona wszystkich czynników
        return sum(quality_factors) / len(quality_factors)

    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        """Generuje odpowiedź z kontekstem wybranej strategii"""
        llm = get_llm_service()
        
        # Sprawdź czy mamy kontekst
        has_context = False
        context_items = []
        
        if "fragments" in context and context["fragments"]:
            has_context = True
            for frag in context["fragments"][:3]:  # Top 3 fragmenty
                title = frag.get("article_title", "Źródło")
                content = frag.get("content", "")[:200]
                context_items.append(f"[TEKST] {title}: {content}")
        
        if "facts" in context and context["facts"]:
            has_context = True
            for fact in context["facts"][:3]:  # Top 3 fakty
                content = fact.get("content", "")[:200]
                confidence = fact.get("confidence", 0.0)
                context_items.append(f"[FAKT] ({confidence:.0%}): {content}")
        
        if "paths" in context and context["paths"]:
            has_context = True
            for path in context["paths"][:2]:  # Top 2 ścieżki
                nodes = [n.get("name", "") for n in path.get("nodes", [])]
                context_items.append(f"[GRAF] {' -> '.join(nodes)}")
        
        if "fused" in context and context["fused"]:
            has_context = True
            for item in context["fused"][:5]:  # Top 5 połączonych wyników
                item_type = item.get("type", "unknown")
                payload = item.get("payload", {})
                if item_type == "text":
                    title = payload.get("article_title", "Źródło")
                    content = payload.get("content", "")[:150]
                    context_items.append(f"[TEKST] {title}: {content}")
                elif item_type == "fact":
                    content = payload.get("content", "")[:150]
                    confidence = payload.get("confidence", 0.0)
                    context_items.append(f"[FAKT] ({confidence:.0%}): {content}")
                elif item_type == "graph":
                    nodes = [n.get("name", "") for n in payload.get("nodes", [])]
                    context_items.append(f"[GRAF] {' -> '.join(nodes)}")
        
        if not has_context:
            return {
                "response": "Brak kontekstu do odpowiedzi. Spróbuj sformułować zapytanie inaczej.",
                "elapsed_time": 0.0,
                "tokens_used": 0,
                "model": "no-context",
                "temperature": self.config.temperature,
                "selected_strategy": context.get("selected_strategy", "unknown"),
                "quality_score": context.get("quality_score", 0.0)
            }
        
        # Buduj prompt z kontekstem
        system_prompt = (
            "Odpowiadaj wyłącznie na podstawie dostarczonego kontekstu. "
            "Dodawaj krótkie cytowania lub wskazania źródeł. "
            "Jeśli kontekst nie zawiera odpowiedzi, powiedz to jasno."
        )
        
        context_text = "\n".join(context_items)
        user_prompt = f"Pytanie: {query}\n\nKontekst:\n{context_text}\n\nZwięźle odpowiedz na podstawie kontekstu."
        
        # Generuj odpowiedź
        if llm.is_enabled:
            try:
                result = llm.generate(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=self.config.temperature,
                    max_tokens=min(self.config.max_tokens, 800),
                )
                
                response_text = result.text or "Brak odpowiedzi."
                tokens_used = (
                    int(result.usage.get("total_tokens", 0))
                    if isinstance(result.usage.get("total_tokens"), int)
                    else len(response_text.split())
                )
                
                return {
                    "response": response_text,
                    "elapsed_time": 0.0,
                    "tokens_used": tokens_used,
                    "model": result.model,
                    "temperature": self.config.temperature,
                    "selected_strategy": context.get("selected_strategy", "unknown"),
                    "quality_score": context.get("quality_score", 0.0),
                    "context_items_count": len(context_items)
                }
            except Exception as e:
                logger.error(f"Błąd generowania odpowiedzi: {e}")
                # Fallback do prostego formatowania
                fallback_response = f"Na podstawie dostępnego kontekstu:\n\n{context_text[:500]}..."
                return {
                    "response": fallback_response,
                    "elapsed_time": 0.0,
                    "tokens_used": len(fallback_response.split()),
                    "model": "fallback",
                    "temperature": self.config.temperature,
                    "selected_strategy": context.get("selected_strategy", "unknown"),
                    "quality_score": context.get("quality_score", 0.0),
                    "error": str(e)
                }
        else:
            # Fallback bez LLM
            fallback_response = f"Kontekst znaleziony:\n\n{context_text[:500]}..."
            return {
                "response": fallback_response,
                "elapsed_time": 0.0,
                "tokens_used": len(fallback_response.split()),
                "model": "no-llm",
                "temperature": self.config.temperature,
                "selected_strategy": context.get("selected_strategy", "unknown"),
                "quality_score": context.get("quality_score", 0.0)
            }

    def get_justification(self, context: Any) -> Dict[str, Any]:
        """Zwraca uzasadnienie wyboru strategii"""
        return {
            "type": "smart_hybrid",
            "selected_strategy": context.get("selected_strategy", "unknown"),
            "decision_details": context.get("decision_details", {}),
            "quality_score": context.get("quality_score", 0.0),
            "search_time": context.get("search_time", 0.0),
            "items": context.get("fused", []) or context.get("fragments", []) or context.get("facts", [])
        }

    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        """Zwraca metryki wydajności"""
        quality_score = context.get("quality_score", 0.0)
        search_time = context.get("search_time", 0.0)
        selected_strategy = context.get("selected_strategy", "unknown")
        
        # Oblicz metryki na podstawie wybranej strategii
        if selected_strategy == "text":
            base_metrics = self._text.get_metrics(query, response, context)
        elif selected_strategy == "facts":
            base_metrics = self._facts.get_metrics(query, response, context)
        elif selected_strategy == "graph":
            base_metrics = self._graph.get_metrics(query, response, context)
        else:  # hybrid lub fallback
            base_metrics = self._hybrid.get_metrics(query, response, context)
        
        # Dodaj metryki specyficzne dla SmartHybridRAG
        base_metrics.update({
            "smart_selection": True,
            "selected_strategy": selected_strategy,
            "quality_score": quality_score,
            "search_time_ms": search_time * 1000,
            "decision_confidence": context.get("decision_details", {}).get("performance_analysis", {}).get("selected_score", 0.0),
            "cost_estimate": context.get("decision_details", {}).get("cost_analysis", {}).get("selected_cost", 0.0),
            "applied_settings": self.config.to_dict()
        })
        
        return base_metrics

    def set_budget_limit(self, limit: float) -> None:
        """Ustawia limit budżetowy dla wyboru strategii"""
        self.budget_limit = limit
        logger.info(f"Ustawiono limit budżetowy: {limit}")

    def set_quality_threshold(self, threshold: float) -> None:
        """Ustawia próg jakości dla fallback"""
        self.quality_threshold = threshold
        logger.info(f"Ustawiono próg jakości: {threshold}")

    def enable_auto_selection(self, enabled: bool = True) -> None:
        """Włącza/wyłącza automatyczny wybór strategii"""
        self.auto_select = enabled
        logger.info(f"Automatyczny wybór strategii: {'włączony' if enabled else 'wyłączony'}")

    def get_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """Zwraca rekomendacje wszystkich strategii RAG"""
        return self._selector.get_rag_recommendations(query)
