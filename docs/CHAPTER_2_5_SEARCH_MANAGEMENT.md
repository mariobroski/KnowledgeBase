# 2.5 Zarządzanie wyszukiwaniem

W tym podrozdziale przedstawiono moduł wyszukiwania oparty na strategii RAG. Moduł przyjmuje zapytanie, dobiera tryb pracy, wyszukuje kontekst w odpowiednich magazynach i generuje odpowiedź z wykorzystaniem modelu językowego. Zapewniono cztery tryby: **Tekst-RAG**, **Fakt-RAG**, **Graf-RAG** oraz **Hybrid-RAG**. Zastosowano wzorzec Factory do wyboru trybu oraz mechanizmy łączenia wyników i kontroli budżetu tokenów.

## 2.5.1 Automatyczny dobór polityki

System zawiera inteligentny selektor polityk (`PolicySelector`), który analizuje zapytanie i automatycznie wybiera optymalną strategię RAG. Analiza obejmuje identyfikację typu zapytania (faktograficzne, analityczne, opisowe), ocenę złożoności i wymagań kontekstowych oraz wybór między TextRAG, FactRAG, GraphRAG lub HybridRAG.

Dobór trybu realizowany jest w warstwie pośredniej. Najpierw przyjmowane jest żądanie przez REST API wraz z parametrami (top‑k, progi, głębokość grafu, limit tokenów). Następnie instancjonowana jest strategia przez Factory Pattern na podstawie parametru wejściowego lub reguły routingu. Potem uruchamiany jest proces wyszukiwania właściwy dla wybranego trybu. Na końcu budowany jest prompt z cytowalnym kontekstem i uruchamiana jest synteza odpowiedzi w LLM. W przypadku braku wystarczającego kontekstu zwracana jest odpowiedź neutralna z informacją o ograniczeniach.

## 2.5.2 TextRAG - wyszukiwanie semantyczne

W trybie TextRAG wykorzystano indeks wektorowy (Qdrant/Weaviate/FAISS). Najpierw obliczane jest osadzenie (embedding) zapytania tym samym modelem, którym osadzono fragmenty. Następnie wykonywane jest zapytanie do indeksu wektorowego z parametrami top‑k i progiem podobieństwa. Potem pobierane są metadane fragmentów przez ORM (tytuł artykułu, pozycja, tagi). Później wykonywany jest reranking lokalny, który porządkuje fragmenty według odległości wektorowej oraz reguł jakości (np. penalizacja duplikatów, preferencja różnorodności). Na końcu budowany jest kontekst z kontrolą budżetu tokenów i deduplikacją zdań brzegowych. Zastosowano cytowanie źródeł w treści promptu. W razie niskiej zgodności semantycznej odrzucane są fragmenty poniżej progu.

## 2.5.3 FactRAG - wyszukiwanie faktograficzne

W trybie FactRAG wykorzystano warstwę faktograficzną w bazie relacyjnej (PostgreSQL). Najpierw parsowane jest zapytanie i wydzielane są istotne lematy i słowa kluczowe. Następnie wykonywane jest zapytanie SQL do tabeli „facts" z połączeniami do „fragments" i „articles". Potem nakładane są filtry progu confidence i ewentualne warunki temporalne. Później obliczana jest miara rankingowa łącząca dopasowanie słów kluczowych, confidence i świeżość. Na końcu budowany jest zwięzły, cytowalny kontekst w postaci wypunktowanych stwierdzeń lub krótkiego opisu faktów. Zastosowano odwołania do fragmentów źródłowych, co umożliwia audyt. Wariant minimalny działa bez pełnotekstowego indeksu, a wariant rozszerzony może korzystać z indeksów FT lub trigramów.

## 2.5.4 GraphRAG - wyszukiwanie w grafie wiedzy

W trybie GraphRAG wykorzystano graf wiedzy (JanusGraph). Najpierw wydzielane są potencjalne encje z zapytania (NER lub dopasowanie nazw). Następnie mapowane są nazwy na węzły grafu z tolerancją aliasów. Potem wyznaczane są ścieżki między węzłami istotnymi dla zapytania w ograniczonej głębokości (BFS lub k‑najkrótszych ścieżek). Później agregowany jest podgraf z wagami krawędzi i listą dowodów (fakty). Na końcu budowany jest kontekst opisujący relacje i kolejność w ścieżkach oraz przygotowywane są cytaty dowodowe. Zastosowano priorytetyzację ścieżek krótszych i lepiej udokumentowanych (większa liczba dowodów, wyższe wagi).

## 2.5.5 HybridRAG - strategia łączona

