"""
Testy importu RAGBench do systemu KnowledgeBase
"""

import pytest
from unittest.mock import Mock, patch
from app.services.ragbench_service import RAGBenchService, RAGBenchQuery
from app.services.trace_service import TRACEService


class TestRAGBenchImport:
    """Testy importu korpusów RAGBench"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
        self.trace_service = TRACEService()
    
    def test_import_finqa_corpus(self):
        """Test importu korpusu FinQA"""
        result = self.ragbench_service.import_corpus("FinQA")
        
        assert result["domain"] == "FinQA"
        assert result["status"] == "success"
        assert result["documents_imported"] > 0
        assert result["queries_imported"] > 0
        assert "timestamp" in result
    
    def test_import_tatqa_corpus(self):
        """Test importu korpusu TAT-QA"""
        result = self.ragbench_service.import_corpus("TAT-QA")
        
        assert result["domain"] == "TAT-QA"
        assert result["status"] == "success"
        assert result["documents_imported"] > 0
        assert result["queries_imported"] > 0
    
    def test_import_techqa_corpus(self):
        """Test importu korpusu TechQA"""
        result = self.ragbench_service.import_corpus("TechQA")
        
        assert result["domain"] == "TechQA"
        assert result["status"] == "success"
        assert result["documents_imported"] > 0
        assert result["queries_imported"] > 0
    
    def test_import_unsupported_domain(self):
        """Test importu nieobsługiwanej domeny"""
        with pytest.raises(ValueError, match="Nieobsługiwana domena"):
            self.ragbench_service.import_corpus("UnknownDomain")
    
    def test_corpus_data_structure(self):
        """Test struktury danych korpusu"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("FinQA")
        
        assert "documents" in corpus_data
        assert "queries" in corpus_data
        assert len(corpus_data["documents"]) > 0
        assert len(corpus_data["queries"]) > 0
        
        # Sprawdź strukturę dokumentu
        doc = corpus_data["documents"][0]
        assert "id" in doc
        assert "title" in doc
        assert "content" in doc
        assert "domain" in doc
        
        # Sprawdź strukturę zapytania
        query = corpus_data["queries"][0]
        assert "query_id" in query
        assert "query" in query
        assert "ground_truth" in query
        assert "expected_answer" in query


class TestRAGBenchQueries:
    """Testy zapytań RAGBench"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
    
    def test_finqa_queries(self):
        """Test zapytań FinQA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("FinQA")
        queries = corpus_data["queries"]
        
        assert len(queries) > 0
        
        for query in queries:
            assert query["domain"] == "FinQA"
            assert query["query"] is not None
            assert query["ground_truth"] is not None
            assert query["expected_answer"] is not None
    
    def test_tatqa_queries(self):
        """Test zapytań TAT-QA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("TAT-QA")
        queries = corpus_data["queries"]
        
        assert len(queries) > 0
        
        for query in queries:
            assert query["domain"] == "TAT-QA"
            assert query["query"] is not None
            assert query["ground_truth"] is not None
            assert query["expected_answer"] is not None
    
    def test_techqa_queries(self):
        """Test zapytań TechQA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("TechQA")
        queries = corpus_data["queries"]
        
        assert len(queries) > 0
        
        for query in queries:
            assert query["domain"] == "TechQA"
            assert query["query"] is not None
            assert query["ground_truth"] is not None
            assert query["expected_answer"] is not None


class TestRAGBenchDocuments:
    """Testy dokumentów RAGBench"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
    
    def test_finqa_documents(self):
        """Test dokumentów FinQA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("FinQA")
        documents = corpus_data["documents"]
        
        assert len(documents) > 0
        
        for doc in documents:
            assert doc["domain"] == "FinQA"
            assert doc["title"] is not None
            assert doc["content"] is not None
            assert len(doc["content"]) > 0
    
    def test_tatqa_documents(self):
        """Test dokumentów TAT-QA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("TAT-QA")
        documents = corpus_data["documents"]
        
        assert len(documents) > 0
        
        for doc in documents:
            assert doc["domain"] == "TAT-QA"
            assert doc["title"] is not None
            assert doc["content"] is not None
            assert len(doc["content"]) > 0
    
    def test_techqa_documents(self):
        """Test dokumentów TechQA"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("TechQA")
        documents = corpus_data["documents"]
        
        assert len(documents) > 0
        
        for doc in documents:
            assert doc["domain"] == "TechQA"
            assert doc["title"] is not None
            assert doc["content"] is not None
            assert len(doc["content"]) > 0


class TestRAGBenchIntegration:
    """Testy integracji RAGBench z systemem"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
    
    @patch('app.services.ragbench_service.get_db')
    def test_document_import_integration(self, mock_get_db):
        """Test integracji importu dokumentów"""
        # Mock bazy danych
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock ArticleService
        with patch('app.services.ragbench_service.ArticleService') as mock_article_service:
            mock_service = Mock()
            mock_article_service.return_value = mock_service
            
            # Mock tworzenia artykułu
            mock_article = Mock()
            mock_article.id = 1
            mock_article.title = "Test Article"
            mock_service.create_article.return_value = mock_article
            
            # Mock przetwarzania artykułu
            mock_service.process_article.return_value = {
                "status": "indexed",
                "fragments_created": 5,
                "facts_created": 3
            }
            
            # Test importu
            result = self.ragbench_service.import_corpus("FinQA")
            
            assert result["status"] == "success"
            assert result["documents_imported"] > 0
            assert result["fragments_created"] > 0
            assert result["facts_created"] > 0
    
    def test_query_import_structure(self):
        """Test struktury importu zapytań"""
        corpus_data = self.ragbench_service._fetch_ragbench_corpus("FinQA")
        queries = corpus_data["queries"]
        
        # Test importu zapytań
        imported_queries = self.ragbench_service._import_queries(queries)
        
        assert len(imported_queries) == len(queries)
        
        for query in imported_queries:
            assert isinstance(query, RAGBenchQuery)
            assert query.query_id is not None
            assert query.query is not None
            assert query.domain is not None
            assert query.ground_truth is not None
            assert query.expected_answer is not None


class TestRAGBenchErrorHandling:
    """Testy obsługi błędów RAGBench"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
    
    def test_import_error_handling(self):
        """Test obsługi błędów importu"""
        # Test z nieprawidłową domeną
        with pytest.raises(ValueError):
            self.ragbench_service.import_corpus("InvalidDomain")
    
    def test_corpus_data_validation(self):
        """Test walidacji danych korpusu"""
        # Test z pustymi danymi
        empty_corpus = {"documents": [], "queries": []}
        
        # Mock _fetch_ragbench_corpus
        with patch.object(self.ragbench_service, '_fetch_ragbench_corpus', return_value=empty_corpus):
            result = self.ragbench_service.import_corpus("FinQA")
            
            assert result["status"] == "success"
            assert result["documents_imported"] == 0
            assert result["queries_imported"] == 0
    
    def test_import_partial_failure(self):
        """Test częściowego niepowodzenia importu"""
        # Mock częściowego niepowodzenia
        with patch.object(self.ragbench_service, '_import_documents') as mock_import:
            mock_import.side_effect = Exception("Import error")
            
            result = self.ragbench_service.import_corpus("FinQA")
            
            assert result["status"] == "error"
            assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
