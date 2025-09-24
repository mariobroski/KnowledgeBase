#!/usr/bin/env python3
"""
Skrypt do aktualizacji artykułów - usunięcie artykułów o historii Polski
i dodanie artykułów związanych z projektem RAG/AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.database_models import Article, Tag, Fragment, article_tag, Fact, Entity, Relation
from datetime import datetime

def clear_database():
    """Czyści bazę danych z istniejących danych"""
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

def create_project_articles():
    """Tworzy artykuły związane z projektem RAG/AI"""
    db = SessionLocal()
    
    try:
        # Przykładowe tagi
        tags_data = [
            "RAG", "AI", "machine learning", "NLP", "retrieval", "generation",
            "embeddings", "vector database", "LLM", "transformers", "BERT",
            "GPT", "semantic search", "knowledge base", "chatbot", "QA system",
            "text processing", "information retrieval", "neural networks", "deep learning"
        ]
        
        # Tworzenie tagów
        tag_objects = {}
        for tag_name in tags_data:
            tag = Tag(name=tag_name)
            db.add(tag)
            tag_objects[tag_name] = tag
        
        db.flush()  # Zapisz tagi, aby uzyskać ID
        
        # Dane artykułów związanych z projektem
        articles_data = [
            {
                "title": "Wprowadzenie do Retrieval-Augmented Generation (RAG)",
                "content": """Retrieval-Augmented Generation (RAG) to zaawansowana technika w dziedzinie sztucznej inteligencji, która łączy możliwości wyszukiwania informacji z generowaniem tekstu. RAG został opracowany w celu rozwiązania problemów związanych z ograniczeniami tradycyjnych modeli językowych.

Główne komponenty RAG:

1. Retriever (Wyszukiwarka):
- Odpowiada za znajdowanie relevantnych dokumentów
- Wykorzystuje embeddingi do reprezentacji tekstu
- Może używać różnych algorytmów wyszukiwania (BM25, dense retrieval)
- Indeksuje bazę wiedzy w formie wektorowej

2. Generator:
- Generuje odpowiedzi na podstawie znalezionych dokumentów
- Zazwyczaj wykorzystuje modele typu transformer
- Łączy kontekst z zapytaniem użytkownika
- Może być dostrojony do konkretnej domeny

Zalety RAG:
- Dostęp do aktualnych informacji
- Redukcja halucynacji modelu
- Możliwość weryfikacji źródeł
- Elastyczność w aktualizacji wiedzy
- Lepsza kontrola nad generowanymi odpowiedziami

Zastosowania:
- Systemy pytań i odpowiedzi
- Chatboty korporacyjne
- Asystenci badawczy
- Systemy rekomendacji treści
- Automatyczne streszczanie dokumentów

RAG stanowi przełom w budowaniu inteligentnych systemów, które mogą efektywnie wykorzystywać zewnętrzne źródła wiedzy.""",
                "tags": ["RAG", "AI", "retrieval", "generation", "NLP", "knowledge base"]
            },
            {
                "title": "Embeddingi i Wyszukiwanie Semantyczne",
                "content": """Embeddingi to numeryczne reprezentacje tekstu, które umożliwiają maszynom zrozumienie znaczenia i kontekstu słów, zdań czy całych dokumentów. W systemach RAG odgrywają kluczową rolę w procesie wyszukiwania semantycznego.

Rodzaje embeddingów:

1. Word Embeddings:
- Word2Vec: Wykorzystuje kontekst słów do tworzenia reprezentacji
- GloVe: Łączy statystyki globalne i lokalne
- FastText: Uwzględnia strukturę morfologiczną słów

2. Sentence Embeddings:
- BERT: Bidirectional Encoder Representations from Transformers
- Sentence-BERT: Zoptymalizowany do reprezentacji zdań
- Universal Sentence Encoder: Model Google do embeddingów zdań

3. Document Embeddings:
- Doc2Vec: Rozszerzenie Word2Vec na dokumenty
- BERT-based: Wykorzystanie BERT do reprezentacji dokumentów
- Transformer-based: Nowoczesne modele transformer

Wyszukiwanie semantyczne:

Proces wyszukiwania:
1. Konwersja zapytania na embedding
2. Obliczenie podobieństwa z dokumentami w bazie
3. Ranking wyników według podobieństwa
4. Zwrócenie najbardziej relevantnych dokumentów

Metryki podobieństwa:
- Cosine similarity: Najczęściej używana
- Euclidean distance: Odległość euklidesowa
- Dot product: Iloczyn skalarny

Bazy danych wektorowych:
- Pinecone: Zarządzana usługa w chmurze
- Weaviate: Open-source z GraphQL
- Chroma: Lekka baza dla aplikacji AI
- FAISS: Biblioteka Facebook do szybkiego wyszukiwania

Optymalizacja:
- Approximate Nearest Neighbor (ANN)
- Hierarchical Navigable Small World (HNSW)
- Locality-Sensitive Hashing (LSH)

