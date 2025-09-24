"""
Modele danych dla benchmarków RAG (RAGBench, FinanceBench)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

Base = declarative_base()

class BenchmarkResult(Base):
    """Wyniki ewaluacji na benchmarkach"""
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True)
    benchmark_name = Column(String(50), nullable=False)  # "ragbench" | "financebench"
    domain = Column(String(50))                          # "finqa" | "tat-qa" | "techqa" | "cuad"
    policy = Column(String(20), nullable=False)          # "text" | "facts" | "graph"
    
    # Metryki TRACe
    relevance = Column(Float)      # Jakość retrievera (0-1)
    utilization = Column(Float)    # Wykorzystanie kontekstu (0-1)
    adherence = Column(Float)      # Faithfulness/unikanie halucynacji (0-1)
    completeness = Column(Float)   # Kompletność odpowiedzi (0-1)
    
    # Metryki wydajności
    latency_p50 = Column(Float)           # Mediana czasu odpowiedzi (ms)
    latency_p95 = Column(Float)           # 95 percentyl czasu (ms)
    avg_search_time = Column(Float)       # Średni czas wyszukiwania (ms)
    avg_generation_time = Column(Float)   # Średni czas generowania (ms)
    
    # Metryki kosztów
    tokens_per_query = Column(Integer)    # Średnia liczba tokenów na zapytanie
    cost_per_query = Column(Float)        # Średni koszt na zapytanie ($)
    total_queries = Column(Integer)       # Liczba przetworzonych zapytań
    
    # Metryki dodatkowe
    hallucination_rate = Column(Float)    # Poziom halucynacji (0-1)
    factual_accuracy = Column(Float)      # Dokładność faktyczna (0-1)
    
    # Metadane
    created_at = Column(DateTime, default=datetime.utcnow)
    evaluation_config = Column(JSON)      # Konfiguracja ewaluacji
    notes = Column(Text)                  # Dodatkowe notatki

class BenchmarkDataset(Base):
    """Informacje o załadowanych datasetach benchmarków"""
    __tablename__ = "benchmark_datasets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)     # "ragbench_finqa" | "financebench"
    domain = Column(String(50))                    # Domena datasetu
    version = Column(String(20))                   # Wersja datasetu
    
    # Statystyki datasetu
    total_documents = Column(Integer)              # Liczba dokumentów
    total_queries = Column(Integer)                # Liczba zapytań
    avg_doc_length = Column(Float)                 # Średnia długość dokumentu
    
    # Status
    is_indexed = Column(Boolean, default=False)    # Czy zindeksowany
    indexed_at = Column(DateTime)                  # Kiedy zindeksowany
    
    # Metadane
    source_path = Column(String(500))              # Ścieżka do źródła
    description = Column(Text)                     # Opis datasetu
    created_at = Column(DateTime, default=datetime.utcnow)

class BenchmarkQuery(Base):
    """Pojedyncze zapytania z benchmarków z ground truth"""
    __tablename__ = "benchmark_queries"
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, nullable=False)   # FK do BenchmarkDataset
    
    # Dane zapytania
    query_id = Column(String(100))                 # ID z oryginalnego benchmarku
    question = Column(Text, nullable=False)        # Treść pytania
    context_documents = Column(JSON)               # Lista ID dokumentów kontekstu
    
    # Ground truth dla TRACe
    relevant_spans = Column(JSON)                  # Relevantne fragmenty tekstu
    expected_answer = Column(Text)                 # Oczekiwana odpowiedź
    adherence_labels = Column(JSON)                # Etykiety faithfulness
    completeness_criteria = Column(JSON)           # Kryteria kompletności
    
    # Metadane
    difficulty_level = Column(String(20))          # "easy" | "medium" | "hard"
    question_type = Column(String(50))             # Typ pytania
    domain_specific_tags = Column(JSON)            # Tagi specyficzne dla domeny

# Pydantic modele dla API

class TRACeMetrics(BaseModel):
    """Metryki TRACe"""
    relevance: float        # 0-1, jakość retrievera
    utilization: float      # 0-1, wykorzystanie kontekstu
    adherence: float        # 0-1, faithfulness
    completeness: float     # 0-1, kompletność odpowiedzi

class PerformanceMetrics(BaseModel):
    """Metryki wydajności"""
    latency_p50: float           # ms
    latency_p95: float           # ms
    avg_search_time: float       # ms
    avg_generation_time: float   # ms
    tokens_per_query: int
    cost_per_query: float        # $

class BenchmarkDatasetCreate(BaseModel):
    """Request do tworzenia datasetu benchmarku"""
    name: str
    domain: str
    version: str = "1.0"
    source_path: str
    description: Optional[str] = None

class BenchmarkEvaluationRequest(BaseModel):
    """Request do ewaluacji benchmarku"""
    benchmark_name: str          # "ragbench" | "financebench"
    domain: Optional[str]        # "finqa" | "tat-qa" | etc.
    policy: str                  # "text" | "facts" | "graph"
    max_queries: Optional[int] = 100  # Limit zapytań do ewaluacji
    config: Optional[Dict[str, Any]] = {}  # Dodatkowa konfiguracja

class BenchmarkEvaluationResponse(BaseModel):
    """Response z wynikami ewaluacji"""
    evaluation_id: int
    benchmark_name: str
    domain: Optional[str]
    policy: str
    
    # Wyniki
    trace_metrics: TRACeMetrics
    performance_metrics: PerformanceMetrics
    
    # Statystyki
    total_queries_processed: int
    success_rate: float          # Odsetek udanych zapytań
    
    # Porównanie z baseline (jeśli dostępne)
    baseline_comparison: Optional[Dict[str, float]] = None

class BenchmarkComparisonRequest(BaseModel):
    """Request do porównania wyników"""
    benchmark_name: str
    domains: List[str]
    policies: List[str]
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class PolicyComparisonResult(BaseModel):
    """Wynik porównania polityk"""
    policy: str
    trace_metrics: TRACeMetrics
    performance_metrics: PerformanceMetrics
    
    # Delty względem baseline (Text-RAG)
    adherence_delta: Optional[float] = None      # % zmiana
    tokens_delta: Optional[float] = None         # % zmiana
    latency_delta: Optional[float] = None        # % zmiana

class DomainComparisonResult(BaseModel):
    """Wynik porównania domen"""
    domain: str
    policies: List[PolicyComparisonResult]
    
    # Statystyki domeny
    avg_query_complexity: float
    document_coverage: float     # % dokumentów wykorzystanych

class BenchmarkSummaryReport(BaseModel):
    """Raport podsumowujący wyniki benchmarków"""
    
    # Wyniki RAGBench
    ragbench_results: List[DomainComparisonResult]
    
    # Wyniki FinanceBench
    financebench_results: List[PolicyComparisonResult]
    
    # Porównanie z literaturą
    literature_comparison: Dict[str, Any]
    
    # Wnioski
    key_findings: List[str]
    recommendations: List[str]
    
    # Metadane raportu
    generated_at: datetime
    evaluation_period: str
    total_queries_evaluated: int

# Konfiguracje dla różnych benchmarków

RAGBENCH_DOMAINS = {
    "finqa": {
        "name": "FinQA",
        "description": "Financial Question Answering",
        "expected_queries": 8000,
        "focus_areas": ["numerical_reasoning", "financial_concepts"]
    },
    "tat-qa": {
        "name": "TAT-QA", 
        "description": "Table and Text Question Answering",
        "expected_queries": 16500,
        "focus_areas": ["table_reasoning", "hybrid_qa"]
    },
    "techqa": {
        "name": "TechQA",
        "description": "Technical Documentation QA",
        "expected_queries": 600,
        "focus_areas": ["technical_knowledge", "procedural_qa"]
    },
    "cuad": {
        "name": "CUAD",
        "description": "Contract Understanding Atticus Dataset",
        "expected_queries": 500,
        "focus_areas": ["legal_reasoning", "contract_analysis"]
    }
}

TRACE_METRIC_THRESHOLDS = {
    "excellent": {"relevance": 0.9, "utilization": 0.85, "adherence": 0.9, "completeness": 0.85},
    "good": {"relevance": 0.8, "utilization": 0.75, "adherence": 0.8, "completeness": 0.75},
    "acceptable": {"relevance": 0.7, "utilization": 0.65, "adherence": 0.7, "completeness": 0.65},
    "poor": {"relevance": 0.6, "utilization": 0.55, "adherence": 0.6, "completeness": 0.55}
}

PERFORMANCE_SLO = {
    "latency_p95_ms": 2000,      # p95 ≤ 2s
    "token_reduction_pct": 30,    # ≥30% oszczędność vs Text-RAG
    "min_adherence": 0.85         # ≥0.85 adherence dla Graph-RAG
}