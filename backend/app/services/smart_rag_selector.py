"""
Inteligentny selektor RAG z analizą kosztów i wydajności
"""
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class RAGType(Enum):
    TEXT = "text"
    FACTS = "facts" 
    GRAPH = "graph"
    HYBRID = "hybrid"

@dataclass
class RAGCostProfile:
    """Profil kosztów dla danego typu RAG"""
    embedding_cost_per_token: float = 0.0001  # Koszt embeddingów
    llm_cost_per_token: float = 0.002        # Koszt LLM
    vector_search_cost: float = 0.001         # Koszt wyszukiwania wektorowego
    sql_query_cost: float = 0.0005           # Koszt zapytań SQL
    graph_traversal_cost: float = 0.002      # Koszt przechodzenia grafu
    base_overhead: float = 0.01              # Koszt bazowy

@dataclass
class RAGPerformanceProfile:
    """Profil wydajności dla danego typu RAG"""
    avg_latency_ms: float = 1000.0           # Średni czas odpowiedzi
    accuracy_score: float = 0.8              # Średnia dokładność
    context_utilization: float = 0.7         # Wykorzystanie kontekstu
    reliability_score: float = 0.9           # Niezawodność

@dataclass
class QueryAnalysis:
    """Analiza zapytania"""
    complexity: float = 0.5                  # Złożoność (0-1)
    factual_need: float = 0.5                # Potrzeba faktów (0-1)
    relational_need: float = 0.5            # Potrzeba relacji (0-1)
    semantic_need: float = 0.5               # Potrzeba semantyki (0-1)
    expected_tokens: int = 100              # Oczekiwana liczba tokenów
    urgency: float = 0.5                     # Pilność (0-1)