Embeddingi rewolucjonizują sposób, w jaki maszyny rozumieją i przetwarzają język naturalny.""",
                "tags": ["embeddings", "semantic search", "BERT", "vector database", "NLP", "similarity"]
            },
            {
                "title": "Architektura Systemów RAG",
                "content": """Projektowanie efektywnej architektury systemu RAG wymaga przemyślanego podejścia do integracji komponentów wyszukiwania i generowania. Nowoczesne systemy RAG składają się z kilku kluczowych warstw.

Warstwy architektury RAG:

1. Warstwa danych:
- Źródła danych (dokumenty, bazy wiedzy, API)
- Preprocessing i czyszczenie danych
- Segmentacja dokumentów na fragmenty
- Metadane i indeksowanie

2. Warstwa embeddingów:
- Model embeddingów (BERT, Sentence-BERT, OpenAI)
- Baza danych wektorowych
- Indeksowanie i aktualizacja
- Optymalizacja wyszukiwania

3. Warstwa wyszukiwania:
- Query processing i rozszerzanie zapytań
- Ranking i filtrowanie wyników
- Hybrydowe wyszukiwanie (dense + sparse)
- Kontekst i personalizacja

4. Warstwa generowania:
- Model językowy (GPT, T5, BART)
- Prompt engineering i templating
- Kontrola jakości odpowiedzi
- Post-processing i formatowanie

5. Warstwa aplikacji:
- API i interfejsy użytkownika
- Zarządzanie sesjami
- Monitoring i logowanie
- Bezpieczeństwo i autoryzacja

Wzorce architektoniczne:

1. Pipeline RAG:
- Sekwencyjne przetwarzanie
- Prosty w implementacji
- Ograniczona elastyczność

2. Modular RAG:
- Komponenty wymienne
- Łatwość testowania
- Skalowalna architektura

3. Adaptive RAG:
- Dynamiczny wybór strategii
- Optymalizacja w czasie rzeczywistym
- Uczenie się z feedbacku

Najlepsze praktyki:
- Monitoring wydajności i jakości
- A/B testing różnych konfiguracji
- Caching często używanych wyników
- Graceful degradation przy awariach
- Continuous integration/deployment

Wyzwania techniczne:
- Latencja vs. jakość wyników
- Skalowanie z rosnącą bazą wiedzy
- Konsystencja i aktualność danych
- Bezpieczeństwo i prywatność

Dobrze zaprojektowana architektura RAG jest kluczem do sukcesu systemu AI.""",
                "tags": ["RAG", "architecture", "system design", "AI", "scalability", "performance"]
            },
            {
                "title": "Modele Językowe w Systemach RAG",
                "content": """Modele językowe stanowią serce systemów RAG, odpowiadając za generowanie naturalnych i spójnych odpowiedzi na podstawie wyszukanych informacji. Wybór odpowiedniego modelu ma kluczowy wpływ na jakość całego systemu.

Typy modeli językowych:

1. Autoregressive Models:
- GPT (Generative Pre-trained Transformer)
- GPT-2, GPT-3, GPT-4: Ewolucja możliwości
- Generowanie tekstu token po token
- Doskonałe w zadaniach generatywnych

2. Encoder-Decoder Models:
- T5 (Text-to-Text Transfer Transformer)
- BART (Bidirectional and Auto-Regressive Transformers)
- Uniwersalne w różnych zadaniach NLP
- Efektywne w kondensacji informacji

3. Encoder-Only Models:
- BERT i jego warianty
- Głównie do zadań rozumienia tekstu
- Wykorzystywane w komponencie retrieval

Kluczowe charakterystyki:

Rozmiar modelu:
- Small (< 1B parametrów): Szybkie, ograniczone możliwości
- Medium (1B-10B): Balans między wydajnością a jakością
- Large (10B-100B): Wysoka jakość, wymagają więcej zasobów
- Very Large (100B+): Najlepsza jakość, kosztowne w utrzymaniu

Fine-tuning:
- Domain adaptation: Dostrojenie do konkretnej dziedziny
- Task-specific tuning: Optymalizacja pod konkretne zadanie
- Few-shot learning: Uczenie z małą ilością przykładów
- In-context learning: Uczenie w kontekście zapytania

Prompt Engineering:
- System prompts: Instrukcje dla modelu
- Few-shot examples: Przykłady w prompcie
- Chain-of-thought: Prowadzenie rozumowania
- Template design: Strukturyzacja promptów

Optymalizacja wydajności:
- Model quantization: Redukcja precyzji
- Knowledge distillation: Transfer wiedzy do mniejszego modelu
- Caching: Przechowywanie częstych odpowiedzi
- Batching: Grupowanie zapytań

Ewaluacja jakości:
- BLEU, ROUGE: Metryki podobieństwa
- Perplexity: Miara niepewności modelu
- Human evaluation: Ocena przez ludzi
- Task-specific metrics: Metryki dedykowane

Wyzwania:
- Hallucination: Generowanie nieprawdziwych informacji
- Bias: Uprzedzenia w danych treningowych
- Consistency: Spójność odpowiedzi
- Factual accuracy: Dokładność faktyczna

