#!/usr/bin/env python3
"""
Prosty skrypt do dodania przykładowych artykułów historycznych do bazy danych
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.database_models import Article, Tag, Fragment, article_tag
from datetime import datetime

def create_sample_articles():
    """Tworzy przykładowe artykuły historyczne"""
    db = SessionLocal()
    
    try:
        # Sprawdź czy już są artykuły
        existing_count = db.query(Article).count()
        if existing_count > 0:
            print(f"Baza już zawiera {existing_count} artykułów. Pomijam dodawanie.")
            return
        
        # Przykładowe tagi
        tags_data = [
            "historia", "średniowiecze", "bitwy", "Jagiełło", "Krzyżacy",
            "konstytucja", "reformy", "Stanisław August", "oświecenie", "XVIII wiek",
            "powstanie", "II wojna światowa", "Warszawa", "AK", "1944",
            "chrzest", "Mieszko I", "966", "chrześcijaństwo", "początki Polski",
            "unia", "Lublin", "1569", "Rzeczpospolita", "Litwa",
            "Solidarność", "Wałęsa", "stan wojenny", "1980", "demokracja"
        ]
        
        # Tworzenie tagów
        tag_objects = {}
        for tag_name in tags_data:
            tag = Tag(name=tag_name)
            db.add(tag)
            tag_objects[tag_name] = tag
        
        db.flush()  # Zapisz tagi, aby uzyskać ID
        
        # Przykładowe artykuły
        articles_data = [
            {
                "title": "Bitwa pod Grunwaldem 1410",
                "content": """Bitwa pod Grunwaldem, stoczona 15 lipca 1410 roku, była jedną z najważniejszych bitew w historii Polski i Europy Środkowej. Wojska polsko-litewskie pod dowództwem króla Władysława II Jagiełły pokonały armię Zakonu Krzyżackiego.

W bitwie wzięło udział około 39 000 żołnierzy po stronie polsko-litewskiej oraz około 27 000 po stronie krzyżackiej. Była to jedna z największych bitew średniowiecznej Europy.

Przebieg bitwy rozpoczął się rano 15 lipca 1410 roku, gdy armie stanęły naprzeciw siebie na polach między wsiami Grunwald i Tannenberg. Decydujący moment nastąpił, gdy zginął wielki mistrz Ulrich von Jungingen.

Skutki bitwy obejmowały załamanie potęgi militarnej Zakonu Krzyżackiego, umocnienie pozycji Polski i Litwy w regionie oraz początek upadku państwa krzyżackiego w Prusach.""",
                "tags": ["historia", "średniowiecze", "bitwy", "Jagiełło", "Krzyżacy"]
            },
            {
                "title": "Konstytucja 3 Maja 1791",
                "content": """Konstytucja 3 maja 1791 roku była pierwszą nowoczesną konstytucją w Europie i drugą na świecie po amerykańskiej z 1787 roku. Została uchwalona przez Sejm Wielki Rzeczypospolitej Obojga Narodów.

Główne postanowienia Konstytucji wprowadzały monarchię konstytucyjną z dziedzicznym tronem, podział władzy na ustawodawczą, wykonawczą i sądowniczą, zniesienie liberum veto oraz wzmocnienie władzy królewskiej.

Autorami i twórcami byli Stanisław August Poniatowski, Hugo Kołłątaj, Ignacy Potocki i Stanisław Małachowski. Konstytucja była próbą reformy ustroju Rzeczypospolitej znajdującej się w głębokim kryzysie.

Reakcje obejmowały entuzjazm części społeczeństwa polskiego, sprzeciw konserwatywnej szlachty oraz interwencję zbrojną Rosji, co doprowadziło do drugiego rozbioru Polski w 1793 roku.""",
                "tags": ["konstytucja", "reformy", "Stanisław August", "oświecenie", "XVIII wiek"]
            },
            {
                "title": "Powstanie Warszawskie 1944",
                "content": """Powstanie Warszawskie było największą akcją zbrojną polskiego podziemia podczas II wojny światowej. Trwało od 1 sierpnia do 2 października 1944 roku i miało na celu wyzwolenie Warszawy spod okupacji niemieckiej.

Przyczyny wybuchu powstania obejmowały zbliżanie się Armii Czerwonej do Warszawy, chęć wyzwolenia stolicy własnymi siłami oraz dążenie do odzyskania niepodległości przed wkroczeniem Sowietów.

Siły powstańcze liczyły około 40 000 żołnierzy Armii Krajowej, Batalionów Chłopskich, Armii Ludowej oraz ochotników cywilnych. Dowódcami byli gen. Tadeusz Bór-Komorowski i gen. Antoni Chruściel "Monter".

