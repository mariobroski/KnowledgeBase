#!/usr/bin/env python3
"""
Skrypt do uzupełnienia systemu danymi historycznymi z polskiej historii
dla celów demonstracyjnych i tworzenia zrzutów ekranu.
"""

import requests
import json
import os
from typing import List, Dict

# Konfiguracja API
API_BASE_URL = "http://localhost:8000/api"

# Dane historyczne z polskiej historii
HISTORICAL_ARTICLES = [
    {
        "title": "Bitwa pod Grunwaldem 1410",
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
- Wzmocnienie unii polsko-litewskiej""",
        "tags": ["historia", "średniowiecze", "bitwy", "Jagiełło", "Krzyżacy"]
    },
    {
        "title": "Konstytucja 3 Maja 1791",
        "content": """Konstytucja 3 maja 1791 roku była pierwszą nowoczesną konstytucją w Europie i drugą na świecie (po amerykańskiej z 1787 roku). Została uchwalona przez Sejm Wielki Rzeczypospolitej Obojga Narodów.

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

Reakcje i skutki:
- Entuzjazm części społeczeństwa polskiego
- Sprzeciw konserwatywnej szlachty
- Interwencja zbrojna Rosji (wojna 1792 roku)
- Konfederacja targowicka
- Drugi rozbiór Polski (1793)

Konstytucja 3 maja pozostaje symbolem polskiego dążenia do wolności i reform demokratycznych.""",
        "tags": ["konstytucja", "reformy", "Stanisław August", "oświecenie", "XVIII wiek"]
    },
    {
        "title": "Powstanie Warszawskie 1944",
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

Przebieg powstania:
Dzień 1 (1 sierpnia): Jednoczesny atak na niemieckie pozycje w całej Warszawie
Pierwsze dni: Zdobycie znacznej części miasta
Sierpień: Walki o Stare Miasto i centrum
Wrzesień: Obrona Śródmieścia i Żoliborza
Październik: Kapitulacja powstania

Dowódcy powstania:
- Gen. Tadeusz Bór-Komorowski - komendant główny AK
- Gen. Antoni Chruściel "Monter" - komendant Okręgu Warszawskiego AK
- Płk Stefan Rowecki "Grot" - poprzedni komendant główny AK (aresztowany w 1943)

Skutki powstania:
- Śmierć około 200 000 cywilów
- Zniszczenie 85% zabudowy Warszawy
- Deportacja pozostałej ludności
- Likwidacja struktur polskiego państwa podziemnego
- Wzmocnienie pozycji komunistów

Powstanie Warszawskie pozostaje symbolem heroizmu i walki o wolność, choć jego celowość jest przedmiotem debat historyków.""",
        "tags": ["powstanie", "II wojna światowa", "Warszawa", "AK", "1944"]
    },
    {
        "title": "Chrzest Polski 966",
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

Konsekwencje polityczne:
- Wejście Polski do kręgu cywilizacji łacińskiej
- Nawiązanie stosunków z papiestwem
- Wzmocnienie władzy książęcej
- Unifikacja kulturowa plemion polskich

Źródła historyczne:
- Kronika Thietmara z Merseburga
- Roczniki Hildesheimskie
- Kronika Galla Anonima
- Dokumenty papieskie

Długofalowe skutki:
- Trwałe związanie Polski z cywilizacją zachodnią
- Rozwój kultury pisanej
- Powstanie pierwszych szkół
- Budowa fundamentów państwowości polskiej

Chrzest Polski w 966 roku rozpoczął nowy rozdział w dziejach narodu polskiego i zadecydował o jego przynależności cywilizacyjnej na kolejne stulecia.""",
        "tags": ["chrzest", "Mieszko I", "966", "chrześcijaństwo", "początki Polski"]
    },
    {
        "title": "Unia Lubelska 1569",
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

Struktura nowego państwa:
- Korona Królestwa Polskiego
- Wielkie Księstwo Litewskie
- Wspólne instytucje centralne
- Elekcyjność tronu

Znaczenie historyczne:
- Powstanie największego państwa w Europie XVI wieku
- Utworzenie unikalnego systemu politycznego
- Rozwój kultury szlacheckiej i sarmatyzmu
- Wzrost znaczenia sejmu i demokracji szlacheckiej

Konsekwencje długofalowe:
- Złoty wiek kultury polskiej (XVI-XVII wiek)
- Ekspansja na wschód
- Konflikty z Rosją, Szwecją i Turcją
- Stopniowe osłabienie władzy centralnej

Unia Lubelska była jednym z najważniejszych aktów w historii Polski i Litwy, tworząc państwo, które przez ponad 200 lat odgrywało kluczową rolę w Europie Środkowo-Wschodniej.""",
        "tags": ["unia", "Lublin", "1569", "Rzeczpospolita", "Litwa"]
    },
    {
        "title": "Solidarność i stan wojenny 1980-1989",
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

Działalność podziemna (1982-1989):
- Podziemne struktury Solidarności
- Wydawnictwa niezależne
- Strajki i protesty
- Wsparcie Kościoła katolickiego

Okrągły Stół (1989):
- Negocjacje między władzą a opozycją
- Porozumienie z 5 kwietnia 1989
- Częściowo wolne wybory 4 czerwca 1989
- Zwycięstwo Solidarności

Znaczenie historyczne:
- Pierwszy krok do upadku komunizmu w Europie
- Inspiracja dla innych krajów bloku wschodniego
- Pokojowa rewolucja
- Przywrócenie demokracji w Polsce

Solidarność pozostaje symbolem walki o wolność i prawa człowieka, a jej pokojowa rewolucja stała się wzorem dla przemian demokratycznych na całym świecie.""",
        "tags": ["Solidarność", "Wałęsa", "stan wojenny", "1980", "demokracja"]
    }
]

def create_article_with_content(title: str, content: str, tags: List[str]) -> bool:
    """Tworzy artykuł z zawartością tekstową"""
    try:
        # Przygotowanie danych
        files = {
            'file': ('article.txt', content, 'text/plain')
        }
        data = {
            'title': title,
            'tags': tags
        }
        
        # Wysłanie żądania POST
        response = requests.post(
            f"{API_BASE_URL}/articles/",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            print(f"✅ Utworzono artykuł: {title}")
            return True
        else:
            print(f"❌ Błąd przy tworzeniu artykułu {title}: {response.status_code}")
            print(f"   Odpowiedź: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Wyjątek przy tworzeniu artykułu {title}: {str(e)}")
        return False

def seed_historical_data():
    """Uzupełnia system danymi historycznymi"""
    print("🚀 Rozpoczynam uzupełnianie systemu danymi historycznymi...")
    print(f"📡 API URL: {API_BASE_URL}")
    
    success_count = 0
    total_count = len(HISTORICAL_ARTICLES)
    
    for article_data in HISTORICAL_ARTICLES:
        if create_article_with_content(
            title=article_data["title"],
            content=article_data["content"],
            tags=article_data["tags"]
        ):
            success_count += 1
    
    print(f"\n📊 Podsumowanie:")
    print(f"   Utworzono: {success_count}/{total_count} artykułów")
    print(f"   Sukces: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 Wszystkie artykuły zostały pomyślnie utworzone!")
    else:
        print("⚠️  Niektóre artykuły nie zostały utworzone. Sprawdź logi powyżej.")

def check_api_connection():
    """Sprawdza połączenie z API"""
    try:
        response = requests.get(f"{API_BASE_URL}/articles/")
        if response.status_code == 200:
            print("✅ Połączenie z API działa poprawnie")
            return True
        else:
            print(f"❌ API zwróciło kod: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nie można połączyć się z API: {str(e)}")
        print("   Upewnij się, że serwer backend działa na http://localhost:8000")
        return False

if __name__ == "__main__":
    print("📚 Skrypt uzupełniania danymi historycznymi z polskiej historii")
    print("=" * 60)
    
    # Sprawdzenie połączenia
    if not check_api_connection():
        print("\n❌ Nie można kontynuować bez połączenia z API")
        exit(1)
    
    # Uzupełnienie danymi
    seed_historical_data()
    
    print("\n✨ Skrypt zakończony. System jest gotowy do demonstracji!")