import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.db.database_models import (
    Article as ArticleModel,
    Fragment as FragmentModel,
    Tag as TagModel,
)
from app.services.embedding_service import get_embedding_service
from app.services.fact_service import FactService
from app.utils.text_chunker import TextChunker

class ArticleService:
    """Serwis do zarządzania artykułami
    
    Ta klasa jest odpowiedzialna za operacje CRUD na artykułach i ich fragmentach.
    """
    
    def __init__(self, db: Session):
        """Inicjalizacja serwisu
        
        Args:
            db: Sesja bazy danych
        """
        self.db = db
    
    def get_articles(self, skip: int = 0, limit: int = 100) -> List[ArticleModel]:
        """Pobierz listę artykułów
        
        Args:
            skip: Liczba artykułów do pominięcia
            limit: Maksymalna liczba artykułów do zwrócenia
            
        Returns:
            Lista artykułów
        """
        return self.db.query(ArticleModel).offset(skip).limit(limit).all()
    
    def get_article(self, article_id: int) -> Optional[ArticleModel]:
        """Pobierz artykuł po ID
        
        Args:
            article_id: ID artykułu
            
        Returns:
            Artykuł lub None, jeśli nie znaleziono
        """
        return self.db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
    
    def create_article(
        self,
        *,
        title: str,
        content: str,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        author_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> ArticleModel:
        """Utwórz nowy artykuł wraz z fragmentami i indeksacją."""

        file_text = content or ""
        file_type = "text/plain"
        if file_content:
            try:
                file_text = file_content.decode("utf-8")
            except Exception:
                file_text = file_content.decode("latin-1", errors="ignore")
            file_type = "uploaded"

        tag_models: List[TagModel] = []
        if tags:
            for tag_name in tags:
                tag = self.db.query(TagModel).filter(TagModel.name == tag_name).first()
                if not tag:
                    tag = TagModel(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                tag_models.append(tag)

        article = ArticleModel(
            title=title,
            file_path=filename,
            file_type=file_type,
            status="szkic",
            created_by_id=author_id,
            created_by=str(author_id) if author_id else None,
        )
        article.tags = tag_models
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)

        from app.utils.text_chunker import TextChunker

        chunker = TextChunker(max_chunk_size=500, overlap=50)
        chunks = chunker.chunk_text(file_text)

        fragments: List[FragmentModel] = []
        for chunk in chunks:
            fragment = FragmentModel(
                article_id=article.id,
                content=chunk["content"],
                start_position=chunk["start_position"],
                end_position=chunk["end_position"],
                position=chunk["position"],
            )
            self.db.add(fragment)
            fragments.append(fragment)

        self.db.commit()
        for fragment in fragments:
            self.db.refresh(fragment)

        self._index_fragments(fragments, article)

        return article
    
    def update_article(self, article_id: int, article_data: Dict[str, Any]) -> Optional[ArticleModel]:
        """Aktualizuj artykuł
        
        Args:
            article_id: ID artykułu
            article_data: Dane artykułu do aktualizacji
            
        Returns:
            Zaktualizowany artykuł lub None, jeśli nie znaleziono
        """
        article = self.get_article(article_id)
        if not article:
            return None
        
        # Obsługa tagów
        if "tags" in article_data:
            tags = []
            tag_names = article_data.pop("tags")
            for tag_name in tag_names:
                tag = self.db.query(TagModel).filter(TagModel.name == tag_name).first()
                if not tag:
                    tag = TagModel(name=tag_name)
                    self.db.add(tag)
                    self.db.flush()
                tags.append(tag)
            article.tags = tags
        
        # Aktualizacja pozostałych pól
        for key, value in article_data.items():
            setattr(article, key, value)
        
        self.db.commit()
        self.db.refresh(article)
        return article
    
    def delete_article(self, article_id: int) -> bool:
        """Usuń artykuł
        
        Args:
            article_id: ID artykułu
            
        Returns:
            True, jeśli usunięto, False w przeciwnym razie
        """
        article = self.get_article(article_id)
        if not article:
            return False
        
        self.db.delete(article)
        self.db.commit()
        return True
    
    def get_fragments(self, article_id: int) -> List[FragmentModel]:
        """Pobierz fragmenty artykułu
        
        Args:
            article_id: ID artykułu
            
        Returns:
            Lista fragmentów
        """
        return (
            self.db.query(FragmentModel)
            .options(joinedload(FragmentModel.article))
            .filter(FragmentModel.article_id == article_id)
            .all()
        )
    
    def create_fragment(self, fragment_data: Dict[str, Any]) -> FragmentModel:
        """Utwórz nowy fragment
        
        Args:
            fragment_data: Dane fragmentu
            
        Returns:
            Utworzony fragment
        """
        fragment = FragmentModel(**fragment_data)
        self.db.add(fragment)
        self.db.commit()
        self.db.refresh(fragment)
        article = fragment.article or self.get_article(fragment.article_id)
        if article:
            self._index_fragments([fragment], article)
        return fragment
    
    def index_article(self, article_id: int) -> bool:
        """Indeksuj artykuł dla RAG
        
        Args:
            article_id: ID artykułu
            
        Returns:
            True, jeśli zindeksowano, False w przeciwnym razie
        """
        from app.services.fact_service import FactService
        
        article = self.get_article(article_id)
        if not article:
            return False
        
        # Oznacz artykuł jako zindeksowany
        article.indexed = True
        
        # Pobierz fragmenty artykułu
        fragments = self.db.query(FragmentModel).filter(FragmentModel.article_id == article_id).all()
        
        # Indeksuj każdy fragment
        fact_service = FactService(self.db)
        for fragment in fragments:
            # Oznacz fragment jako zindeksowany
            fragment.indexed = True
            
            # Wyodrębnij fakty z fragmentu
            try:
                facts = fact_service.extract_facts_from_fragment(fragment.id)
                fragment.facts_extracted = True
                fragment.fact_count = len(facts)
            except Exception as e:
                print(f"Błąd podczas ekstrakcji faktów z fragmentu {fragment.id}: {e}")
                fragment.facts_extracted = False
                fragment.fact_count = 0
        
        self.db.commit()
        return True

    def _index_fragments(self, fragments: List[FragmentModel], article: ArticleModel) -> None:
        """Generuje embeddingi fragmentów i zapisuje je w Qdrant."""
        embedding_service = get_embedding_service()
        if not embedding_service.is_enabled:
            return

        try:
            payloads = []
            for fragment in fragments:
                payloads.append(
                    {
                        "id": fragment.id,
                        "content": fragment.content or "",
                        "article_id": article.id,
                        "article_title": article.title,
                        "position": fragment.position,
                    }
                )
            vectors = embedding_service.upsert_fragments(payloads)

            if vectors is not None:
                for fragment, vector in zip(fragments, vectors):
                    fragment.embedding = vector.tolist()
                    fragment.indexed = True

            self.db.commit()
        except Exception as exc:  # pragma: no cover - best effort
            logger = logging.getLogger(__name__)
            logger.warning("Nie udało się zindeksować fragmentów w Qdrant: %s", exc)
    
    def process_article(self, article_id: int) -> Dict[str, Any]:
        """Uruchamia kompletny pipeline indeksacji dla istniejącego artykułu."""

        logger = logging.getLogger(__name__)

        article = (
            self.db.query(ArticleModel)
            .options(joinedload(ArticleModel.fragments))
            .filter(ArticleModel.id == article_id)
            .first()
        )
        if not article:
            return {
                "article_id": article_id,
                "status": "error",
                "errors": ["Artykuł nie istnieje"],
            }

        fragments = list(article.fragments or [])

        stats: Dict[str, Any] = {
            "article_id": article_id,
            "title": article.title,
            "status": "processing",
            "fragments_total": len(fragments),
            "fragments_indexed": 0,
            "fragments_processed": 0,
            "facts_created": 0,
            "sizes": {"chars": 0, "words": 0},
            "timings_ms": {"total": 0, "embedding": 0, "facts": 0},
            "warnings": [],
            "errors": [],
        }

        try:
            article.status = "processing"
            article.indexed = False
            article.updated_at = datetime.now()
            self.db.commit()

            fragments = sorted(
                fragments,
                key=lambda fragment: (fragment.position or 0, fragment.id),
            )

            if not fragments:
                stats["errors"].append("Brak fragmentów do przetworzenia")
                article.status = "error"
                self.db.commit()
                return stats

            t0 = time.perf_counter()

            # --- Embeddingi ---
            embedding_service = get_embedding_service()
            fragments_to_embed = [
                fragment
                for fragment in fragments
                if not fragment.indexed or not fragment.embedding
            ]

            if embedding_service.is_enabled and fragments_to_embed:
                t_emb_start = time.perf_counter()
                self._index_fragments(fragments_to_embed, article)
                stats["timings_ms"]["embedding"] = int((time.perf_counter() - t_emb_start) * 1000)
                stats["fragments_indexed"] = len(fragments_to_embed)
            elif not embedding_service.is_enabled:
                stats["warnings"].append(
                    "EmbeddingService niedostępny – pomijam aktualizację wektorów"
                )

            # --- Ekstrakcja faktów i aktualizacja grafu ---
            fact_service = FactService(self.db)
            fragments_to_process = [
                fragment for fragment in fragments if not fragment.facts_extracted
            ]

            created_facts_total = 0
            t_fact_start = time.perf_counter()
            for fragment in fragments_to_process:
                facts = fact_service.extract_facts_from_fragment(fragment.id)
                fragment.facts_extracted = True
                fragment.fact_count = len(facts)
                created_facts_total += len(facts)
            stats["fragments_processed"] = len(fragments_to_process)
            stats["facts_created"] = created_facts_total
            stats["timings_ms"]["facts"] = int((time.perf_counter() - t_fact_start) * 1000)

            # --- Rozmiar przetworzonej treści ---
            total_chars = sum(len((f.content or "")) for f in fragments)
            total_words = sum(len((f.content or "").split()) for f in fragments)
            stats["sizes"]["chars"] = total_chars
            stats["sizes"]["words"] = total_words

            # --- Finalizacja ---
            if stats["errors"]:
                article.status = "error"
            else:
                article.status = "indexed"
                article.indexed = True

            article.updated_at = datetime.now()
            self.db.commit()
            stats["timings_ms"]["total"] = int((time.perf_counter() - t0) * 1000)
            stats["status"] = article.status

            return stats

        except Exception as exc:  # pragma: no cover - safety net
            logger.error("Article processing failed: %s", exc)
            stats["errors"].append(str(exc))
            article.status = "error"
            article.updated_at = datetime.now()
            self.db.commit()
            stats["status"] = "error"
            return stats
