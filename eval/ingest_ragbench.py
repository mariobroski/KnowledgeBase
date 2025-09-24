#!/usr/bin/env python3
"""
Importer RAGBench - pobiera i wczytuje domeny (FinQA, TAT-QA, TechQA, CUAD, EManual)
do tabel articles/fragments z zachowaniem oryginalnych ID dokumentów
"""

import os
import sys
import json
import logging
import requests
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Session

# Dodaj ścieżkę do backend
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.database import get_db, engine
from app.db.database_models import Article, Fragment, Tag
from app.services.article_service import ArticleService
from app.services.embedding_service import get_embedding_service
from app.services.fact_service import FactService
from app.services.graph_update_service import graph_update_service

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGBenchImporter:
    """Importer korpusów RAGBench"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # URL-e do pobrania korpusów RAGBench
        self.corpus_urls = {
            "FinQA": "https://github.com/czyssrs/FinQA/archive/refs/heads/main.zip",
            "TAT-QA": "https://github.com/NExTplusplus/TAT-QA/archive/refs/heads/main.zip",
            "TechQA": "https://github.com/IBM/TechQA/archive/refs/heads/main.zip",
            "CUAD": "https://github.com/TheAtticusProject/cuad/archive/refs/heads/main.zip",
            "EManual": "https://github.com/allenai/EManual/archive/refs/heads/main.zip"
        }
        
        # Mapowanie ID dokumentów benchmarku na nasze ID fragmentów
        self.ref_map = {}
        
    def download_corpus(self, domain: str) -> bool:
        """
        Pobiera korpus z RAGBench
        
        Args:
            domain: Nazwa domeny (FinQA, TAT-QA, TechQA, CUAD, EManual)
            
        Returns:
            True jeśli pobieranie się powiodło
        """
        if domain not in self.corpus_urls:
            logger.error(f"Nieobsługiwana domena: {domain}")
            return False
        
        logger.info(f"Pobieranie korpusu {domain}...")
        
        try:
            url = self.corpus_urls[domain]
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Zapisz do pliku ZIP
            zip_path = self.data_dir / f"{domain}.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Rozpakuj ZIP
            extract_dir = self.data_dir / domain
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Korpus {domain} pobrany i rozpakowany")
            return True
            
        except Exception as e:
            logger.error(f"Błąd pobierania korpusu {domain}: {e}")
            return False
    
    def parse_finqa_corpus(self, data_dir: Path) -> Dict[str, Any]:
        """Parsuje korpus FinQA"""
        logger.info("Parsowanie korpusu FinQA...")
        
        # Ścieżki do plików FinQA
        train_file = data_dir / "FinQA-main" / "dataset" / "train.json"
        dev_file = data_dir / "FinQA-main" / "dataset" / "dev.json"
        test_file = data_dir / "FinQA-main" / "dataset" / "test.json"
        
        documents = []
        queries = []
        
        # Parsuj pliki JSON
        for file_path in [train_file, dev_file, test_file]:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    # Dodaj dokument
                    doc_id = f"finqa_{item['id']}"
                    documents.append({
                        "id": doc_id,
                        "title": f"Financial Report {item['id']}",
                        "content": self._format_finqa_content(item),
                        "domain": "FinQA",
                        "metadata": {
                            "original_id": item['id'],
                            "split": file_path.stem
                        }
                    })
                    
                    # Dodaj zapytania
                    for qa in item.get('qa_pairs', []):
                        query_id = f"finqa_{item['id']}_{qa['id']}"
                        queries.append({
                            "query_id": query_id,
                            "query": qa['question'],
                            "ground_truth": qa.get('answer', []),
                            "expected_answer": qa.get('answer', ''),
                            "domain": "FinQA",
                            "metadata": {
                                "original_doc_id": item['id'],
                                "original_qa_id": qa['id']
                            }
                        })
        
        return {
            "documents": documents,
            "queries": queries
        }
    
    def parse_tatqa_corpus(self, data_dir: Path) -> Dict[str, Any]:
        """Parsuje korpus TAT-QA"""
        logger.info("Parsowanie korpusu TAT-QA...")
        
        # Ścieżki do plików TAT-QA
        train_file = data_dir / "TAT-QA-main" / "dataset" / "train.json"
        dev_file = data_dir / "TAT-QA-main" / "dataset" / "dev.json"
        test_file = data_dir / "TAT-QA-main" / "dataset" / "test.json"
        
        documents = []
        queries = []
        
        # Parsuj pliki JSON
        for file_path in [train_file, dev_file, test_file]:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    # Dodaj dokument
                    doc_id = f"tatqa_{item['id']}"
                    documents.append({
                        "id": doc_id,
                        "title": f"Financial Table {item['id']}",
                        "content": self._format_tatqa_content(item),
                        "domain": "TAT-QA",
                        "metadata": {
                            "original_id": item['id'],
                            "split": file_path.stem
                        }
                    })
                    
                    # Dodaj zapytania
                    for qa in item.get('questions', []):
                        query_id = f"tatqa_{item['id']}_{qa['id']}"
                        queries.append({
                            "query_id": query_id,
                            "query": qa['question'],
                            "ground_truth": qa.get('answer', []),
                            "expected_answer": qa.get('answer', ''),
                            "domain": "TAT-QA",
                            "metadata": {
                                "original_doc_id": item['id'],
                                "original_qa_id": qa['id']
                            }
                        })
        
        return {
            "documents": documents,
            "queries": queries
        }
    
    def parse_techqa_corpus(self, data_dir: Path) -> Dict[str, Any]:
        """Parsuje korpus TechQA"""
        logger.info("Parsowanie korpusu TechQA...")
        
        # Ścieżki do plików TechQA
        train_file = data_dir / "TechQA-main" / "dataset" / "train.json"
        dev_file = data_dir / "TechQA-main" / "dataset" / "dev.json"
        test_file = data_dir / "TechQA-main" / "dataset" / "test.json"
        
        documents = []
        queries = []
        
        # Parsuj pliki JSON
        for file_path in [train_file, dev_file, test_file]:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    # Dodaj dokument
                    doc_id = f"techqa_{item['id']}"
                    documents.append({
                        "id": doc_id,
                        "title": f"Technical Document {item['id']}",
                        "content": self._format_techqa_content(item),
                        "domain": "TechQA",
                        "metadata": {
                            "original_id": item['id'],
                            "split": file_path.stem
                        }
                    })
                    
                    # Dodaj zapytania
                    for qa in item.get('questions', []):
                        query_id = f"techqa_{item['id']}_{qa['id']}"
                        queries.append({
                            "query_id": query_id,
                            "query": qa['question'],
                            "ground_truth": qa.get('answer', []),
                            "expected_answer": qa.get('answer', ''),
                            "domain": "TechQA",
                            "metadata": {
                                "original_doc_id": item['id'],
                                "original_qa_id": qa['id']
                            }
                        })
        
        return {
            "documents": documents,
            "queries": queries
        }
    
    def parse_cuad_corpus(self, data_dir: Path) -> Dict[str, Any]:
        """Parsuje korpus CUAD"""
        logger.info("Parsowanie korpusu CUAD...")
        
        # Ścieżki do plików CUAD
        train_file = data_dir / "cuad-main" / "dataset" / "train.json"
        dev_file = data_dir / "cuad-main" / "dataset" / "dev.json"
        test_file = data_dir / "cuad-main" / "dataset" / "test.json"
        
        documents = []
        queries = []
        
        # Parsuj pliki JSON
        for file_path in [train_file, dev_file, test_file]:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    # Dodaj dokument
                    doc_id = f"cuad_{item['id']}"
                    documents.append({
                        "id": doc_id,
                        "title": f"Legal Contract {item['id']}",
                        "content": self._format_cuad_content(item),
                        "domain": "CUAD",
                        "metadata": {
                            "original_id": item['id'],
                            "split": file_path.stem
                        }
                    })
                    
                    # Dodaj zapytania
                    for qa in item.get('questions', []):
                        query_id = f"cuad_{item['id']}_{qa['id']}"
                        queries.append({
                            "query_id": query_id,
                            "query": qa['question'],
                            "ground_truth": qa.get('answer', []),
                            "expected_answer": qa.get('answer', ''),
                            "domain": "CUAD",
                            "metadata": {
                                "original_doc_id": item['id'],
                                "original_qa_id": qa['id']
                            }
                        })
        
        return {
            "documents": documents,
            "queries": queries
        }
    
    def parse_emanual_corpus(self, data_dir: Path) -> Dict[str, Any]:
        """Parsuje korpus EManual"""
        logger.info("Parsowanie korpusu EManual...")
        
        # Ścieżki do plików EManual
        train_file = data_dir / "EManual-main" / "dataset" / "train.json"
        dev_file = data_dir / "EManual-main" / "dataset" / "dev.json"
        test_file = data_dir / "EManual-main" / "dataset" / "test.json"
        
        documents = []
        queries = []
        
        # Parsuj pliki JSON
        for file_path in [train_file, dev_file, test_file]:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    # Dodaj dokument
                    doc_id = f"emanual_{item['id']}"
                    documents.append({
                        "id": doc_id,
                        "title": f"Equipment Manual {item['id']}",
                        "content": self._format_emanual_content(item),
                        "domain": "EManual",
                        "metadata": {
                            "original_id": item['id'],
                            "split": file_path.stem
                        }
                    })
                    
                    # Dodaj zapytania
                    for qa in item.get('questions', []):
                        query_id = f"emanual_{item['id']}_{qa['id']}"
                        queries.append({
                            "query_id": query_id,
                            "query": qa['question'],
                            "ground_truth": qa.get('answer', []),
                            "expected_answer": qa.get('answer', ''),
                            "domain": "EManual",
                            "metadata": {
                                "original_doc_id": item['id'],
                                "original_qa_id": qa['id']
                            }
                        })
        
        return {
            "documents": documents,
            "queries": queries
        }
    
    def _format_finqa_content(self, item: Dict[str, Any]) -> str:
        """Formatuje treść dokumentu FinQA"""
        content_parts = []
        
        # Dodaj tabelę
        if 'table' in item:
            content_parts.append("Table:")
            for row in item['table']:
                content_parts.append(" | ".join(str(cell) for cell in row))
        
        # Dodaj tekst
        if 'text' in item:
            content_parts.append("\nText:")
            content_parts.append(item['text'])
        
        return "\n".join(content_parts)
    
    def _format_tatqa_content(self, item: Dict[str, Any]) -> str:
        """Formatuje treść dokumentu TAT-QA"""
        content_parts = []
        
        # Dodaj tabelę
        if 'table' in item:
            content_parts.append("Table:")
            for row in item['table']:
                content_parts.append(" | ".join(str(cell) for cell in row))
        
        # Dodaj tekst
        if 'text' in item:
            content_parts.append("\nText:")
            content_parts.append(item['text'])
        
        return "\n".join(content_parts)
    
    def _format_techqa_content(self, item: Dict[str, Any]) -> str:
        """Formatuje treść dokumentu TechQA"""
        content_parts = []
        
        # Dodaj tytuł
        if 'title' in item:
            content_parts.append(f"Title: {item['title']}")
        
        # Dodaj treść
        if 'content' in item:
            content_parts.append(f"Content: {item['content']}")
        
        return "\n".join(content_parts)
    
    def _format_cuad_content(self, item: Dict[str, Any]) -> str:
        """Formatuje treść dokumentu CUAD"""
        content_parts = []
        
        # Dodaj tytuł
        if 'title' in item:
            content_parts.append(f"Title: {item['title']}")
        
        # Dodaj treść
        if 'content' in item:
            content_parts.append(f"Content: {item['content']}")
        
        return "\n".join(content_parts)
    
    def _format_emanual_content(self, item: Dict[str, Any]) -> str:
        """Formatuje treść dokumentu EManual"""
        content_parts = []
        
        # Dodaj tytuł
        if 'title' in item:
            content_parts.append(f"Title: {item['title']}")
        
        # Dodaj treść
        if 'content' in item:
            content_parts.append(f"Content: {item['content']}")
        
        return "\n".join(content_parts)
    
    def import_corpus(self, domain: str) -> Dict[str, Any]:
        """
        Importuje korpus do systemu
        
        Args:
            domain: Nazwa domeny
            
        Returns:
            Statystyki importu
        """
        logger.info(f"Rozpoczynanie importu korpusu {domain}")
        
        try:
            # Pobierz korpus
            if not self.download_corpus(domain):
                return {"status": "error", "error": "Nie udało się pobrać korpusu"}
            
            # Parsuj korpus
            data_dir = self.data_dir / domain
            if domain == "FinQA":
                corpus_data = self.parse_finqa_corpus(data_dir)
            elif domain == "TAT-QA":
                corpus_data = self.parse_tatqa_corpus(data_dir)
            elif domain == "TechQA":
                corpus_data = self.parse_techqa_corpus(data_dir)
            elif domain == "CUAD":
                corpus_data = self.parse_cuad_corpus(data_dir)
            elif domain == "EManual":
                corpus_data = self.parse_emanual_corpus(data_dir)
            else:
                return {"status": "error", "error": f"Nieobsługiwana domena: {domain}"}
            
            # Importuj dokumenty
            imported_docs = self._import_documents(corpus_data["documents"])
            
            # Importuj zapytania
            imported_queries = self._import_queries(corpus_data["queries"])
            
            # Indeksuj dokumenty
            indexing_stats = self._index_documents(imported_docs)
            
            stats = {
                "domain": domain,
                "documents_imported": len(imported_docs),
                "queries_imported": len(imported_queries),
                "fragments_created": indexing_stats["fragments"],
                "facts_extracted": indexing_stats["facts"],
                "entities_created": indexing_stats["entities"],
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Import korpusu {domain} zakończony: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Błąd importu korpusu {domain}: {e}")
            return {
                "domain": domain,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _import_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Importuje dokumenty do systemu"""
        db = next(get_db())
        article_service = ArticleService(db)
        
        imported_docs = []
        
        for doc in documents:
            try:
                # Utwórz artykuł
                article = article_service.create_article(
                    title=doc["title"],
                    content=doc["content"],
                    summary=f"RAGBench document from {doc['domain']}",
                    tags=[doc["domain"]],
                    created_by_id=1  # System user
                )
                
                # Przetwórz artykuł
                processing_result = article_service.process_article(article.id)
                
                # Zapisz mapowanie ID
                self.ref_map[doc["id"]] = {
                    "article_id": article.id,
                    "fragment_ids": [f.id for f in article.fragments]
                }
                
                imported_docs.append({
                    "id": article.id,
                    "ragbench_id": doc["id"],
                    "title": article.title,
                    "status": processing_result["status"],
                    "fragments": processing_result.get("fragments_created", 0),
                    "facts": processing_result.get("facts_created", 0)
                })
                
            except Exception as e:
                logger.error(f"Błąd importu dokumentu {doc['id']}: {e}")
                continue
        
        return imported_docs
    
    def _import_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Importuje zapytania z RAGBench"""
        # Zapisz zapytania do pliku JSON
        queries_file = self.data_dir / "queries.json"
        
        if queries_file.exists():
            with open(queries_file, 'r', encoding='utf-8') as f:
                existing_queries = json.load(f)
        else:
            existing_queries = []
        
        existing_queries.extend(queries)
        
        with open(queries_file, 'w', encoding='utf-8') as f:
            json.dump(existing_queries, f, indent=2, ensure_ascii=False)
        
        return queries
    
    def _index_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Indeksuje zaimportowane dokumenty"""
        # Statystyki indeksacji są już dostępne z process_article
        total_fragments = sum(doc.get("fragments", 0) for doc in documents)
        total_facts = sum(doc.get("facts", 0) for doc in documents)
        
        return {
            "fragments": total_fragments,
            "facts": total_facts,
            "entities": 0  # Będzie obliczone przez GraphUpdateService
        }
    
    def save_ref_map(self):
        """Zapisuje mapowanie ID do pliku"""
        ref_map_file = self.data_dir / "ref_map.json"
        
        with open(ref_map_file, 'w', encoding='utf-8') as f:
            json.dump(self.ref_map, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Mapowanie ID zapisane do {ref_map_file}")


def main():
    """Główna funkcja"""
    if len(sys.argv) < 2:
        print("Użycie: python ingest_ragbench.py <domain>")
        print("Dostępne domeny: FinQA, TAT-QA, TechQA, CUAD, EManual")
        sys.exit(1)
    
    domain = sys.argv[1]
    
    importer = RAGBenchImporter()
    result = importer.import_corpus(domain)
    
    if result["status"] == "success":
        print(f"✅ Import korpusu {domain} zakończony pomyślnie")
        print(f"📊 Dokumenty: {result['documents_imported']}")
        print(f"📊 Zapytania: {result['queries_imported']}")
        print(f"📊 Fragmenty: {result['fragments_created']}")
        print(f"📊 Fakty: {result['facts_extracted']}")
        
        # Zapisz mapowanie ID
        importer.save_ref_map()
    else:
        print(f"❌ Błąd importu korpusu {domain}: {result.get('error', 'Nieznany błąd')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
