# 🚀 KnowledgeBase Infrastructure Setup

## Szybki start

### 1. Przygotowanie środowiska

```bash
# Klonowanie repozytorium (jeśli nie masz)
git clone <repository-url>
cd FinalnyProjektTrae

# Kopiowanie konfiguracji
cp env.example .env
# Edytuj .env według potrzeb
```

### 2. Uruchomienie infrastruktury

```bash
# Uruchomienie wszystkich serwisów
docker-compose -f docker-compose-open-source.yml up -d

# Sprawdzenie statusu
docker-compose -f docker-compose-open-source.yml ps
```

### 3. Testowanie infrastruktury

```bash
# Instalacja zależności testowych
pip install psycopg2-binary qdrant-client redis gremlinpython requests

# Uruchomienie testów
python test_infrastructure.py
```

## 📋 Wymagania systemowe

### Minimalne wymagania:
- **RAM**: 8GB (16GB zalecane)
- **CPU**: 4 cores
- **Dysk**: 20GB wolnego miejsca
- **GPU**: Opcjonalne (dla TGI/Ollama)

### Zalecane wymagania:
- **RAM**: 32GB
- **CPU**: 8 cores
- **Dysk**: 50GB SSD
- **GPU**: NVIDIA RTX 3080+ (dla lokalnych modeli LLM)

## 🔧 Konfiguracja serwisów

### PostgreSQL
- **Port**: 5432
- **Database**: rag_system
- **User**: postgres
- **Password**: postgres

### Qdrant
- **Port**: 6333
- **Collection**: fragments
- **Vector size**: 384 (all-MiniLM-L6-v2)

### JanusGraph
- **Port**: 8182
- **Storage**: BerkeleyDB (lokalny)
- **Query language**: Gremlin

### Redis
- **Port**: 6379
- **Use case**: Cache, sessions

### Ollama (LLM)
- **Port**: 11434
- **Models**: llama3, mistral, codellama
- **Use case**: Lokalne modele LLM

### TGI (Text Generation Inference)
- **Port**: 8080
- **Model**: Mistral-7B-Instruct
- **Use case**: Wysokowydajne generowanie tekstu

## 🐳 Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| postgres | postgres:15 | 5432 | Main database |
| qdrant | qdrant/qdrant | 6333 | Vector database |
| janusgraph | janusgraph/janusgraph | 8182 | Graph database |
| redis | redis:7-alpine | 6379 | Cache |
| ollama | ollama/ollama | 11434 | Local LLM |
| tgi | huggingface/tgi | 8080 | High-performance LLM |
| weaviate | semitechnologies/weaviate | 8080 | Alternative vector DB |

## 🔍 Troubleshooting

### Problem: JanusGraph nie startuje
```bash
# Sprawdź logi
docker logs janusgraph

# Sprawdź czy port 8182 jest wolny
netstat -tulpn | grep 8182

# Restart serwisu
docker-compose -f docker-compose-open-source.yml restart janusgraph
```

### Problem: TGI nie startuje (brak GPU)
```bash
# Sprawdź czy masz NVIDIA GPU
nvidia-smi

# Jeśli nie masz GPU, wyłącz TGI w docker-compose
# Skomentuj sekcję tgi w docker-compose-open-source.yml
```

### Problem: Qdrant connection refused
```bash
# Sprawdź status
docker-compose -f docker-compose-open-source.yml ps qdrant

# Restart
docker-compose -f docker-compose-open-source.yml restart qdrant
```

### Problem: Ollama nie pobiera modeli
```bash
# Sprawdź logi
docker logs ollama

# Ręczne pobranie modelu
docker exec -it ollama ollama pull llama3
```

## 📊 Monitoring

### Sprawdzenie statusu serwisów:
```bash
# Status wszystkich serwisów
docker-compose -f docker-compose-open-source.yml ps

# Logi konkretnego serwisu
docker-compose -f docker-compose-open-source.yml logs <service_name>

# Zasoby systemowe
docker stats
```

### Sprawdzenie połączeń:
```bash
# PostgreSQL
psql -h localhost -p 5432 -U postgres -d rag_system

# Qdrant
curl http://localhost:6333/collections

# JanusGraph
curl http://localhost:8182/status

# Redis
redis-cli -h localhost -p 6379 ping

# Ollama
curl http://localhost:11434/api/tags
```

## 🚀 Następne kroki

Po pomyślnym uruchomieniu infrastruktury:

1. **Backend**: `cd backend && python -m uvicorn app.main:app --reload`
2. **Frontend**: `cd frontend && npm start`
3. **Test API**: `curl http://localhost:8000/api/health`

## 📝 Notatki

- **JanusGraph** może potrzebować kilku minut na inicjalizację
- **TGI** wymaga GPU dla optymalnej wydajności
- **Ollama** automatycznie pobiera modele przy pierwszym użyciu
- **Qdrant** tworzy kolekcje automatycznie przy pierwszym użyciu

## 🆘 Wsparcie

W przypadku problemów:
1. Sprawdź logi: `docker-compose logs <service>`
2. Sprawdź status: `docker-compose ps`
3. Restart serwisów: `docker-compose restart`
4. Sprawdź wymagania systemowe
