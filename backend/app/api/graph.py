from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from app.db.models import RelationModel, EntityModel  # SQLAlchemy models
from app.db.models import Relation, Entity  # Pydantic models for response
from app.services.graph_service import GraphService
from app.services.sql_graph_service import SQLGraphService, get_sql_graph_service
from app.db.database import get_db
from app.services.janusgraph_service import janusgraph_service
from app.db.database_models import Fact as FactModel, Fragment as FragmentModel
from app.services.graph_consistency_service import GraphConsistencyService

router = APIRouter()

def get_graph_service(db: Session = Depends(get_db)) -> GraphService:
    return GraphService(db)

def get_sql_graph_service_dep(db: Session = Depends(get_db)):
    return get_sql_graph_service(db)

@router.get("/relations", response_model=List[Relation])
async def get_relations(
    skip: int = 0, 
    limit: int = 100, 
    source_entity_id: Optional[int] = None,
    target_entity_id: Optional[int] = None,
    relation_type: Optional[str] = None,
    service: GraphService = Depends(get_graph_service)
):
    """Pobierz listę relacji z opcjonalnym filtrowaniem"""
    return service.get_relations(skip=skip, limit=limit, 
                               source_entity_id=source_entity_id,
                               target_entity_id=target_entity_id,
                               relation_type=relation_type)

@router.post("/relations", response_model=Relation)
async def create_relation(
    source_entity_id: int,
    target_entity_id: int,
    relation_type: str,
    weight: float = 0.8,
    sql_service: SQLGraphService = Depends(get_sql_graph_service_dep)
):
    """Dodaj nową relację"""
    success = sql_service.upsert_relation(
        source_id=str(source_entity_id),
        target_id=str(target_entity_id),
        relation_type=relation_type,
        weight=weight
    )
    if not success:
        raise HTTPException(status_code=400, detail="Nie udało się utworzyć relacji")
    
    # Pobierz utworzoną relację
    from app.db.database_models import Relation as RelationModel
    db = next(get_db())
    relation = db.query(RelationModel).filter(
        RelationModel.source_entity_id == source_entity_id,
        RelationModel.target_entity_id == target_entity_id,
        RelationModel.relation_type == relation_type
    ).first()
    
    if not relation:
        raise HTTPException(status_code=500, detail="Relacja została utworzona, ale nie można jej pobrać")
    
    return relation

