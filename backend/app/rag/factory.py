from __future__ import annotations

from app.rag.base import RAGPolicy
from app.rag.fact_rag import FactRAG
from app.rag.graph_rag import GraphRAG
from app.rag.hybrid_rag import HybridRAG
from app.rag.smart_hybrid_rag import SmartHybridRAG
from app.rag.settings import RAGSettings
from app.rag.text_rag import TextRAG


class RAGPolicyFactory:
    """Fabryka polityk RAG uwzględniająca konfigurację zapytania."""

    @staticmethod
    def create_policy(policy_type: str, config: RAGSettings | None = None) -> RAGPolicy:
        if policy_type == "text":
            return TextRAG(config=config)
        if policy_type == "facts":
            return FactRAG(config=config)
        if policy_type == "graph":
            return GraphRAG(config=config)
        if policy_type == "hybrid":
            return HybridRAG(config=config)
        if policy_type == "smart_hybrid":
            return SmartHybridRAG(config=config)
        raise ValueError(f"Nieznany typ polityki: {policy_type}")
