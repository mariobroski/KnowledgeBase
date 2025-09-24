"""
RAGBench Service - integracja z benchmarkiem RAGBench
Obsługuje import korpusów, testowanie strategii RAG oraz obliczanie metryk TRACe
"""

import logging
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from app.db.database import get_db
from app.services.article_service import ArticleService
from app.services.search_service import SearchService
from app.services.trace_service import TRACEService
from app.rag.factory import RAGPolicyFactory

logger = logging.getLogger(__name__)


@dataclass
class RAGBenchQuery:
    """Reprezentuje zapytanie z RAGBench"""
    query_id: str
    query: str
    domain: str
    ground_truth: List[str]
    context: List[str]
    expected_answer: str
    metadata: Dict[str, Any]


@dataclass
class RAGBenchResult:
    """Reprezentuje wynik testu RAGBench"""
    query_id: str
    strategy: str
    response: str
    context_used: List[str]
    metrics: Dict[str, float]
    latency: float
    tokens: int
    cost: float
    timestamp: datetime


class RAGBenchService:
    """Serwis do integracji z benchmarkiem RAGBench"""
    
    def __init__(self):
        self.trace_service = TRACEService()
        self.policy_factory = RAGPolicyFactory()
        self.supported_domains = ["FinQA", "TAT-QA", "TechQA", "CUAD", "EManual"]
        self.ragbench_base_url = "https://ragbench.github.io/data"
    
    def import_corpus(self, domain: str) -> Dict[str, Any]:
        """
        Importuje korpus z RAGBench do systemu
        
        Args:
            domain: Nazwa domeny (FinQA, TAT-QA, TechQA, CUAD, EManual)
            
        Returns:
            Statystyki importu
        """
        if domain not in self.supported_domains:
            raise ValueError(f"Nieobsługiwana domena: {domain}")
        
        logger.info(f"Rozpoczynanie importu korpusu {domain}")
        
        try:
            # Pobierz dane z RAGBench
            corpus_data = self._fetch_ragbench_corpus(domain)
            
            # Importuj dokumenty
            imported_docs = self._import_documents(corpus_data["documents"])
            
            # Importuj zapytania
            imported_queries = self._import_queries(corpus_data["queries"])
            
            # Indeksuj dokumenty
            indexing_stats = self._index_documents(imported_docs)
            
            stats = {
                "domain": domain,
                "documents_imported": len(imported_docs),
                "queries_imported": len(imported_queries),
                "fragments_created": indexing_stats["fragments"],
                "facts_extracted": indexing_stats["facts"],
                "entities_created": indexing_stats["entities"],
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Import korpusu {domain} zakończony: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Błąd importu korpusu {domain}: {e}")
            return {
                "domain": domain,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _fetch_ragbench_corpus(self, domain: str) -> Dict[str, Any]:
        """Pobiera dane korpusu z RAGBench"""
        # Symulacja pobierania danych (w rzeczywistości z API RAGBench)
        # Tutaj można zaimplementować rzeczywiste pobieranie danych
        
        if domain == "FinQA":
            return self._get_finqa_sample()
        elif domain == "TAT-QA":
            return self._get_tatqa_sample()
        elif domain == "TechQA":
            return self._get_techqa_sample()
        elif domain == "CUAD":
            return self._get_cuad_sample()
        elif domain == "EManual":
            return self._get_emanual_sample()
        else:
            raise ValueError(f"Nieznana domena: {domain}")
    
    def _get_finqa_sample(self) -> Dict[str, Any]:
        """Przykładowe dane FinQA"""
        return {
            "documents": [
                {
                    "id": "finqa_1",
                    "title": "Company Financial Report 2023",
                    "content": "Company XYZ reported revenue of $1.2M in Q3 2023, representing a 15% increase from Q2. Net profit was $200K, up 25% from previous quarter.",
                    "domain": "FinQA",
                    "metadata": {"year": 2023, "quarter": "Q3"}
                },
                {
                    "id": "finqa_2", 
                    "title": "Market Analysis Q3 2023",
                    "content": "The market showed strong growth in Q3 2023 with average stock prices increasing by 12%. Technology sector led the gains with 18% growth.",
                    "domain": "FinQA",
                    "metadata": {"year": 2023, "quarter": "Q3"}
                }
            ],
            "queries": [
                {
                    "query_id": "finqa_q1",
                    "query": "What was Company XYZ's revenue in Q3 2023?",
                    "ground_truth": ["Company XYZ reported revenue of $1.2M in Q3 2023"],
                    "expected_answer": "$1.2M",
                    "domain": "FinQA"
                },
                {
                    "query_id": "finqa_q2",
                    "query": "What was the net profit for Company XYZ?",
                    "ground_truth": ["Net profit was $200K"],
                    "expected_answer": "$200K",
                    "domain": "FinQA"
                }
            ]
        }
    
    def _get_tatqa_sample(self) -> Dict[str, Any]:
        """Przykładowe dane TAT-QA"""
        return {
            "documents": [
                {
                    "id": "tatqa_1",
                    "title": "Financial Statements Analysis",
                    "content": "The company's total assets increased from $500M to $600M in 2023. Current ratio improved from 1.5 to 2.0, indicating better liquidity position.",
                    "domain": "TAT-QA",
                    "metadata": {"year": 2023}
                }
            ],
            "queries": [
                {
                    "query_id": "tatqa_q1",
                    "query": "What was the current ratio in 2023?",
                    "ground_truth": ["Current ratio improved from 1.5 to 2.0"],
                    "expected_answer": "2.0",
                    "domain": "TAT-QA"
                }
            ]
        }
    
    def _get_techqa_sample(self) -> Dict[str, Any]:
        """Przykładowe dane TechQA"""
        return {
            "documents": [
                {
                    "id": "techqa_1",
                    "title": "Software Architecture Guide",
                    "content": "Microservices architecture provides better scalability and maintainability. Each service should be independently deployable and loosely coupled.",
                    "domain": "TechQA",
                    "metadata": {"topic": "architecture"}
                }
            ],
            "queries": [
                {
                    "query_id": "techqa_q1",
                    "query": "What are the benefits of microservices architecture?",
                    "ground_truth": ["Microservices architecture provides better scalability and maintainability"],
                    "expected_answer": "Better scalability and maintainability",
                    "domain": "TechQA"
                }
            ]
        }
    
    def _get_cuad_sample(self) -> Dict[str, Any]:
        """Przykładowe dane CUAD"""
        return {
            "documents": [
                {
                    "id": "cuad_1",
                    "title": "Contract Law Principles",
                    "content": "A valid contract requires offer, acceptance, and consideration. The parties must have legal capacity and the subject matter must be legal.",
                    "domain": "CUAD",
                    "metadata": {"area": "contract_law"}
                }
            ],
            "queries": [
                {
                    "query_id": "cuad_q1",
                    "query": "What are the requirements for a valid contract?",
                    "ground_truth": ["A valid contract requires offer, acceptance, and consideration"],
                    "expected_answer": "Offer, acceptance, and consideration",
                    "domain": "CUAD"
                }
            ]
        }
    
    def _get_emanual_sample(self) -> Dict[str, Any]:
        """Przykładowe dane EManual"""
        return {
            "documents": [
                {
                    "id": "emanual_1",
                    "title": "Equipment Maintenance Manual",
                    "content": "Regular maintenance should be performed every 6 months. Check oil levels, replace filters, and inspect electrical connections.",
                    "domain": "EManual",
                    "metadata": {"equipment_type": "general"}
                }
            ],
            "queries": [
                {
                    "query_id": "emanual_q1",
                    "query": "How often should maintenance be performed?",
                    "ground_truth": ["Regular maintenance should be performed every 6 months"],
                    "expected_answer": "Every 6 months",
                    "domain": "EManual"
                }
            ]
        }
    
    def _import_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Importuje dokumenty do systemu"""
        db = next(get_db())
        article_service = ArticleService(db)
        
        imported_docs = []
        
        for doc in documents:
            try:
                article = article_service.create_article(
                    title=doc["title"],
                    content=doc["content"],
                    summary=f"RAGBench document from {doc['domain']}",
                    tags=[doc["domain"]],
                    created_by_id=1  # System user
                )
                
                # Przetwórz artykuł
                processing_result = article_service.process_article(article.id)
                
                imported_docs.append({
                    "id": article.id,
                    "ragbench_id": doc["id"],
                    "title": article.title,
                    "status": processing_result["status"],
                    "fragments": processing_result.get("fragments_created", 0),
                    "facts": processing_result.get("facts_created", 0)
                })
                
            except Exception as e:
                logger.error(f"Błąd importu dokumentu {doc['id']}: {e}")
                continue
        
        return imported_docs
    
    def _import_queries(self, queries: List[Dict[str, Any]]) -> List[RAGBenchQuery]:
        """Importuje zapytania z RAGBench"""
        imported_queries = []
        
        for query_data in queries:
            query = RAGBenchQuery(
                query_id=query_data["query_id"],
                query=query_data["query"],
                domain=query_data["domain"],
                ground_truth=query_data["ground_truth"],
                context=[],  # Będzie wypełnione podczas testowania
                expected_answer=query_data["expected_answer"],
                metadata=query_data.get("metadata", {})
            )
            imported_queries.append(query)
        
        return imported_queries
    
    def _index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Indeksuje zaimportowane dokumenty"""
        # Statystyki indeksacji są już dostępne z process_article
        total_fragments = sum(doc.get("fragments", 0) for doc in documents)
        total_facts = sum(doc.get("facts", 0) for doc in documents)
        
        return {
            "fragments": total_fragments,
            "facts": total_facts,
            "entities": 0  # Będzie obliczone przez GraphUpdateService
        }
    
    def evaluate_strategy(self, domain: str, strategy: str, queries: List[RAGBenchQuery]) -> List[RAGBenchResult]:
        """
        Ewaluuje strategię RAG na zapytaniach z RAGBench
        
        Args:
            domain: Nazwa domeny
            strategy: Strategia RAG (text, facts, graph)
            queries: Lista zapytań do testowania
            
        Returns:
            Lista wyników testów
        """
        logger.info(f"Rozpoczynanie ewaluacji strategii {strategy} dla domeny {domain}")
        
        db = next(get_db())
        search_service = SearchService(db)
        results = []
        
        for query in queries:
            try:
                start_time = datetime.now()
                
                # Wykonaj wyszukiwanie
                search_result = search_service.search(
                    query=query.query,
                    policy_type=strategy,
                    params={"limit": 5}
                )
                
                end_time = datetime.now()
                latency = (end_time - start_time).total_seconds() * 1000  # ms
                
                # Oblicz metryki TRACe
                trace_metrics = self.trace_service.calculate_metrics(
                    query=query.query,
                    response=search_result["response"],
                    context=search_result.get("context", {}),
                    ground_truth=query.ground_truth
                )
                
                # Oblicz tokeny i koszt
                tokens = search_result.get("tokens_used", 0)
                cost = self._calculate_cost(tokens, strategy)
                
                result = RAGBenchResult(
                    query_id=query.query_id,
                    strategy=strategy,
                    response=search_result["response"],
                    context_used=search_result.get("context", {}).get("fragments", []),
                    metrics=trace_metrics,
                    latency=latency,
                    tokens=tokens,
                    cost=cost,
                    timestamp=end_time
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Błąd ewaluacji zapytania {query.query_id}: {e}")
                continue
        
        logger.info(f"Ewaluacja strategii {strategy} zakończona: {len(results)} wyników")
        return results
    
    def _calculate_cost(self, tokens: int, strategy: str) -> float:
        """Oblicza koszt na podstawie tokenów i strategii"""
        # Koszty per token (przykładowe)
        cost_per_token = {
            "text": 0.00002,  # $0.02 per 1K tokens
            "facts": 0.000015,  # 25% taniej
            "graph": 0.00001   # 50% taniej
        }
        
        return tokens * cost_per_token.get(strategy, 0.00002)
    
    def generate_comparison_report(self, results: Dict[str, Dict[str, List[RAGBenchResult]]]) -> Dict[str, Any]:
        """
        Generuje raport porównawczy strategii
        
        Args:
            results: Wyniki testów pogrupowane według domeny i strategii
            
        Returns:
            Raport porównawczy
        """
        report = {
            "summary": {},
            "domains": {},
            "recommendations": []
        }
        
        # Oblicz statystyki dla każdej domeny
        for domain, strategies in results.items():
            domain_stats = {}
            
            for strategy, strategy_results in strategies.items():
                if not strategy_results:
                    continue
                
                # Oblicz średnie metryki
                avg_metrics = self._calculate_average_metrics(strategy_results)
                
                domain_stats[strategy] = {
                    "adherence": avg_metrics["adherence"],
                    "completeness": avg_metrics["completeness"],
                    "utilization": avg_metrics["utilization"],
                    "relevance": avg_metrics["relevance"],
                    "p95_latency": self._calculate_p95_latency(strategy_results),
                    "avg_tokens": avg_metrics["tokens"],
                    "avg_cost": avg_metrics["cost"],
                    "total_queries": len(strategy_results)
                }
            
            report["domains"][domain] = domain_stats
        
        # Generuj rekomendacje
        report["recommendations"] = self._generate_recommendations(report["domains"])
        
        return report
    
    def _calculate_average_metrics(self, results: List[RAGBenchResult]) -> Dict[str, float]:
        """Oblicza średnie metryki z wyników"""
        if not results:
            return {}
        
        total_adherence = sum(r.metrics.get("adherence", 0) for r in results)
        total_completeness = sum(r.metrics.get("completeness", 0) for r in results)
        total_utilization = sum(r.metrics.get("utilization", 0) for r in results)
        total_relevance = sum(r.metrics.get("relevance", 0) for r in results)
        total_tokens = sum(r.tokens for r in results)
        total_cost = sum(r.cost for r in results)
        
        count = len(results)
        
        return {
            "adherence": total_adherence / count,
            "completeness": total_completeness / count,
            "utilization": total_utilization / count,
            "relevance": total_relevance / count,
            "tokens": total_tokens / count,
            "cost": total_cost / count
        }
    
    def _calculate_p95_latency(self, results: List[RAGBenchResult]) -> float:
        """Oblicza 95 percentyl latencji"""
        if not results:
            return 0.0
        
        latencies = [r.latency for r in results]
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        return latencies[p95_index] if p95_index < len(latencies) else latencies[-1]
    
    def _generate_recommendations(self, domains_stats: Dict[str, Dict[str, Dict[str, Any]]]) -> List[str]:
        """Generuje rekomendacje na podstawie statystyk"""
        recommendations = []
        
        for domain, strategies in domains_stats.items():
            if "graph" in strategies and "text" in strategies:
                graph_stats = strategies["graph"]
                text_stats = strategies["text"]
                
                if graph_stats["adherence"] > text_stats["adherence"]:
                    recommendations.append(f"GraphRAG osiąga lepszą adherence w domenie {domain}")
                
                if graph_stats["avg_tokens"] < text_stats["avg_tokens"]:
                    token_reduction = (text_stats["avg_tokens"] - graph_stats["avg_tokens"]) / text_stats["avg_tokens"]
                    recommendations.append(f"GraphRAG redukuje tokeny o {token_reduction:.1%} w domenie {domain}")
        
        return recommendations


# Global instance
ragbench_service = RAGBenchService()