Przyszłość modeli w RAG:
- Multimodal models: Obsługa tekstu, obrazów, audio
- Retrieval-augmented pre-training: Integracja retrieval w pre-trainingu
- Adaptive models: Modele dostosowujące się do kontekstu
- Efficient architectures: Nowe architektury zoptymalizowane pod RAG

Wybór odpowiedniego modelu językowego jest kluczowy dla sukcesu systemu RAG.""",
                "tags": ["LLM", "GPT", "BERT", "transformers", "fine-tuning", "prompt engineering"]
            },
            {
                "title": "Ewaluacja i Metryki Systemów RAG",
                "content": """Ewaluacja systemów RAG jest kompleksowym procesem, który wymaga oceny zarówno komponentu wyszukiwania, jak i generowania. Właściwe metryki pozwalają na obiektywną ocenę wydajności i jakości systemu.

Metryki komponentu Retrieval:

1. Precision i Recall:
- Precision: Odsetek relevantnych dokumentów wśród zwróconych
- Recall: Odsetek relevantnych dokumentów znalezionych
- F1-score: Harmoniczna średnia precision i recall

2. Ranking Metrics:
- Mean Average Precision (MAP): Średnia precyzja dla różnych poziomów recall
- Normalized Discounted Cumulative Gain (NDCG): Uwzględnia pozycję w rankingu
- Mean Reciprocal Rank (MRR): Średnia odwrotność pozycji pierwszego relevantnego wyniku

3. Coverage Metrics:
- Document coverage: Procent dokumentów w bazie, które są wyszukiwane
- Query coverage: Procent zapytań, dla których system znajduje odpowiedzi

Metryki komponentu Generation:

1. Automatic Metrics:
- BLEU: Podobieństwo n-gramów z referencją
- ROUGE: Overlap z tekstem referencyjnym
- METEOR: Uwzględnia synonimy i parafrazowanie
- BERTScore: Podobieństwo semantyczne używając BERT

2. Semantic Metrics:
- Semantic similarity: Podobieństwo semantyczne odpowiedzi
- Factual accuracy: Dokładność faktyczna informacji
- Consistency: Spójność odpowiedzi na podobne pytania

3. Quality Metrics:
- Fluency: Płynność i naturalność tekstu
- Coherence: Spójność logiczna odpowiedzi
- Relevance: Trafność odpowiedzi względem pytania

Metryki end-to-end:

1. Task-specific Metrics:
- Exact Match (EM): Dokładne dopasowanie odpowiedzi
- F1 na poziomie tokenów: Overlap tokenów z referencją
- Answer accuracy: Poprawność odpowiedzi w zadaniach QA

2. User Experience Metrics:
- Response time: Czas odpowiedzi systemu
- User satisfaction: Zadowolenie użytkowników
- Task completion rate: Wskaźnik ukończenia zadań

Human Evaluation:

1. Relevance Assessment:
- Czy odpowiedź jest relevantna do pytania?
- Skala 1-5 lub binary (tak/nie)

2. Factual Accuracy:
- Czy informacje w odpowiedzi są prawdziwe?
- Weryfikacja z wiarygodnymi źródłami

3. Completeness:
- Czy odpowiedź jest kompletna?
- Czy zawiera wszystkie istotne informacje?

4. Clarity and Readability:
- Czy odpowiedź jest jasna i zrozumiała?
- Ocena stylu i struktury tekstu

Automated Evaluation Frameworks:

1. RAGAS (RAG Assessment):
- Framework do automatycznej ewaluacji RAG
- Metryki: faithfulness, answer relevancy, context precision

2. TruthfulQA:
- Benchmark do oceny prawdziwości odpowiedzi
- Fokus na unikanie halucynacji

3. Natural Questions:
- Dataset z naturalnymi pytaniami
- Ewaluacja w realistic scenarios

Best Practices:

1. Multi-dimensional Evaluation:
- Nie polegaj tylko na jednej metryce
- Kombinuj automatic i human evaluation
- Uwzględnij różne aspekty jakości

2. Continuous Monitoring:
- Regularnie monitoruj wydajność w produkcji
- Ustaw alerty dla spadków jakości
- Zbieraj feedback od użytkowników

3. A/B Testing:
- Testuj różne konfiguracje systemu
- Porównuj metryki między wersjami
- Podejmuj decyzje oparte na danych

Ewaluacja jest kluczowa dla rozwoju i utrzymania wysokiej jakości systemów RAG.""",
                "tags": ["evaluation", "metrics", "RAG", "quality assessment", "benchmarking", "testing"]
            }
        ]
        
        # Tworzenie artykułów
        for i, article_data in enumerate(articles_data, 1):
            article = Article(
                title=article_data["title"],
                file_path=f"rag_article_{i}.txt",
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
        print(f"\n🎉 Pomyślnie utworzono {len(articles_data)} artykułów o RAG/AI!")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia artykułów: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Aktualizacja artykułów - usunięcie historii Polski i dodanie artykułów o RAG/AI")
    print("=" * 80)
    
    clear_database()
    create_project_articles()
    
    print("✨ Gotowe! System zawiera teraz artykuły związane z projektem RAG/AI.")