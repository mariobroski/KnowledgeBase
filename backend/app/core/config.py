import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "KnowledgeBase"
    API_V1_STR: str = "/api"

    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "rag_system")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./app.db"  # Domyślnie SQLite dla lokalnego uruchomienia
    )
    
    # JanusGraph (replacing Neo4j)
    JANUSGRAPH_HOST: str = os.getenv("JANUSGRAPH_HOST", "localhost")
    JANUSGRAPH_PORT: int = int(os.getenv("JANUSGRAPH_PORT", "8182"))
    JANUSGRAPH_TIMEOUT: int = int(os.getenv("JANUSGRAPH_TIMEOUT", "30"))
    JANUSGRAPH_STORAGE_BACKEND: str = os.getenv("JANUSGRAPH_STORAGE_BACKEND", "berkeleyje")
    JANUSGRAPH_STORAGE_DIRECTORY: str = os.getenv("JANUSGRAPH_STORAGE_DIRECTORY", "./janusgraph_data")
    
    # RAG
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Keep for compatibility with components expecting a local vector path
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vector_db")

    # LLM provider configuration (no OpenAI by default)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "")  # e.g. "ollama"
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")        # e.g. "llama3"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    TGI_BASE_URL: str = os.getenv("TGI_BASE_URL", "http://localhost:8080")
    TGI_MODEL_ID: str = os.getenv("TGI_MODEL_ID", "")
    TGI_NUM_SHARD: int = int(os.getenv("TGI_NUM_SHARD", "1"))
    TGI_MAX_BATCH_PREFILL_TOKENS: int = int(os.getenv("TGI_MAX_BATCH_PREFILL_TOKENS", "4096"))
    TGI_MAX_INPUT_LENGTH: int = int(os.getenv("TGI_MAX_INPUT_LENGTH", "4096"))
    TGI_MAX_TOTAL_TOKENS: int = int(os.getenv("TGI_MAX_TOTAL_TOKENS", "8192"))
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    # Vector Database (Qdrant - open source alternative to ChromaDB)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "fragments")
    
    # Alternative vector databases (if needed)
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "qdrant")  # qdrant, weaviate, faiss
    WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
    WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./faiss_index")
    JANUSGRAPH_RETRY_ATTEMPTS: int = int(os.getenv("JANUSGRAPH_RETRY_ATTEMPTS", "3"))
    
    # RAG Parameters - configurable via admin panel
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    FACT_CONFIDENCE_THRESHOLD: float = float(os.getenv("FACT_CONFIDENCE_THRESHOLD", "0.8"))
    GRAPH_MAX_DEPTH: int = int(os.getenv("GRAPH_MAX_DEPTH", "3"))
    GRAPH_MAX_PATHS: int = int(os.getenv("GRAPH_MAX_PATHS", "10"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    GRAFANA_ENABLED: bool = os.getenv("GRAFANA_ENABLED", "false").lower() == "true"
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4000"))
    
    # Search Parameters
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
    SEARCH_TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "30"))
    
    # Model Parameters
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
    
    # Performance Parameters
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()