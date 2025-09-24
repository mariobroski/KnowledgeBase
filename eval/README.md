# 📊 Ewaluacja RAGBench + FinanceBench

## 🎯 **Cel**

Kompletny system ewaluacji strategii RAG (Text, Facts, Graph, Hybrid) na benchmarkach RAGBench i FinanceBench z metrykami TRACe i RAGAS.

## 🏗️ **Architektura**

```
eval/
├── ingest_ragbench.py      # Importer korpusów RAGBench
├── ingest_financebench.py  # Importer korpusów FinanceBench  
├── run_eval.py             # Harness oceniający TRACe + RAGAS
├── generate_report.py      # Generator raportów i wykresów
├── run_full_pipeline.py    # Pełny pipeline ewaluacji
├── data/                   # Dane korpusów
├── results/                # Wyniki ewaluacji (CSV, JSON)
└── reports/                # Raporty i wykresy
```

## 🚀 **Szybki start**

### **1. Przygotowanie środowiska**

```bash
# Uruchom backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# W nowym terminalu
cd eval
```

### **2. Szybki test**

```bash
# Test jednej domeny i polityki
python run_full_pipeline.py --quick FinQA text

# Sprawdź wyniki
ls results/
ls reports/
```

### **3. Pełny pipeline**

```bash
# Wszystkie domeny i polityki
python run_full_pipeline.py --full

# Konkretne domeny i polityki
python run_full_pipeline.py --full FinQA,TAT-QA text,facts,graph
```

### **4. Demonstracja zaawansowanych funkcjonalności**

```bash
# Uruchom demonstrację
python demo_advanced_features.py

# Sprawdź wygenerowane wykresy
ls *.png
```

## 📋 **Dostępne domeny**

### **RAGBench**
- **FinQA** - Pytania finansowe z tabelami
- **TAT-QA** - Pytania tabelaryczne
- **TechQA** - Pytania techniczne
- **CUAD** - Pytania prawne
- **EManual** - Pytania z instrukcji

### **FinanceBench**
- **FinanceBench** - Sprawozdania finansowe
- **FinancialQA** - Pytania finansowe
- **FinNLP** - NLP finansowe

## 🔧 **Dostępne polityki**

- **text** - TextRAG (semantic search)
- **facts** - FactRAG (fact-based)
- **graph** - GraphRAG (knowledge graph)
- **hybrid** - HybridRAG (kombinacja)

## 📊 **Metryki ewaluacji**

### **TRACe (RAGBench)**
- **Relevance** - trafność odpowiedzi względem pytania
- **Utilization** - wykorzystanie kontekstu
- **Adherence** - zgodność z kontekstem (faithfulness)
- **Completeness** - kompletność względem ground truth

### **RAGAS**
- **Faithfulness** - zgodność odpowiedzi z kontekstem
- **Answer Relevance** - trafność odpowiedzi
- **Context Precision** - precyzja kontekstu
- **Context Recall** - recall kontekstu

### **Operacyjne**
- **Latency** - czas odpowiedzi (p50, p95)
- **Tokens** - liczba tokenów
- **Cost** - koszt ($)

## 🛠️ **Użycie**

### **Import korpusów**

```bash
# RAGBench
python ingest_ragbench.py FinQA
python ingest_ragbench.py TAT-QA
python ingest_ragbench.py TechQA

# FinanceBench
python ingest_financebench.py FinanceBench
python ingest_financebench.py FinancialQA
```

### **Ewaluacja**

```bash
# Wszystkie polityki
python run_eval.py FinQA

# Konkretne polityki
python run_eval.py FinQA text,facts,graph
```

### **Raporty**

```bash
# Raport dla domeny
python generate_report.py FinQA

# Zbiorczy raport
python generate_report.py FinQA,TAT-QA,FinanceBench --combined
```

## 📈 **Wyniki**

### **Pliki wyników**
- `results/{domain}_results_{timestamp}.csv` - Wyniki ewaluacji
- `results/{domain}_summary_{timestamp}.json` - Podsumowanie

### **Raporty**
- `reports/{domain}_report.json` - Raport domeny
- `reports/{domain}_comparison.csv` - Tabela porównawcza
- `reports/{domain}_*.png` - Wykresy

