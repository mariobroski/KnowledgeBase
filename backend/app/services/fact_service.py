import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.db.database_models import Fact as FactModel, Entity as EntityModel, Fragment as FragmentModel, Relation as RelationModel
from app.services.fact_extraction import get_fact_extractor, FactCandidate
from app.services.graph_service import GraphService
from app.services.sql_graph_service import get_sql_graph_service

class FactService:
    """Serwis do zarządzania faktami i encjami
    
    Ta klasa jest odpowiedzialna za operacje CRUD na faktach i encjach.
    """
    
    def __init__(self, db: Session):
        """Inicjalizacja serwisu
        
        Args:
            db: Sesja bazy danych
        """
        self.db = db
    
    def get_facts(self, skip: int = 0, limit: int = 100) -> List[FactModel]:
        """Pobierz listę faktów
        
        Args:
            skip: Liczba faktów do pominięcia
            limit: Maksymalna liczba faktów do zwrócenia
            
        Returns:
            Lista faktów
        """
        facts = self.db.query(FactModel).join(FragmentModel).join(FragmentModel.article).offset(skip).limit(limit).all()
        
        # Dodaj tytuł artykułu i pozycję fragmentu do każdego faktu
        for fact in facts:
            fact.article_title = fact.source_fragment.article.title
            # Oblicz pozycję fragmentu na podstawie pola position lub jako fallback
            if hasattr(fact.source_fragment, 'position') and fact.source_fragment.position:
                fact.fragment_position = fact.source_fragment.position
            else:
                # Fallback: oblicz pozycję na podstawie ID fragmentu w artykule
                fragment_position = self.db.query(FragmentModel).filter(
                    FragmentModel.article_id == fact.source_fragment.article_id,
                    FragmentModel.id <= fact.source_fragment.id
                ).count()
                fact.fragment_position = fragment_position
            
        return facts
    
    def get_fact(self, fact_id: int) -> Optional[FactModel]:
        """Pobierz fakt po ID
        
        Args:
            fact_id: ID faktu
            
        Returns:
            Fakt lub None, jeśli nie znaleziono
        """
        return self.db.query(FactModel).filter(FactModel.id == fact_id).first()
    
    def create_fact(self, fact_data: Dict[str, Any]) -> FactModel:
        """Utwórz nowy fakt
        
        Args:
            fact_data: Dane faktu
            
        Returns:
            Utworzony fakt
        """
        # Obsługa encji - usuwamy entity_ids z fact_data przed utworzeniem faktu
        entity_ids = fact_data.pop("entity_ids", [])
        subject_id = fact_data.pop("subject_id", None)
        object_id = fact_data.pop("object_id", None)
        
        fact = FactModel(**fact_data)
        
        # Dodaj encje do faktu
        if entity_ids:
            for entity_id in entity_ids:
                entity = self.get_entity(entity_id)
                if entity:
                    fact.entities.append(entity)
        
        if subject_id:
            subject = self.get_entity(subject_id)
            if subject:
                fact.subject = subject
        
        if object_id:
            object_entity = self.get_entity(object_id)
            if object_entity:
                fact.object = object_entity
        
        self.db.add(fact)
        self.db.commit()
        self.db.refresh(fact)
        return fact
    
    def update_fact(self, fact_id: int, fact_data: Dict[str, Any]) -> Optional[FactModel]:
        """Aktualizuj fakt
        
        Args:
            fact_id: ID faktu
            fact_data: Dane faktu do aktualizacji
            
        Returns:
            Zaktualizowany fakt lub None, jeśli nie znaleziono
        """
        fact = self.get_fact(fact_id)
        if not fact:
            return None
        
        # Obsługa encji
        subject_id = fact_data.pop("subject_id", None)
        object_id = fact_data.pop("object_id", None)
        
        if subject_id:
            subject = self.get_entity(subject_id)
            if subject:
                fact.subject = subject
        
        if object_id:
            object_entity = self.get_entity(object_id)
            if object_entity:
                fact.object = object_entity
        
        # Aktualizacja pozostałych pól
        for key, value in fact_data.items():
            setattr(fact, key, value)
        
        self.db.commit()
        self.db.refresh(fact)
        return fact
    
    def delete_fact(self, fact_id: int) -> bool:
        """Usuń fakt
        
        Args:
            fact_id: ID faktu
            
        Returns:
            True, jeśli usunięto, False w przeciwnym razie
        """
        fact = self.get_fact(fact_id)
        if not fact:
            return False
        
        self.db.delete(fact)
        self.db.commit()
        return True
    
    def get_entities(self, skip: int = 0, limit: int = 100) -> List[EntityModel]:
        """Pobierz listę encji
        
        Args:
            skip: Liczba encji do pominięcia
            limit: Maksymalna liczba encji do zwrócenia
            
        Returns:
            Lista encji
        """
        return self.db.query(EntityModel).offset(skip).limit(limit).all()
    
    def get_entity(self, entity_id: int) -> Optional[EntityModel]:
        """Pobierz encję po ID
        
        Args:
            entity_id: ID encji
            
        Returns:
            Encja lub None, jeśli nie znaleziono
        """
        return self.db.query(EntityModel).filter(EntityModel.id == entity_id).first()
    
    def create_entity(self, entity_data: Dict[str, Any]) -> EntityModel:
        """Utwórz nową encję
        
        Args:
            entity_data: Dane encji
            
        Returns:
            Utworzona encja
        """
        entity = EntityModel(**entity_data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update_entity(self, entity_id: int, entity_data: Dict[str, Any]) -> Optional[EntityModel]:
        """Aktualizuj encję
        
        Args:
            entity_id: ID encji
            entity_data: Dane encji do aktualizacji
            
        Returns:
            Zaktualizowana encja lub None, jeśli nie znaleziono
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return None
        
        for key, value in entity_data.items():
            setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete_entity(self, entity_id: int) -> bool:
        """Usuń encję
        
        Args:
            entity_id: ID encji
            
        Returns:
            True, jeśli usunięto, False w przeciwnym razie
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.commit()
        return True
    
    def merge_entities(self, source_id: int, target_id: int) -> bool:
        """Połącz dwie encje
        
        Args:
            source_id: ID encji źródłowej
            target_id: ID encji docelowej
            
        Returns:
            True, jeśli połączono, False w przeciwnym razie
        """
        source = self.get_entity(source_id)
        target = self.get_entity(target_id)
        
        if not source or not target:
            return False
        
        # Aktualizacja faktów, gdzie source jest podmiotem
        for fact in source.facts_as_subject:
            fact.subject = target
        
        # Aktualizacja faktów, gdzie source jest obiektem
        for fact in source.facts_as_object:
            fact.object = target
        
        # Usunięcie encji źródłowej
        self.db.delete(source)
        self.db.commit()
        return True
    
    def extract_facts_from_fragment(self, fragment_id: int) -> List[FactModel]:
        """Wyodrębnij fakty z fragmentu tekstu
        
        Args:
            fragment_id: ID fragmentu
            
        Returns:
            Lista wyodrębnionych faktów
        """
        # W rzeczywistej implementacji, tutaj byłoby wywołanie modelu językowego
        # do ekstrakcji faktów z fragmentu tekstu
        fragment = self.db.query(FragmentModel).filter(FragmentModel.id == fragment_id).first()
        if not fragment or not fragment.content:
            return []

        extractor = get_fact_extractor()
        candidates = extractor.extract(fragment.content)
        if not candidates:
            fragment.facts_extracted = True
            fragment.fact_count = 0
            self.db.commit()
            return []

        logger = logging.getLogger(__name__)
        graph_service = GraphService(self.db)
        created_facts: List[FactModel] = []

        for candidate in candidates:
            fact = self._create_fact_from_candidate(fragment, candidate)
            if not fact:
                continue
            created_facts.append(fact)

            # Utwórz relację w grafie (SQL - backup)
            try:
                relation = graph_service.get_or_create_relation(
                    source_entity_id=fact.entities[0].id,
                    target_entity_id=fact.entities[1].id,
                    relation_type=candidate.relation or "powiązany",
                )
                relation.evidence_facts.append(fact)
            except Exception as exc:
                logger.warning("Nie udało się utworzyć relacji grafowej w SQL: %s", exc)

            # Utwórz encje i relacje w grafie SQL
            try:
                sql_graph_service = get_sql_graph_service(self.db)
                if sql_graph_service:
                    # Dodaj encje do grafu SQL
                    subject_vertex_id = sql_graph_service.upsert_entity(
                        name=fact.entities[0].name,
                        entity_type=fact.entities[0].type or "UNKNOWN",
                        aliases=None
                    )
                    
                    object_vertex_id = sql_graph_service.upsert_entity(
                        name=fact.entities[1].name,
                        entity_type=fact.entities[1].type or "UNKNOWN",
                        aliases=None
                    )
                    
                    # Dodaj relację do grafu SQL
                    if subject_vertex_id and object_vertex_id:
                        sql_graph_service.upsert_relation(
                            source_id=subject_vertex_id,
                            target_id=object_vertex_id,
                            relation_type=candidate.relation or "powiązany",
                            weight=float(candidate.confidence),
                            evidence_fact_id=fact.id
                        )
                        logger.debug(f"Dodano relację do grafu SQL: {fact.entities[0].name} -> {fact.entities[1].name}")
                else:
                    logger.warning("Serwis grafu SQL nie jest dostępny")
                
            except Exception as exc:
                logger.warning("Nie udało się utworzyć relacji w grafie SQL: %s", exc)

        fragment.facts_extracted = True
        fragment.fact_count = len(created_facts)
        self.db.commit()
        return created_facts

    def _create_fact_from_candidate(self, fragment: FragmentModel, candidate: FactCandidate) -> Optional[FactModel]:
        subject_entity = self._get_or_create_entity(candidate.subject, candidate.subject_type)
        object_entity = self._get_or_create_entity(candidate.object, candidate.object_type)
        if not subject_entity or not object_entity:
            return None

        fact = FactModel(
            content=candidate.text,
            source_fragment_id=fragment.id,
            status="oczekujący",
            confidence=float(candidate.confidence),
        )
        fact.entities.append(subject_entity)
        fact.entities.append(object_entity)
        self.db.add(fact)
        self.db.flush()
        self.db.refresh(fact)
        return fact

    def _get_or_create_entity(self, name: str, entity_type: Optional[str] = None) -> EntityModel:
        name = name.strip()
        if not name:
            raise ValueError("Nazwa encji nie może być pusta")

        entity = self.db.query(EntityModel).filter(EntityModel.name == name).first()
        if entity:
            if entity_type and not entity.type:
                entity.type = entity_type
            return entity

        entity = EntityModel(name=name, type=entity_type)
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity