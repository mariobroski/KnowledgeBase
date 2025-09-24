from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.analytics_service import AnalyticsService
from app.db.database import get_db

router = APIRouter()

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/dashboard")
async def get_dashboard_data(service: AnalyticsService = Depends(get_analytics_service)):
    """Pobierz dane do dashboardu"""
    return service.get_dashboard_data()

@router.get("/metrics")
async def get_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    policy: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Pobierz metryki systemu"""
    return service.get_metrics(start_date=start_date, end_date=end_date, policy=policy)

@router.get("/metrics/quality")
async def get_quality_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    policy: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Pobierz metryki jakości odpowiedzi"""
    return service.get_quality_metrics(start_date=start_date, end_date=end_date, policy=policy)

@router.get("/metrics/performance")
async def get_performance_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    policy: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Pobierz metryki wydajności"""
    return service.get_performance_metrics(start_date=start_date, end_date=end_date, policy=policy)

@router.get("/metrics/cost")
async def get_cost_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    policy: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Pobierz metryki kosztów"""
    return service.get_cost_metrics(start_date=start_date, end_date=end_date, policy=policy)

@router.get("/metrics/comparison")
async def compare_policies(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Porównaj różne polityki RAG"""
    return service.compare_policies(start_date=start_date, end_date=end_date)