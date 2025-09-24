from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
import psutil
import time
import os
from datetime import datetime, timedelta
import shutil
import sqlite3
import json
import logging

from ..db.database import get_db
from ..db.models import UserModel, ArticleModel, FactModel, EntityModel, RelationModel
from ..schemas.system_settings import SystemSettingsResponse, SystemSettingsUpdate
from ..core.config import settings
from ..services.sql_graph_service import get_sql_graph_service
from ..services.fact_service import FactService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/system-stats")
async def get_system_stats(
    db: Session = Depends(get_db)
):
    """Pobiera statystyki aplikacji"""
    try:
        # Statystyki aplikacji zamiast systemu
        articles_count = db.query(func.count(ArticleModel.id)).scalar()
        facts_count = db.query(func.count(FactModel.id)).scalar()
        entities_count = db.query(func.count(EntityModel.id)).scalar()
        relations_count = db.query(func.count(RelationModel.id)).scalar()
        users_count = db.query(func.count(UserModel.id)).scalar()
        
        # Statystyki aktywności (ostatnie 30 dni)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_articles = db.query(func.count(ArticleModel.id)).filter(
            ArticleModel.created_at >= thirty_days_ago
        ).scalar()
        
        recent_users = db.query(func.count(UserModel.id)).filter(
            UserModel.created_at >= thirty_days_ago
        ).scalar()
        
        # Rozmiar bazy danych
        db_path = "app.db"
        db_size_mb = 0
        if os.path.exists(db_path):
            db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        
        # Status aplikacji
        app_status = "healthy"
        if articles_count == 0:
            app_status = "no_content"
        elif users_count == 1:  # tylko admin
            app_status = "setup_needed"
        
        return {
            "app_status": app_status,
            "total_articles": articles_count,
            "total_facts": facts_count,
            "total_entities": entities_count,
            "total_relations": relations_count,
            "total_users": users_count,
            "recent_articles_30d": recent_articles,
            "recent_users_30d": recent_users,
            "database_size_mb": db_size_mb,
            "knowledge_graph_density": round(relations_count / max(entities_count, 1), 2),
            "avg_facts_per_article": round(facts_count / max(articles_count, 1), 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania statystyk aplikacji: {str(e)}"
        )

@router.get("/users-stats")
async def get_users_stats(
    db: Session = Depends(get_db)
):
    """Pobiera szczegółowe statystyki użytkowników"""
    try:
        # Łączna liczba użytkowników
        total_users = db.query(func.count(UserModel.id)).scalar()
        
        # Użytkownicy według ról (poprawione nazwy ról)
        admin_users = db.query(func.count(UserModel.id)).filter(UserModel.role == "administrator").scalar()
        editor_users = db.query(func.count(UserModel.id)).filter(UserModel.role == "editor").scalar()
        regular_users = db.query(func.count(UserModel.id)).filter(UserModel.role == "user").scalar()
        
        # Aktywni użytkownicy (zalogowani w ostatnich 7 dniach)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(func.count(UserModel.id)).filter(
            UserModel.last_login >= week_ago
        ).scalar()
        
        # Nowi użytkownicy w ostatnim miesiącu
        month_ago = datetime.utcnow() - timedelta(days=30)
        new_users_month = db.query(func.count(UserModel.id)).filter(
            UserModel.created_at >= month_ago
        ).scalar()
        
        # Zweryfikowani użytkownicy
        verified_users = db.query(func.count(UserModel.id)).filter(
            UserModel.is_verified == True
        ).scalar()
        
        # Nieaktywni użytkownicy
        inactive_users = db.query(func.count(UserModel.id)).filter(
            UserModel.is_active == False
        ).scalar()
        
        return {
            "total_users": total_users,
            "active_users_7d": active_users,
            "admin_users": admin_users,
            "editor_users": editor_users,
            "regular_users": regular_users,
            "new_users_30d": new_users_month,
            "verified_users": verified_users,
            "inactive_users": inactive_users,
            "verification_rate": round((verified_users / max(total_users, 1)) * 100, 1),
            "activity_rate": round((active_users / max(total_users, 1)) * 100, 1)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania statystyk użytkowników: {str(e)}"
        )

