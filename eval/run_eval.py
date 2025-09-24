#!/usr/bin/env python3
"""
Harness oceniający - wywołuje /api/search z parametrami, loguje response, context, metrics
Oblicza TRACe (Relevance/Utilization/Adherence/Completeness) i RAGAS metryki
"""

import os
import sys
import json
import logging
import requests
import time
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

# Dodaj ścieżkę do backend
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.trace_service import TRACEService

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGBenchEvaluator:
    """Harness oceniający RAGBench"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.trace_service = TRACEService()
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Parametry testowe
        self.test_params = {
            "text": {"policy": "text", "top_k": 5, "similarity_threshold": 0.7},
            "facts": {"policy": "facts", "top_k": 5, "fact_confidence_threshold": 0.8},
            "graph": {"policy": "graph", "top_k": 5, "graph_max_depth": 3, "graph_max_paths": 10},
            "hybrid": {"policy": "hybrid", "top_k": 5, "similarity_threshold": 0.7}
        }
    
    def load_queries(self, domain: str) -> List[Dict[str, Any]]:
        """
        Ładuje zapytania z pliku JSON
        
        Args:
            domain: Nazwa domeny
            
        Returns:
            Lista zapytań
        """
        queries_file = Path(__file__).parent / "data" / "queries.json"
        
        if not queries_file.exists():
            logger.error(f"Plik zapytań nie istnieje: {queries_file}")
            return []
        
        with open(queries_file, 'r', encoding='utf-8') as f:
            all_queries = json.load(f)
        
        # Filtruj zapytania dla danej domeny
        domain_queries = [q for q in all_queries if q.get('domain') == domain]
        
        logger.info(f"Załadowano {len(domain_queries)} zapytań dla domeny {domain}")
        return domain_queries
    
    def evaluate_query(self, query: Dict[str, Any], policy: str) -> Dict[str, Any]:
        """
        Ewaluuje pojedyncze zapytanie
        
        Args:
            query: Zapytanie do ewaluacji
            policy: Polityka RAG (text, facts, graph, hybrid)
            
        Returns:
            Wynik ewaluacji
        """
        start_time = time.time()
        
        try:
            # Przygotuj parametry
            params = self.test_params.get(policy, {})
            params["query"] = query["query"]
            
            # Wywołaj API
            response = requests.post(
                f"{self.base_url}/api/search",
                json=params,
                timeout=30
            )
            response.raise_for_status()
            
            search_result = response.json()
            
            # Oblicz czasy
            end_time = time.time()
            total_time = (end_time - start_time) * 1000  # ms
            
            # Pobierz metryki z odpowiedzi
            metrics = search_result.get("metrics", {})
            search_time = metrics.get("search_time", 0)
            generation_time = metrics.get("generation_time", 0)
            tokens_used = metrics.get("tokens_used", 0)
            cost = metrics.get("cost", 0)
            
            # Oblicz metryki TRACe
            trace_metrics = self.trace_service.calculate_metrics(
                query=query["query"],
                response=search_result.get("response", ""),
                context=search_result.get("context", {}),
                ground_truth=query.get("ground_truth", [])
            )
            
            # Oblicz metryki RAGAS
            ragas_metrics = self._calculate_ragas_metrics(
                question=query["query"],
                answer=search_result.get("response", ""),
                context=search_result.get("context", {})
            )
            
            # Połącz wszystkie metryki
            all_metrics = {
                **trace_metrics,
                **ragas_metrics,
                "search_time": search_time,
                "generation_time": generation_time,
                "total_time": total_time,
                "tokens_used": tokens_used,
                "cost": cost
            }
            
            return {
                "query_id": query["query_id"],
                "domain": query["domain"],
                "policy": policy,
                "query": query["query"],
                "response": search_result.get("response", ""),
                "context": search_result.get("context", {}),
                "metrics": all_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Błąd ewaluacji zapytania {query['query_id']}: {e}")
            return {
                "query_id": query["query_id"],
                "domain": query["domain"],
                "policy": policy,
                "query": query["query"],
                "response": "",
                "context": {},
                "metrics": {
                    "relevance": 0.0,
                    "utilization": 0.0,
                    "adherence": 0.0,
                    "completeness": 0.0,
                    "faithfulness": 0.0,
                    "answer_relevance": 0.0,
                    "context_precision": 0.0,
                    "context_recall": 0.0,
                    "search_time": 0.0,
                    "generation_time": 0.0,
                    "total_time": 0.0,
                    "tokens_used": 0,
                    "cost": 0.0
                },
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_ragas_metrics(self, question: str, answer: str, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Oblicza metryki RAGAS
        
        Args:
            question: Pytanie
            answer: Odpowiedź
            context: Kontekst
            
        Returns:
            Metryki RAGAS
        """
        try:
            # Faithfulness - zgodność odpowiedzi z kontekstem
            faithfulness = self._calculate_faithfulness(answer, context)
            
            # Answer Relevance - trafność odpowiedzi względem pytania
            answer_relevance = self._calculate_answer_relevance(question, answer)
            
            # Context Precision - precyzja kontekstu
            context_precision = self._calculate_context_precision(question, context)
            
            # Context Recall - recall kontekstu
            context_recall = self._calculate_context_recall(question, context)
            
            return {
                "faithfulness": faithfulness,
                "answer_relevance": answer_relevance,
                "context_precision": context_precision,
                "context_recall": context_recall
            }
            
        except Exception as e:
            logger.error(f"Błąd obliczania metryk RAGAS: {e}")
            return {
                "faithfulness": 0.0,
                "answer_relevance": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0
            }
    
    def _calculate_faithfulness(self, answer: str, context: Dict[str, Any]) -> float:
        """Oblicza faithfulness - zgodność odpowiedzi z kontekstem"""
        if not answer or not context:
            return 0.0
        
        # Pobierz fragmenty z kontekstu
        fragments = context.get("fragments", [])
        if not fragments:
            return 0.0
        
        # Sprawdź czy odpowiedź zawiera informacje z kontekstu
        context_text = " ".join([f.get("content", "") for f in fragments])
        
        if not context_text:
            return 0.0
        
        # Oblicz podobieństwo semantyczne
        if self.trace_service.embedding_model:
            try:
                answer_embedding = self.trace_service.embedding_model.encode([answer])
                context_embedding = self.trace_service.embedding_model.encode([context_text])
                
                from sklearn.metrics.pairwise import cosine_similarity
                similarity = cosine_similarity(answer_embedding, context_embedding)[0][0]
                return float(similarity)
            except Exception:
                pass
        
        # Fallback na podobieństwo tokenów
        return self.trace_service._calculate_token_similarity(answer, context_text)
    
    def _calculate_answer_relevance(self, question: str, answer: str) -> float:
        """Oblicza answer relevance - trafność odpowiedzi względem pytania"""
        if not question or not answer:
            return 0.0
        
        # Użyj metryki relevance z TRACe
        return self.trace_service._calculate_relevance(question, answer)
    
    def _calculate_context_precision(self, question: str, context: Dict[str, Any]) -> float:
        """Oblicza context precision - precyzja kontekstu"""
        if not question or not context:
            return 0.0
        
        # Pobierz fragmenty z kontekstu
        fragments = context.get("fragments", [])
        if not fragments:
            return 0.0
        
        # Sprawdź ile fragmentów jest istotnych dla pytania
        relevant_fragments = 0
        
        for fragment in fragments:
            content = fragment.get("content", "")
            if content:
                # Oblicz podobieństwo fragmentu do pytania
                similarity = self.trace_service._calculate_relevance(question, content)
                if similarity > 0.5:  # Próg istotności
                    relevant_fragments += 1
        
        return relevant_fragments / len(fragments) if fragments else 0.0
    
    def _calculate_context_recall(self, question: str, context: Dict[str, Any]) -> float:
        """Oblicza context recall - recall kontekstu"""
        if not question or not context:
            return 0.0
        
        # Pobierz fragmenty z kontekstu
        fragments = context.get("fragments", [])
        if not fragments:
            return 0.0
        
        # Sprawdź czy kontekst zawiera wszystkie istotne informacje
        # (uproszczona implementacja)
        total_similarity = 0.0
        
        for fragment in fragments:
            content = fragment.get("content", "")
            if content:
                similarity = self.trace_service._calculate_relevance(question, content)
                total_similarity += similarity
        
        return total_similarity / len(fragments) if fragments else 0.0
    
    def evaluate_domain(self, domain: str, policies: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ewaluuje domenę dla wszystkich polityk
        
        Args:
            domain: Nazwa domeny
            policies: Lista polityk do testowania
            
        Returns:
            Wyniki ewaluacji pogrupowane według polityki
        """
        if policies is None:
            policies = ["text", "facts", "graph", "hybrid"]
        
        logger.info(f"Rozpoczynanie ewaluacji domeny {domain} dla polityk: {policies}")
        
        # Załaduj zapytania
        queries = self.load_queries(domain)
        if not queries:
            logger.error(f"Brak zapytań dla domeny {domain}")
            return {}
        
        # Ogranicz liczbę zapytań dla testów
        max_queries = 100
        if len(queries) > max_queries:
            queries = queries[:max_queries]
            logger.info(f"Ograniczono do {max_queries} zapytań")
        
        results = {}
        
        for policy in policies:
            logger.info(f"Ewaluacja polityki {policy}...")
            policy_results = []
            
            for i, query in enumerate(queries):
                logger.info(f"Zapytanie {i+1}/{len(queries)}: {query['query'][:50]}...")
                
                result = self.evaluate_query(query, policy)
                policy_results.append(result)
                
                # Krótka przerwa między zapytaniami
                time.sleep(0.1)
            
            results[policy] = policy_results
            logger.info(f"Zakończono ewaluację polityki {policy}: {len(policy_results)} wyników")
        
        return results
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]], domain: str):
        """
        Zapisuje wyniki do plików
        
        Args:
            results: Wyniki ewaluacji
            domain: Nazwa domeny
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Zapisz wyniki JSON
        json_file = self.results_dir / f"{domain}_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Zapisz wyniki CSV
        csv_file = self.results_dir / f"{domain}_results_{timestamp}.csv"
        self._save_results_csv(results, csv_file)
        
        # Zapisz podsumowanie
        summary_file = self.results_dir / f"{domain}_summary_{timestamp}.json"
        self._save_summary(results, summary_file)
        
        logger.info(f"Wyniki zapisane do {self.results_dir}")
    
    def _save_results_csv(self, results: Dict[str, List[Dict[str, Any]]], csv_file: Path):
        """Zapisuje wyniki do pliku CSV"""
        rows = []
        
        for policy, policy_results in results.items():
            for result in policy_results:
                row = {
                    "query_id": result["query_id"],
                    "domain": result["domain"],
                    "policy": policy,
                    "query": result["query"],
                    "response": result["response"],
                    **result["metrics"]
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False, encoding='utf-8')
    
    def _save_summary(self, results: Dict[str, List[Dict[str, Any]]], summary_file: Path):
        """Zapisuje podsumowanie wyników"""
        summary = {}
        
        for policy, policy_results in results.items():
            if not policy_results:
                continue
            
            # Oblicz statystyki
            metrics = [r["metrics"] for r in policy_results]
            
            # Średnie metryki
            avg_metrics = {}
            for metric in ["relevance", "utilization", "adherence", "completeness", 
                          "faithfulness", "answer_relevance", "context_precision", "context_recall"]:
                values = [m.get(metric, 0) for m in metrics if metric in m]
                avg_metrics[metric] = np.mean(values) if values else 0.0
            
            # Percentyle czasu
            times = [m.get("total_time", 0) for m in metrics]
            p50_time = np.percentile(times, 50) if times else 0.0
            p95_time = np.percentile(times, 95) if times else 0.0
            
            # Średnie tokeny i koszt
            avg_tokens = np.mean([m.get("tokens_used", 0) for m in metrics])
            avg_cost = np.mean([m.get("cost", 0) for m in metrics])
            
            summary[policy] = {
                "total_queries": len(policy_results),
                "avg_metrics": avg_metrics,
                "p50_time": p50_time,
                "p95_time": p95_time,
                "avg_tokens": avg_tokens,
                "avg_cost": avg_cost
            }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    """Główna funkcja"""
    if len(sys.argv) < 2:
        print("Użycie: python run_eval.py <domain> [policies]")
        print("Dostępne domeny: FinQA, TAT-QA, TechQA, CUAD, EManual")
        print("Dostępne polityki: text, facts, graph, hybrid")
        sys.exit(1)
    
    domain = sys.argv[1]
    policies = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    
    evaluator = RAGBenchEvaluator()
    results = evaluator.evaluate_domain(domain, policies)
    
    if results:
        evaluator.save_results(results, domain)
        print(f"✅ Ewaluacja domeny {domain} zakończona pomyślnie")
        print(f"📊 Wyniki zapisane do {evaluator.results_dir}")
    else:
        print(f"❌ Błąd ewaluacji domeny {domain}")
        sys.exit(1)


if __name__ == "__main__":
    main()
