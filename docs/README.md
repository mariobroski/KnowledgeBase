# System Zarządzania Wiedzą RAG

## Przegląd Systemu

System zarządzania wiedzą oparty na technologii RAG (Retrieval-Augmented Generation) z wykorzystaniem grafów wiedzy i zaawansowanych modeli językowych.

## Architektura

### Backend
- FastAPI
- PostgreSQL (dane relacyjne)
- JanusGraph (graf wiedzy)
- Qdrant (wektory embeddings)
- Ollama (LLM provider)

### Frontend
- React
- Material-UI
- TypeScript

## Funkcjonalności

1. **Zarządzanie Dokumentami**
   - Upload i przetwarzanie dokumentów
   - Automatyczna ekstrakcja wiedzy
   - Indeksowanie wektorowe

2. **Graf Wiedzy**
   - Automatyczne tworzenie relacji
   - Wizualizacja połączeń
   - Analiza semantyczna

3. **System RAG**
   - Inteligentne wyszukiwanie
   - Generowanie odpowiedzi
   - Kontekstowe rekomendacje

4. **Benchmarki i Ewaluacja**
   - Testy wydajności
   - Metryki jakości
   - Analiza wyników

## Instalacja i Uruchomienie

### Wymagania
- Python 3.9+
- Node.js 16+
- Docker i Docker Compose
- Ollama

### Konfiguracja
1. Sklonuj repozytorium
2. Skonfiguruj zmienne środowiskowe w `.env`
3. Uruchom `docker-compose -f docker-compose-open-source.yml up`
4. Zainstaluj zależności backendu: `pip install -r backend/requirements.txt`
5. Zainstaluj zależności frontendu: `cd frontend && npm install`

### Uruchomienie
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm start`
- Ollama: `ollama serve`

## Migracja do Open Source

System został zmigrowany z komercyjnych rozwiązań na open source:
- OpenAI → Ollama (Llama 3.1)
- Pinecone → Qdrant
- Neo4j → JanusGraph

## Technologie

### LLM i Embeddings
- Ollama z modelem Llama 3.1:8b-instruct-q4_K_M
- Sentence Transformers dla embeddingów

### Bazy Danych
- PostgreSQL - dane strukturalne
- Qdrant - wektory i embeddings
- JanusGraph - graf wiedzy

### Infrastruktura
- Docker Compose
- FastAPI
- React + TypeScript

## Rozwój

### Struktura Projektu
```
├── backend/          # API i logika biznesowa
├── frontend/         # Interfejs użytkownika
├── eval/            # Testy i benchmarki
├── docs/            # Dokumentacja
└── docker-compose-open-source.yml
```

### Testowanie
- Backend: `pytest`
- Frontend: `npm test`
- Ewaluacja: `cd eval && python run_evaluation.py`

## Licencja

Open Source - szczegóły w pliku LICENSE