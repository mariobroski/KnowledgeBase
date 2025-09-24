from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.db.models import SearchQueryModel, ArticleModel, FragmentModel, FactModel, EntityModel, RelationModel  # SQLAlchemy models
from app.db.database import get_db

class AnalyticsService:
    """Serwis do analizy danych i metryk
    
    Ta klasa jest odpowiedzialna za analizę danych i obliczanie metryk.
    """
    
    def __init__(self, db: Session):
        """Inicjalizacja serwisu
        
        Args:
            db: Sesja bazy danych
        """
        self.db = db
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Pobierz dane do dashboardu
        
        Returns:
            Dane do dashboardu
        """
        # Liczba artykułów
        article_count = self.db.query(func.count(ArticleModel.id)).scalar() or 0
        
        # Liczba fragmentów
        fragment_count = self.db.query(func.count(FragmentModel.id)).scalar() or 0
        
        # Liczba faktów
        fact_count = self.db.query(func.count(FactModel.id)).scalar() or 0
        
        # Liczba encji
        entity_count = self.db.query(func.count(EntityModel.id)).scalar() or 0
        
        # Liczba relacji
        relation_count = self.db.query(func.count(RelationModel.id)).scalar() or 0
        
        # Liczba zapytań
        query_count = self.db.query(func.count(SearchQueryModel.id)).scalar() or 0
        
        # Liczba zapytań według polityki
        policy_counts = self.db.query(
            SearchQueryModel.policy,
            func.count(SearchQueryModel.id).label('count')
        ).group_by(SearchQueryModel.policy).all()
        
        policy_data = {}
        for policy_type, count in policy_counts:
            policy_data[policy_type] = count
        
        return {
            "article_count": article_count,
            "fragment_count": fragment_count,
            "fact_count": fact_count,
            "entity_count": entity_count,
            "relation_count": relation_count,
            "query_count": query_count,
            "policy_data": policy_data
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Pobierz metryki systemu
        
        Returns:
            Metryki systemu
        """
        # W rzeczywistej implementacji, tutaj byłyby obliczenia metryk
        # Dla demonstracji zwracamy przykładowe dane
        
        # Metryki jakości
        quality_metrics = {
            "relevance": 0.85,  # Trafność odpowiedzi
            "hallucination": 0.12,  # Poziom halucynacji
            "factual_accuracy": 0.92  # Dokładność faktyczna
        }
        
        # Metryki wydajności
        performance_metrics = {
            "avg_search_time": 0.35,  # Średni czas wyszukiwania
            "avg_generation_time": 0.42,  # Średni czas generowania
            "avg_total_time": 0.77,  # Średni całkowity czas
            "queries_per_minute": 78  # Zapytania na minutę
        }
        
        # Metryki kosztów
        cost_metrics = {
            "avg_tokens_per_query": 320,  # Średnia liczba tokenów na zapytanie
            "avg_cost_per_query": 0.0064,  # Średni koszt na zapytanie
            "total_cost": 12.80  # Całkowity koszt
        }
        
        return {
            "quality": quality_metrics,
            "performance": performance_metrics,
            "cost": cost_metrics
        }
    
    def get_metrics(self, start_date: Optional[str] = None, end_date: Optional[str] = None, policy: Optional[str] = None) -> Dict[str, Any]:
        """Pobierz metryki systemu
        
        Args:
            start_date: Data początkowa
            end_date: Data końcowa
            policy: Typ polityki
            
        Returns:
            Metryki systemu
        """
        return self.get_system_metrics()
    
    def get_quality_metrics(self, start_date: Optional[str] = None, end_date: Optional[str] = None, policy: Optional[str] = None) -> Dict[str, Any]:
        """Pobierz metryki jakości odpowiedzi
        
        Args:
            start_date: Data początkowa
            end_date: Data końcowa
            policy: Typ polityki
            
        Returns:
            Metryki jakości
        """
        return {
            "relevance": 0.85,  # Trafność odpowiedzi
            "hallucination": 0.12,  # Poziom halucynacji
            "factual_accuracy": 0.92  # Dokładność faktyczna
        }
    
    def get_performance_metrics(self, start_date: Optional[str] = None, end_date: Optional[str] = None, policy: Optional[str] = None) -> Dict[str, Any]:
        """Pobierz metryki wydajności
        
        Args:
            start_date: Data początkowa
            end_date: Data końcowa
            policy: Typ polityki
            
        Returns:
            Metryki wydajności
        """
        return {
            "avg_search_time": 0.35,  # Średni czas wyszukiwania
            "avg_generation_time": 0.42,  # Średni czas generowania
            "avg_total_time": 0.77,  # Średni całkowity czas
            "queries_per_minute": 78  # Zapytania na minutę
        }
    
    def get_cost_metrics(self, start_date: Optional[str] = None, end_date: Optional[str] = None, policy: Optional[str] = None) -> Dict[str, Any]:
        """Pobierz metryki kosztów
        
        Args:
            start_date: Data początkowa
            end_date: Data końcowa
            policy: Typ polityki
            
        Returns:
            Metryki kosztów
        """
        return {
            "avg_tokens_per_query": 320,  # Średnia liczba tokenów na zapytanie
            "avg_cost_per_query": 0.0064,  # Średni koszt na zapytanie
            "total_cost": 12.80  # Całkowity koszt
        }

    def compare_policies(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Porównaj polityki RAG
        
        Returns:
            Porównanie polityk
        """
        # W rzeczywistej implementacji, tutaj byłyby obliczenia metryk dla każdej polityki
        # Dla demonstracji zwracamy przykładowe dane
        
        # Metryki dla TekstRAG
        text_rag_metrics = {
            "relevance": 0.80,
            "hallucination": 0.15,
            "factual_accuracy": 0.85,
            "avg_search_time": 0.25,
            "avg_generation_time": 0.45,
            "avg_total_time": 0.70,
            "avg_tokens_per_query": 350,
            "avg_cost_per_query": 0.0070
        }
        
        # Metryki dla FaktRAG
        fact_rag_metrics = {
            "relevance": 0.85,
            "hallucination": 0.10,
            "factual_accuracy": 0.90,
            "avg_search_time": 0.35,
            "avg_generation_time": 0.30,
            "avg_total_time": 0.65,
            "avg_tokens_per_query": 280,
            "avg_cost_per_query": 0.0056
        }
        
        # Metryki dla GrafRAG
        graph_rag_metrics = {
            "relevance": 0.90,
            "hallucination": 0.08,
            "factual_accuracy": 0.95,
            "avg_search_time": 0.40,
            "avg_generation_time": 0.35,
            "avg_total_time": 0.75,
            "avg_tokens_per_query": 300,
            "avg_cost_per_query": 0.0060
        }
        
        return {
            "text": text_rag_metrics,
            "facts": fact_rag_metrics,
            "graph": graph_rag_metrics
        }