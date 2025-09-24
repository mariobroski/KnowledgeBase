#!/usr/bin/env python3
"""
Skrypt do wyczyszczenia bazy i dodania przykładowych artykułów historycznych
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.database_models import Article, Tag, Fragment, article_tag, Fact, Entity, Relation
from datetime import datetime

def clear_database():
    """Czyści bazę danych z istniejących artykułów"""
    db = SessionLocal()
    
    try:
        # Usuń w odpowiedniej kolejności ze względu na klucze obce
        db.query(Relation).delete()
        db.query(Fact).delete()
        db.query(Fragment).delete()
        db.execute(article_tag.delete())
        db.query(Article).delete()
        db.query(Tag).delete()
        db.query(Entity).delete()
        
        db.commit()
        print("🗑️  Wyczyszczono bazę danych")
        
    except Exception as e:
        print(f"❌ Błąd podczas czyszczenia bazy: {str(e)}")
        db.rollback()
    finally:
        db.close()

def create_sample_articles():
    """Tworzy przykładowe artykuły historyczne"""
    db = SessionLocal()
    
    try:
        # Przykładowe tagi
        tags_data = [
            "historia", "średniowiecze", "bitwy", "Jagiełło", "Krzyżacy",
            "konstytucja", "reformy", "Stanisław August", "oświecenie", "XVIII wiek",
            "powstanie", "II wojna światowa", "Warszawa", "AK", "1944",
            "chrzest", "Mieszko I", "966", "chrześcijaństwo", "początki Polski",
            "unia", "Lublin", "1569", "Rzeczpospolita", "Litwa",
            "Solidarność", "Wałęsa", "stan wojenny", "1980", "demokracja",
            "Piastowie", "Jagiellonowie", "szlachta", "kultura", "polityka"
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
                "title": "Bitwa pod Grunwaldem 1410 - Zwycięstwo nad Krzyżakami",
                "content": """Bitwa pod Grunwaldem, stoczona 15 lipca 1410 roku, była jedną z najważniejszych bitew w historii Polski i Europy Środkowej. Wojska polsko-litewskie pod dowództwem króla Władysława II Jagiełły pokonały armię Zakonu Krzyżackiego.

W bitwie wzięło udział około 39 000 żołnierzy po stronie polsko-litewskiej oraz około 27 000 po stronie krzyżackiej. Była to jedna z największych bitew średniowiecznej Europy.

Przebieg bitwy:
- Rano 15 lipca 1410 roku armie stanęły naprzeciw siebie na polach między wsiami Grunwald i Tannenberg
- Bitwa rozpoczęła się od ataku ciężkiej jazdy krzyżackiej na skrzydło litewskie
- Litwini początkowo cofnęli się, co było prawdopodobnie manewrem taktycznym
- Następnie do walki włączyły się wojska polskie pod dowództwem króla Jagiełły
- Decydujący moment nastąpił, gdy zginął wielki mistrz Ulrich von Jungingen

Skutki bitwy:
- Załamanie potęgi militarnej Zakonu Krzyżackiego
- Umocnienie pozycji Polski i Litwy w regionie
- Początek upadku państwa krzyżackiego w Prusach
- Wzmocnienie unii polsko-litewskiej

Bitwa pod Grunwaldem pozostaje jednym z najważniejszych zwycięstw w historii Polski.""",
                "tags": ["historia", "średniowiecze", "bitwy", "Jagiełło", "Krzyżacy"]
            },
            {
                "title": "Konstytucja 3 Maja 1791 - Pierwsza Konstytucja w Europie",
                "content": """Konstytucja 3 maja 1791 roku była pierwszą nowoczesną konstytucją w Europie i drugą na świecie po amerykańskiej z 1787 roku. Została uchwalona przez Sejm Wielki Rzeczypospolitej Obojga Narodów.

Główne postanowienia Konstytucji:
- Wprowadzenie monarchii konstytucyjnej z dziedzicznym tronem
- Podział władzy na ustawodawczą, wykonawczą i sądowniczą
- Zniesienie liberum veto
- Wzmocnienie władzy królewskiej
- Rozszerzenie praw mieszczaństwa
- Ochrona chłopów przed nadużyciami

Kontekst historyczny:
Konstytucja była próbą reformy ustroju Rzeczypospolitej, która znajdowała się w głębokim kryzysie. Słabość państwa wykorzystywały sąsiednie mocarstwa - Rosja, Prusy i Austria.

Autorzy i twórcy:
- Stanisław August Poniatowski - król Polski
- Hugo Kołłątaj - główny ideolog reform
- Ignacy Potocki - marszałek Sejmu Wielkiego
- Stanisław Małachowski - marszałek konfederacji

Konstytucja 3 maja pozostaje symbolem polskiego dążenia do wolności i reform demokratycznych.""",
                "tags": ["konstytucja", "reformy", "Stanisław August", "oświecenie", "XVIII wiek"]
            },
            {
                "title": "Powstanie Warszawskie 1944 - Heroiczna Walka o Wolność",
                "content": """Powstanie Warszawskie było największą akcją zbrojną polskiego podziemia podczas II wojny światowej. Trwało od 1 sierpnia do 2 października 1944 roku i miało na celu wyzwolenie Warszawy spod okupacji niemieckiej.

