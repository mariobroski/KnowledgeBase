from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable, List, Sequence, Optional

import numpy as np

try:  # pragma: no cover - zależność opcjonalna
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore

try:  # pragma: no cover - jeśli qdrant nie jest dostępny
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:  # pragma: no cover
    QdrantClient = None  # type: ignore
    qmodels = None  # type: ignore

try:  # pragma: no cover - Weaviate alternative
    import weaviate
except Exception:  # pragma: no cover
    weaviate = None  # type: ignore

try:  # pragma: no cover - FAISS alternative
    import faiss
    import numpy as np
except Exception:  # pragma: no cover
    faiss = None  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "fragments"


class EmbeddingService:
    """Odpowiada za generowanie embeddingów i integrację z różnymi bazami wektorowymi."""

    def __init__(self) -> None:
        self._model = None
        self._client = None
        self._collection_ready = False
        self._enabled = False
        self._vector_db_type = settings.VECTOR_DB_TYPE

        if SentenceTransformer is None:
            logger.warning("SentenceTransformer niedostępny – funkcje wektorowe zostaną wyłączone.")
            return

        try:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._initialize_vector_db()
            self._enabled = True
            logger.info("EmbeddingService został zainicjalizowany (model: %s, DB: %s)", 
                       settings.EMBEDDING_MODEL, self._vector_db_type)
        except Exception as exc:  # pragma: no cover - inicjalizacja best effort
            logger.warning("Nie udało się zainicjalizować EmbeddingService: %s", exc)
            self._model = None
            self._client = None
            self._enabled = False

    def _initialize_vector_db(self):
        """Initialize vector database based on configuration."""
        if self._vector_db_type == "qdrant":
            self._initialize_qdrant()
        elif self._vector_db_type == "weaviate":
            self._initialize_weaviate()
        elif self._vector_db_type == "faiss":
            self._initialize_faiss()
        else:
            raise ValueError(f"Unsupported vector database type: {self._vector_db_type}")

    def _initialize_qdrant(self):
        """Initialize Qdrant client."""
        if QdrantClient is None:
            raise RuntimeError("QdrantClient not available")
        
        self._client = QdrantClient(
            url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            api_key=settings.QDRANT_API_KEY or None,
        )
        self._ensure_collection()

    def _initialize_weaviate(self):
        """Initialize Weaviate client."""
        if weaviate is None:
            raise RuntimeError("Weaviate not available")
        
        self._client = weaviate.Client(
            url=f"http://{settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}"
        )
        self._ensure_weaviate_schema()

    def _initialize_faiss(self):
        """Initialize FAISS index."""
        if faiss is None:
            raise RuntimeError("FAISS not available")
        
        self._client = faiss.IndexFlatIP(self.dimension)
        # FAISS doesn't need collection setup
        self._collection_ready = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def dimension(self) -> int:
        if not self._model:
            raise RuntimeError("Model embeddingów nie został załadowany")
        return int(self._model.get_sentence_embedding_dimension())

    def _ensure_collection(self) -> None:
        assert self._client is not None
        if qmodels is None:
            return
        if self._client.collection_exists(COLLECTION_NAME):
            self._collection_ready = True
            return
        self._client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=self.dimension, distance=qmodels.Distance.COSINE),
        )
        self._collection_ready = True

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        if not self._model:
            raise RuntimeError("Model embeddingów niedostępny")
        embeddings = self._model.encode(list(texts), convert_to_numpy=True, show_progress_bar=False)
        if isinstance(embeddings, list):
            embeddings = np.asarray(embeddings)
        return embeddings.astype(np.float32)

    def upsert_fragments(self, fragment_payloads: Iterable[dict]) -> Optional[np.ndarray]:
        """Upsert fragments to vector database"""
        if not self.is_enabled or not self._client:
            return None
        
        payloads = list(fragment_payloads)
        if not payloads:
            return None
        
        if self._vector_db_type == "qdrant":
            return self._upsert_qdrant(payloads)
        elif self._vector_db_type == "weaviate":
            return self._upsert_weaviate(payloads)
        elif self._vector_db_type == "faiss":
            return self._upsert_faiss(payloads)
        else:
            raise ValueError(f"Unsupported vector database type: {self._vector_db_type}")
    
    def _upsert_qdrant(self, payloads: List[dict]) -> np.ndarray:
        """Upsert fragments to Qdrant"""
        if not self._collection_ready:
            self._ensure_collection()
        
        vectors = self.embed_texts([payload["content"] for payload in payloads])
        points = []
        for idx, payload in enumerate(payloads):
            points.append(
                qmodels.PointStruct(
                    id=payload["id"],
                    vector=vectors[idx],
                    payload={key: value for key, value in payload.items() if key != "content"},
                )
        )
        self._client.upsert(collection_name=COLLECTION_NAME, points=points)
        return vectors
    
    def _upsert_weaviate(self, payloads: List[dict]) -> np.ndarray:
        """Upsert fragments to Weaviate"""
        vectors = self.embed_texts([payload["content"] for payload in payloads])
        # TODO: Implement Weaviate upsert
        return vectors
    
    def _upsert_faiss(self, payloads: List[dict]) -> np.ndarray:
        """Upsert fragments to FAISS"""
        vectors = self.embed_texts([payload["content"] for payload in payloads])
        # TODO: Implement FAISS upsert
        return vectors

    def search(self, text: str, limit: int = 5) -> List[dict]:
        if not self.is_enabled or not self._client or qmodels is None:
            raise RuntimeError("EmbeddingService jest wyłączony")
        vector = self.embed_texts([text])[0]
        search_result = self._client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit,
        )
        hits: List[dict] = []
        for point in search_result:
            point_id = point.id
            if isinstance(point_id, str) and point_id.isdigit():
                point_id = int(point_id)
            hits.append(
                {
                    "fragment_id": point_id,
                    "score": float(point.score),
                    "payload": dict(point.payload or {}),
                }
            )
        return hits


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