### **Wykresy**
- **TRACe Metrics** - Porównanie metryk TRACe
- **RAGAS Metrics** - Porównanie metryk RAGAS
- **Latency Comparison** - Porównanie latencji
- **Cost Comparison** - Porównanie kosztów
- **Correlation Heatmap** - Heatmapa korelacji

## 🔍 **Przykładowe wyniki**

### **Tabela porównawcza**

| Policy | Relevance | Adherence | Latency (p95) | Cost |
|--------|-----------|-----------|---------------|------|
| text   | 0.85      | 0.78      | 1200ms        | 0.003 |
| facts  | 0.88      | 0.82      | 1500ms        | 0.002 |
| graph  | 0.92      | 0.89      | 2200ms        | 0.001 |
| hybrid | 0.90      | 0.85      | 1800ms        | 0.002 |

### **Wnioski**
- **GraphRAG** osiąga najlepszą adherence (0.89)
- **GraphRAG** jest najtańszy (0.001$)
- **GraphRAG** jest 1.8x wolniejszy od TextRAG
- **FactsRAG** balansuje wydajność i jakość

## ⚙️ **Konfiguracja**

### **Parametry testowe**

```python
# eval/run_eval.py
test_params = {
    "text": {"policy": "text", "top_k": 5, "similarity_threshold": 0.7},
    "facts": {"policy": "facts", "top_k": 5, "fact_confidence_threshold": 0.8},
    "graph": {"policy": "graph", "top_k": 5, "graph_max_depth": 3, "graph_max_paths": 10},
    "hybrid": {"policy": "hybrid", "top_k": 5, "similarity_threshold": 0.7}
}
```

### **Ograniczenia**
- Maksymalnie 100 zapytań na domenę (dla testów)
- Timeout 30 minut na ewaluację domeny
- Timeout 5 minut na import korpusu

## 🐛 **Rozwiązywanie problemów**

### **API nie jest dostępne**
```bash
# Sprawdź czy backend działa
curl http://localhost:8000/health

# Uruchom backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **Błąd importu korpusu**
```bash
# Sprawdź logi
python ingest_ragbench.py FinQA 2>&1 | tee import.log

# Sprawdź dostępność korpusów
ls data/
```

### **Błąd ewaluacji**
```bash
# Sprawdź logi
python run_eval.py FinQA 2>&1 | tee eval.log

# Sprawdź wyniki
ls results/
```

## 📚 **Dokumentacja**

### **Struktura danych**

```json
{
  "query_id": "finqa_1_1",
  "domain": "FinQA",
  "policy": "text",
  "query": "What was Company XYZ's revenue?",
  "response": "Company XYZ reported revenue of $1.2M",
  "context": {
    "fragments": [
      {"content": "Company XYZ reported revenue of $1.2M in Q3 2023"}
    ]
  },
  "metrics": {
    "relevance": 0.92,
    "utilization": 0.85,
    "adherence": 0.88,
    "completeness": 0.90,
    "faithfulness": 0.87,
    "answer_relevance": 0.91,
    "context_precision": 0.83,
    "context_recall": 0.86,
    "search_time": 150.0,
    "generation_time": 800.0,
    "total_time": 950.0,
    "tokens_used": 120,
    "cost": 0.002
  }
}
```

### **Mapowanie ID**

```json
{
  "finqa_1": {
    "article_id": 123,
    "fragment_ids": [456, 457, 458]
  }
}
```

## 🎯 **Następne kroki**

1. **Uruchom szybki test** - `python run_full_pipeline.py --quick FinQA text`
2. **Sprawdź wyniki** - `ls results/` i `ls reports/`
3. **Uruchom pełny pipeline** - `python run_full_pipeline.py --full`
4. **Analizuj raporty** - Sprawdź wykresy i tabele porównawcze
5. **Porównaj z literaturą** - Sprawdź czy wyniki są zgodne z benchmarkami

## 📞 **Wsparcie**

- **Logi** - Sprawdź logi w konsoli
- **Pliki** - Sprawdź pliki w `results/` i `reports/`
- **API** - Sprawdź status API na `http://localhost:8000/health`
- **Backend** - Sprawdź logi backendu

---

**🎉 Gotowe do ewaluacji!**