Przyczyny wybuchu powstania:
- Zbliżanie się Armii Czerwonej do Warszawy
- Chęć wyzwolenia stolicy własnymi siłami
- Dążenie do odzyskania niepodległości przed wkroczeniem Sowietów
- Rozkaz "Burza" Armii Krajowej

Siły powstańcze:
- Około 40 000 żołnierzy Armii Krajowej
- Bataliony Chłopskie
- Armia Ludowa
- Żydowska Organizacja Bojowa
- Ochotnicy cywilni

Dowódcy powstania:
- Gen. Tadeusz Bór-Komorowski - komendant główny AK
- Gen. Antoni Chruściel "Monter" - komendant Okręgu Warszawskiego AK

Skutki powstania:
- Śmierć około 200 000 cywilów
- Zniszczenie 85% zabudowy Warszawy
- Deportacja pozostałej ludności
- Likwidacja struktur polskiego państwa podziemnego

Powstanie Warszawskie pozostaje symbolem heroizmu i walki o wolność.""",
                "tags": ["powstanie", "II wojna światowa", "Warszawa", "AK", "1944"]
            },
            {
                "title": "Chrzest Polski 966 - Początek Chrześcijańskiej Polski",
                "content": """Chrzest Polski w 966 roku był momentem przełomowym w historii państwa polskiego. Książę Mieszko I przyjął chrzest w obrządku łacińskim, co miało ogromne znaczenie polityczne i kulturowe.

Kontekst polityczny:
- Ekspansja Rzeszy Niemieckiej na wschód
- Zagrożenie ze strony Marchii Północnej
- Potrzeba sojuszy z chrześcijańskimi władcami
- Wzmocnienie pozycji międzynarodowej

Przyczyny przyjęcia chrztu:
- Małżeństwo z czeską księżniczką Dobrawą
- Presja polityczna ze strony Ottona I
- Chęć uniknięcia chrystianizacji siłą
- Możliwość nawiązania relacji dyplomatycznych

Znaczenie religijne:
- Wprowadzenie chrześcijaństwa jako religii państwowej
- Budowa pierwszych kościołów i klasztorów
- Przybycie duchownych z Czech i Niemiec
- Początek organizacji kościelnej w Polsce

Długofalowe skutki:
- Trwałe związanie Polski z cywilizacją zachodnią
- Rozwój kultury pisanej
- Powstanie pierwszych szkół
- Budowa fundamentów państwowości polskiej

Chrzest Polski w 966 roku rozpoczął nowy rozdział w dziejach narodu polskiego.""",
                "tags": ["chrzest", "Mieszko I", "966", "chrześcijaństwo", "początki Polski"]
            },
            {
                "title": "Unia Lubelska 1569 - Powstanie Rzeczypospolitej",
                "content": """Unia Lubelska, podpisana 1 lipca 1569 roku w Lublinie, była aktem prawnym łączącym Królestwo Polskie i Wielkie Księstwo Litewskie w jedno państwo - Rzeczpospolitą Obojga Narodów.

Przyczyny zawarcia unii:
- Zagrożenie ze strony Rosji Iwana Groźnego
- Wojna o Inflanty (1558-1583)
- Potrzeba wzmocnienia militarnego
- Presja szlachty polskiej na inkorporację Litwy

Negocjacje i przebieg:
- Sejm w Lublinie trwał od stycznia do lipca 1569
- Początkowo Litwini opuścili obrady w proteście
- Król Zygmunt August przyłączył Podlasie, Wołyń i Ukrainę do Korony
- Powrót delegacji litewskiej i kompromis

Główne postanowienia unii:
- Wspólny sejm, senat i król
- Wspólna polityka zagraniczna i obronna
- Wspólna moneta
- Zachowanie odrębności prawnej i administracyjnej Litwy
- Równouprawnienie szlachty polskiej i litewskiej

Znaczenie historyczne:
- Powstanie największego państwa w Europie XVI wieku
- Utworzenie unikalnego systemu politycznego
- Rozwój kultury szlacheckiej i sarmatyzmu
- Wzrost znaczenia sejmu i demokracji szlacheckiej

Unia Lubelska była jednym z najważniejszych aktów w historii Polski i Litwy.""",
                "tags": ["unia", "Lublin", "1569", "Rzeczpospolita", "Litwa"]
            },
            {
                "title": "Solidarność 1980-1989 - Droga do Wolności",
                "content": """Ruch Solidarność, powstały w 1980 roku, był pierwszym niezależnym związkiem zawodowym w krajach komunistycznych. Jego działalność doprowadziła do upadku komunizmu w Polsce i zapoczątkowała przemiany demokratyczne w Europie Środkowo-Wschodniej.

Geneza Solidarności:
- Strajki w Stoczni Gdańskiej w sierpniu 1980
- Lech Wałęsa jako przywódca strajkujących
- Porozumienia Sierpniowe z 31 sierpnia 1980
- Rejestracja NSZZ "Solidarność" 10 listopada 1980

