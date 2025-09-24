# Struktura Plików Projektu

## 📊 Podsumowanie

**Całkowita liczba plików:** 115,989  
**Pliki użytkownika (bez zależności):** 222  
**Zależności (node_modules + .venv):** 115,767

## 📁 Rozkład Plików Użytkownika

### Backend (89 plików)
- **Kod Python:** 88 plików .py
- **Konfiguracja:** requirements.txt, Dockerfile, .env
- **Bazy danych:** app.db, test.db, backup files
- **Testy:** test_*.py w folderze tests/

#### Struktura Backend:
```
backend/
├── app/                    # Główna aplikacja
│   ├── api/               # Endpointy API
│   ├── core/              # Konfiguracja i zależności
│   ├── db/                # Modele bazy danych
│   ├── middleware/        # Middleware (auth, audit)
│   ├── models/            # Modele danych
│   ├── rag/               # Implementacje RAG
│   ├── schemas/           # Schematy Pydantic
│   ├── services/          # Logika biznesowa
│   └── utils/             # Narzędzia pomocnicze
├── eval/                  # Ewaluacja i benchmarki
├── tests/                 # Testy jednostkowe
└── skrypty pomocnicze     # seed_data.py, create_admin.py, etc.
```

### Frontend (29 plików)
- **TypeScript/React:** 15 plików .tsx + 53 pliki .ts
- **Konfiguracja:** package.json, tsconfig.json, Dockerfile
- **Statyczne:** public/ (favicon, manifest, index.html)

#### Struktura Frontend:
```
frontend/
├── public/                # Pliki statyczne
├── src/
│   ├── components/        # Komponenty React
│   ├── contexts/          # Context API
│   ├── pages/             # Strony aplikacji
│   ├── services/          # Komunikacja z API
│   ├── types/             # Definicje TypeScript
│   └── utils/             # Narzędzia pomocnicze
└── konfiguracja           # package.json, tsconfig.json
```

### Główny Katalog (20 plików)
- **Dokumentacja:** README.md, MIGRATION_TO_OPEN_SOURCE.md
- **Konfiguracja:** docker-compose*.yml, .env*, .gitignore
- **Skrypty:** package.json, run_ragbench_tests.py
- **Diagramy:** *.png, *.py (UML)

### Eval (10 plików)
- **Benchmarki:** run_eval.py, ingest_*.py
- **Metryki:** advanced_metrics.py, trend_analysis.py
- **Raporty:** generate_report.py, literature_comparison.py

### Docs (1 plik)
- **Dokumentacja:** README.md (skonsolidowana)

## 🎯 Typy Plików Użytkownika

| Typ | Liczba | Opis |
|-----|--------|------|
| .py | 88 | Kod Python (backend) |
| .ts | 53 | TypeScript (frontend) |
| .tsx | 15 | React komponenty |
| .json | 13 | Konfiguracja (package.json, tsconfig.json) |
| .md | 12 | Dokumentacja |
| .db | 4 | Bazy danych SQLite |
| .yml | 2 | Docker Compose |
| .txt | 2 | Pliki tekstowe |
| .png | 2 | Diagramy |
| .env | 2 | Zmienne środowiskowe |
| Inne | 29 | HTML, CSS, SVG, Dockerfile, etc. |

## 🚫 Ignorowane Pliki (.gitignore)

### Zależności
- `node_modules/` - 82,836 plików npm
- `.venv/` - 32,877 plików Python

### Cache i Tymczasowe
- `__pycache__/` - cache Python
- `.pytest_cache/` - cache testów
- `*.pyc`, `*.pyo`, `*.pyd` - skompilowane pliki Python
- `.DS_Store` - pliki macOS

### Build i Dist
- `frontend/build/` - zbudowana aplikacja React
- `dist/` - pliki dystrybucyjne

## 💡 Zalecenia

1. **Regularne czyszczenie:**
   ```bash
   # Usuń cache Python
   find . -name "__pycache__" -type d -exec rm -rf {} +
   
   # Usuń pliki .pyc
   find . -name "*.pyc" -delete
   
   # Usuń build frontend
   rm -rf frontend/build
   ```

2. **Backup ważnych plików:**
   - Kod źródłowy (app/, src/)
   - Konfiguracja (.env, docker-compose.yml)
   - Dokumentacja (docs/, README.md)
   - Bazy danych (*.db)

3. **Monitorowanie rozmiaru:**
   - Pliki użytkownika: ~222 pliki (łatwe do zarządzania)
   - Zależności można odtworzyć z package.json i requirements.txt
   - Regularne czyszczenie cache może zaoszczędzić miejsce

## 🔍 Przydatne Komendy

```bash
# Liczba plików użytkownika
find . -type f -not -path "./frontend/node_modules/*" -not -path "./backend/.venv/*" | wc -l

# Rozmiar katalogów
du -sh */ | sort -hr

# Znajdź największe pliki
find . -type f -not -path "./frontend/node_modules/*" -not -path "./backend/.venv/*" -exec ls -lh {} + | sort -k5 -hr | head -10
```