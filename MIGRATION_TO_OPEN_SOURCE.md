# Migracja na rozwiązania Open Source

## Przegląd zmian

System KnowledgeBase został zmigrowany z komercyjnych rozwiązań na w pełni open source alternatywy:

### Zmiany w bazach danych

| Komponent | Przed | Po | Uzasadnienie |
|-----------|-------|----|--------------|
| **Baza grafowa** | Neo4j (Community/Enterprise) | **JanusGraph** | W pełni open source, lepsza skalowalność |
| **Baza wektorowa** | ChromaDB | **Qdrant** | Lepsza wydajność, więcej funkcji |
| **Alternatywy wektorowe** | - | **Weaviate, FAISS** | Większa elastyczność wyboru |

## Nowe technologie

### 1. JanusGraph (zamiast Neo4j)

**Zalety:**
- W pełni open source (Apache 2.0)
- Lepsza skalowalność horyzontalna
- Wsparcie dla różnych backend storage
- Standardowy język zapytań Gremlin

**Konfiguracja:**
```yaml
JANUSGRAPH_HOST: localhost
JANUSGRAPH_PORT: 8182
JANUSGRAPH_STORAGE_BACKEND: berkeleyje
JANUSGRAPH_STORAGE_DIRECTORY: ./janusgraph_data
```

**Uruchomienie:**
```bash
docker run -p 8182:8182 janusgraph/janusgraph:latest
```

### 2. Qdrant (zamiast ChromaDB)

**Zalety:**
- Wysoka wydajność
- RESTful API
- Filtrowanie metadanych
- Wsparcie dla różnych metryk podobieństwa

**Konfiguracja:**
```yaml
QDRANT_HOST: localhost
QDRANT_PORT: 6333
QDRANT_COLLECTION_NAME: fragments
```

### 3. Alternatywne bazy wektorowe

#### Weaviate
- Open source vector database
- Wbudowane modele ML
- GraphQL API

#### FAISS
- Biblioteka Facebook AI Research
- Lokalne przechowywanie
- Wysoka wydajność

## Instalacja i uruchomienie

### 1. Przygotowanie środowiska

```bash
# Klonowanie repozytorium
git clone <repository-url>
cd FinalnyProjektTrae

# Instalacja zależności
cd backend
pip install -r requirements.txt
```

### 2. Uruchomienie z Docker Compose

```bash
# Uruchomienie wszystkich serwisów
docker-compose -f docker-compose-open-source.yml up -d

# Sprawdzenie statusu
docker-compose -f docker-compose-open-source.yml ps
```

### 3. Konfiguracja środowiska

Utwórz plik `.env` w katalogu `backend/`:

```env
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_system

# JanusGraph
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182
JANUSGRAPH_STORAGE_BACKEND=berkeleyje
JANUSGRAPH_STORAGE_DIRECTORY=./janusgraph_data

# Vector Database
VECTOR_DB_TYPE=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=fragments

# Alternative vector databases
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
FAISS_INDEX_PATH=./faiss_index

# RAG
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Migracja danych

### 1. Migracja z Neo4j do JanusGraph

```python
# Przykład migracji danych
from app.services.janusgraph_service import janusgraph_service

# Połączenie z JanusGraph
janusgraph_service.connect()

# Utworzenie schematu
janusgraph_service.create_schema()

# Migracja węzłów
# (implementacja zależna od struktury danych w Neo4j)
```

### 2. Migracja z ChromaDB do Qdrant

```python
# Przykład migracji embeddings
from app.services.embedding_service import get_embedding_service

embedding_service = get_embedding_service()

# Migracja kolekcji
# (automatyczna przy pierwszym uruchomieniu)
```

## Nowe funkcjonalności

### 1. Elastyczny wybór bazy wektorowej

System obsługuje teraz różne bazy wektorowe:

```python
# Konfiguracja w settings
VECTOR_DB_TYPE = "qdrant"  # lub "weaviate", "faiss"
```

### 2. Ulepszone zapytania grafowe

```python
# Przykład zapytania Gremlin
query = """
g.V().hasLabel('Document')
  .out('CONTAINS')
  .hasLabel('Entity')
  .valueMap(true)
"""
```

### 3. Lepsze monitorowanie

```python
# Statystyki grafu
stats = janusgraph_service.get_graph_stats()
print(f"Vertices: {stats['vertices']}, Edges: {stats['edges']}")
```

## Rozwiązywanie problemów

### 1. Problemy z połączeniem JanusGraph

```bash
# Sprawdzenie statusu
curl http://localhost:8182/status

# Logi kontenera
docker logs janusgraph
```

### 2. Problemy z Qdrant

```bash
# Sprawdzenie zdrowia
curl http://localhost:6333/health

# Logi kontenera
docker logs qdrant
```

### 3. Problemy z embeddings

```python
# Sprawdzenie statusu serwisu
from app.services.embedding_service import get_embedding_service

service = get_embedding_service()
print(f"Service enabled: {service.is_enabled}")
print(f"Vector DB type: {service._vector_db_type}")
```

## Wydajność

### Optymalizacje JanusGraph

1. **Indeksy** - utwórz indeksy dla często używanych właściwości
2. **Batch operations** - używaj transakcji dla operacji masowych
3. **Cache** - skonfiguruj cache dla często używanych zapytań

### Optymalizacje Qdrant

1. **Payload indexing** - indeksuj metadane dla szybkiego filtrowania
2. **Vector quantization** - użyj kompresji wektorów dla oszczędności miejsca
3. **Sharding** - podziel kolekcje na shardy dla lepszej wydajności

## Monitoring i logi

### 1. Logi aplikacji

```bash
# Logi backendu
docker logs backend

# Logi z poziomu aplikacji
tail -f backend/logs/app.log
```

### 2. Metryki baz danych

```python
# Statystyki JanusGraph
stats = janusgraph_service.get_graph_stats()

# Statystyki Qdrant
from qdrant_client import QdrantClient
client = QdrantClient("localhost", port=6333)
collections = client.get_collections()
```

## Wsparcie i dokumentacja

- **JanusGraph**: https://janusgraph.org/
- **Qdrant**: https://qdrant.tech/
- **Weaviate**: https://weaviate.io/
- **FAISS**: https://faiss.ai/

## Podsumowanie

Migracja na rozwiązania open source zapewnia:

✅ **Pełną kontrolę** nad kodem i danymi  
✅ **Brak ograniczeń licencyjnych**  
✅ **Lepsze możliwości skalowania**  
✅ **Aktywne społeczności** open source  
✅ **Elastyczność** w wyborze technologii  

System jest teraz w pełni open source i gotowy do dalszego rozwoju!



