from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.core.config import settings


@dataclass
class RAGSettings:
    """Konfigurowalne parametry dla polityk RAG.

    Wartości domyślne pochodzą z konfiguracji systemowej (pliku .env) i mogą
    zostać nadpisane dla pojedynczego zapytania poprzez przekazanie słownika
    `overrides`.
    """

    chunk_size: int = field(default_factory=lambda: settings.CHUNK_SIZE)
    chunk_overlap: int = field(default_factory=lambda: settings.CHUNK_OVERLAP)
    max_tokens: int = field(default_factory=lambda: settings.MAX_TOKENS)
    similarity_threshold: float = field(default_factory=lambda: settings.SIMILARITY_THRESHOLD)
    top_k_results: int = field(default_factory=lambda: settings.TOP_K_RESULTS)
    max_search_results: int = field(default_factory=lambda: settings.MAX_SEARCH_RESULTS)
    search_timeout: int = field(default_factory=lambda: settings.SEARCH_TIMEOUT)
    temperature: float = field(default_factory=lambda: settings.TEMPERATURE)
    max_response_length: int = field(default_factory=lambda: settings.MAX_RESPONSE_LENGTH)
    cache_ttl: int = field(default_factory=lambda: settings.CACHE_TTL)
    batch_size: int = field(default_factory=lambda: settings.BATCH_SIZE)
    embedding_model: str = field(default_factory=lambda: settings.EMBEDDING_MODEL)
    vector_db_path: str = field(default_factory=lambda: settings.VECTOR_DB_PATH)

    # Ustawienia specyficzne dla poszczególnych polityk
    fact_confidence_threshold: float = 0.4
    fact_rerank_top_n: int = 20
    graph_max_depth: int = 3
    graph_max_paths: int = field(default_factory=lambda: settings.TOP_K_RESULTS)
    text_rerank_top_n: int = 20

    personalization: Dict[str, Any] = field(default_factory=dict)

    # Wagi fuzji wyników (hybrydowy RAG)
    fusion_w_text: float = 0.5
    fusion_w_facts: float = 0.3
    fusion_w_graph: float = 0.2

    @classmethod
    def from_overrides(cls, overrides: Optional[Dict[str, Any]] = None) -> "RAGSettings":
        overrides = overrides or {}
        # Rozdziel pola znane klasie od dodatkowych preferencji użytkownika
        field_names = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[arg-type]
        kwargs: Dict[str, Any] = {}
        personalization: Dict[str, Any] = {}

        for key, value in overrides.items():
            key_lower = key.lower()
            if key_lower in field_names:
                kwargs[key_lower] = value
            else:
                personalization[key] = value

        instance = cls(**kwargs)  # type: ignore[arg-type]
        if personalization:
            instance.personalization.update(personalization)
        return instance

    def override(self, overrides: Optional[Dict[str, Any]] = None) -> "RAGSettings":
        """Zwraca nową instancję z nadpisanymi ustawieniami."""
        if not overrides:
            return self
        merged = self.to_dict()
        merged.update(overrides)
        return RAGSettings.from_overrides(merged)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje konfigurację na słownik serializowalny JSON."""
        data = {field.name: getattr(self, field.name) for field in self.__dataclass_fields__.values()}  # type: ignore[arg-type]
        return data
