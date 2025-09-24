"""
Graph Update Service - aktualizacja grafu wiedzy
Wykorzystuje NER + relacje + JanusGraph
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import spacy
    from spacy import displacy
except ImportError:
    spacy = None

from app.services.sql_graph_service import get_sql_graph_service
from app.services.fact_extraction_service import Fact
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Reprezentuje encję w grafie"""
    name: str
    entity_type: str
    aliases: List[str]
    confidence: float
    source_fragment_id: int
    metadata: Dict[str, Any]


@dataclass
class Relation:
    """Reprezentuje relację w grafie"""
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    source_fact_id: int
    metadata: Dict[str, Any]


class GraphUpdateService:
    """Serwis do aktualizacji grafu wiedzy"""
    
    def __init__(self, db_session=None):
        self._nlp = None
        self._enabled = False
        self._db_session = db_session
        self._graph_service = None
        self._entity_types = {
            "PERSON": "Person",
            "ORG": "Organization", 
            "GPE": "Location",
            "PRODUCT": "Product",
            "EVENT": "Event",
            "WORK_OF_ART": "WorkOfArt",
            "LAW": "Law",
            "LANGUAGE": "Language",
            "DATE": "Date",
            "TIME": "Time",
            "MONEY": "Money",
            "PERCENT": "Percentage",
            "CARDINAL": "Number",
            "ORDINAL": "Ordinal"
        }
        
        # Spróbuj załadować model spaCy - jeśli nie ma, włącz tryb bez spaCy
        if spacy is not None:
            try:
                # Spróbuj różne modele spaCy
                for model_name in ["en_core_web_sm", "pl_core_news_sm", "en_core_web_md"]:
                    try:
                        self._nlp = spacy.load(model_name)
                        logger.info(f"GraphUpdateService initialized with spaCy model: {model_name}")
                        break
                    except OSError:
                        continue
                
                if self._nlp is None:
                    logger.warning("No spaCy model found - using fallback mode")
                    
                # Włącz serwis niezależnie od dostępności spaCy
                self._enabled = True
                
            except Exception as e:
                logger.warning(f"spaCy initialization failed: {e} - using fallback mode")
                self._enabled = True
        else:
            logger.warning("spaCy not available - using fallback mode")
            self._enabled = True
    
    def set_db_session(self, db_session):
        """Ustawia sesję bazy danych"""
        self._db_session = db_session
        if db_session:
            self._graph_service = get_sql_graph_service(db_session)
    
    @property
    def is_enabled(self) -> bool:
        """Check if graph update is enabled"""
        return (self._enabled and self._graph_service is not None and 
                self._graph_service.is_connected())
    
    def update_graph_from_facts(self, facts: List[Fact]) -> Dict[str, Any]:
        """
        Aktualizuje graf wiedzy na podstawie faktów
        
        Args:
            facts: Lista faktów do przetworzenia
            
        Returns:
            Statystyki aktualizacji grafu
        """
        if not self.is_enabled:
            return {"error": "Graph update service not available"}
        
        stats = {
            "entities_created": 0,
            "relations_created": 0,
            "entities_updated": 0,
            "errors": []
        }
        
        try:
            # Ekstraktuj encje z faktów
            entities = self._extract_entities_from_facts(facts)
            
            # Ekstraktuj relacje z faktów
            relations = self._extract_relations_from_facts(facts)
            
            # Aktualizuj graf
            for entity in entities:
                try:
                    self._upsert_entity(entity)
                    stats["entities_created"] += 1
                except Exception as e:
                    logger.error(f"Failed to upsert entity {entity.name}: {e}")
                    stats["errors"].append(f"Entity {entity.name}: {e}")
            
            for relation in relations:
                try:
                    self._upsert_relation(relation)
                    stats["relations_created"] += 1
                except Exception as e:
                    logger.error(f"Failed to upsert relation {relation.source_entity}->{relation.target_entity}: {e}")
                    stats["errors"].append(f"Relation {relation.source_entity}->{relation.target_entity}: {e}")
            
            logger.info(f"Graph updated: {stats['entities_created']} entities, {stats['relations_created']} relations")
            
        except Exception as e:
            logger.error(f"Graph update failed: {e}")
            stats["errors"].append(f"Graph update failed: {e}")
        
        return stats
    
    def _extract_entities_from_facts(self, facts: List[Fact]) -> List[Entity]:
        """Ekstraktuje encje z faktów"""
        entities = []
        seen_entities = set()
        
        for fact in facts:
            if hasattr(fact, 'entities') and fact.entities:
                # Jeśli fakt ma już wyekstraktowane encje
                for entity_model in fact.entities:
                    if entity_model.name not in seen_entities:
                        entity_type = entity_model.type or self._determine_entity_type(entity_model.name, fact)
                        entity = Entity(
                            name=entity_model.name,
                            entity_type=entity_type,
                            aliases=entity_model.aliases or [],
                            confidence=fact.confidence,
                            source_fragment_id=fact.source_fragment_id,
                            metadata={
                                "fact_content": fact.content,
                                "created_at": datetime.now().isoformat(),
                                "entity_id": entity_model.id
                            }
                        )
                        entities.append(entity)
                        seen_entities.add(entity_model.name)
            else:
                # Fallback: ekstraktuj encje z treści faktu
                if self._nlp:
                    # Użyj spaCy jeśli dostępne
                    doc = self._nlp(fact.content)
                    for ent in doc.ents:
                        if ent.text not in seen_entities:
                            entity_type = self._entity_types.get(ent.label_, "Unknown")
                            entity = Entity(
                                name=ent.text,
                                entity_type=entity_type,
                                aliases=[],
                                confidence=fact.confidence * 0.8,  # Niższa pewność dla auto-ekstraktowanych
                                source_fragment_id=fact.source_fragment_id,
                                metadata={
                                    "extraction_method": "spacy",
                                    "spacy_label": ent.label_,
                                    "fact_content": fact.content,
                                    "created_at": datetime.now().isoformat()
                                }
                            )
                            entities.append(entity)
                            seen_entities.add(ent.text)
                else:
                    # Fallback bez spaCy - prosta ekstrakcja słów kluczowych
                    words = fact.content.split()
                    for word in words:
                        if (len(word) > 3 and 
                            word.isalpha() and 
                            word[0].isupper() and 
                            word not in seen_entities):
                            
                            entity_type = self._determine_entity_type(word, fact)
                            entity = Entity(
                                name=word,
                                entity_type=entity_type,
                                aliases=[],
                                confidence=fact.confidence * 0.6,  # Jeszcze niższa pewność
                                source_fragment_id=fact.source_fragment_id,
                                metadata={
                                    "extraction_method": "fallback",
                                    "fact_content": fact.content,
                                    "created_at": datetime.now().isoformat()
                                }
                            )
                            entities.append(entity)
                            seen_entities.add(word)
        
        return entities
    
    def _extract_relations_from_facts(self, facts: List[Fact]) -> List[Relation]:
        """Ekstraktuje relacje z faktów"""
        relations = []
        
        for fact in facts:
            # Sprawdź czy fakt ma co najmniej 2 powiązane encje
            if hasattr(fact, 'entities') and len(fact.entities) >= 2:
                source_entity = fact.entities[0].name
                target_entity = fact.entities[1].name
                
                # Określ typ relacji na podstawie treści faktu
                relation_type = self._determine_relation_type(fact.content)
                
                relation = Relation(
                    source_entity=source_entity,
                    target_entity=target_entity,
                    relation_type=relation_type,
                    confidence=fact.confidence,
                    source_fact_id=fact.source_fragment_id,
                    metadata={
                        "fact_content": fact.content,
                        "created_at": datetime.now().isoformat(),
                        "fact_id": fact.id
                    }
                )
                relations.append(relation)
        
        return relations
    
    def _determine_entity_type(self, entity_text: str, fact: Fact) -> str:
        """Określa typ encji na podstawie kontekstu"""
        # Użyj spaCy do analizy encji
        if self._nlp:
            doc = self._nlp(entity_text)
            if doc.ents:
                spacy_label = doc.ents[0].label_
                return self._entity_types.get(spacy_label, "Unknown")
        
        # Heurystyki na podstawie zawartości
        if any(word in entity_text.lower() for word in ["company", "corp", "inc", "ltd"]):
            return "Organization"
        elif any(word in entity_text.lower() for word in ["mr", "ms", "dr", "prof"]):
            return "Person"
        elif any(word in entity_text.lower() for word in ["city", "country", "state", "nation"]):
            return "Location"
        elif fact.fact_type == "temporal":
            return "Date"
        elif fact.fact_type == "numerical":
            return "Number"
        
        return "Unknown"
    
    def _determine_relation_type(self, fact_content: str) -> str:
        """Określa typ relacji na podstawie treści faktu - rozszerzona wersja"""
        content_lower = fact_content.lower()
        
        # Relacje tożsamości i klasyfikacji
        if any(word in content_lower for word in ["is a", "was a", "are a", "were a", "jest", "była", "są", "były"]):
            return "IS_A"
        
        # Relacje posiadania
        if any(word in content_lower for word in ["has", "have", "had", "ma", "mają", "miał", "posiada", "owns", "possesses"]):
            return "HAS"
        
        # Relacje zawierania
        if any(word in content_lower for word in ["contains", "includes", "zawiera", "obejmuje", "comprises"]):
            return "CONTAINS"
        
        # Relacje przynależności
        if any(word in content_lower for word in ["belongs to", "is part of", "is member of", "należy do", "jest częścią", "jest członkiem"]):
            return "BELONGS_TO"
        
        # Relacje lokalizacji
        if any(word in content_lower for word in ["located", "situated", "found in", "znajduje się", "jest położony", "mieści się"]):
            return "LOCATED_IN"
        
        # Relacje zawodowe i funkcjonalne
        if any(word in content_lower for word in ["works for", "employed by", "serves as", "pracuje dla", "zatrudniony", "pełni funkcję"]):
            return "WORKS_FOR"
        
        # Relacje przyczynowo-skutkowe
        if any(word in content_lower for word in ["causes", "leads to", "results in", "triggers", "powoduje", "prowadzi do", "skutkuje", "wywołuje"]):
            return "CAUSES"
        
        # Relacje czasowe
        if any(word in content_lower for word in ["occurred in", "happened in", "took place in", "miało miejsce", "wydarzyło się", "odbyło się"]):
            return "OCCURRED_IN"
        
        # Relacje tworzenia i autorstwa
        if any(word in content_lower for word in ["created", "developed", "invented", "founded", "established", "stworzył", "opracował", "wynalazł", "założył"]):
            return "CREATED"
        
        # Relacje wykorzystania
        if any(word in content_lower for word in ["uses", "utilizes", "employs", "applies", "wykorzystuje", "używa", "stosuje"]):
            return "USES"
        
        # Relacje podobieństwa
        if any(word in content_lower for word in ["similar to", "resembles", "is like", "podobny do", "przypomina", "jest jak"]):
            return "SIMILAR_TO"
        
        # Relacje hierarchiczne i bazowania
        if any(word in content_lower for word in ["based on", "derives from", "extends", "bazuje na", "wywodzi się", "rozszerza"]):
            return "BASED_ON"
        
        # Relacje przeciwstawienia
        if any(word in content_lower for word in ["differs from", "unlike", "opposite to", "różni się od", "w przeciwieństwie do", "przeciwny do"]):
            return "DIFFERS_FROM"
        
        # Relacje współpracy
        if any(word in content_lower for word in ["collaborates with", "partners with", "współpracuje z", "partneruje z"]):
            return "COLLABORATES_WITH"
        
        # Relacje wpływu
        if any(word in content_lower for word in ["influences", "affects", "impacts", "wpływa na", "oddziałuje na"]):
            return "INFLUENCES"
        
        # Relacje następstwa
        if any(word in content_lower for word in ["follows", "succeeds", "comes after", "następuje po", "przychodzi po"]):
            return "FOLLOWS"
        
        # Relacje poprzedzania
        if any(word in content_lower for word in ["precedes", "comes before", "poprzedza", "przychodzi przed"]):
            return "PRECEDES"
        
        # Domyślny typ relacji
        return "RELATES_TO"
    
    def _upsert_entity(self, entity: Entity) -> str:
        """Dodaje lub aktualizuje encję w grafie"""
        if not self._graph_service:
            logger.error("Graph service not available")
            return None
            
        # Użyj SQL graph service
        entity_id = self._graph_service.upsert_entity(
            name=entity.name,
            entity_type=entity.entity_type,
            aliases=entity.aliases
        )
        return entity_id
    
    def _upsert_relation(self, relation: Relation) -> str:
        """Dodaje lub aktualizuje relację w grafie"""
        if not self._graph_service:
            logger.error("Graph service not available")
            return None
            
        # Najpierw znajdź lub utwórz encje źródłową i docelową
        source_id = self._graph_service.upsert_entity(
            name=relation.source_entity,
            entity_type="Unknown"  # Domyślny typ jeśli nie znamy
        )
        
        target_id = self._graph_service.upsert_entity(
            name=relation.target_entity,
            entity_type="Unknown"  # Domyślny typ jeśli nie znamy
        )
        
        if not source_id or not target_id:
            logger.error(f"Failed to create entities for relation {relation.source_entity} -> {relation.target_entity}")
            return None
        
        # Utwórz relację
        success = self._graph_service.upsert_relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation.relation_type,
            weight=relation.confidence,
            evidence_fact_id=relation.source_fact_id
        )
        
        return str(success) if success else None
    
    def _update_entity_properties(self, entity_id: str, entity: Entity):
        """Aktualizuje właściwości encji"""
        if not self._graph_service:
            logger.error("Graph service not available")
            return False
            
        try:
            # Konwertuj entity_id na int
            entity_id_int = int(entity_id)
            
            # Pobierz istniejącą encję z bazy danych
            from app.db.database_models import Entity as EntityModel
            existing_entity = self._db_session.query(EntityModel).filter(EntityModel.id == entity_id_int).first()
            
            if not existing_entity:
                logger.error(f"Entity with ID {entity_id} not found")
                return False
            
            # Aktualizuj właściwości encji
            existing_entity.name = entity.name
            existing_entity.type = entity.entity_type
            existing_entity.aliases = entity.aliases
            existing_entity.updated_at = datetime.utcnow()
            
            # Zapisz zmiany
            self._db_session.commit()
            self._db_session.refresh(existing_entity)
            
            logger.info(f"Updated entity {entity_id} properties: name={entity.name}, type={entity.entity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update entity {entity_id} properties: {e}")
            self._db_session.rollback()
            return False
    
    def _update_relation_properties(self, relation_id: str, relation: Relation):
        """Aktualizuje właściwości relacji"""
        if not self._graph_service:
            logger.error("Graph service not available")
            return False
            
        try:
            # Konwertuj relation_id na int
            relation_id_int = int(relation_id)
            
            # Pobierz istniejącą relację z bazy danych
            from app.db.database_models import Relation as RelationModel
            existing_relation = self._db_session.query(RelationModel).filter(RelationModel.id == relation_id_int).first()
            
            if not existing_relation:
                logger.error(f"Relation with ID {relation_id} not found")
                return False
            
            # Aktualizuj właściwości relacji
            existing_relation.relation_type = relation.relation_type
            existing_relation.weight = relation.confidence
            existing_relation.updated_at = datetime.utcnow()
            
            # Opcjonalnie aktualizuj metadane jeśli są dostępne
            if hasattr(existing_relation, 'metadata') and relation.metadata:
                existing_relation.metadata = relation.metadata
            
            # Zapisz zmiany
            self._db_session.commit()
            self._db_session.refresh(existing_relation)
            
            logger.info(f"Updated relation {relation_id} properties: type={relation.relation_type}, confidence={relation.confidence}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update relation {relation_id} properties: {e}")
            self._db_session.rollback()
            return False
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Zwraca statystyki grafu wiedzy"""
        if not self._graph_service or not self._graph_service.is_connected():
            return {"error": "Graph service not available"}
        
        try:
            return self._graph_service.get_graph_statistics()
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {"error": str(e)}


# Global instance
graph_update_service = GraphUpdateService()
