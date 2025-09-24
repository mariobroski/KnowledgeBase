from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.rag.settings import RAGSettings


class RAGPolicy(ABC):
    """Abstrakcyjna klasa bazowa dla polityk RAG."""

    def __init__(self, config: Optional[RAGSettings] = None) -> None:
        self.config = config or RAGSettings()

    @abstractmethod
    def search(self, query: str, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        """Wyszukaj informacje na podstawie zapytania i zwróć kontekst."""

    @abstractmethod
    def generate_response(self, query: str, context: Any) -> Dict[str, Any]:
        """Wygeneruj odpowiedź na podstawie zapytania i kontekstu."""

    @abstractmethod
    def get_justification(self, context: Any) -> Dict[str, Any]:
        """Pobierz uzasadnienie dla odpowiedzi."""

    @abstractmethod
    def get_metrics(self, query: str, response: str, context: Any) -> Dict[str, Any]:
        """Oblicz metryki dla wygenerowanej odpowiedzi."""
