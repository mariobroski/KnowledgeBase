from pydantic import BaseModel, Field
from typing import Optional


class SystemSettingsBase(BaseModel):
    # RAG Parameters
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Rozmiar fragmentu tekstu")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Nakładanie się fragmentów")
    max_tokens: int = Field(default=4000, ge=1000, le=8000, description="Maksymalna liczba tokenów")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Próg podobieństwa")
    top_k_results: int = Field(default=5, ge=1, le=20, description="Liczba najlepszych wyników")
    
    # Search Parameters
    max_search_results: int = Field(default=10, ge=1, le=50, description="Maksymalna liczba wyników wyszukiwania")
    search_timeout: int = Field(default=30, ge=5, le=120, description="Timeout wyszukiwania (sekundy)")
    
    # Model Parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura modelu")
    max_response_length: int = Field(default=2000, ge=500, le=5000, description="Maksymalna długość odpowiedzi")
    
    # Performance Parameters
    cache_ttl: int = Field(default=3600, ge=300, le=86400, description="Czas życia cache (sekundy)")
    batch_size: int = Field(default=10, ge=1, le=100, description="Rozmiar batcha")


class SystemSettingsCreate(SystemSettingsBase):
    pass


class SystemSettingsUpdate(BaseModel):
    chunk_size: Optional[int] = Field(None, ge=100, le=5000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    max_tokens: Optional[int] = Field(None, ge=1000, le=8000)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_k_results: Optional[int] = Field(None, ge=1, le=20)
    max_search_results: Optional[int] = Field(None, ge=1, le=50)
    search_timeout: Optional[int] = Field(None, ge=5, le=120)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_response_length: Optional[int] = Field(None, ge=500, le=5000)
    cache_ttl: Optional[int] = Field(None, ge=300, le=86400)
    batch_size: Optional[int] = Field(None, ge=1, le=100)


class SystemSettingsResponse(SystemSettingsBase):
    class Config:
        from_attributes = True