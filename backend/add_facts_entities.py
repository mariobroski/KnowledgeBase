#!/usr/bin/env python3
"""
Skrypt do dodania przykładowych faktów i encji dla demonstracji
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.database_models import Article, Fragment, Fact, Entity, Relation
from datetime import datetime

def add_facts_and_entities():
    """Dodaje przykładowe fakty i encje do istniejących artykułów"""
    db = SessionLocal()
    
    try:
        # Pobierz fragmenty artykułów
        fragments = db.query(Fragment).all()
        
        if not fragments:
            print("❌ Brak fragmentów w bazie danych")
            return
        
        # Przykładowe encje
        entities_data = [
            {"name": "Bolesław Chrobry", "type": "osoba", "aliases": ["Bolesław I Chrobry"]},
            {"name": "Mieszko I", "type": "osoba", "aliases": ["Mieszko I Piastowicz"]},
            {"name": "Bitwa pod Grunwaldem", "type": "wydarzenie", "aliases": ["Bitwa pod Tannenbergiem"]},
            {"name": "Zakon Krzyżacki", "type": "organizacja", "aliases": ["Krzyżacy"]},
            {"name": "Uniwersytet Jagielloński", "type": "instytucja", "aliases": ["UJ", "Akademia Krakowska"]},
            {"name": "Konstytucja 3 Maja", "type": "dokument", "aliases": ["Konstytucja 3 maja 1791"]},
            {"name": "Kraków", "type": "miejsce", "aliases": ["Cracovia"]},
            {"name": "Warszawa", "type": "miejsce", "aliases": ["Varsovia"]},
            {"name": "Władysław Jagiełło", "type": "osoba", "aliases": ["Władysław II Jagiełło"]},
            {"name": "Jadwiga Andegaweńska", "type": "osoba", "aliases": ["Święta Jadwiga"]},
            {"name": "Kazimierz Wielki", "type": "osoba", "aliases": ["Kazimierz III Wielki"]},
            {"name": "Dynastia Piastów", "type": "dynastia", "aliases": ["Piastowie"]},
            {"name": "Dynastia Jagiellonów", "type": "dynastia", "aliases": ["Jagiellonowie"]},
            {"name": "Rzeczpospolita Obojga Narodów", "type": "państwo", "aliases": ["I Rzeczpospolita"]},
            {"name": "Sejm", "type": "instytucja", "aliases": ["Parlament"]},
            {"name": "Liberum veto", "type": "prawo", "aliases": ["Prawo liberum veto"]},
            {"name": "Konfederacja Barska", "type": "organizacja", "aliases": ["Konfederaci barscy"]},
            {"name": "Stanisław August Poniatowski", "type": "osoba", "aliases": ["Stanisław II August"]},
            {"name": "Tadeusz Kościuszko", "type": "osoba", "aliases": ["Naczelnik Kościuszko"]},
            {"name": "Powstanie Kościuszkowskie", "type": "wydarzenie", "aliases": ["Insurekcja kościuszkowska"]},
            {"name": "Rozbiory Polski", "type": "wydarzenie", "aliases": ["Rozbiory Rzeczypospolitej"]},
            {"name": "Prusy", "type": "państwo", "aliases": ["Królestwo Prus"]},
            {"name": "Austria", "type": "państwo", "aliases": ["Cesarstwo Austriackie"]},
            {"name": "Rosja", "type": "państwo", "aliases": ["Imperium Rosyjskie"]}
        ]
        
        # Tworzenie encji
        entity_objects = {}
        for entity_data in entities_data:
            entity = Entity(
                    name=entity_data["name"],
                    type=entity_data["type"],
                    aliases=entity_data.get("aliases", [])
                )
            db.add(entity)
            entity_objects[entity_data["name"]] = entity
        
        db.flush()  # Zapisz encje, aby uzyskać ID
        print(f"✅ Utworzono {len(entities_data)} encji")
        
        # Przykładowe fakty dla każdego fragmentu
        facts_data = [
            {
                "content": "Bitwa pod Grunwaldem została stoczona 15 lipca 1410 roku",
                "confidence": 0.95,
                "entities": ["Bitwa pod Grunwaldem", "1410"]
            },
            {
                "content": "Władysław II Jagiełło dowodził wojskami polsko-litewskimi",
                "confidence": 0.98,
                "entities": ["Władysław II Jagiełło", "Bitwa pod Grunwaldem"]
            },
            {
                "content": "W bitwie zginął wielki mistrz Ulrich von Jungingen",
                "confidence": 0.92,
                "entities": ["Bitwa pod Grunwaldem", "Zakon Krzyżacki"]
            },
            {
                "content": "Konstytucja 3 maja została uchwalona w 1791 roku",
                "confidence": 0.99,
                "entities": ["Konstytucja 3 Maja", "1791"]
            },
            {
                "content": "Stanisław August Poniatowski był królem Polski podczas uchwalania konstytucji",
                "confidence": 0.96,
                "entities": ["Stanisław August Poniatowski", "Konstytucja 3 Maja"]
            },
            {
                "content": "Konstytucja była pierwszą nowoczesną konstytucją w Europie",
                "confidence": 0.94,
                "entities": ["Konstytucja 3 Maja"]
            },
            {
                "content": "Powstanie Warszawskie trwało od 1 sierpnia do 2 października 1944 roku",
                "confidence": 0.99,
                "entities": ["Powstanie Warszawskie", "1944", "Warszawa"]
            },
            {
                "content": "Tadeusz Bór-Komorowski był komendantem głównym AK",
                "confidence": 0.97,
                "entities": ["Tadeusz Bór-Komorowski", "Armia Krajowa"]
            },
            {
                "content": "W powstaniu zginęło około 200 000 cywilów",
                "confidence": 0.90,
                "entities": ["Powstanie Warszawskie", "Warszawa"]
            },
            {
                "content": "Mieszko I przyjął chrzest w 966 roku",
                "confidence": 0.98,
                "entities": ["Mieszko I", "Chrzest Polski", "966"]
            },
            {
                "content": "Chrzest Polski rozpoczął nowy rozdział w dziejach narodu",
                "confidence": 0.93,
                "entities": ["Chrzest Polski", "Mieszko I"]
            },
            {
                "content": "Unia Lubelska została podpisana 1 lipca 1569 roku",
                "confidence": 0.99,
                "entities": ["Unia Lubelska", "1569", "Lublin"]
            },
            {
                "content": "Unia połączyła Królestwo Polskie i Wielkie Księstwo Litewskie",
                "confidence": 0.98,
                "entities": ["Unia Lubelska", "Rzeczpospolita Obojga Narodów"]
            },
            {
                "content": "Solidarność powstała w 1980 roku w Gdańsku",
                "confidence": 0.99,
                "entities": ["NSZZ Solidarność", "1980", "Gdańsk"]
            },
            {
                "content": "Lech Wałęsa był przywódcą strajkujących w Stoczni Gdańskiej",
                "confidence": 0.97,
                "entities": ["Lech Wałęsa", "NSZZ Solidarność", "Gdańsk"]
            },
            {
                "content": "Solidarność była pierwszym niezależnym związkiem zawodowym w bloku wschodnim",
                "confidence": 0.95,
                "entities": ["NSZZ Solidarność"]
            }
        ]
        
        # Tworzenie faktów
        fact_count = 0
        for i, fragment in enumerate(fragments[:len(facts_data)]):
            fact_data = facts_data[i]
            
            fact = Fact(
                content=fact_data["content"],
                confidence=fact_data["confidence"],
                status="verified",
                source_fragment_id=fragment.id,
                created_at=datetime.utcnow()
            )
            db.add(fact)
            db.flush()  # Zapisz fakt, aby uzyskać ID
            
            # Dodaj powiązania z encjami
            for entity_name in fact_data["entities"]:
                if entity_name in entity_objects:
                    fact.entities.append(entity_objects[entity_name])
            
            fact_count += 1
            print(f"✅ Utworzono fakt: {fact.content[:50]}...")
        
        # Dodawanie relacji między encjami
        relations_data = [
            {"source": "Władysław Jagiełło", "target": "Bitwa pod Grunwaldem", "type": "DOWODZIŁ", "weight": 0.95},
            {"source": "Zakon Krzyżacki", "target": "Bitwa pod Grunwaldem", "type": "UCZESTNICZYŁ", "weight": 0.95},
            {"source": "Stanisław August Poniatowski", "target": "Konstytucja 3 Maja", "type": "PODPISAŁ", "weight": 0.90},
            {"source": "Tadeusz Kościuszko", "target": "Powstanie Kościuszkowskie", "type": "DOWODZIŁ", "weight": 0.95},
            {"source": "Mieszko I", "target": "Dynastia Piastów", "type": "NALEŻAŁ_DO", "weight": 0.95},
            {"source": "Władysław Jagiełło", "target": "Dynastia Jagiellonów", "type": "ZAŁOŻYŁ", "weight": 0.90},
            {"source": "Kraków", "target": "Uniwersytet Jagielloński", "type": "ZNAJDUJE_SIĘ", "weight": 0.95},
            {"source": "Rzeczpospolita Obojga Narodów", "target": "Sejm", "type": "MIAŁA", "weight": 0.90}
        ]
        
        # Tworzenie relacji
        relation_count = 0
        for relation_data in relations_data:
            source_entity = entity_objects.get(relation_data["source"])
            target_entity = entity_objects.get(relation_data["target"])
            
            if source_entity and target_entity:
                relation = Relation(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relation_type=relation_data["type"],
                    weight=relation_data["weight"]
                )
                db.add(relation)
                relation_count += 1
                print(f"✅ Utworzono relację: {relation_data['source']} -> {relation_data['target']}")
            else:
                print(f"⚠️ Nie można utworzyć relacji: {relation_data['source']} -> {relation_data['target']}")
        
        db.commit()
        
        print(f"\n🎉 Podsumowanie:")
        print(f"   Encje: {len(entities_data)}")
        print(f"   Fakty: {fact_count}")
        print(f"   Relacje: {relation_count}")
        print("✨ System jest teraz wypełniony danymi do pełnej demonstracji!")
        
    except Exception as e:
        print(f"❌ Błąd podczas dodawania faktów i encji: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧠 Dodawanie faktów i encji do systemu")
    print("=" * 40)
    add_facts_and_entities()