class SmartRAGSelector:
    """Inteligentny selektor RAG z analizą kosztów i wydajności"""
    
    def __init__(self):
        self.cost_profiles = {
            RAGType.TEXT: RAGCostProfile(
                embedding_cost_per_token=0.0001,
                llm_cost_per_token=0.002,
                vector_search_cost=0.001,
                base_overhead=0.01
            ),
            RAGType.FACTS: RAGCostProfile(
                llm_cost_per_token=0.002,
                sql_query_cost=0.0005,
                base_overhead=0.005
            ),
            RAGType.GRAPH: RAGCostProfile(
                llm_cost_per_token=0.002,
                graph_traversal_cost=0.002,
                base_overhead=0.015
            ),
            RAGType.HYBRID: RAGCostProfile(
                embedding_cost_per_token=0.0001,
                llm_cost_per_token=0.002,
                vector_search_cost=0.001,
                sql_query_cost=0.0005,
                graph_traversal_cost=0.002,
                base_overhead=0.02
            )
        }
        
        self.performance_profiles = {
            RAGType.TEXT: RAGPerformanceProfile(
                avg_latency_ms=800.0,
                accuracy_score=0.75,
                context_utilization=0.8,
                reliability_score=0.95
            ),
            RAGType.FACTS: RAGPerformanceProfile(
                avg_latency_ms=500.0,
                accuracy_score=0.9,
                context_utilization=0.6,
                reliability_score=0.98
            ),
            RAGType.GRAPH: RAGPerformanceProfile(
                avg_latency_ms=2000.0,
                accuracy_score=0.85,
                context_utilization=0.7,
                reliability_score=0.85
            ),
            RAGType.HYBRID: RAGPerformanceProfile(
                avg_latency_ms=1500.0,
                accuracy_score=0.88,
                context_utilization=0.85,
                reliability_score=0.9
            )
        }
        
        # Wagi dla różnych czynników
        self.weights = {
            'cost': 0.3,           # 30% wagi na koszt
            'performance': 0.4,     # 40% wagi na wydajność
            'quality': 0.3         # 30% wagi na jakość
        }
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analizuje zapytanie i określa jego charakterystyki"""
        query_lower = query.lower()
        
        # Analiza złożoności na podstawie długości i słów kluczowych
        complexity_indicators = ['porównaj', 'analizuj', 'wyjaśnij', 'dlaczego', 'jak', 'co jeśli']
        complexity = min(1.0, len(query.split()) / 20.0 + sum(1 for word in complexity_indicators if word in query_lower) * 0.2)
        
        # Analiza potrzeby faktów
        factual_indicators = ['ile', 'kiedy', 'gdzie', 'kto', 'co', 'który', 'prawda', 'fakt']
        factual_need = min(1.0, sum(1 for word in factual_indicators if word in query_lower) * 0.3)
        
        # Analiza potrzeby relacji
        relational_indicators = ['związek', 'relacja', 'powiązanie', 'wpływ', 'zależność', 'korelacja']
        relational_need = min(1.0, sum(1 for word in relational_indicators if word in query_lower) * 0.4)
        
        # Analiza potrzeby semantyki
        semantic_indicators = ['znaczenie', 'definicja', 'opis', 'charakterystyka', 'cechy']
        semantic_need = min(1.0, sum(1 for word in semantic_indicators if word in query_lower) * 0.3)
        
        # Oszacowanie liczby tokenów
        expected_tokens = max(50, len(query.split()) * 3)
        
        # Analiza pilności
        urgency_indicators = ['pilne', 'szybko', 'natychmiast', 'asap']
        urgency = min(1.0, sum(1 for word in urgency_indicators if word in query_lower) * 0.5)
        
        return QueryAnalysis(
            complexity=complexity,
            factual_need=factual_need,
            relational_need=relational_need,
            semantic_need=semantic_need,
            expected_tokens=expected_tokens,
            urgency=urgency
        )
    
    def calculate_cost(self, rag_type: RAGType, query_analysis: QueryAnalysis) -> float:
        """Oblicza przewidywany koszt dla danego typu RAG"""
        profile = self.cost_profiles[rag_type]
        
        # Koszt embeddingów (jeśli potrzebne)
        embedding_cost = profile.embedding_cost_per_token * query_analysis.expected_tokens
        
        # Koszt wyszukiwania
        search_cost = 0.0
        if rag_type in [RAGType.TEXT, RAGType.HYBRID]:
            search_cost += profile.vector_search_cost
        if rag_type in [RAGType.FACTS, RAGType.HYBRID]:
            search_cost += profile.sql_query_cost
        if rag_type in [RAGType.GRAPH, RAGType.HYBRID]:
            search_cost += profile.graph_traversal_cost
        
        # Koszt LLM (zależny od złożoności)
        llm_cost = profile.llm_cost_per_token * query_analysis.expected_tokens * (1 + query_analysis.complexity)
        
        total_cost = embedding_cost + search_cost + llm_cost + profile.base_overhead
        
        return total_cost
    
    def calculate_performance_score(self, rag_type: RAGType, query_analysis: QueryAnalysis) -> float:
        """Oblicza score wydajności dla danego typu RAG"""
        profile = self.performance_profiles[rag_type]
        
        # Score bazowy
        base_score = (
            profile.accuracy_score * 0.4 +
            profile.context_utilization * 0.3 +
            profile.reliability_score * 0.3
        )
        
        # Modyfikatory na podstawie analizy zapytania
        modifiers = 1.0
        
        # Jeśli zapytanie wymaga faktów, preferuj FactRAG
        if rag_type == RAGType.FACTS and query_analysis.factual_need > 0.7:
            modifiers += 0.2
        
        # Jeśli zapytanie wymaga relacji, preferuj GraphRAG
        if rag_type == RAGType.GRAPH and query_analysis.relational_need > 0.7:
            modifiers += 0.2
        
        # Jeśli zapytanie wymaga semantyki, preferuj TextRAG
        if rag_type == RAGType.TEXT and query_analysis.semantic_need > 0.7:
            modifiers += 0.2
        
        # Jeśli zapytanie jest pilne, preferuj szybsze opcje
        if query_analysis.urgency > 0.7:
            if profile.avg_latency_ms < 1000:
                modifiers += 0.1
            else:
                modifiers -= 0.1
        
        return min(1.0, base_score * modifiers)
    
    def select_optimal_rag(self, query: str, budget_limit: Optional[float] = None) -> Tuple[RAGType, Dict[str, Any]]:
        """Wybiera optymalny typ RAG na podstawie analizy zapytania i ograniczeń"""
        query_analysis = self.analyze_query(query)
        
        # Oblicz score dla każdego typu RAG
        scores = {}
        costs = {}
        
        for rag_type in RAGType:
            cost = self.calculate_cost(rag_type, query_analysis)
            performance = self.calculate_performance_score(rag_type, query_analysis)
            
            # Sprawdź ograniczenia budżetowe
            if budget_limit and cost > budget_limit:
                continue
            
            # Znormalizuj koszt (niższy koszt = wyższy score)
            cost_score = 1.0 / (1.0 + cost)
            
            # Oblicz końcowy score
            final_score = (
                cost_score * self.weights['cost'] +
                performance * self.weights['performance'] +
                performance * self.weights['quality']  # Jakość = wydajność
            )
            
            scores[rag_type] = final_score
            costs[rag_type] = cost
        
        if not scores:
            # Jeśli wszystkie opcje przekraczają budżet, wybierz najtańszą
            best_rag = min(costs.keys(), key=lambda x: costs[x])
            logger.warning(f"Wszystkie opcje przekraczają budżet. Wybrano najtańszą: {best_rag.value}")
        else:
            # Wybierz opcję z najwyższym score
            best_rag = max(scores.keys(), key=lambda x: scores[x])
        
        # Przygotuj szczegóły decyzji
        decision_details = {
            'selected_rag': best_rag.value,
            'query_analysis': {
                'complexity': query_analysis.complexity,
                'factual_need': query_analysis.factual_need,
                'relational_need': query_analysis.relational_need,
                'semantic_need': query_analysis.semantic_need,
                'expected_tokens': query_analysis.expected_tokens,
                'urgency': query_analysis.urgency
            },
            'cost_analysis': {
                'selected_cost': costs.get(best_rag, 0.0),
                'budget_limit': budget_limit,
                'all_costs': {rag.value: cost for rag, cost in costs.items()}
            },
            'performance_analysis': {
                'selected_score': scores.get(best_rag, 0.0),
                'all_scores': {rag.value: score for rag, score in scores.items()}
            },
            'reasoning': self._generate_reasoning(best_rag, query_analysis, costs, scores)
        }
        
        return best_rag, decision_details
    
    def _generate_reasoning(self, selected_rag: RAGType, query_analysis: QueryAnalysis, 
                          costs: Dict[RAGType, float], scores: Dict[RAGType, float]) -> str:
        """Generuje wyjaśnienie decyzji"""
        reasons = []
        
        if selected_rag == RAGType.TEXT:
            reasons.append("Wybrano TextRAG dla wyszukiwania semantycznego")
        elif selected_rag == RAGType.FACTS:
            reasons.append("Wybrano FactRAG dla zapytań faktograficznych")
        elif selected_rag == RAGType.GRAPH:
            reasons.append("Wybrano GraphRAG dla analizy relacji")
        elif selected_rag == RAGType.HYBRID:
            reasons.append("Wybrano HybridRAG dla kompleksowej analizy")
        
        if query_analysis.factual_need > 0.7:
            reasons.append(f"Zapytanie wymaga faktów (score: {query_analysis.factual_need:.2f})")
        if query_analysis.relational_need > 0.7:
            reasons.append(f"Zapytanie wymaga analizy relacji (score: {query_analysis.relational_need:.2f})")
        if query_analysis.urgency > 0.7:
            reasons.append(f"Zapytanie jest pilne (score: {query_analysis.urgency:.2f})")
        
        cost = costs.get(selected_rag, 0.0)
        reasons.append(f"Przewidywany koszt: {cost:.4f}")
        
        return "; ".join(reasons)
    
    def get_rag_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """Zwraca rekomendacje wszystkich typów RAG z analizą"""
        query_analysis = self.analyze_query(query)
        recommendations = []
        
        for rag_type in RAGType:
            cost = self.calculate_cost(rag_type, query_analysis)
            performance = self.calculate_performance_score(rag_type, query_analysis)
            
            recommendations.append({
                'rag_type': rag_type.value,
                'cost': cost,
                'performance_score': performance,
                'latency_ms': self.performance_profiles[rag_type].avg_latency_ms,
                'accuracy': self.performance_profiles[rag_type].accuracy_score,
                'suitable_for': self._get_suitability_description(rag_type, query_analysis)
            })
        
        return sorted(recommendations, key=lambda x: x['performance'], reverse=True)
    
    def _get_suitability_description(self, rag_type: RAGType, query_analysis: QueryAnalysis) -> str:
        """Zwraca opis przydatności danego RAG dla zapytania"""
        if rag_type == RAGType.TEXT:
            return "Idealny dla zapytań semantycznych i opisowych"
        elif rag_type == RAGType.FACTS:
            return "Najlepszy dla zapytań faktograficznych i konkretnych danych"
        elif rag_type == RAGType.GRAPH:
            return "Skuteczny dla analizy relacji i złożonych zależności"
        elif rag_type == RAGType.HYBRID:
            return "Kompleksowa analiza łącząca wszystkie podejścia"
    
    def update_performance_metrics(self, rag_type: RAGType, actual_latency: float, 
                                 actual_cost: float, quality_score: float):
        """Aktualizuje metryki wydajności na podstawie rzeczywistych wyników"""
        # Implementacja uczenia się z rzeczywistych danych
        profile = self.performance_profiles[rag_type]
        
        # Eksponencjalne wygładzanie
        alpha = 0.1
        profile.avg_latency_ms = (1 - alpha) * profile.avg_latency_ms + alpha * actual_latency
        profile.accuracy_score = (1 - alpha) * profile.accuracy_score + alpha * quality_score
        
        logger.info(f"Zaktualizowano metryki dla {rag_type.value}: latency={profile.avg_latency_ms:.1f}ms, accuracy={profile.accuracy_score:.3f}")
