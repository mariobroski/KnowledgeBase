from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.rag.settings import RAGSettings
from app.services.policy_selector import PolicySelector
from app.services.search_service import SearchService

class AutoSearchRequest(BaseModel):
    query: str
    confidence_threshold: float = 0.6
    limit: int = 5
    settings: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    policy: str = "text"
    limit: int = 5
    settings: Optional[Dict[str, Any]] = None

class AnalyzeRequest(BaseModel):
    query: str

router = APIRouter()

def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    return SearchService(db)

def get_policy_selector() -> PolicySelector:
    return PolicySelector()

@router.post("/auto", response_model=Dict[str, Any])
async def auto_search(
    request: AutoSearchRequest,
    service: SearchService = Depends(get_search_service),
    policy_selector: PolicySelector = Depends(get_policy_selector)
):
    """Wyszukaj informacje z automatycznym wyborem polityki RAG"""
    # Przekieruj do SearchService z policy="auto" i przekaż próg jako parametr
    params: Dict[str, Any] = {"limit": request.limit, "auto_confidence_threshold": request.confidence_threshold}
    if request.settings:
        params["settings"] = request.settings

    result = service.search(
        query=request.query,
        policy_type="auto",
        params=params,
    )
    return result

@router.post("/", response_model=Dict[str, Any])
async def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service)
):
    """Wyszukaj informacje używając wybranej polityki RAG"""
    if request.policy not in ["text", "facts", "graph", "hybrid", "auto"]:
        raise HTTPException(status_code=400, detail="Nieprawidłowa polityka wyszukiwania")
    
    params: Dict[str, Any] = {"limit": request.limit}
    if request.settings:
        params["settings"] = request.settings

    result = service.search(query=request.query, policy_type=request.policy, params=params)
    return result

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_query(
    request: AnalyzeRequest,
    policy_selector: PolicySelector = Depends(get_policy_selector)
):
    """Analizuj zapytanie i zwróć rekomendacje polityk bez wykonywania wyszukiwania"""
    
    selected_policy, confidence, all_scores = policy_selector.select_policy(request.query)
    
    return {
        "query": request.query,
        "recommended_policy": selected_policy,
        "confidence": confidence,
        "all_scores": all_scores,
        "explanation": policy_selector.get_policy_explanation(selected_policy, confidence, all_scores),
        "policy_details": {
            "text": {
                "score": all_scores.get("text", 0.0),
                "description": "Najlepszy dla pytań opisowych i wyjaśnień"
            },
            "facts": {
                "score": all_scores.get("facts", 0.0),
                "description": "Najlepszy dla pytań o konkretne fakty i dane"
            },
            "graph": {
                "score": all_scores.get("graph", 0.0),
                "description": "Najlepszy dla pytań o relacje i powiązania"
            }
        }
    }

@router.get("/policies")
async def get_available_policies():
    """Pobierz dostępne polityki wyszukiwania"""
    return {
        "policies": [
            {
                "id": "auto",
                "name": "AutoRAG",
                "description": "Automatyczny wybór polityki na podstawie zapytania (heurystyki)"
            },
            {
                "id": "text",
                "name": "TekstRAG",
                "description": "Standardowy tryb, w którym system wyszukuje pasujące fragmenty tekstu"
            },
            {
                "id": "facts",
                "name": "FaktRAG",
                "description": "Tryb oparty na faktach, w którym system wyszukuje strukturalne informacje"
            },
            {
                "id": "graph",
                "name": "GrafRAG",
                "description": "Tryb grafowy, w którym system wykorzystuje relacje między encjami"
            },
            {
                "id": "hybrid",
                "name": "HybrydRAG",
                "description": "Tryb łączący wyniki TekstRAG, FaktRAG i GrafRAG z fuzją późną"
            }
        ]
    }


@router.get("/settings/defaults", response_model=Dict[str, Any])
async def get_default_rag_settings() -> Dict[str, Any]:
    """Zwraca domyślną konfigurację polityk RAG."""
    return RAGSettings().to_dict()

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_search_history(
    skip: int = 0,
    limit: int = 20,
    service: SearchService = Depends(get_search_service)
):
    """Pobierz historię wyszukiwań"""
    return service.get_search_history(skip=skip, limit=limit)

@router.get("/history/{search_id}", response_model=Dict[str, Any])
async def get_search_details(search_id: int, service: SearchService = Depends(get_search_service)):
    """Pobierz szczegóły wyszukiwania"""
    search = service.get_search_details(search_id=search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Wyszukiwanie nie znalezione")
    return search
