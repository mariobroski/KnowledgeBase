# Szablony Tabel Wyników Benchmarków

## Rozdział 3.A - RAGBench (TRACe)

### Tabela 3.1: Wyniki RAGBench - Domena FinQA

| Polityka | Adherence ↑ | Completeness ↑ | Utilization ↑ | Relevance ↑ | Latencja P95 (ms) ↓ | Tokeny/Zapytanie ↓ | Koszt/Zapytanie ($) ↓ |
|----------|-------------|----------------|---------------|-------------|---------------------|--------------------|-----------------------|
| Text-RAG | 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Facts-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Graph-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |

**Δ względem Text-RAG:**
- Facts-RAG: Adherence +X.X%, Tokeny -X.X%, Koszt -X.X%
- Graph-RAG: Adherence +X.X%, Tokeny -X.X%, Koszt -X.X%

### Tabela 3.2: Wyniki RAGBench - Domena TAT-QA

| Polityka | Adherence ↑ | Completeness ↑ | Utilization ↑ | Relevance ↑ | Latencja P95 (ms) ↓ | Tokeny/Zapytanie ↓ | Koszt/Zapytanie ($) ↓ |
|----------|-------------|----------------|---------------|-------------|---------------------|--------------------|-----------------------|
| Text-RAG | 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Facts-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Graph-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |

**Δ względem Text-RAG:**
- Facts-RAG: Adherence +X.X%, Tokeny -X.X%, Koszt -X.X%
- Graph-RAG: Adherence +X.X%, Tokeny -X.X%, Koszt -X.X%

### Tabela 3.3: Wyniki RAGBench - Domena TechQA (opcjonalnie)

| Polityka | Adherence ↑ | Completeness ↑ | Utilization ↑ | Relevance ↑ | Latencja P95 (ms) ↓ | Tokeny/Zapytanie ↓ | Koszt/Zapytanie ($) ↓ |
|----------|-------------|----------------|---------------|-------------|---------------------|--------------------|-----------------------|
| Text-RAG | 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Facts-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |
| Graph-RAG| 0.XXX       | 0.XXX          | 0.XXX         | 0.XXX       | XXX                 | XXX                | 0.XXXX                |

## Rozdział 3.B - FinanceBench

### Tabela 3.4: Porównanie z GraphRAG na FinanceBench

| Polityka | Faithfulness ↑ | Halucynacje ↓ | Tokeny/Zapytanie ↓ | Latencja P95 (ms) ↓ | Koszt/Zapytanie ($) ↓ | Δ vs Literatura |
|----------|----------------|---------------|--------------------|--------------------|----------------------|-----------------|
| Text-RAG | 0.XXX          | X.X%          | XXX                | XXX                | 0.XXXX               | Baseline        |
| Facts-RAG| 0.XXX          | X.X%          | XXX                | XXX                | 0.XXXX               | -               |
| Graph-RAG| 0.XXX          | X.X%          | XXX                | XXX                | 0.XXXX               | Literatura: -6% halucynacji, -80% tokenów |

**Porównanie z literaturą GraphRAG:**
- Nasze Graph-RAG vs Text-RAG: Halucynacje -X.X%, Tokeny -X.X%
- Literatura GraphRAG: Halucynacje -6%, Tokeny -80%
- **Wniosek:** Trendy zgodne z literaturą, rząd wielkości porównywalny

## Rozdział 3.C - Tabela Zbiorcza

### Tabela 3.5: Podsumowanie Wszystkich Benchmarków

| Benchmark | Domena | Polityka | Adherence/Faithfulness ↑ | Completeness ↑ | Relevance ↑ | Latencja P95 ↓ | Tokeny ↓ | Koszt ↓ |
|-----------|--------|----------|--------------------------|----------------|-------------|----------------|----------|---------|
| RAGBench  | FinQA  | Text     | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| RAGBench  | FinQA  | Facts    | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| RAGBench  | FinQA  | Graph    | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| RAGBench  | TAT-QA | Text     | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| RAGBench  | TAT-QA | Facts    | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| RAGBench  | TAT-QA | Graph    | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| FinanceBench | Finance | Text  | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| FinanceBench | Finance | Facts | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |
| FinanceBench | Finance | Graph | 0.XXX                    | 0.XXX          | 0.XXX       | XXX ms         | XXX      | $0.XXXX |