@router.get("/database-stats")
async def get_database_stats(
    db: Session = Depends(get_db)
):
    """Pobiera statystyki bazy danych"""
    try:
        # Liczba rekordów w tabelach
        articles_count = db.query(func.count(ArticleModel.id)).scalar()
        facts_count = db.query(func.count(FactModel.id)).scalar()
        entities_count = db.query(func.count(EntityModel.id)).scalar()
        relations_count = db.query(func.count(RelationModel.id)).scalar()
        users_count = db.query(func.count(UserModel.id)).scalar()
        
        # Rozmiar bazy danych
        db_path = "app.db"  # Ścieżka do bazy SQLite
        db_size_mb = 0
        if os.path.exists(db_path):
            db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        
        return {
            "articles": articles_count,
            "facts": facts_count,
            "entities": entities_count,
            "relations": relations_count,
            "users": users_count,
            "database_size_mb": db_size_mb,
            "total_records": articles_count + facts_count + entities_count + relations_count + users_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania statystyk bazy danych: {str(e)}"
        )


@router.get("/graph/status")
async def graph_status(db: Session = Depends(get_db)):
    """Sprawdź status połączenia z grafem wiedzy"""
    try:
        graph_service = get_sql_graph_service(db)
        is_connected = graph_service.test_connection()
        return {
            "status": "connected" if is_connected else "disconnected",
            "message": "Graf wiedzy jest dostępny" if is_connected else "Brak połączenia z grafem wiedzy"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Błąd podczas sprawdzania połączenia: {str(e)}"
        }