HybridRAG łączy wszystkie trzy podstawowe strategie, umożliwiając równoległe wyszukiwanie we wszystkich magazynach, inteligentne łączenie wyników z różnymi wagami oraz adaptacyjne dostosowanie do złożoności zapytania. Strategia optymalizuje budżet tokenów poprzez selekcję najlepszych fragmentów z każdego źródła.

## 2.5.6 Łączenie wyników

Łączenie wyników realizowane jest jako fuzja późna. Najpierw standaryzowane są wyniki z trybów (teksty fragmentów, fakty, opisy ścieżek). Następnie przydzielane są wagi komponentom kontekstu zależnie od zaufania (np. confidence, długość ścieżki, odległość wektorowa). Potem odrzucane są duplikaty i treści o niskiej wartości informacyjnej. Później wykonywana jest kontrola budżetu tokenów i skracanie nadmiarowych cytatów. Na końcu budowany jest jeden prompt z częścią instrukcyjną, zblokowanym kontekstem oraz wymaganiem cytowania. Zastosowano ścisłe reguły formatowania cytatów (identyfikator artykułu, pozycja fragmentu) w celu weryfikowalności.

## 2.5.7 Generowanie odpowiedzi LLM

Generowanie odpowiedzi LLM przebiega deterministycznie. Najpierw przygotowywane są parametry modelu (temperatura, limit nowych tokenów). Następnie wysyłany jest prompt do usługi generacji (Ollama/TGI) lub alternatywnego dostawcy. Potem odbierany jest wynik oraz metryki użycia (tokeny wejściowe i wyjściowe, czas inferencji). Na końcu weryfikowana jest obecność cytowań i spójność odpowiedzi z kontekstem. W przypadku niespełnienia warunków stosowana jest strategia uzupełnienia lub zwrot odpowiedzi z informacją o braku podstaw.

## 2.5.8 Obsługa halucynacji

Obsługa halucynacji zrealizowana została na dwóch poziomach. Na poziomie retrievalu stosowany jest próg podobieństwa i confidence. Na poziomie syntezy stosowane jest wymaganie cytowania oraz reguła „bez kontekstu – bez twierdzenia". Dodatkowo rejestrowany jest wskaźnik zgodności (faithfulness) na podstawie heurystyk dopasowania fragmentów do odpowiedzi. W przypadku niskiej zgodności sygnalizowany jest alert w metrykach jakości.

## 2.5.9 Rejestrowanie metryk

Rejestrowanie metryk odbywa się po każdej odpowiedzi. Zapisywane są parametry zapytania, identyfikatory kontekstu, czasy etapów, użycie tokenów, liczby wyników, progi i finalny tryb. Metryki utrwalane są w tabeli „search_queries" oraz, w razie potrzeby, w dzienniku audytu. Na tej podstawie weryfikowane jest działanie routingu, progi w trybach i stabilność czasów odpowiedzi. Wyniki wykorzystywane są w module analitycznym do wizualizacji trendów i strojenia parametrów.

## 2.5.10 Ewaluacja i benchmarki

System integruje zaawansowane narzędzia ewaluacyjne umożliwiające obiektywną ocenę wydajności i porównania z benchmarkami naukowymi:

### RAGBench Integration
- **Import benchmarków**: FinQA, TAT-QA, TechQA, CUAD, EManual
- **Automatyczna ewaluacja**: testowanie wszystkich strategii RAG
- **Porównania z literaturą**: analiza wyników względem publikacji naukowych

### TRACe Metrics
- **Relevance**: jakość retrievera i dopasowania kontekstu
- **Utilization**: wykorzystanie dostarczonego kontekstu
- **Adherence**: wierność odpowiedzi względem kontekstu (faithfulness)
- **Completeness**: kompletność odpowiedzi względem ground truth

### Zaawansowana analiza
- **Advanced Metrics**: hallucination score, factual accuracy, context utilization
- **Literature Comparison**: porównania z wynikami z literatury naukowej
- **Trend Analysis**: analiza trendów wydajności w czasie
- **Quality Reports**: automatyczne generowanie raportów jakości

## 2.5.11 Podsumowanie

Opracowano moduł wyszukiwania, który scala cztery komplementarne ścieżki pozyskiwania kontekstu. Zastosowano mechanizmy wyboru strategii, kontroli jakości kontekstu i budżetu tokenów oraz reguły syntezy z cytowaniem. Rozwiązanie umożliwia dobór optymalnej ścieżki dla różnych typów zapytań i przygotowuje podstawę do oceny jakości oraz kosztów w module analitycznym. Dodatkowo system oferuje zaawansowane narzędzia ewaluacyjne umożliwiające obiektywną ocenę wydajności i porównania z benchmarkami naukowymi.
