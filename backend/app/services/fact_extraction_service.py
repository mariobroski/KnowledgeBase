"""
Fact Extraction Service - ekstrakcja faktów z tekstu
Wykorzystuje spaCy + heurystyki do identyfikacji faktów
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import spacy
    from spacy import displacy
except ImportError:
    spacy = None

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Fact:
    """Reprezentuje pojedynczy fakt"""
    content: str
    confidence: float
    source_fragment_id: int
    entities: List[str]
    fact_type: str
    created_at: datetime
    metadata: Dict[str, Any]


class FactExtractionService:
    """Serwis do ekstrakcji faktów z tekstu"""
    
    def __init__(self):
        self._nlp = None
        self._enabled = False
        self._confidence_threshold = settings.FACT_CONFIDENCE_THRESHOLD
        
        if spacy is None:
            logger.warning("spaCy not available - fact extraction disabled")
            return
        
        try:
            # Załaduj model spaCy (może być pl_core_news_lg dla polskiego)
            self._nlp = spacy.load("en_core_web_sm")  # Fallback na angielski
            self._enabled = True
            logger.info("FactExtractionService initialized with spaCy")
        except OSError:
            logger.warning("spaCy model not found - fact extraction disabled")
            self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if fact extraction is enabled"""
        return self._enabled and self._nlp is not None
    
    def extract_facts_from_fragment(self, fragment_id: int, content: str) -> List[Fact]:
        """
        Ekstraktuje fakty z fragmentu tekstu
        
        Args:
            fragment_id: ID fragmentu w bazie danych
            content: Treść fragmentu
            
        Returns:
            Lista wyekstraktowanych faktów
        """
        if not self.is_enabled:
            return []
        
        facts = []
        
        # Podziel tekst na zdania
        sentences = self._split_into_sentences(content)
        
        for sentence in sentences:
            # Analizuj każde zdanie
            doc = self._nlp(sentence)
            
            # Ekstraktuj fakty różnymi metodami
            facts.extend(self._extract_entity_facts(doc, fragment_id))
            facts.extend(self._extract_relation_facts(doc, fragment_id))
            facts.extend(self._extract_temporal_facts(doc, fragment_id))
            facts.extend(self._extract_numerical_facts(doc, fragment_id))
        
        # Filtruj fakty według progu pewności
        filtered_facts = [
            fact for fact in facts 
            if fact.confidence >= self._confidence_threshold
        ]
        
        logger.info(f"Extracted {len(filtered_facts)} facts from fragment {fragment_id}")
        return filtered_facts
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Dzieli tekst na zdania"""
        if not self._nlp:
            return [text]
        
        doc = self._nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    def _extract_entity_facts(self, doc, fragment_id: int) -> List[Fact]:
        """Ekstraktuje fakty o encjach"""
        facts = []
        
        # Znajdź encje
        entities = [(ent.text, ent.label_, ent.start_char, ent.end_char) 
                   for ent in doc.ents]
        
        for entity_text, label, start, end in entities:
            # Utwórz fakt o encji
            fact_content = f"Entity {entity_text} is a {label}"
            confidence = self._calculate_entity_confidence(entity_text, label)
            
            if confidence >= self._confidence_threshold:
                fact = Fact(
                    content=fact_content,
                    confidence=confidence,
                    source_fragment_id=fragment_id,
                    entities=[entity_text],
                    fact_type="entity",
                    created_at=datetime.now(),
                    metadata={
                        "entity_text": entity_text,
                        "entity_label": label,
                        "start_char": start,
                        "end_char": end
                    }
                )
                facts.append(fact)
        
        return facts
    
    def _extract_relation_facts(self, doc, fragment_id: int) -> List[Fact]:
        """Ekstraktuje fakty o relacjach między encjami"""
        facts = []
        
        # Znajdź wzorce relacji - rozszerzone o więcej typów semantycznych
        relation_patterns = [
            # Relacje tożsamości i klasyfikacji
            r"(\w+(?:\s+\w+)*)\s+(is|was|are|were)\s+(a|an)?\s*(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(jest|była|są|były)\s+(to)?\s*(\w+(?:\s+\w+)*)",
            
            # Relacje posiadania i zawierania
            r"(\w+(?:\s+\w+)*)\s+(has|have|had|contains|includes?)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(ma|mają|miał|zawiera|obejmuje)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje przynależności
            r"(\w+(?:\s+\w+)*)\s+(belongs to|is part of|is member of)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(należy do|jest częścią|jest członkiem)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje lokalizacji
            r"(\w+(?:\s+\w+)*)\s+(is located in|is situated in|is found in)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(znajduje się w|jest położony w|mieści się w)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje przyczynowo-skutkowe
            r"(\w+(?:\s+\w+)*)\s+(causes|leads to|results in|triggers)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(powoduje|prowadzi do|skutkuje|wywołuje)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje czasowe
            r"(\w+(?:\s+\w+)*)\s+(occurred in|happened in|took place in)\s+(\d{4}|\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(miało miejsce w|wydarzyło się w|odbyło się w)\s+(\d{4}|\w+(?:\s+\w+)*)",
            
            # Relacje funkcjonalne i zawodowe
            r"(\w+(?:\s+\w+)*)\s+(works for|is employed by|serves as)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(pracuje dla|jest zatrudniony w|pełni funkcję)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje tworzenia i autorstwa
            r"(\w+(?:\s+\w+)*)\s+(created|developed|invented|founded|established)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(stworzył|opracował|wynalazł|założył|ustanowił)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje wykorzystania i zastosowania
            r"(\w+(?:\s+\w+)*)\s+(uses|utilizes|employs|applies)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(wykorzystuje|używa|stosuje|aplikuje)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje podobieństwa i różnicy
            r"(\w+(?:\s+\w+)*)\s+(is similar to|resembles|is like)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(jest podobny do|przypomina|jest jak)\s+(\w+(?:\s+\w+)*)",
            
            # Relacje hierarchiczne
            r"(\w+(?:\s+\w+)*)\s+(is based on|derives from|extends)\s+(\w+(?:\s+\w+)*)",
            r"(\w+(?:\s+\w+)*)\s+(bazuje na|wywodzi się z|rozszerza)\s+(\w+(?:\s+\w+)*)",
        ]
        
        for pattern in relation_patterns:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                # Obsługa różnych formatów grup (2, 3 lub 4 elementy)
                if len(groups) == 4:  # format: entity1, relation, optional_word, entity2
                    entity1, relation, optional, entity2 = groups
                    if optional and optional.lower() in ['a', 'an', 'to']:
                        relation = f"{relation} {optional}"
                elif len(groups) == 3:  # format: entity1, relation, entity2
                    entity1, relation, entity2 = groups
                else:
                    continue  # Pomiń niepasujące wzorce
                
                # Oczyść encje z białych znaków
                entity1 = entity1.strip()
                entity2 = entity2.strip()
                
                # Pomiń bardzo krótkie encje
                if len(entity1) < 2 or len(entity2) < 2:
                    continue
                
                fact_content = f"{entity1} {relation} {entity2}"
                confidence = self._calculate_relation_confidence(entity1, relation, entity2)
                
                if confidence >= self._confidence_threshold:
                    fact = Fact(
                        content=fact_content,
                        confidence=confidence,
                        source_fragment_id=fragment_id,
                        entities=[entity1, entity2],
                        fact_type="relation",
                        created_at=datetime.now(),
                        metadata={
                            "entity1": entity1,
                            "relation": relation,
                            "entity2": entity2,
                            "pattern": pattern
                        }
                    )
                    facts.append(fact)
        
        return facts
    
    def _extract_temporal_facts(self, doc, fragment_id: int) -> List[Fact]:
        """Ekstraktuje fakty czasowe"""
        facts = []
        
        # Znajdź daty i czasy
        temporal_entities = [ent for ent in doc.ents if ent.label_ in ["DATE", "TIME"]]
        
        for entity in temporal_entities:
            fact_content = f"Temporal reference: {entity.text}"
            confidence = 0.8  # Wysoka pewność dla dat
            
            fact = Fact(
                content=fact_content,
                confidence=confidence,
                source_fragment_id=fragment_id,
                entities=[entity.text],
                fact_type="temporal",
                created_at=datetime.now(),
                metadata={
                    "temporal_text": entity.text,
                    "temporal_label": entity.label_
                }
            )
            facts.append(fact)
        
        return facts
    
    def _extract_numerical_facts(self, doc, fragment_id: int) -> List[Fact]:
        """Ekstraktuje fakty numeryczne"""
        facts = []
        
        # Znajdź liczby
        numerical_entities = [ent for ent in doc.ents if ent.label_ in ["CARDINAL", "ORDINAL", "MONEY", "PERCENT"]]
        
        for entity in numerical_entities:
            fact_content = f"Numerical value: {entity.text}"
            confidence = 0.9  # Bardzo wysoka pewność dla liczb
            
            fact = Fact(
                content=fact_content,
                confidence=confidence,
                source_fragment_id=fragment_id,
                entities=[entity.text],
                fact_type="numerical",
                created_at=datetime.now(),
                metadata={
                    "numerical_text": entity.text,
                    "numerical_label": entity.label_
                }
            )
            facts.append(fact)
        
        return facts
    
    def _calculate_entity_confidence(self, entity_text: str, label: str) -> float:
        """Oblicza pewność dla faktów o encjach"""
        base_confidence = 0.5
        
        # Zwiększ pewność dla dłuższych encji
        if len(entity_text.split()) > 1:
            base_confidence += 0.2
        
        # Zwiększ pewność dla konkretnych typów encji
        if label in ["PERSON", "ORG", "GPE"]:
            base_confidence += 0.3
        
        return min(base_confidence, 1.0)
    
    def _calculate_relation_confidence(self, entity1: str, relation: str, entity2: str) -> float:
        """Oblicza pewność dla faktów o relacjach"""
        base_confidence = 0.6
        
        # Zwiększ pewność dla konkretnych relacji
        if relation.lower() in ["is", "was", "are", "were"]:
            base_confidence += 0.2
        
        # Zwiększ pewność dla dłuższych encji
        if len(entity1.split()) > 1 and len(entity2.split()) > 1:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def get_fact_statistics(self, facts: List[Fact]) -> Dict[str, Any]:
        """Zwraca statystyki o faktach"""
        if not facts:
            return {"total": 0, "by_type": {}, "avg_confidence": 0.0}
        
        by_type = {}
        for fact in facts:
            by_type[fact.fact_type] = by_type.get(fact.fact_type, 0) + 1
        
        avg_confidence = sum(fact.confidence for fact in facts) / len(facts)
        
        return {
            "total": len(facts),
            "by_type": by_type,
            "avg_confidence": avg_confidence,
            "high_confidence": len([f for f in facts if f.confidence > 0.8])
        }


# Global instance
fact_extraction_service = FactExtractionService()