@router.get("/relations/{relation_id}", response_model=Relation)
async def get_relation(relation_id: int, service: GraphService = Depends(get_graph_service)):
    """Pobierz szczegóły relacji"""
    relation = service.get_relation(relation_id=relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relacja nie znaleziona")
    return relation

@router.get("/relations/{relation_id}/evidence", response_model=Dict[str, Any])
async def get_relation_evidence(
    relation_id: int,
    db: Session = Depends(get_db)
):
    """Zwróć listę faktów będących dowodami dla relacji."""
    from app.db.database_models import Relation as RelationModel
    rel = db.query(RelationModel).filter(RelationModel.id == relation_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relacja nie znaleziona")
    facts = getattr(rel, 'evidence_facts', []) or []
    return {
        "relation_id": relation_id,
        "evidence": [
            {
                "id": f.id,
                "content": f.content,
                "confidence": float(f.confidence or 0.0),
                "source_fragment_id": f.source_fragment_id,
            }
            for f in facts
        ],
        "count": len(facts),
    }

@router.put("/relations/{relation_id}", response_model=Relation)
async def update_relation(
    relation_id: int,
    relation_type: Optional[str] = None,
    weight: Optional[float] = None,
    metadata: Optional[dict] = None,
    sql_service: SQLGraphService = Depends(get_sql_graph_service_dep)
):
    """Aktualizuj relację"""
    relation = sql_service.update_relation(
        relation_id=relation_id, 
        relation_type=relation_type,
        weight=weight,
        metadata=metadata
    )
    if not relation:
        raise HTTPException(status_code=404, detail="Relacja nie znaleziona")
    return relation

@router.delete("/relations/{relation_id}")
async def delete_relation(relation_id: int, service: GraphService = Depends(get_graph_service)):
    """Usuń relację"""
    success = service.delete_relation(relation_id=relation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relacja nie znaleziona")
    return {"message": "Relacja usunięta"}

@router.get("/subgraph/{entity_id}")
async def get_entity_subgraph(
    entity_id: int,
    depth: int = 1,
    service: GraphService = Depends(get_graph_service)
):
    """Pobierz podgraf dla encji"""
    subgraph = service.get_entity_subgraph(entity_id=entity_id, depth=depth)
    if not subgraph:
        raise HTTPException(status_code=404, detail="Encja nie znaleziona")
    return subgraph

@router.get("/paths")
async def find_paths_between_entities(
    source_entity_id: int,
    target_entity_id: int,
    max_length: int = 3,
    service: GraphService = Depends(get_graph_service)
):
    """Znajdź ścieżki między encjami"""
    paths = service.find_paths(source_id=source_entity_id,
                              target_id=target_entity_id,
                              max_depth=max_length)
    if not paths:
        raise HTTPException(status_code=404, detail="Nie znaleziono ścieżek między encjami")
    return {"paths": paths}

@router.post("/promote-path")
async def promote_path_to_justification(
    path_nodes: List[int],
    path_relations: List[int],
    service: GraphService = Depends(get_graph_service)
):
    """Promuj ścieżkę do uzasadnienia"""
    justification = service.promote_path_to_justification(path_nodes=path_nodes,
                                                        path_relations=path_relations)
    if not justification:
        raise HTTPException(status_code=400, detail="Nie można utworzyć uzasadnienia")
    return {"justification": justification}

@router.get("/visualization")
async def get_graph_visualization_data(service: GraphService = Depends(get_graph_service)):
    """Pobierz dane do wizualizacji grafu"""
    data = service.get_graph_visualization_data()
    return data

# Nowe endpointy dla pełnej edycji grafu
@router.get("/entities", response_model=List[Dict[str, Any]])
async def get_graph_entities(
    skip: int = 0,
    limit: int = 100,
    name_pattern: Optional[str] = None,
    sql_service = Depends(get_sql_graph_service_dep)
):
    """Pobierz listę encji z grafu wiedzy"""
    try:
        entities = sql_service.find_vertices(
            name_pattern=name_pattern,
            limit=limit
        )
        return entities[skip:skip+limit] if entities else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania encji: {str(e)}")

@router.post("/entities")
async def create_graph_entity(
    name: str,
    entity_type: str,
    aliases: List[str] = [],
    sql_service = Depends(get_sql_graph_service_dep)
):
    """Utwórz nową encję w grafie wiedzy"""
    try:
        entity_id = sql_service.upsert_entity(
            name=name,
            entity_type=entity_type,
            aliases=aliases
        )
        if entity_id:
            return {"id": entity_id, "name": name, "type": entity_type, "aliases": aliases}
        else:
            raise HTTPException(status_code=400, detail="Nie udało się utworzyć encji")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd tworzenia encji: {str(e)}")

@router.put("/entities/{entity_id}")
async def update_graph_entity(
    entity_id: int,
    name: Optional[str] = None,
    entity_type: Optional[str] = None,
    aliases: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """Aktualizuj encję w grafie wiedzy"""
    try:
        from app.db.database_models import Entity as EntityModel
        
        entity = db.query(EntityModel).filter(EntityModel.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Encja nie znaleziona")
        
        if name is not None:
            entity.name = name
        if entity_type is not None:
            entity.type = entity_type
        if aliases is not None:
            entity.aliases = aliases
        
        entity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(entity)
        
        return {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "aliases": entity.aliases
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd aktualizacji encji: {str(e)}")

@router.delete("/entities/{entity_id}")
async def delete_graph_entity(
    entity_id: int,
    db: Session = Depends(get_db)
):
    """Usuń encję z grafu wiedzy"""
    try:
        from app.db.database_models import Entity as EntityModel, Relation as RelationModel
        
        # Usuń wszystkie relacje związane z encją
        db.query(RelationModel).filter(
            or_(RelationModel.source_entity_id == entity_id,
                RelationModel.target_entity_id == entity_id)
        ).delete()
        
        # Usuń encję
        entity = db.query(EntityModel).filter(EntityModel.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Encja nie znaleziona")
        
        db.delete(entity)
        db.commit()
        
        return {"message": "Encja usunięta"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd usuwania encji: {str(e)}")

@router.get("/entities/{entity_id}/neighbors")
async def get_entity_neighbors(
    entity_id: int,
    depth: int = 1,
    sql_service = Depends(get_sql_graph_service_dep)
):
    """Pobierz sąsiadów encji do określonej głębokości"""
    try:
        neighbors = sql_service.get_entity_neighbors(entity_id, depth)
        return neighbors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania sąsiadów encji: {str(e)}")

@router.get("/statistics")
async def get_graph_statistics(sql_service = Depends(get_sql_graph_service_dep)):
    """Pobierz statystyki grafu wiedzy"""
    try:
        stats = sql_service.get_graph_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania statystyk: {str(e)}")


@router.get("/consistency/report", response_model=Dict[str, Any])
async def get_consistency_report(
    orphans_limit: int = 100,
    edges_no_evidence_limit: int = 200,
    type_issues_limit: int = 200,
    db: Session = Depends(get_db)
):
    """Raport spójności grafu (osierocone węzły, krawędzie bez dowodów, problemy z typami)."""
    svc = GraphConsistencyService(db)
    report = svc.report({
        "orphans": orphans_limit,
        "edges_no_evidence": edges_no_evidence_limit,
        "type_issues": type_issues_limit,
    })
    return report


@router.post("/rebuild")
async def rebuild_graph(
    article_id: Optional[int] = None,
    relation_type: str = "powiązany",
    db: Session = Depends(get_db),
):
    """Przebudowuje graf wiedzy w JanusGraph z istniejących faktów w bazie SQL.

    - Jeśli podano `article_id`, przebudowa dotyczy tylko faktów związanych z tym artykułem.
    - W przeciwnym razie przebudowywane są wszystkie fakty.
    """
    if not janusgraph_service.is_connected():
        raise HTTPException(status_code=503, detail="JanusGraph niedostępny")

    q = db.query(FactModel)
    if article_id is not None:
        q = q.join(FragmentModel).filter(FragmentModel.article_id == article_id)

    facts = q.all()
    created_entities = 0
    created_relations = 0
    processed_facts = 0
    errors: list[str] = []

    for fact in facts:
        try:
            entities = list(fact.entities or [])
            if len(entities) < 2:
                continue
            subj = entities[0]
            obj = entities[1]
            sid = janusgraph_service.upsert_entity(
                name=subj.name,
                entity_type=subj.type or "UNKNOWN",
                aliases=subj.aliases or None,
            )
            oid = janusgraph_service.upsert_entity(
                name=obj.name,
                entity_type=obj.type or "UNKNOWN",
                aliases=obj.aliases or None,
            )
            if sid:
                created_entities += 1
            if oid:
                created_entities += 1
            if sid and oid:
                if janusgraph_service.upsert_relation(
                    source_id=sid,
                    target_id=oid,
                    relation_type=relation_type,
                    weight=float(fact.confidence or 0.6),
                    evidence_fact_id=fact.id,
                ):
                    created_relations += 1
            processed_facts += 1
        except Exception as exc:  # pragma: no cover
            errors.append(str(exc))

    return {
        "article_id": article_id,
        "facts_processed": processed_facts,
        "entities_upserted": created_entities,
        "relations_upserted": created_relations,
        "errors": errors,
    }
