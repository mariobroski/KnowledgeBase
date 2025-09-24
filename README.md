# KnowledgeBase - Administrator

Aplikacja demonstracyjna systemu RAG (Retrieval-Augmented Generation) z trzema trybami wyszukiwania: TekstRAG, FaktRAG i GrafRAG.

## Opis projektu

System umożliwia zarządzanie wiedzą poprzez:
- Zarządzanie artykułami (dokumentami źródłowymi)
- Zarządzanie faktami i encjami (wiedzą ustrukturyzowaną)
- Zarządzanie grafem wiedzy (relacjami między encjami)
- Wyszukiwanie informacji z wykorzystaniem trzech polityk RAG
- Analizę danych i metryk systemu

## Struktura projektu

```
├── backend/               # Kod backendu (FastAPI)
│   ├── app/              # Główny kod aplikacji
│   │   ├── api/         # Endpointy API
│   │   ├── core/        # Konfiguracja i ustawienia
│   │   ├── db/          # Modele bazy danych
│   │   ├── rag/         # Implementacja RAG
│   │   └── services/    # Usługi biznesowe
│   ├── tests/           # Testy
│   └── requirements.txt  # Zależności Pythona
└── frontend/             # Kod frontendu (React)
    ├── public/          # Statyczne pliki
    ├── src/             # Kod źródłowy
    │   ├── components/  # Komponenty React
    │   ├── pages/       # Strony aplikacji
    │   ├── services/    # Usługi API
    │   └── utils/       # Narzędzia pomocnicze
    └── package.json     # Zależności npm
```

## Funkcjonalności

1. **Zarządzanie artykułami**
   - Dodawanie, edycja i usuwanie dokumentów
   - Indeksowanie dokumentów
   - Przeglądanie fragmentów

2. **Zarządzanie faktami i encjami**
   - Tworzenie i edycja faktów
   - Zarządzanie encjami i ich aliasami
   - Łączenie faktów z dokumentami źródłowymi

3. **Graf wiedzy**
   - Wizualizacja grafu wiedzy
   - Tworzenie i edycja relacji między encjami
   - Wyszukiwanie ścieżek w grafie

4. **Wyszukiwanie (RAG)**
   - TekstRAG - wyszukiwanie oparte na fragmentach tekstu
   - FaktRAG - wyszukiwanie oparte na faktach
   - GrafRAG - wyszukiwanie oparte na grafie wiedzy

5. **Analiza danych**
   - Dashboard z kluczowymi metrykami
   - Historia zapytań
   - Metryki jakości odpowiedzi

## Technologie

- **Backend**: FastAPI (Python)
- **Frontend**: React, TypeScript
- **Baza danych**: PostgreSQL (relacyjna), Qdrant (wektorowa), Neo4j (grafowa)
- **RAG**: LangChain, embeddingi wektorowe (sentence-transformers)
- **UI**: Material-UI lub podobna biblioteka komponentów

## Uruchomienie środowiska lokalnego

1. Uruchom usługi zależne (PostgreSQL oraz Qdrant):

   ```bash
   docker-compose up -d
   ```

2. Ustaw zmienne środowiskowe (przykład w `.env`):

   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_system
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```

3. Zainstaluj zależności backendu i uruchom API:

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. Frontend:

   ```bash
   cd frontend
   npm install
   npm start
   ```
