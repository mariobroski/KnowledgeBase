from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.db.database_models import Entity as EntityModel, Relation as RelationModel

class GraphService:
    """Serwis do zarządzania grafem wiedzy
    
    Ta klasa jest odpowiedzialna za operacje na grafie wiedzy.
    """
    
    def __init__(self, db: Session):
        """Inicjalizacja serwisu
        
        Args:
            db: Sesja bazy danych
        """
        self.db = db
    
    def get_relations(self, skip: int = 0, limit: int = 100, source_entity_id: Optional[int] = None, target_entity_id: Optional[int] = None, relation_type: Optional[str] = None) -> List[RelationModel]:
        """
        Pobiera listę relacji z bazy danych.
        
        Args:
            skip: Liczba rekordów do pominięcia
            limit: Maksymalna liczba rekordów do pobrania
            source_entity_id: Opcjonalne filtrowanie po ID encji źródłowej
            target_entity_id: Opcjonalne filtrowanie po ID encji docelowej
            relation_type: Opcjonalne filtrowanie po typie relacji
            
        Returns:
            List[Relation]: Lista relacji
        """
        query = self.db.query(RelationModel)
        
        if source_entity_id:
            query = query.filter(RelationModel.source_entity_id == source_entity_id)
        if target_entity_id:
            query = query.filter(RelationModel.target_entity_id == target_entity_id)
        if relation_type:
            query = query.filter(RelationModel.relation_type == relation_type)
            
        return query.offset(skip).limit(limit).all()

    def get_relation(self, relation_id: int) -> Optional[RelationModel]:
        """
        Pobiera konkretną relację po ID.
        
        Args:
            relation_id: ID relacji
            
        Returns:
            Optional[Relation]: Relacja lub None jeśli nie znaleziono
        """
        return self.db.query(RelationModel).filter(RelationModel.id == relation_id).first()

    def create_relation(self, relation_data: Dict[str, Any]) -> RelationModel:
        """
        Tworzy nową relację w bazie danych.
        
        Args:
            relation_data: Dane relacji
            
        Returns:
            Relation: Utworzona relacja
        """
        # Sprawdź czy encje źródłowa i docelowa istnieją
        source_id = relation_data.get("source_entity_id")
        target_id = relation_data.get("target_entity_id")
        
        if not source_id or not target_id:
            raise ValueError("source_entity_id i target_entity_id są wymagane")
        
        source = self.db.query(EntityModel).filter(EntityModel.id == source_id).first()
        target = self.db.query(EntityModel).filter(EntityModel.id == target_id).first()
        
        if not source or not target:
            raise ValueError("Jedna lub obie encje nie istnieją")
        
        relation = RelationModel(**relation_data)
        relation.source = source
        relation.target = target
        
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    def get_or_create_relation(self, source_entity_id: int, target_entity_id: int, relation_type: str) -> RelationModel:
        relation = (
            self.db.query(RelationModel)
            .filter(
                RelationModel.source_entity_id == source_entity_id,
                RelationModel.target_entity_id == target_entity_id,
                RelationModel.relation_type == relation_type,
            )
            .first()
        )
        if relation:
            return relation

        relation_data = {
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "relation_type": relation_type,
            "weight": 1.0,
        }
        return self.create_relation(relation_data)

    def update_relation(self, relation_id: int, relation_data: Dict[str, Any]) -> Optional[RelationModel]:
        """
        Aktualizuje istniejącą relację.
        
        Args:
            relation_id: ID relacji do aktualizacji
            relation_data: Nowe dane relacji
            
        Returns:
            Optional[Relation]: Zaktualizowana relacja lub None jeśli nie znaleziono
        """
        relation = self.get_relation(relation_id)
        if not relation:
            return None
        
        # Sprawdź czy nowe encje istnieją (jeśli są podane)
        source_id = relation_data.get("source_entity_id")
        if source_id:
            source = self.db.query(EntityModel).filter(EntityModel.id == source_id).first()
            if source:
                relation.source = source
        
        target_id = relation_data.get("target_entity_id")
        if target_id:
            target = self.db.query(EntityModel).filter(EntityModel.id == target_id).first()
            if target:
                relation.target = target
        
        # Aktualizuj pozostałe pola
        for key, value in relation_data.items():
            if key not in ["source_entity_id", "target_entity_id"] and hasattr(relation, key):
                setattr(relation, key, value)
        
        self.db.commit()
        self.db.refresh(relation)
        return relation
    
    def delete_relation(self, relation_id: int) -> bool:
        """Usuń relację
        
        Args:
            relation_id: ID relacji
            
        Returns:
            True, jeśli usunięto, False w przeciwnym razie
        """
        relation = self.get_relation(relation_id)
        if not relation:
            return False
        
        self.db.delete(relation)
        self.db.commit()
        return True
    
    def get_entity_subgraph(self, entity_id: int, depth: int = 1) -> Dict[str, Any]:
        """Pobierz podgraf dla encji
        
        Args:
            entity_id: ID encji
            depth: Głębokość podgrafu
            
        Returns:
            Podgraf w formacie JSON
        """
        # W rzeczywistej implementacji, tutaj byłoby zapytanie do bazy grafowej
        # Dla demonstracji zwracamy przykładowe dane
        entity = self.db.query(EntityModel).filter(EntityModel.id == entity_id).first()
        if not entity:
            return {"nodes": [], "edges": []}
        
        # Symulacja podgrafu
        nodes = [{
            "id": entity.id,
            "label": entity.name,
            "type": entity.type
        }]
        
        edges = []
        
        # Relacje wychodzące
        outgoing_relations = self.db.query(RelationModel).filter(RelationModel.source_entity_id == entity_id).all()
        for relation in outgoing_relations:
            target = relation.target_entity
            nodes.append({
                "id": target.id,
                "label": target.name,
                "type": target.type
            })
            edges.append({
                "id": relation.id,
                "source": entity.id,
                "target": target.id,
                "label": relation.relation_type,
                "weight": relation.weight
            })
        
        # Relacje przychodzące
        incoming_relations = self.db.query(RelationModel).filter(RelationModel.target_entity_id == entity_id).all()
        for relation in incoming_relations:
            source = relation.source_entity
            nodes.append({
                "id": source.id,
                "label": source.name,
                "type": source.type
            })
            edges.append({
                "id": relation.id,
                "source": source.id,
                "target": entity.id,
                "label": relation.relation_type,
                "weight": relation.weight
            })
        
        # Usunięcie duplikatów
        unique_nodes = {}
        for node in nodes:
            unique_nodes[node["id"]] = node
        
        return {
            "nodes": list(unique_nodes.values()),
            "edges": edges
        }
    
    def find_paths(self, source_id: int, target_id: int, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Znajdź ścieżki między encjami
        
        Args:
            source_id: ID encji źródłowej
            target_id: ID encji docelowej
            max_depth: Maksymalna głębokość ścieżki
            
        Returns:
            Lista ścieżek
        """
        # W rzeczywistej implementacji, tutaj byłoby zapytanie do bazy grafowej
        # Dla demonstracji zwracamy przykładowe dane
        source = self.db.query(EntityModel).filter(EntityModel.id == source_id).first()
        target = self.db.query(EntityModel).filter(EntityModel.id == target_id).first()
        
        if not source or not target:
            return []
        
        # Symulacja ścieżek
        paths = []
        
        # Ścieżka 1
        paths.append({
            "path": [
                {"id": source.id, "name": source.name, "type": source.type},
                {"relation": "WYKORZYSTUJE", "id": 1},
                {"id": target.id, "name": target.name, "type": target.type}
            ],
            "weight": 0.9,
            "length": 1
        })
        
        # Ścieżka 2 (dłuższa)
        intermediate_entity = self.db.query(EntityModel).filter(EntityModel.id != source_id, EntityModel.id != target_id).first()
        if intermediate_entity:
            paths.append({
                "path": [
                    {"id": source.id, "name": source.name, "type": source.type},
                    {"relation": "ZAWIERA", "id": 2},
                    {"id": intermediate_entity.id, "name": intermediate_entity.name, "type": intermediate_entity.type},
                    {"relation": "JEST_CZĘŚCIĄ", "id": 3},
                    {"id": target.id, "name": target.name, "type": target.type}
                ],
                "weight": 0.7,
                "length": 2
            })
        
        return paths
    
    def promote_path_to_justification(self, path_data: Dict[str, Any]) -> bool:
        """Promuj ścieżkę do uzasadnienia
        
        Args:
            path_data: Dane ścieżki
            
        Returns:
            True, jeśli promowano, False w przeciwnym razie
        """
        # W rzeczywistej implementacji, tutaj byłoby zapisanie ścieżki jako uzasadnienia
        # Dla demonstracji zwracamy True
        return True
    
    def get_graph_visualization_data(self, limit: int = 100) -> Dict[str, Any]:
        """Pobierz dane do wizualizacji grafu
        
        Args:
            limit: Maksymalna liczba encji do zwrócenia
            
        Returns:
            Dane grafu w formacie JSON
        """
        # W rzeczywistej implementacji, tutaj byłoby zapytanie do bazy grafowej
        # Dla demonstracji zwracamy przykładowe dane
        entities = self.db.query(EntityModel).limit(limit).all()
        relations = self.db.query(RelationModel).limit(limit).all()
        
        nodes = [{
            "id": entity.id,
            "label": entity.name,
            "type": entity.type
        } for entity in entities]
        
        edges = [{
            "id": relation.id,
            "source": relation.source_entity_id,
            "target": relation.target_entity_id,
            "label": relation.relation_type,
            "weight": relation.weight
        } for relation in relations]
        
        return {
            "nodes": nodes,
            "edges": edges
        }