## Formuły Obliczeń TRACe

### Relevance (Jakość Retrievera)
```
Relevance = |Retrieved ∩ Relevant| / |Retrieved ∪ Relevant|
```
- Retrieved: Tokeny z pobranych fragmentów kontekstu
- Relevant: Tokeny z etykiet ground truth (relevant spans)
- Miara: Jaccard similarity

### Utilization (Wykorzystanie Kontekstu)
```
Utilization = |Response ∩ Context| / |Context|
```
- Response: Tokeny z wygenerowanej odpowiedzi
- Context: Tokeny z dostarczonego kontekstu
- Miara: Odsetek tokenów kontekstu wykorzystanych w odpowiedzi

### Adherence (Faithfulness/Unikanie Halucynacji)
```
Adherence = |Response ∩ Context| / |Response|
```
- Response: Tokeny z wygenerowanej odpowiedzi
- Context: Tokeny z kontekstu źródłowego
- Miara: Odsetek tokenów odpowiedzi mających pokrycie w kontekście

### Completeness (Kompletność Odpowiedzi)
```
Completeness = |Response ∩ Expected| / |Expected|
```
- Response: Tokeny z wygenerowanej odpowiedzi
- Expected: Tokeny z oczekiwanej odpowiedzi (ground truth)
- Miara: Odsetek kluczowych informacji uwzględnionych w odpowiedzi

## Progi Metryk (SLO)

### Metryki TRACe
- **Adherence (min):** 0.80 (80% faithfulness)
- **Completeness (min):** 0.70 (70% kompletności)
- **Relevance (min):** 0.65 (65% trafności retrievera)
- **Utilization (min):** 0.50 (50% wykorzystania kontekstu)

### Metryki Wydajności
- **Latencja P95 (max):** 2000ms
- **Oszczędność tokenów (min):** 30% vs Text-RAG
- **Koszt/zapytanie (max):** $0.05

## Interpretacja Wyników

### Kryteria Sukcesu
1. **Graph-RAG vs Text-RAG:**
   - Adherence: +5-15% (redukcja halucynacji)
   - Tokeny: -20-50% (oszczędność kosztów)
   - Latencja: ±10% (akceptowalna zmiana)

2. **Facts-RAG vs Text-RAG:**
   - Adherence: +3-10% (lepsza faktyczność)
   - Tokeny: -30-60% (znacząca oszczędność)
   - Completeness: ≥90% Text-RAG (zachowanie jakości)

3. **Zgodność z Literaturą:**
   - GraphRAG: ~6% mniej halucynacji, ~80% mniej tokenów
   - Nasze wyniki powinny pokazywać podobne trendy

### Wnioski Badawcze
1. **Hipoteza H1:** Graph-RAG redukuje halucynacje przy zachowaniu kompletności
2. **Hipoteza H2:** Facts-RAG optymalizuje koszt przy minimalnej utracie jakości
3. **Hipoteza H3:** System spełnia wymagania niefunkcjonalne (latencja, koszt)

## Szablon Raportu

### Sekcja Wyników
"Na korpusach RAGBench (FinQA, TAT-QA) i FinanceBench nasz system osiągnął następujące wyniki:

- **Graph-RAG:** Adherence X.XXX (vs X.XXX Text-RAG), redukcja tokenów o XX%
- **Facts-RAG:** Adherence X.XXX, redukcja tokenów o XX%, koszt $X.XXXX/zapytanie
- **Wydajność:** P95 latencja XXXms, spełnienie SLO ≤2000ms

Wyniki są zgodne z trendami raportowanymi w literaturze GraphRAG (6% redukcja halucynacji, 80% redukcja tokenów), potwierdzając skuteczność implementacji na realnych korpusach bez sztucznych scenariuszy."