from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.services.janusgraph_service import janusgraph_service


def _upsert_entity(name: str, e_type: str) -> Optional[str]:
    return janusgraph_service.upsert_entity(name=name, entity_type=e_type, aliases=None)


def _upsert_rel(src: Optional[str], dst: Optional[str], r_type: str, weight: float = 0.8) -> bool:
    if not src or not dst:
        return False
    return janusgraph_service.upsert_relation(src, dst, r_type, weight=weight)


def seed_demo_graph(variant: str = "medium") -> Dict[str, int]:
    """Seeds a richer demo graph into JanusGraph. Idempotent.

    variant: "small" | "medium" | "large"
    """
    # Upewnij się, że jesteśmy połączeni
    if not janusgraph_service.is_connected():
        if not janusgraph_service.connect():
            raise RuntimeError("JanusGraph not connected")

    # Core concepts
    core_entities: List[Tuple[str, str]] = [
        ("RAG", "Technologia"),
        ("TekstRAG", "Technologia"),
        ("FaktRAG", "Technologia"),
        ("GrafRAG", "Technologia"),
        ("Embeddings", "Technologia"),
        ("VectorDB", "Kategoria"),
        ("Qdrant", "BazaWektorowa"),
        ("Weaviate", "BazaWektorowa"),
        ("FAISS", "Biblioteka"),
        ("JanusGraph", "BazaGrafowa"),
        ("Gremlin", "Interfejs"),
        ("Elasticsearch", "Wyszukiwarka"),
        ("Cassandra", "BazaKluczWartosc"),
        ("NER", "Technika"),
        ("RelationExtraction", "Technika"),
        ("Chunking", "Technika"),
        ("ReRanking", "Technika"),
        ("BM25", "Algorytm"),
        ("HNSW", "Algorytm"),
        ("CosineSimilarity", "Metryka"),
        ("LangChain", "Framework"),
        ("Ollama", "RuntimeLLM"),
        ("LLaMA", "ModelLLM"),
        ("Transformers", "Architektura"),
        ("Cache", "Komponent"),
        ("Monitoring", "Komponent"),
    ]

    # Larger variants add more examples
    if variant in ("medium", "large"):
        core_entities += [
            ("BM25+Embeddings", "Strategia"),
            ("Summarization", "Technika"),
            ("KeywordSearch", "Technika"),
            ("SentenceTransformers", "ModelEmbeddingow"),
        ]
    if variant == "large":
        core_entities += [
            ("Mistral", "ModelLLM"),
            ("Mixtral", "ModelLLM"),
            ("Reranker", "Model"),
            ("DCG", "Metryka"),
            ("MRR", "Metryka"),
            ("Precision", "Metryka"),
            ("Recall", "Metryka"),
        ]

    ids: Dict[str, Optional[str]] = {name: _upsert_entity(name, et) for name, et in core_entities}

    rels: List[Tuple[str, str, str, float]] = [
        ("RAG", "TekstRAG", "ZAWIERA", 0.9),
        ("RAG", "FaktRAG", "ZAWIERA", 0.9),
        ("RAG", "GrafRAG", "ZAWIERA", 0.9),
        ("RAG", "Embeddings", "WYKORZYSTUJE", 0.8),
        ("RAG", "VectorDB", "WYKORZYSTUJE", 0.8),
        ("Embeddings", "CosineSimilarity", "PORÓWNUJE", 0.8),
        ("VectorDB", "Qdrant", "PRZYKŁAD", 0.9),
        ("VectorDB", "Weaviate", "PRZYKŁAD", 0.8),
        ("VectorDB", "FAISS", "PRZYKŁAD", 0.7),
        ("TekstRAG", "Chunking", "WYKORZYSTUJE", 0.8),
        ("TekstRAG", "ReRanking", "WYKORZYSTUJE", 0.7),
        ("TekstRAG", "BM25", "ŁĄCZY_Z", 0.6),
        ("FaktRAG", "NER", "WYKORZYSTUJE", 0.9),
        ("FaktRAG", "RelationExtraction", "WYKORZYSTUJE", 0.9),
        ("GrafRAG", "JanusGraph", "WYKORZYSTUJE", 0.95),
        ("JanusGraph", "Gremlin", "INTERFEJS", 0.95),
        ("JanusGraph", "Elasticsearch", "INDEKSUJE", 0.7),
        ("JanusGraph", "Cassandra", "MAGAZYNUJE", 0.85),
        ("LangChain", "RAG", "WSPIERA", 0.7),
        ("Ollama", "LLaMA", "URUCHAMIA", 0.9),
        ("Transformers", "SentenceTransformers", "RODZINA", 0.7),
    ]

    if variant in ("medium", "large"):
        rels += [
            ("Embeddings", "SentenceTransformers", "GENERUJE", 0.85),
            ("BM25+Embeddings", "BM25", "ŁĄCZY_Z", 0.7),
            ("BM25+Embeddings", "Embeddings", "ŁĄCZY_Z", 0.7),
            ("Summarization", "Transformers", "WYKORZYSTUJE", 0.6),
        ]
    if variant == "large":
        rels += [
            ("Ollama", "Mistral", "URUCHAMIA", 0.8),
            ("Ollama", "Mixtral", "URUCHAMIA", 0.8),
            ("ReRanking", "Reranker", "WYKORZYSTUJE", 0.7),
            ("MRR", "Precision", "POWIĄZANY", 0.6),
            ("MRR", "Recall", "POWIĄZANY", 0.6),
            ("DCG", "ReRanking", "OCENIA", 0.6),
        ]

    created = 0
    for s, t, r, w in rels:
        if _upsert_rel(ids.get(s), ids.get(t), r, w):
            created += 1

    return {"entities": len(core_entities), "relations_upserted": created}