Główne postulaty:
- Prawo do strajku
- Niezależne związki zawodowe
- Wolność słowa i prasy
- Uwolnienie więźniów politycznych
- Reformy gospodarcze

Rozwój ruchu (1980-1981):
- 10 milionów członków
- I Krajowy Zjazd Delegatów w Gdańsku
- Program reform społeczno-gospodarczych
- Konflikty z władzami komunistycznymi

Stan wojenny (13 grudnia 1981):
- Wprowadzenie stanu wojennego przez gen. Jaruzelskiego
- Internowanie przywódców Solidarności
- Delegalizacja związku
- Wprowadzenie cenzury i ograniczeń

Okrągły Stół (1989):
- Negocjacje między władzą a opozycją
- Porozumienie z 5 kwietnia 1989
- Częściowo wolne wybory 4 czerwca 1989
- Zwycięstwo Solidarności

Solidarność pozostaje symbolem walki o wolność i prawa człowieka.""",
                "tags": ["Solidarność", "Wałęsa", "stan wojenny", "1980", "demokracja"]
            },
            {
                "title": "Dynastia Piastów - Pierwsi Władcy Polski",
                "content": """Dynastia Piastów rządziła Polską od X do XIV wieku, tworząc fundamenty polskiej państwowości. Pierwszym historycznym władcą był Mieszko I, a ostatnim Kazimierz III Wielki.

Najważniejsi władcy z dynastii Piastów:

Mieszko I (960-992):
- Pierwszy historyczny władca Polski
- Przyjął chrzest w 966 roku
- Stworzył podstawy państwa polskiego
- Rozszerzył granice na zachód i południe

Bolesław I Chrobry (992-1025):
- Pierwszy król Polski (koronacja w 1025)
- Rozszerzył granice państwa
- Prowadził wojny z Cesarstwem i Rusią
- Umocnił pozycję międzynarodową Polski

Kazimierz I Odnowiciel (1034-1058):
- Odbudował państwo po kryzysie lat 30. XI wieku
- Przeniósł stolicę do Krakowa
- Odnowił organizację kościelną
- Wzmocnił władzę książęcą

Bolesław III Krzywousty (1102-1138):
- Zjednoczył Polskę po okresie walk
- Wydał Statut Bolesława Krzywoustego
- Prowadził udane wojny z Cesarstwem
- Wprowadził zasadę senioratu

Kazimierz III Wielki (1333-1370):
- Ostatni król z dynastii Piastów
- Przeprowadził reformy prawne i administracyjne
- Założył Uniwersytet Krakowski (1364)
- Rozbudował sieć miast i zamków

Znaczenie dynastii Piastów:
- Stworzenie podstaw państwowości polskiej
- Wprowadzenie chrześcijaństwa
- Rozwój kultury i sztuki
- Budowa silnej pozycji międzynarodowej

Dynastia Piastów położyła fundamenty pod przyszłą wielkość Polski.""",
                "tags": ["Piastowie", "Mieszko I", "Bolesław Chrobry", "Kazimierz Wielki", "dynastia"]
            },
            {
                "title": "Kultura Sarmatyzmu w Rzeczypospolitej",
                "content": """Sarmatyzm był ideologią kulturową szlachty polskiej w XVI-XVIII wieku, opartą na przekonaniu o pochodzeniu Polaków od starożytnych Sarmatów. Wpłynął znacząco na kulturę, politykę i mentalność społeczeństwa szlacheckiego.

Główne elementy sarmatyzmu:

Ideologia polityczna:
- Przekonanie o wyższości ustroju Rzeczypospolitej
- Kult wolności szlacheckiej (libertas)
- Równość wszystkich szlachciców
- Sprzeciw wobec absolutyzmu

Kultura materialna:
- Charakterystyczny strój szlachecki (żupan, kontusz, pas słucki)
- Architektura dworska i pałacowa
- Sztuka portretowa (portrety trumienny)
- Rzemiosło artystyczne (broń, srebra)

Obyczajowość:
- Gościnność i hojność
- Kult tradycji i przodków
- Ceremoniał dworski
- Znaczenie honoru i godności

Literatura i sztuka:
- Poezja okolicznościowa
- Pamiętnikarstwo
- Kroniki rodzinne
- Malarstwo portretowe

Wpływ na politykę:
- Liberum veto jako wyraz wolności
- Elekcyjność tronu
- Słabość władzy centralnej
- Konfederacje szlacheckie

Krytyka sarmatyzmu:
- Zacofanie wobec Europy Zachodniej
- Ksenofobia i nietolerancja
- Hamowanie rozwoju gospodarczego
- Osłabienie państwa

Sarmatyzm był zjawiskiem unikalnym w skali europejskiej, kształtującym polską tożsamość przez wieki.""",
                "tags": ["sarmatyzm", "szlachta", "kultura", "Rzeczpospolita", "tradycja"]
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
    print("📚 Wyczyszczenie bazy i dodanie przykładowych artykułów historycznych")
    print("=" * 70)
    
    clear_database()
    create_sample_articles()
    
    print("✨ Gotowe! System jest teraz wypełniony danymi do demonstracji.")