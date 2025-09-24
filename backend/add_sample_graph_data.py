#!/usr/bin/env python3
"""
Skrypt do dodania przykładowych danych grafu wiedzy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.database_models import Entity as EntityModel, Relation as RelationModel, Fact as FactModel, Article as ArticleModel, Fragment as FragmentModel

def add_sample_data():
    """Dodaje przykładowe dane do bazy"""
    db: Session = SessionLocal()
    
    try:
        print("Dodaję przykładowe artykuły...")
        
        # Dodaj przykładowe artykuły
        article1 = ArticleModel(
            title="Wprowadzenie do RAG",
            file_path="/sample/rag_intro.txt",
            file_type="text",
            status="zindeksowany",
            created_by="System",
            indexed=True
        )
        
        article2 = ArticleModel(
            title="Modele językowe i AI",
            file_path="/sample/ai_models.txt", 
            file_type="text",
            status="zindeksowany",
            created_by="System",
            indexed=True
        )
        
        db.add(article1)
        db.add(article2)
        db.commit()
        db.refresh(article1)
        db.refresh(article2)
        
        print("Dodaję przykładowe fragmenty...")
        
        # Dodaj fragmenty
        fragment1 = FragmentModel(
            article_id=article1.id,
            content="RAG (Retrieval-Augmented Generation) to technika łącząca wyszukiwanie informacji z generowaniem tekstu.",
            start_position=0,
            end_position=100,
            indexed=True
        )
        
        fragment2 = FragmentModel(
            article_id=article1.id,
            content="Istnieją różne warianty RAG: TekstRAG, FaktRAG i GrafRAG.",
            start_position=101,
            end_position=160,
            indexed=True
        )
        
        fragment3 = FragmentModel(
            article_id=article2.id,
            content="Modele językowe to systemy AI wykorzystujące uczenie maszynowe do przetwarzania języka naturalnego.",
            start_position=0,
            end_position=95,
            indexed=True
        )
        
        db.add(fragment1)
        db.add(fragment2)
        db.add(fragment3)
        db.commit()
        db.refresh(fragment1)
        db.refresh(fragment2)
        db.refresh(fragment3)
        
        print("Dodaję przykładowe encje...")
        
        # Dodaj encje
        entities_data = [
            {"name": "RAG", "type": "Technologia"},
            {"name": "TekstRAG", "type": "Technologia"},
            {"name": "FaktRAG", "type": "Technologia"},
            {"name": "GrafRAG", "type": "Technologia"},
            {"name": "modele językowe", "type": "Narzędzie"},
            {"name": "uczenie maszynowe", "type": "Metoda"},
            {"name": "AI", "type": "Dziedzina"},
            {"name": "język naturalny", "type": "Koncepcja"},
        ]
        
        entities = []
        for entity_data in entities_data:
            entity = EntityModel(**entity_data)
            db.add(entity)
            entities.append(entity)
        
        db.commit()
        for entity in entities:
            db.refresh(entity)
        
        print("Dodaję przykładowe fakty...")
        
        # Dodaj fakty
        facts_data = [
            {
                "content": "RAG łączy wyszukiwanie informacji z generowaniem tekstu",
                "source_fragment_id": fragment1.id,
                "status": "zatwierdzony"
            },
            {
                "content": "Istnieją trzy warianty RAG: TekstRAG, FaktRAG i GrafRAG",
                "source_fragment_id": fragment2.id,
                "status": "zatwierdzony"
            },
            {
                "content": "Modele językowe wykorzystują uczenie maszynowe",
                "source_fragment_id": fragment3.id,
                "status": "zatwierdzony"
            },
        ]
        
        facts = []
        for fact_data in facts_data:
            fact = FactModel(**fact_data)
            db.add(fact)
            facts.append(fact)
        
        db.commit()
        for fact in facts:
            db.refresh(fact)
        
        print("Dodaję przykładowe relacje...")
        
        # Znajdź encje po nazwach
        rag_entity = next(e for e in entities if e.name == "RAG")
        tekstrag_entity = next(e for e in entities if e.name == "TekstRAG")
        faktrag_entity = next(e for e in entities if e.name == "FaktRAG")
        grafrag_entity = next(e for e in entities if e.name == "GrafRAG")
        modele_entity = next(e for e in entities if e.name == "modele językowe")
        ml_entity = next(e for e in entities if e.name == "uczenie maszynowe")
        ai_entity = next(e for e in entities if e.name == "AI")
        jezyk_entity = next(e for e in entities if e.name == "język naturalny")
        
        # Dodaj relacje
        relations_data = [
            {
                "source_entity_id": rag_entity.id,
                "target_entity_id": tekstrag_entity.id,
                "relation_type": "ZAWIERA",
                "weight": 0.9
            },
            {
                "source_entity_id": rag_entity.id,
                "target_entity_id": faktrag_entity.id,
                "relation_type": "ZAWIERA",
                "weight": 0.8
            },
            {
                "source_entity_id": rag_entity.id,
                "target_entity_id": grafrag_entity.id,
                "relation_type": "ZAWIERA",
                "weight": 0.7
            },
            {
                "source_entity_id": modele_entity.id,
                "target_entity_id": ml_entity.id,
                "relation_type": "WYKORZYSTUJE",
                "weight": 0.9
            },
            {
                "source_entity_id": modele_entity.id,
                "target_entity_id": ai_entity.id,
                "relation_type": "JEST_CZĘŚCIĄ",
                "weight": 0.8
            },
            {
                "source_entity_id": modele_entity.id,
                "target_entity_id": jezyk_entity.id,
                "relation_type": "PRZETWARZA",
                "weight": 0.9
            },
            {
                "source_entity_id": rag_entity.id,
                "target_entity_id": modele_entity.id,
                "relation_type": "WYKORZYSTUJE",
                "weight": 0.8
            },
        ]
        
        for relation_data in relations_data:
            relation = RelationModel(**relation_data)
            db.add(relation)
        
        db.commit()
        
        print("✅ Przykładowe dane zostały dodane pomyślnie!")
        print(f"Dodano {len(entities)} encji")
        print(f"Dodano {len(relations_data)} relacji")
        print(f"Dodano {len(facts)} faktów")
        print(f"Dodano 2 artykuły z 3 fragmentami")
        
    except Exception as e:
        print(f"❌ Błąd podczas dodawania danych: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()