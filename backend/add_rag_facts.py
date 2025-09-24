#!/usr/bin/env python3
"""
Skrypt do dodania faktów i encji związanych z RAG/AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.database_models import Article, Fragment, Fact, Entity, Relation
from datetime import datetime

def add_rag_facts_and_entities():
    """Dodaje fakty i encje związane z RAG/AI do artykułów"""
    db = SessionLocal()
    
    try:
        # Pobierz fragmenty artykułów
        fragments = db.query(Fragment).all()
        
        if not fragments:
            print("❌ Brak fragmentów w bazie danych")
            return
        
        # Usuń istniejące fakty i encje (jeśli są z poprzedniego skryptu)
        db.query(Relation).delete()
        db.query(Fact).delete()
        db.query(Entity).delete()
        db.commit()
        
        # Encje związane z RAG/AI
        entities_data = [
            {"name": "RAG", "type": "technologia", "aliases": ["Retrieval-Augmented Generation"]},
            {"name": "BERT", "type": "model", "aliases": ["Bidirectional Encoder Representations from Transformers"]},
            {"name": "GPT", "type": "model", "aliases": ["Generative Pre-trained Transformer"]},
            {"name": "Transformer", "type": "architektura", "aliases": ["Transformer Architecture"]},
            {"name": "Embeddings", "type": "technologia", "aliases": ["Word Embeddings", "Sentence Embeddings"]},
            {"name": "Vector Database", "type": "technologia", "aliases": ["Baza danych wektorowych"]},
            {"name": "Semantic Search", "type": "technologia", "aliases": ["Wyszukiwanie semantyczne"]},
            {"name": "NLP", "type": "dziedzina", "aliases": ["Natural Language Processing", "Przetwarzanie języka naturalnego"]},
            {"name": "Machine Learning", "type": "dziedzina", "aliases": ["ML", "Uczenie maszynowe"]},
            {"name": "Deep Learning", "type": "dziedzina", "aliases": ["Głębokie uczenie"]},
            {"name": "Neural Networks", "type": "technologia", "aliases": ["Sieci neuronowe"]},
            {"name": "Attention Mechanism", "type": "technologia", "aliases": ["Mechanizm uwagi"]},
            {"name": "Fine-tuning", "type": "technika", "aliases": ["Dostrajanie modelu"]},
            {"name": "Prompt Engineering", "type": "technika", "aliases": ["Inżynieria promptów"]},
            {"name": "Knowledge Base", "type": "system", "aliases": ["Baza wiedzy"]},
            {"name": "Information Retrieval", "type": "dziedzina", "aliases": ["Wyszukiwanie informacji"]},
            {"name": "Text Generation", "type": "zadanie", "aliases": ["Generowanie tekstu"]},
            {"name": "Question Answering", "type": "zadanie", "aliases": ["QA", "Systemy pytań i odpowiedzi"]},
            {"name": "Cosine Similarity", "type": "metryka", "aliases": ["Podobieństwo kosinusowe"]},
            {"name": "FAISS", "type": "biblioteka", "aliases": ["Facebook AI Similarity Search"]},
            {"name": "Pinecone", "type": "usługa", "aliases": ["Pinecone Vector Database"]},
            {"name": "Chroma", "type": "biblioteka", "aliases": ["ChromaDB"]},
            {"name": "LangChain", "type": "framework", "aliases": ["LangChain Framework"]},
            {"name": "OpenAI", "type": "organizacja", "aliases": ["OpenAI Inc."]},
            {"name": "Hugging Face", "type": "platforma", "aliases": ["HF", "Hugging Face Hub"]},
            {"name": "BLEU", "type": "metryka", "aliases": ["Bilingual Evaluation Understudy"]},
            {"name": "ROUGE", "type": "metryka", "aliases": ["Recall-Oriented Understudy for Gisting Evaluation"]},
            {"name": "Hallucination", "type": "problem", "aliases": ["Halucynacje AI"]},
            {"name": "Context Window", "type": "ograniczenie", "aliases": ["Okno kontekstu"]},
            {"name": "Token", "type": "jednostka", "aliases": ["Token tekstowy"]}
        ]
        
        # Tworzenie encji
        entity_objects = {}
        for entity_data in entities_data:
            entity = Entity(
                name=entity_data["name"],
                type=entity_data["type"],
                aliases=entity_data["aliases"],
                created_at=datetime.utcnow()
            )
            db.add(entity)
            entity_objects[entity_data["name"]] = entity
        
        db.flush()  # Zapisz encje, aby uzyskać ID
        
        # Fakty związane z RAG/AI
        facts_data = [
            {
                "content": "RAG łączy wyszukiwanie informacji z generowaniem tekstu w celu tworzenia dokładniejszych odpowiedzi",
                "confidence": 0.95,
                "source_fragment_id": fragments[0].id if fragments else None,
                "entities": ["RAG", "Text Generation", "Information Retrieval"]
            },
            {
                "content": "BERT wykorzystuje bidirectional attention do lepszego zrozumienia kontekstu w tekście",
                "confidence": 0.92,
                "source_fragment_id": fragments[1].id if len(fragments) > 1 else fragments[0].id,
                "entities": ["BERT", "Attention Mechanism", "NLP"]
            },
            {
                "content": "Embeddingi przekształcają tekst na numeryczne reprezentacje umożliwiające wyszukiwanie semantyczne",
                "confidence": 0.94,
                "source_fragment_id": fragments[1].id if len(fragments) > 1 else fragments[0].id,
                "entities": ["Embeddings", "Semantic Search", "Vector Database"]
            },
            {
                "content": "GPT to autoregressive model językowy generujący tekst token po token",
                "confidence": 0.96,
                "source_fragment_id": fragments[3].id if len(fragments) > 3 else fragments[0].id,
                "entities": ["GPT", "Token", "Text Generation"]
            },
            {
                "content": "Fine-tuning pozwala dostosować pre-trenowane modele do konkretnych zadań i domen",
                "confidence": 0.93,
                "source_fragment_id": fragments[3].id if len(fragments) > 3 else fragments[0].id,
                "entities": ["Fine-tuning", "Machine Learning", "Deep Learning"]
            },
            {
                "content": "Cosine similarity jest najczęściej używaną metryką do porównywania embeddingów w systemach RAG",
                "confidence": 0.91,
                "source_fragment_id": fragments[1].id if len(fragments) > 1 else fragments[0].id,
                "entities": ["Cosine Similarity", "Embeddings", "RAG"]
            },
            {
                "content": "BLEU i ROUGE to standardowe metryki do ewaluacji jakości generowanego tekstu",
                "confidence": 0.89,
                "source_fragment_id": fragments[4].id if len(fragments) > 4 else fragments[0].id,
                "entities": ["BLEU", "ROUGE", "Text Generation"]
            },
            {
                "content": "Hallucination to problem modeli językowych polegający na generowaniu nieprawdziwych informacji",
                "confidence": 0.97,
                "source_fragment_id": fragments[3].id if len(fragments) > 3 else fragments[0].id,
                "entities": ["Hallucination", "GPT", "NLP"]
            },
            {
                "content": "Prompt engineering to technika optymalizacji instrukcji dla modeli językowych",
                "confidence": 0.88,
                "source_fragment_id": fragments[3].id if len(fragments) > 3 else fragments[0].id,
                "entities": ["Prompt Engineering", "GPT", "Fine-tuning"]
            },
            {
                "content": "FAISS to biblioteka Facebook do efektywnego wyszukiwania podobieństwa w dużych zbiorach wektorów",
                "confidence": 0.90,
                "source_fragment_id": fragments[1].id if len(fragments) > 1 else fragments[0].id,
                "entities": ["FAISS", "Vector Database", "Semantic Search"]
            }
        ]
        
        # Tworzenie faktów
        fact_objects = []
        for fact_data in facts_data:
            fact = Fact(
                content=fact_data["content"],
                confidence=fact_data["confidence"],
                source_fragment_id=fact_data["source_fragment_id"],
                status="zatwierdzony",
                created_at=datetime.utcnow()
            )
            db.add(fact)
            fact_objects.append((fact, fact_data["entities"]))
            print(f"✅ Utworzono fakt: {fact_data['content'][:50]}...")
        
        db.flush()  # Zapisz fakty, aby uzyskać ID
        
        # Relacje między encjami
        relations_data = [
            ("RAG", "Information Retrieval", "wykorzystuje"),
            ("RAG", "Text Generation", "łączy_z"),
            ("BERT", "Transformer", "bazuje_na"),
            ("GPT", "Transformer", "bazuje_na"),
            ("Embeddings", "Semantic Search", "umożliwia"),
            ("Fine-tuning", "Machine Learning", "jest_techniką"),
            ("BLEU", "Text Generation", "ewaluuje"),
            ("ROUGE", "Text Generation", "ewaluuje"),
            ("Prompt Engineering", "GPT", "optymalizuje"),
            ("FAISS", "Vector Database", "implementuje"),
            ("Cosine Similarity", "Embeddings", "porównuje"),
            ("Hallucination", "GPT", "problem_w")
        ]
        
        # Tworzenie relacji
        for entity1_name, entity2_name, relation_type in relations_data:
            if entity1_name in entity_objects and entity2_name in entity_objects:
                relation = Relation(
                    source_entity_id=entity_objects[entity1_name].id,
                    target_entity_id=entity_objects[entity2_name].id,
                    relation_type=relation_type,
                    created_at=datetime.utcnow()
                )
                db.add(relation)
                print(f"✅ Utworzono relację: {entity1_name} -> {entity2_name}")
        
        db.commit()
        
        print(f"\n🎉 Podsumowanie:")
        print(f"   Encje: {len(entities_data)}")
        print(f"   Fakty: {len(facts_data)}")
        print(f"   Relacje: {len(relations_data)}")
        print("✨ System RAG jest teraz wypełniony danymi związanymi z AI/ML!")
        
    except Exception as e:
        print(f"❌ Błąd podczas dodawania faktów i encji: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧠 Dodawanie faktów i encji RAG/AI do systemu")
    print("=" * 50)
    add_rag_facts_and_entities()