Skutki powstania były tragiczne - śmierć około 200 000 cywilów, zniszczenie 85% zabudowy Warszawy oraz deportacja pozostałej ludności. Powstanie pozostaje symbolem heroizmu i walki o wolność.""",
                "tags": ["powstanie", "II wojna światowa", "Warszawa", "AK", "1944"]
            },
            {
                "title": "Chrzest Polski 966",
                "content": """Chrzest Polski w 966 roku był momentem przełomowym w historii państwa polskiego. Książę Mieszko I przyjął chrzest w obrządku łacińskim, co miało ogromne znaczenie polityczne i kulturowe.

Kontekst polityczny obejmował ekspansję Rzeszy Niemieckiej na wschód, zagrożenie ze strony Marchii Północnej oraz potrzebę sojuszy z chrześcijańskimi władcami w celu wzmocnienia pozycji międzynarodowej.

Przyczyny przyjęcia chrztu były związane z małżeństwem z czeską księżniczką Dobrawą, presją polityczną ze strony Ottona I oraz chęcią uniknięcia chrystianizacji siłą.

Znaczenie religijne obejmowało wprowadzenie chrześcijaństwa jako religii państwowej, budowę pierwszych kościołów i klasztorów oraz początek organizacji kościelnej w Polsce. Długofalowe skutki zadecydowały o trwałym związaniu Polski z cywilizacją zachodnią.""",
                "tags": ["chrzest", "Mieszko I", "966", "chrześcijaństwo", "początki Polski"]
            },
            {
                "title": "Unia Lubelska 1569",
                "content": """Unia Lubelska, podpisana 1 lipca 1569 roku w Lublinie, była aktem prawnym łączącym Królestwo Polskie i Wielkie Księstwo Litewskie w jedno państwo - Rzeczpospolitą Obojga Narodów.

Przyczyny zawarcia unii obejmowały zagrożenie ze strony Rosji Iwana Groźnego, wojnę o Inflanty oraz potrzebę wzmocnienia militarnego. Negocjacje w sejmie lubelskim trwały od stycznia do lipca 1569 roku.

Główne postanowienia unii wprowadzały wspólny sejm, senat i króla, wspólną politykę zagraniczną i obronną oraz wspólną monetę, zachowując jednocześnie odrębność prawną i administracyjną Litwy.

Znaczenie historyczne obejmowało powstanie największego państwa w Europie XVI wieku, utworzenie unikalnego systemu politycznego oraz rozwój kultury szlacheckiej. Unia była jednym z najważniejszych aktów w historii Polski i Litwy.""",
                "tags": ["unia", "Lublin", "1569", "Rzeczpospolita", "Litwa"]
            },
            {
                "title": "Solidarność i transformacja 1980-1989",
                "content": """Ruch Solidarność, powstały w 1980 roku, był pierwszym niezależnym związkiem zawodowym w krajach komunistycznych. Jego działalność doprowadziła do upadku komunizmu w Polsce i zapoczątkowała przemiany demokratyczne.

Geneza Solidarności związana była ze strajkami w Stoczni Gdańskiej w sierpniu 1980 roku pod przywództwem Lecha Wałęsy. Porozumienia Sierpniowe z 31 sierpnia 1980 roku doprowadziły do rejestracji NSZZ "Solidarność" 10 listopada 1980.

Stan wojenny wprowadzony 13 grudnia 1981 roku przez gen. Jaruzelskiego spowodował internowanie przywódców Solidarności i delegalizację związku. Ruch przeszedł do podziemia, kontynuując działalność przez całe lata 80.

Okrągły Stół w 1989 roku doprowadził do porozumienia między władzą a opozycją, częściowo wolnych wyborów 4 czerwca 1989 oraz zwycięstwa Solidarności, co oznaczało początek transformacji ustrojowej.""",
                "tags": ["Solidarność", "Wałęsa", "stan wojenny", "1980", "demokracja"]
            }
        ]
        
        # Tworzenie artykułów
        for i, article_data in enumerate(articles_data, 1):
            article = Article(
                title=article_data["title"],
                file_path=f"historical_article_{i}.txt",
                file_type="text/plain",
                status="zindeksowany",
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="system"
            )
            
            db.add(article)
            db.flush()  # Zapisz artykuł, aby uzyskać ID
            
            # Dodaj tagi do artykułu
            for tag_name in article_data["tags"]:
                if tag_name in tag_objects:
                    article.tags.append(tag_objects[tag_name])
            
            # Utwórz fragment z zawartością
            fragment = Fragment(
                article_id=article.id,
                content=article_data["content"],
                start_position=0,
                end_position=len(article_data["content"])
            )
            db.add(fragment)
            
            print(f"✅ Utworzono artykuł: {article.title}")
        
        db.commit()
        print(f"\n🎉 Pomyślnie utworzono {len(articles_data)} artykułów historycznych!")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia artykułów: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("📚 Dodawanie przykładowych artykułów historycznych do bazy danych")
    print("=" * 60)
    create_sample_articles()
    print("✨ Gotowe! System jest teraz wypełniony danymi do demonstracji.")