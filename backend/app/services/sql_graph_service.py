"""
Alternatywny serwis grafu wiedzy używający SQL zamiast JanusGraph
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging
from datetime import datetime

from app.db.database_models import Entity, Relation, Fact

logger = logging.getLogger(__name__)


class SQLGraphService:
    """Serwis grafu wiedzy używający SQL zamiast JanusGraph"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_connected(self) -> bool:
        """Sprawdza czy połączenie z bazą danych jest aktywne"""
        try:
            # Prosta próba zapytania do bazy
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Alias dla is_connected dla kompatybilności"""
        return self.is_connected()
    
    def upsert_entity(self, name: str, entity_type: str, aliases: Optional[List[str]] = None) -> Optional[str]:
        """Tworzy lub aktualizuje encję"""
        try:
            # Sprawdź czy encja już istnieje
            existing_entity = self.db.query(Entity).filter(Entity.name == name).first()
            
            if existing_entity:
                # Aktualizuj istniejącą encję
                existing_entity.type = entity_type
                if aliases:
                    existing_entity.aliases = aliases
                existing_entity.updated_at = datetime.utcnow()
                self.db.commit()
                self.db.refresh(existing_entity)
                return str(existing_entity.id)
            else:
                # Utwórz nową encję
                new_entity = Entity(
                    name=name,
                    type=entity_type,
                    aliases=aliases or [],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_entity)
                self.db.commit()
                self.db.refresh(new_entity)
                return str(new_entity.id)
                
        except Exception as e:
            logger.error(f"Failed to upsert entity {name}: {e}")
            self.db.rollback()
            return None
    
    def upsert_relation(self, source_id: str, target_id: str, relation_type: str,
                        weight: float = 0.8, evidence_fact_id: Optional[int] = None) -> bool:
        """Tworzy lub aktualizuje relację z akumulacją wagi.

        Jeżeli relacja istnieje, zwiększa jej wagę o `weight` zamiast nadpisywać.
        """
        try:
            # Konwertuj ID na int
            source_entity_id = int(source_id)
            target_entity_id = int(target_id)
            
            # Sprawdź czy encje istnieją
            source_entity = self.db.query(Entity).filter(Entity.id == source_entity_id).first()
            target_entity = self.db.query(Entity).filter(Entity.id == target_entity_id).first()
            
            if not source_entity or not target_entity:
                logger.error(f"Source or target entity not found: {source_entity_id}, {target_entity_id}")
                return False
            
            # Sprawdź czy relacja już istnieje
            existing_relation = self.db.query(Relation).filter(
                and_(
                    Relation.source_entity_id == source_entity_id,
                    Relation.target_entity_id == target_entity_id,
                    Relation.relation_type == relation_type
                )
            ).first()
            
            if existing_relation:
                # Akumuluj wagę (suma dowodów)
                try:
                    current = float(existing_relation.weight or 0.0)
                except Exception:
                    current = 0.0
                existing_relation.weight = current + float(weight)
                existing_relation.updated_at = datetime.utcnow()
                # Zapisz dowód, jeśli podano
                if evidence_fact_id is not None:
                    try:
                        fact = self.db.query(Fact).filter(Fact.id == int(evidence_fact_id)).first()
                        if fact and fact not in getattr(existing_relation, 'evidence_facts', []):
                            existing_relation.evidence_facts.append(fact)  # type: ignore[attr-defined]
                    except Exception:
                        # Ignoruj błąd dowodu – kluczowe jest utrzymanie relacji
                        pass
                self.db.commit()
                return True
            else:
                # Utwórz nową relację
                new_relation = Relation(
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    relation_type=relation_type,
                    weight=weight,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_relation)
                self.db.commit()
                # Dopięcie dowodu, jeśli dostępny
                if evidence_fact_id is not None:
                    try:
                        fact = self.db.query(Fact).filter(Fact.id == int(evidence_fact_id)).first()
                        if fact:
                            # Odśwież instancję relacji po commicie
                            self.db.refresh(new_relation)
                            new_relation.evidence_facts.append(fact)  # type: ignore[attr-defined]
                            self.db.commit()
                    except Exception:
                        # Dowód opcjonalny – nie blokuj operacji
                        pass
                return True
                
        except Exception as e:
            logger.error(f"Failed to upsert relation {source_id}->{target_id}: {e}")
            self.db.rollback()
            return False
    
    def find_vertices(self, label: str = None, properties: Dict[str, Any] = None, 
                     name_pattern: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Znajduje wierzchołki (encje) na podstawie właściwości lub wzorca nazwy"""
        try:
            query = self.db.query(Entity)
            
            # Filtruj na podstawie wzorca nazwy
            if name_pattern:
                query = query.filter(Entity.name.ilike(f"%{name_pattern}%"))
            
            # Filtruj na podstawie właściwości
            if properties:
                for key, value in properties.items():
                    if key == "name":
                        query = query.filter(Entity.name == value)
                    elif key == "type":
                        query = query.filter(Entity.type == value)
            
            # Zastosuj limit
            if limit:
                query = query.limit(limit)
            
            entities = query.all()
            
            # Konwertuj na format podobny do JanusGraph
            result = []
            for entity in entities:
                result.append({
                    "id": str(entity.id),
                    "name": entity.name,
                    "entity_type": entity.type,
                    "label": label or entity.type,
                    "properties": {
                        "name": entity.name,
                        "type": entity.type,
                        "aliases": entity.aliases
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to find vertices: {e}")
            return []
    
    def create_vertex(self, label: str, properties: Dict[str, Any]) -> str:
        """Tworzy nowy wierzchołek (encję)"""
        try:
            entity = Entity(
                name=properties.get("name", ""),
                type=properties.get("entity_type", properties.get("type", "")),
                aliases=properties.get("aliases", []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return str(entity.id)
            
        except Exception as e:
            logger.error(f"Failed to create vertex: {e}")
            self.db.rollback()
            return None
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Wykonuje zapytanie (symulacja Gremlin dla SQL)"""
        # To jest uproszczona implementacja
        # W rzeczywistości można by zaimplementować parser Gremlin -> SQL
        logger.warning(f"Query execution not fully implemented: {query}")
        return []
    
    def get_entity_neighbors(self, entity_id: int, depth: int = 1) -> Dict[str, Any]:
        """Pobiera sąsiadów encji do określonej głębokości"""
        try:
            # Pobierz encję główną
            main_entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
            if not main_entity:
                return {"nodes": [], "edges": []}
            
            nodes = [{
                "id": main_entity.id,
                "label": main_entity.name,
                "type": main_entity.type,
                "aliases": main_entity.aliases
            }]
            
            edges = []
            visited_entities = {entity_id}
            
            # Pobierz relacje wychodzące
            outgoing_relations = self.db.query(Relation).filter(
                Relation.source_entity_id == entity_id
            ).all()
            
            for relation in outgoing_relations:
                target_entity = relation.target_entity
                if target_entity.id not in visited_entities:
                    nodes.append({
                        "id": target_entity.id,
                        "label": target_entity.name,
                        "type": target_entity.type,
                        "aliases": target_entity.aliases
                    })
                    visited_entities.add(target_entity.id)
                
                edges.append({
                    "id": relation.id,
                    "source": relation.source_entity_id,
                    "target": relation.target_entity_id,
                    "label": relation.relation_type,
                    "weight": relation.weight
                })
            
            # Pobierz relacje przychodzące
            incoming_relations = self.db.query(Relation).filter(
                Relation.target_entity_id == entity_id
            ).all()
            
            for relation in incoming_relations:
                source_entity = relation.source_entity
                if source_entity.id not in visited_entities:
                    nodes.append({
                        "id": source_entity.id,
                        "label": source_entity.name,
                        "type": source_entity.type,
                        "aliases": source_entity.aliases
                    })
                    visited_entities.add(source_entity.id)
                
                edges.append({
                    "id": relation.id,
                    "source": relation.source_entity_id,
                    "target": relation.target_entity_id,
                    "label": relation.relation_type,
                    "weight": relation.weight
                })
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
        except Exception as e:
            logger.error(f"Failed to get entity neighbors: {e}")
            return {"nodes": [], "edges": []}
    
    def get_shortest_path(self, source_id: int, target_id: int, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        Znajdź najkrótszą ścieżkę między dwoma encjami używając BFS
        """
        # Konwertuj ID na int dla spójności
        source_id = int(source_id)
        target_id = int(target_id)
        
        # Sprawdź czy encje istnieją
        source_entity = self.db.query(Entity).filter(Entity.id == source_id).first()
        target_entity = self.db.query(Entity).filter(Entity.id == target_id).first()
        
        if not source_entity or not target_entity:
            return []
        
        # BFS
        queue = [(source_id, [])]  # (current_entity_id, path_so_far)
        visited = {source_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            # Znajdź wszystkich sąsiadów
            neighbors = self.db.query(Relation).filter(
                or_(
                    Relation.source_entity_id == current_id,
                    Relation.target_entity_id == current_id
                )
            ).all()
            
            for relation in neighbors:
                 # Określ ID sąsiada
                 if relation.source_entity_id == current_id:
                     neighbor_id = relation.target_entity_id
                 else:
                     neighbor_id = relation.source_entity_id
                 
                 # Sprawdź czy to cel
                 if neighbor_id == target_id:
                     # Znaleźliśmy cel - zbuduj ścieżkę
                     final_path = path + [{
                         'source': current_id,
                         'target': neighbor_id,
                         'relation_type': relation.relation_type,
                         'weight': relation.weight or 0.8
                     }]
                     return final_path
                 
                 # Dodaj do kolejki jeśli nie był odwiedzony
                 if neighbor_id not in visited:
                     visited.add(neighbor_id)
                     new_path = path + [{
                         'source': current_id,
                         'target': neighbor_id,
                         'relation_type': relation.relation_type,
                         'weight': relation.weight or 0.8
                     }]
                     queue.append((neighbor_id, new_path))
        
        return []
    
    def update_relation(self, relation_id: int, relation_type: str = None, weight: float = None, metadata: dict = None) -> Optional[Relation]:
        """Aktualizuje istniejącą relację"""
        try:
            relation = self.db.query(Relation).filter(Relation.id == relation_id).first()
            if not relation:
                return None
            
            if relation_type is not None:
                relation.relation_type = relation_type
            if weight is not None:
                relation.weight = weight
            if metadata is not None:
                relation.metadata = metadata
            
            relation.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(relation)
            return relation
        except Exception as e:
            logger.error(f"Failed to update relation {relation_id}: {e}")
            self.db.rollback()
            return None

    def get_graph_statistics(self) -> Dict[str, int]:
        """Zwraca statystyki grafu"""
        try:
            entity_count = self.db.query(func.count(Entity.id)).scalar()
            relation_count = self.db.query(func.count(Relation.id)).scalar()
            
            # Pobierz typy encji
            entity_types = self.db.query(Entity.type, func.count(Entity.id)).group_by(Entity.type).all()
            entity_types_dict = {entity_type: count for entity_type, count in entity_types}
            
            # Pobierz typy relacji
            relation_types = self.db.query(Relation.relation_type, func.count(Relation.id)).group_by(Relation.relation_type).all()
            
            return {
                "entity_count": entity_count,
                "relation_count": relation_count,
                "entity_types": entity_types_dict,
                "relation_types": dict(relation_types)
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                "entity_count": 0,
                "relation_count": 0,
                "entity_types": {},
                "relation_types": {}
            }


# Globalna instancja serwisu (będzie inicjalizowana w endpointach)
sql_graph_service = None

def get_sql_graph_service(db: Session) -> SQLGraphService:
    """Factory function dla serwisu grafu"""
    return SQLGraphService(db)
