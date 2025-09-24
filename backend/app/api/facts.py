from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Fact, Entity  # Pydantic models for response
from app.db.models import Fact as FactModel, Entity as EntityModel  # SQLAlchemy models
from app.services.fact_service import FactService
from app.db.database import get_db

router = APIRouter()

def get_fact_service(db: Session = Depends(get_db)) -> FactService:
    return FactService(db)

@router.get("/facts", response_model=List[Fact])
async def get_facts(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    article_id: Optional[int] = None,
    entity_id: Optional[int] = None,
    service: FactService = Depends(get_fact_service)
):
    """Pobierz listę faktów z opcjonalnym filtrowaniem"""
    return service.get_facts(skip=skip, limit=limit)

@router.post("/facts", response_model=Fact)
async def create_fact(
    content: str,
    source_fragment_id: int,
    status: str = "oczekujący",
    entity_ids: List[int] = [],
    service: FactService = Depends(get_fact_service)
):
    """Dodaj nowy fakt"""
    fact_data = {
        "content": content,
        "source_fragment_id": source_fragment_id,
        "status": status,
        "entity_ids": entity_ids
    }
    return service.create_fact(fact_data=fact_data)

@router.get("/facts/{fact_id}", response_model=Fact)
async def get_fact(fact_id: int, service: FactService = Depends(get_fact_service)):
    """Pobierz szczegóły faktu"""
    fact = service.get_fact(fact_id=fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fakt nie znaleziony")
    return fact

@router.put("/facts/{fact_id}", response_model=Fact)
async def update_fact(
    fact_id: int,
    content: Optional[str] = None,
    status: Optional[str] = None,
    entity_ids: List[int] = [],
    service: FactService = Depends(get_fact_service)
):
    """Aktualizuj fakt"""
    fact = service.update_fact(fact_id=fact_id, content=content, status=status, entity_ids=entity_ids)
    if not fact:
        raise HTTPException(status_code=404, detail="Fakt nie znaleziony")
    return fact

@router.delete("/facts/{fact_id}")
async def delete_fact(fact_id: int, service: FactService = Depends(get_fact_service)):
    """Usuń fakt"""
    success = service.delete_fact(fact_id=fact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fakt nie znaleziony")
    return {"message": "Fakt usunięty"}

# Endpointy dla encji
@router.get("/entities", response_model=List[Entity])
async def get_entities(
    skip: int = 0, 
    limit: int = 100, 
    name: Optional[str] = None,
    service: FactService = Depends(get_fact_service)
):
    """Pobierz listę encji z opcjonalnym filtrowaniem"""
    return service.get_entities(skip=skip, limit=limit)

@router.post("/entities", response_model=Entity)
async def create_entity(
    name: str,
    aliases: List[str] = [],
    type: Optional[str] = None,
    service: FactService = Depends(get_fact_service)
):
    """Dodaj nową encję"""
    entity_data = {
        "name": name,
        "aliases": aliases,
        "type": type
    }
    return service.create_entity(entity_data=entity_data)

@router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(entity_id: int, service: FactService = Depends(get_fact_service)):
    """Pobierz szczegóły encji"""
    entity = service.get_entity(entity_id=entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Encja nie znaleziona")
    return entity

@router.put("/entities/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: int,
    name: Optional[str] = None,
    aliases: List[str] = [],
    type: Optional[str] = None,
    service: FactService = Depends(get_fact_service)
):
    """Aktualizuj encję"""
    entity = service.update_entity(entity_id=entity_id, name=name, aliases=aliases, type=type)
    if not entity:
        raise HTTPException(status_code=404, detail="Encja nie znaleziona")
    return entity

@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: int, service: FactService = Depends(get_fact_service)):
    """Usuń encję"""
    success = service.delete_entity(entity_id=entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Encja nie znaleziona")
    return {"message": "Encja usunięta"}

@router.post("/entities/merge")
async def merge_entities(
    source_entity_id: int,
    target_entity_id: int,
    service: FactService = Depends(get_fact_service)
):
    """Połącz dwie encje"""
    success = service.merge_entities(source_entity_id=source_entity_id, target_entity_id=target_entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Jedna z encji nie znaleziona")
    return {"message": "Encje połączone"}

@router.post("/extract-facts")
async def extract_facts_from_fragment(
    fragment_id: int,
    service: FactService = Depends(get_fact_service)
):
    """Wyodrębnij fakty z fragmentu"""
    facts = service.extract_facts_from_fragment(fragment_id=fragment_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Fragment nie znaleziony")
    return {"facts": facts}