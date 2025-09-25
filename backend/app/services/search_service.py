from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.database_models import SearchQuery as SearchQueryModel
from app.rag.factory import RAGPolicyFactory
from app.rag.settings import RAGSettings
from app.services.policy_selector import PolicySelector

class SearchService:
    """Serwis do wyszukiwania z wykorzystaniem RAG
    
    Ta klasa jest odpowiedzialna za wyszukiwanie z wykorzystaniem różnych polityk RAG.
    """
    
    def __init__(self, db: Session):
        """Inicjalizacja serwisu
        
        Args:
            db: Sesja bazy danych
        """
        self.db = db
        self.policy_factory = RAGPolicyFactory()
    
    def search(self, query: str, policy_type: str = "text", params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Wyszukaj z wykorzystaniem wybranej polityki RAG
        
        Args:
            query: Zapytanie użytkownika
            policy_type: Typ polityki (text, facts, graph)
            params: Dodatkowe parametry wyszukiwania
            
        Returns:
            Wyniki wyszukiwania
        """
        params = params or {}
        overrides = params.get("settings") if isinstance(params, dict) else None
        config = RAGSettings.from_overrides(overrides)

        # Obsługa trybu automatycznego wyboru polityki
        policy_selection_info: Optional[Dict[str, Any]] = None
        effective_policy_type = policy_type
        if policy_type == "auto":
            selector = PolicySelector()
            threshold = 0.6
            if isinstance(params, dict):
                threshold = float(params.get("auto_confidence_threshold", threshold))
            selected_policy, confidence, all_scores = selector.select_policy(query, threshold)
            explanation = selector.get_policy_explanation(selected_policy, confidence, all_scores)
            policy_selection_info = {
                "selected_policy": selected_policy,
                "confidence": confidence,
                "all_scores": all_scores,
                "explanation": explanation,
                "auto_selected": True,
            }
            effective_policy_type = selected_policy

        policy = self.policy_factory.create_policy(effective_policy_type, config=config)

        effective_limit = params.get("limit") if isinstance(params, dict) else None
        search_context = policy.search(query, db=self.db, limit=effective_limit)
        search_context.setdefault("applied_settings", config.to_dict())

        response_data = policy.generate_response(query, search_context)
        search_context["generation_time"] = response_data.get("elapsed_time", 0.0)

        justification = policy.get_justification(search_context)
        metrics = policy.get_metrics(query, response_data["response"], search_context)

        # Zapisanie zapytania w historii
        search_query = SearchQueryModel(
            query=query,
            policy=effective_policy_type,
            response=response_data["response"],
            context=search_context,
            metrics=metrics
        )
        self.db.add(search_query)
        self.db.commit()
        self.db.refresh(search_query)
        
        # Zwrócenie wyników
        result: Dict[str, Any] = {
            "query": query,
            "policy_type": effective_policy_type,
            "response": response_data["response"],
            "response_details": response_data,
            "justification": justification,
            "context": search_context,
            "metrics": metrics,
            "search_id": search_query.id,
        }

        if policy_selection_info:
            result["policy_selection"] = policy_selection_info

        return result
    
    def get_available_policies(self) -> List[Dict[str, Any]]:
        """Pobierz dostępne polityki RAG
        
        Returns:
            Lista dostępnych polityk
        """
        return [
            {
                "id": "auto",
                "name": "AutoRAG",
                "description": "Automatyczny wybór polityki na podstawie zapytania (heurystyki)",
            },
            {
                "id": "text",
                "name": "TekstRAG",
                "description": "Standardowa polityka RAG, która wykorzystuje fragmenty tekstu jako kontekst."
            },
            {
                "id": "facts",
                "name": "FaktRAG",
                "description": "Polityka RAG, która wykorzystuje wyekstrahowane fakty jako kontekst."
            },
            {
                "id": "graph",
                "name": "GrafRAG",
                "description": "Polityka RAG, która wykorzystuje graf wiedzy jako kontekst."
            },
            {
                "id": "hybrid",
                "name": "HybrydRAG",
                "description": "Polityka RAG, która łączy TekstRAG, FaktRAG i GrafRAG (fuzja późna)."
            },
            {
                "id": "smart_hybrid",
                "name": "SmartHybrydRAG",
                "description": "Inteligentny RAG z automatycznym wyborem strategii na podstawie analizy kosztów i wydajności."
            }
        ]
    
    def get_search_history(self, skip: int = 0, limit: int = 100) -> List[SearchQueryModel]:
        """Pobierz historię wyszukiwania
        
        Args:
            skip: Liczba zapytań do pominięcia
            limit: Maksymalna liczba zapytań do zwrócenia
            
        Returns:
            Lista zapytań
        """
        return self.db.query(SearchQueryModel).order_by(SearchQueryModel.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_search_query(self, search_id: int) -> Optional[SearchQueryModel]:
        """Pobierz zapytanie po ID
        
        Args:
            search_id: ID zapytania
            
        Returns:
            Zapytanie lub None, jeśli nie znaleziono
        """
        return self.db.query(SearchQueryModel).filter(SearchQueryModel.id == search_id).first()
    
    def get_search_details(self, search_id: int) -> Optional[SearchQueryModel]:
        """Pobierz szczegóły wyszukiwania (alias dla get_search_query)
        
        Args:
            search_id: ID wyszukiwania
            
        Returns:
            Wyszukiwanie lub None
        """
        return self.get_search_query(search_id)