@router.post("/graph/rebuild")
async def rebuild_graph(db: Session = Depends(get_db)):
    """Odbuduj graf wiedzy z istniejących faktów z wykorzystaniem nowych typów relacji"""
    try:
        from app.services.fact_extraction_service import FactExtractionService
        from app.services.graph_update_service import graph_update_service
        from app.db.models import FactModel
        
        fact_service = FactService(db)
        fact_extraction_service = FactExtractionService()
        
        # Ustaw sesję bazy danych dla graph_update_service
        graph_update_service.set_db_session(db)
        
        # Sprawdź, czy GraphUpdateService jest włączony
        if not graph_update_service.is_enabled:
            raise HTTPException(status_code=503, detail="Graph update service is not available")
        
        # Pobierz wszystkie istniejące fakty z bazy danych
        existing_facts = db.query(FactModel).all()
        
        # Użyj GraphUpdateService do aktualizacji grafu z istniejącymi faktami
        result = graph_update_service.update_graph_from_facts(existing_facts)
        
        # Sprawdź, czy wystąpił błąd w GraphUpdateService
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"Graph update service error: {result['error']}")
        
        return {
            "message": f"Odbudowano graf z {result.get('relations_created', 0)} relacji i {result.get('entities_created', 0)} encji",
            "entities_created": result.get('entities_created', 0),
            "relations_created": result.get('relations_created', 0),
            "total_facts_processed": len(existing_facts),
            "errors": result.get('errors', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas odbudowy grafu: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas odbudowy grafu: {str(e)}")


@router.get("/graph/stats")
async def graph_stats(db: Session = Depends(get_db)):
    """Pobierz statystyki grafu wiedzy"""
    try:
        graph_service = get_sql_graph_service(db)
        
        # Pobierz statystyki z serwisu grafu
        stats = graph_service.get_graph_statistics()
        
        return {
            "entities": stats.get("entity_count", 0),
            "relations": stats.get("relation_count", 0),
            "entity_types": stats.get("entity_types", {}),
            "relation_types": stats.get("relation_types", {}),
            "status": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania statystyk grafu: {str(e)}"
        )


@router.post("/graph/seed-demo")
async def graph_seed_demo(variant: str = "medium", db: Session = Depends(get_db)):
    """Dodaje rozbudowane przykładowe dane grafowe

    variant: small | medium | large
    """
    try:
        graph_service = get_sql_graph_service(db)
        
        # Dodaj przykładowe encje
        entities = []
        if variant == "small":
            entity_data = [
                ("Jan Kowalski", "PERSON"),
                ("Warszawa", "LOCATION"),
                ("Python", "TECHNOLOGY")
            ]
        elif variant == "medium":
            entity_data = [
                ("Jan Kowalski", "PERSON"),
                ("Anna Nowak", "PERSON"),
                ("Warszawa", "LOCATION"),
                ("Kraków", "LOCATION"),
                ("Python", "TECHNOLOGY"),
                ("JavaScript", "TECHNOLOGY"),
                ("Uniwersytet Warszawski", "ORGANIZATION")
            ]
        else:  # large
            entity_data = [
                ("Jan Kowalski", "PERSON"),
                ("Anna Nowak", "PERSON"),
                ("Piotr Wiśniewski", "PERSON"),
                ("Warszawa", "LOCATION"),
                ("Kraków", "LOCATION"),
                ("Gdańsk", "LOCATION"),
                ("Python", "TECHNOLOGY"),
                ("JavaScript", "TECHNOLOGY"),
                ("React", "TECHNOLOGY"),
                ("Uniwersytet Warszawski", "ORGANIZATION"),
                ("Google", "ORGANIZATION"),
                ("Microsoft", "ORGANIZATION")
            ]
        
        for name, entity_type in entity_data:
            entity_id = graph_service.upsert_entity(name=name, entity_type=entity_type)
            entities.append(entity_id)
        
        # Dodaj przykładowe relacje
        relations_count = 0
        if len(entities) >= 2:
            # Dodaj kilka przykładowych relacji
            for i in range(0, len(entities) - 1, 2):
                if i + 1 < len(entities):
                    graph_service.upsert_relation(
                        source_id=entities[i],
                        target_id=entities[i + 1],
                        relation_type="powiązany",
                        weight=0.8
                    )
                    relations_count += 1
        
        return {
            "variant": variant,
            "message": f"Dodano przykładowe dane grafowe ({variant})",
            "details": {
                "entities_added": len(entities),
                "relations_added": relations_count
            }
        }
    except Exception as e:
        logger.error(f"Błąd podczas dodawania przykładowych danych: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Błąd podczas dodawania przykładowych danych: {str(e)}"
        )

# Globalna zmienna do przechowywania stanu konserwacji
maintenance_mode = False

@router.get("/maintenance-status")
async def get_maintenance_status():
    """Sprawdza status trybu konserwacji"""
    return {"maintenance_mode": maintenance_mode}

@router.post("/maintenance/enable")
async def enable_maintenance_mode():
    """Włącza tryb konserwacji"""
    global maintenance_mode
    maintenance_mode = True
    return {"message": "Tryb konserwacji został włączony", "maintenance_mode": True}

@router.post("/maintenance/disable")
async def disable_maintenance_mode():
    """Wyłącza tryb konserwacji"""
    global maintenance_mode
    maintenance_mode = False
    return {"message": "Tryb konserwacji został wyłączony", "maintenance_mode": False}

@router.post("/backup/create")
async def create_backup():
    """Tworzy kopię zapasową bazy danych"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = f"backups/{backup_filename}"
        
        # Utwórz katalog backups jeśli nie istnieje
        os.makedirs("backups", exist_ok=True)
        
        # Skopiuj bazę danych
        if os.path.exists("app.db"):
            shutil.copy2("app.db", backup_path)
            backup_size_mb = round(os.path.getsize(backup_path) / (1024 * 1024), 2)
            
            return {
                "message": "Kopia zapasowa została utworzona pomyślnie",
                "backup_filename": backup_filename,
                "backup_path": backup_path,
                "backup_size_mb": backup_size_mb,
                "created_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plik bazy danych nie został znaleziony"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas tworzenia kopii zapasowej: {str(e)}"
        )

@router.get("/backups/list")
async def list_backups():
    """Lista dostępnych kopii zapasowych"""
    try:
        backups_dir = "backups"
        if not os.path.exists(backups_dir):
            return {"backups": []}
        
        backups = []
        for filename in os.listdir(backups_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(backups_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    "filename": filename,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sortuj według daty utworzenia (najnowsze pierwsze)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania listy kopii zapasowych: {str(e)}"
        )


# System Settings Endpoints
@router.get("/system-settings", response_model=SystemSettingsResponse)
async def get_system_settings():
    """Pobiera aktualne ustawienia systemowe"""
    try:
        return SystemSettingsResponse(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            max_tokens=settings.MAX_TOKENS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
            top_k_results=settings.TOP_K_RESULTS,
            max_search_results=settings.MAX_SEARCH_RESULTS,
            search_timeout=settings.SEARCH_TIMEOUT,
            temperature=settings.TEMPERATURE,
            max_response_length=settings.MAX_RESPONSE_LENGTH,
            cache_ttl=settings.CACHE_TTL,
            batch_size=settings.BATCH_SIZE
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania ustawień systemowych: {str(e)}"
        )


@router.put("/system-settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_update: SystemSettingsUpdate
):
    """Aktualizuje ustawienia systemowe"""
    try:
        # Ścieżka do pliku .env
        env_file_path = ".env"
        
        # Wczytaj istniejące zmienne środowiskowe z pliku .env
        env_vars = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        # Aktualizuj zmienne środowiskowe na podstawie przesłanych danych
        update_data = settings_update.model_dump(exclude_unset=True)
        
        for field_name, value in update_data.items():
            env_key = field_name.upper()
            env_vars[env_key] = str(value)
            # Aktualizuj również w bieżącej sesji
            os.environ[env_key] = str(value)
            setattr(settings, env_key, value)
        
        # Zapisz zaktualizowane zmienne do pliku .env
        with open(env_file_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Zwróć zaktualizowane ustawienia
        return SystemSettingsResponse(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            max_tokens=settings.MAX_TOKENS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
            top_k_results=settings.TOP_K_RESULTS,
            max_search_results=settings.MAX_SEARCH_RESULTS,
            search_timeout=settings.SEARCH_TIMEOUT,
            temperature=settings.TEMPERATURE,
            max_response_length=settings.MAX_RESPONSE_LENGTH,
            cache_ttl=settings.CACHE_TTL,
            batch_size=settings.BATCH_SIZE
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas aktualizacji ustawień systemowych: {str(e)}"
        )


@router.post("/system-settings/reset")
async def reset_system_settings():
    """Resetuje ustawienia systemowe do wartości domyślnych"""
    try:
        # Domyślne wartości
        default_settings = {
            "CHUNK_SIZE": "1000",
            "CHUNK_OVERLAP": "200",
            "MAX_TOKENS": "4000",
            "SIMILARITY_THRESHOLD": "0.7",
            "TOP_K_RESULTS": "5",
            "MAX_SEARCH_RESULTS": "10",
            "SEARCH_TIMEOUT": "30",
            "TEMPERATURE": "0.7",
            "MAX_RESPONSE_LENGTH": "2000",
            "CACHE_TTL": "3600",
            "BATCH_SIZE": "10"
        }
        
        # Ścieżka do pliku .env
        env_file_path = ".env"
        
        # Wczytaj istniejące zmienne środowiskowe
        env_vars = {}
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        
        # Aktualizuj do wartości domyślnych
        for key, value in default_settings.items():
            env_vars[key] = value
            os.environ[key] = value
            setattr(settings, key, int(value) if value.isdigit() else float(value) if '.' in value else value)
        
        # Zapisz do pliku .env
        with open(env_file_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        return {"message": "Ustawienia systemowe zostały zresetowane do wartości domyślnych"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas resetowania ustawień systemowych: {str(e)}"
        )