"""
API endpoints dla benchmarków RAG
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.benchmarks import (
    BenchmarkDataset, BenchmarkEvaluationResponse, BenchmarkResult,
    DomainComparisonResult, BenchmarkSummaryReport, PolicyComparisonResult,
    BenchmarkDatasetCreate, BenchmarkEvaluationRequest, BenchmarkComparisonRequest
)
from app.services.benchmark_service import BenchmarkService
from app.services.search_service import SearchService
from app.services.analytics_service import AnalyticsService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


# Dependency injection
def get_benchmark_service() -> BenchmarkService:
    search_service = SearchService()
    analytics_service = AnalyticsService()
    return BenchmarkService(search_service, analytics_service)


@router.post("/datasets/ragbench/load")
async def load_ragbench_dataset(
    domain: str,
    dataset_path: str,
    background_tasks: BackgroundTasks,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Załaduj dataset RAGBench dla wybranej domeny
    
    Dostępne domeny:
    - finqa: Pytania finansowe
    - tat-qa: Tabele i tekst finansowy
    - techqa: Dokumentacja techniczna
    - cuad: Dokumenty prawne
    """
    try:
        # Uruchom ładowanie w tle
        background_tasks.add_task(
            benchmark_service.load_ragbench_dataset,
            domain,
            dataset_path
        )
        
        # Zwróć informacje o rozpoczętym procesie
        return BenchmarkDataset(
            name=f"ragbench_{domain}",
            domain=domain,
            version="1.0",
            total_documents=0,  # Będzie zaktualizowane po załadowaniu
            total_queries=0,
            source_path=dataset_path,
            description=f"RAGBench dataset dla domeny {domain}",
            is_indexed=False,
            created_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas ładowania datasetu: {str(e)}")


@router.post("/datasets/financebench/load")
async def load_financebench_dataset(
    dataset_path: str,
    background_tasks: BackgroundTasks,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Załaduj dataset FinanceBench
    """
    try:
        # Placeholder - implementacja podobna do RAGBench
        background_tasks.add_task(
            benchmark_service.load_ragbench_dataset,  # Będzie osobna metoda
            "finance",
            dataset_path
        )
        
        return BenchmarkDataset(
            name="financebench",
            domain="finance",
            version="1.0",
            total_documents=0,
            total_queries=0,
            source_path=dataset_path,
            description="FinanceBench dataset - realne dokumenty finansowe",
            is_indexed=False,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas ładowania FinanceBench: {str(e)}")


@router.get("/datasets")
async def list_benchmark_datasets(
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Lista dostępnych datasetów benchmarkowych
    """
    # Placeholder - w rzeczywistości pobierałby z bazy danych
    return [
        BenchmarkDataset(
            name="ragbench_finqa",
            domain="finqa",
            version="1.0",
            total_documents=1500,
            total_queries=300,
            source_path="/data/ragbench/finqa",
            description="RAGBench FinQA - pytania finansowe",
            is_indexed=True,
            created_at=datetime.utcnow()
        ),
        BenchmarkDataset(
            name="financebench",
            domain="finance",
            version="1.0",
            total_documents=2000,
            total_queries=500,
            source_path="/data/financebench",
            description="FinanceBench - dokumenty finansowe",
            is_indexed=True,
            created_at=datetime.utcnow()
        )
    ]


@router.post("/evaluate", response_model=BenchmarkEvaluationResponse)
async def evaluate_policy_on_benchmark(
    request: BenchmarkEvaluationRequest,
    background_tasks: BackgroundTasks,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Ewaluuj politykę RAG na wybranym benchmarku
    
    Przykład request body:
    {
        "benchmark_name": "ragbench",
        "domain": "finqa",
        "policy": "graph",
        "max_queries": 100,
        "policy_config": {
            "graph_max_depth": 3,
            "fact_confidence_threshold": 0.8
        }
    }
    """
    try:
        result = await benchmark_service.evaluate_policy_on_benchmark(
            benchmark_name=request.benchmark_name,
            domain=request.domain,
            policy=request.policy,
            max_queries=request.max_queries or 100
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas ewaluacji: {str(e)}")


@router.post("/compare", response_model=DomainComparisonResult)
async def compare_policies_on_benchmark(
    request: BenchmarkComparisonRequest,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Porównaj różne polityki RAG na tym samym benchmarku
    
    Przykład request body:
    {
        "benchmark_name": "ragbench",
        "domain": "finqa",
        "policies": ["text", "facts", "graph"],
        "max_queries_per_policy": 100
    }
    """
    try:
        result = await benchmark_service.compare_policies(
            benchmark_name=request.benchmark_name,
            domain=request.domain,
            policies=request.policies or ["text", "facts", "graph"]
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas porównania: {str(e)}")


@router.get("/results/{benchmark_name}")
async def get_benchmark_results(
    benchmark_name: str,
    domain: Optional[str] = None,
    policy: Optional[str] = None,
    limit: int = 50,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Pobierz historyczne wyniki benchmarków z filtrami
    """
    # Placeholder - w rzeczywistości pobierałby z bazy danych
    return []


@router.get("/results/{benchmark_name}/summary", response_model=Dict[str, Any])
async def get_benchmark_summary(
    benchmark_name: str,
    domain: Optional[str] = None,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Pobierz podsumowanie wyników benchmarku
    """
    # Placeholder - agregacja wyników
    return {
        "benchmark_name": benchmark_name,
        "domain": domain,
        "total_evaluations": 0,
        "avg_metrics": {
            "adherence": 0.0,
            "completeness": 0.0,
            "relevance": 0.0,
            "utilization": 0.0
        },
        "performance_summary": {
            "avg_latency_p95": 0.0,
            "avg_tokens_per_query": 0,
            "avg_cost_per_query": 0.0
        }
    }


@router.post("/reports/comprehensive", response_model=BenchmarkSummaryReport)
async def generate_comprehensive_report(
    background_tasks: BackgroundTasks,
    ragbench_domains: List[str] = ["finqa", "tat-qa"],
    include_financebench: bool = True,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Wygeneruj kompletny raport z wyników benchmarków
    
    Ten endpoint generuje raport porównawczy obejmujący:
    - Wyniki RAGBench dla wybranych domen
    - Wyniki FinanceBench (opcjonalnie)
    - Porównanie z literaturą (GraphRAG)
    - Kluczowe wnioski i rekomendacje
    """
    try:
        report = await benchmark_service.generate_benchmark_report(
            ragbench_domains=ragbench_domains,
            include_financebench=include_financebench
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas generowania raportu: {str(e)}")


@router.get("/metrics/trace/thresholds")
async def get_trace_metric_thresholds():
    """
    Pobierz progi metryk TRACe używane w ewaluacji
    """
    from app.models.benchmarks import TRACE_METRIC_THRESHOLDS
    return TRACE_METRIC_THRESHOLDS


@router.get("/slo/performance")
async def get_performance_slo():
    """
    Pobierz cele wydajnościowe (SLO) systemu
    """
    from app.models.benchmarks import PERFORMANCE_SLO
    return PERFORMANCE_SLO


@router.post("/export/results/{format}")
async def export_benchmark_results(
    format: str,  # csv, json, xlsx
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user),
    benchmark_name: Optional[str] = None,
    domain: Optional[str] = None,
    policy: Optional[str] = None
):
    """
    Eksportuj wyniki benchmarków w wybranym formacie
    """
    if format not in ["csv", "json", "xlsx"]:
        raise HTTPException(status_code=400, detail="Nieobsługiwany format eksportu")
    
    # Placeholder - implementacja eksportu
    return {"message": f"Eksport w formacie {format} zostanie wygenerowany"}


# Endpoints do monitorowania postępu ewaluacji

@router.get("/evaluation/{evaluation_id}/status")
async def get_evaluation_status(
    evaluation_id: str,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Sprawdź status trwającej ewaluacji
    """
    # Placeholder - sprawdzanie statusu zadania w tle
    return {
        "evaluation_id": evaluation_id,
        "status": "completed",  # pending, running, completed, failed
        "progress": 100,
        "queries_processed": 100,
        "total_queries": 100,
        "estimated_completion": None
    }


@router.delete("/evaluation/{evaluation_id}")
async def cancel_evaluation(
    evaluation_id: str,
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
    current_user = Depends(get_current_user)
):
    """
    Anuluj trwającą ewaluację
    """
    # Placeholder - anulowanie zadania w tle
    return {"message": f"Ewaluacja {evaluation_id} została anulowana"}