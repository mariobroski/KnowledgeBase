"""
Testy metryk TRACe dla systemu KnowledgeBase
"""

import pytest
from unittest.mock import Mock, patch
from app.services.trace_service import TRACEService


class TestTRACEMetrics:
    """Testy metryk TRACe"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.trace_service = TRACEService()
    
    def test_relevance_calculation(self):
        """Test obliczania relevance"""
        query = "What is the capital of Poland?"
        response = "Warsaw is the capital of Poland"
        
        relevance = self.trace_service._calculate_relevance(query, response)
        
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.5  # Powinno być wysokie podobieństwo
    
    def test_relevance_low_similarity(self):
        """Test relevance dla niskiego podobieństwa"""
        query = "What is the capital of Poland?"
        response = "The weather is nice today"
        
        relevance = self.trace_service._calculate_relevance(query, response)
        
        assert 0.0 <= relevance <= 1.0
        assert relevance < 0.5  # Powinno być niskie podobieństwo
    
    def test_utilization_calculation(self):
        """Test obliczania utilization"""
        response = "Warsaw is the capital of Poland"
        context = {
            "fragments": [
                {"content": "Warsaw is the capital of Poland since 1596"},
                {"content": "Poland is a country in Central Europe"}
            ]
        }
        
        utilization = self.trace_service._calculate_utilization(response, context)
        
        assert 0.0 <= utilization <= 1.0
        assert utilization > 0.5  # Powinno być wysokie wykorzystanie kontekstu
    
    def test_utilization_empty_context(self):
        """Test utilization dla pustego kontekstu"""
        response = "Warsaw is the capital of Poland"
        context = {"fragments": []}
        
        utilization = self.trace_service._calculate_utilization(response, context)
        
        assert utilization == 0.0
    
    def test_adherence_calculation(self):
        """Test obliczania adherence"""
        response = "Warsaw is the capital of Poland"
        context = {
            "fragments": [
                {"content": "Warsaw is the capital of Poland since 1596"},
                {"content": "Poland is a country in Central Europe"}
            ]
        }
        
        adherence = self.trace_service._calculate_adherence(response, context)
        
        assert 0.0 <= adherence <= 1.0
        assert adherence > 0.5  # Powinno być wysokie podobieństwo do kontekstu
    
    def test_adherence_hallucination(self):
        """Test adherence dla halucynacji"""
        response = "Warsaw has 10 million inhabitants"
        context = {
            "fragments": [
                {"content": "Warsaw has about 1.8 million inhabitants"},
                {"content": "Poland is a country in Central Europe"}
            ]
        }
        
        adherence = self.trace_service._calculate_adherence(response, context)
        
        assert 0.0 <= adherence <= 1.0
        assert adherence < 0.5  # Powinno być niskie podobieństwo (halucynacja)
    
    def test_completeness_calculation(self):
        """Test obliczania completeness"""
        response = "Warsaw is the capital of Poland"
        ground_truth = ["Warsaw is the capital of Poland", "Poland's capital is Warsaw"]
        
        completeness = self.trace_service._calculate_completeness(response, ground_truth)
        
        assert 0.0 <= completeness <= 1.0
        assert completeness > 0.5  # Powinno być wysokie podobieństwo do ground truth
    
    def test_completeness_missing_info(self):
        """Test completeness dla brakujących informacji"""
        response = "Warsaw is a city"
        ground_truth = ["Warsaw is the capital of Poland"]
        
        completeness = self.trace_service._calculate_completeness(response, ground_truth)
        
        assert 0.0 <= completeness <= 1.0
        assert completeness < 0.5  # Powinno być niskie podobieństwo
    
    def test_complete_metrics_calculation(self):
        """Test obliczania wszystkich metryk TRACe"""
        query = "What is the capital of Poland?"
        response = "Warsaw is the capital of Poland"
        context = {
            "fragments": [
                {"content": "Warsaw is the capital of Poland since 1596"},
                {"content": "Poland is a country in Central Europe"}
            ]
        }
        ground_truth = ["Warsaw is the capital of Poland"]
        
        metrics = self.trace_service.calculate_metrics(query, response, context, ground_truth)
        
        assert "relevance" in metrics
        assert "utilization" in metrics
        assert "adherence" in metrics
        assert "completeness" in metrics
        
        for metric, value in metrics.items():
            assert 0.0 <= value <= 1.0
    
    def test_metrics_edge_cases(self):
        """Test metryk dla przypadków brzegowych"""
        # Puste dane
        metrics = self.trace_service.calculate_metrics("", "", {}, [])
        
        assert metrics["relevance"] == 0.0
        assert metrics["utilization"] == 0.0
        assert metrics["adherence"] == 0.0
        assert metrics["completeness"] == 0.0
        
        # None values
        metrics = self.trace_service.calculate_metrics(None, None, None, None)
        
        assert metrics["relevance"] == 0.0
        assert metrics["utilization"] == 0.0
        assert metrics["adherence"] == 0.0
        assert metrics["completeness"] == 0.0
    
    def test_hallucination_rate_calculation(self):
        """Test obliczania wskaźnika halucynacji"""
        responses = [
            "Warsaw is the capital of Poland",  # Dobra odpowiedź
            "Warsaw has 10 million inhabitants",  # Halucynacja
            "Poland is in Europe"  # Dobra odpowiedź
        ]
        
        contexts = [
            {"fragments": [{"content": "Warsaw is the capital of Poland"}]},
            {"fragments": [{"content": "Warsaw has about 1.8 million inhabitants"}]},
            {"fragments": [{"content": "Poland is a country in Central Europe"}]}
        ]
        
        hallucination_rate = self.trace_service.calculate_hallucination_rate(responses, contexts)
        
        assert 0.0 <= hallucination_rate <= 1.0
        assert hallucination_rate > 0.0  # Powinna być co najmniej jedna halucynacja
    
    def test_average_metrics_calculation(self):
        """Test obliczania średnich metryk"""
        results = [
            {"relevance": 0.8, "utilization": 0.7, "adherence": 0.9, "completeness": 0.8},
            {"relevance": 0.6, "utilization": 0.5, "adherence": 0.7, "completeness": 0.6},
            {"relevance": 0.9, "utilization": 0.8, "adherence": 0.8, "completeness": 0.9}
        ]
        
        averages = self.trace_service.calculate_average_metrics(results)
        
        assert "relevance" in averages
        assert "utilization" in averages
        assert "adherence" in averages
        assert "completeness" in averages
        
        # Sprawdź czy średnie są w odpowiednim zakresie
        assert 0.0 <= averages["relevance"] <= 1.0
        assert 0.0 <= averages["utilization"] <= 1.0
        assert 0.0 <= averages["adherence"] <= 1.0
        assert 0.0 <= averages["completeness"] <= 1.0
        
        # Sprawdź czy średnie są logiczne
        assert averages["relevance"] > 0.5
        assert averages["utilization"] > 0.5
        assert averages["adherence"] > 0.5
        assert averages["completeness"] > 0.5
    
    def test_token_similarity_fallback(self):
        """Test fallback na podobieństwo tokenów"""
        text1 = "Warsaw is the capital of Poland"
        text2 = "Warsaw is the capital of Poland"
        
        similarity = self.trace_service._calculate_token_similarity(text1, text2)
        
        assert similarity == 1.0  # Identyczne teksty
    
    def test_token_similarity_different_texts(self):
        """Test podobieństwa tokenów dla różnych tekstów"""
        text1 = "Warsaw is the capital of Poland"
        text2 = "The weather is nice today"
        
        similarity = self.trace_service._calculate_token_similarity(text1, text2)
        
        assert 0.0 <= similarity <= 1.0
        assert similarity < 0.5  # Powinno być niskie podobieństwo
    
    def test_sentence_splitting(self):
        """Test dzielenia tekstu na zdania"""
        text = "Warsaw is the capital of Poland. It has about 1.8 million inhabitants. The city is located on the Vistula River."
        
        sentences = self.trace_service._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "Warsaw is the capital of Poland" in sentences
        assert "It has about 1.8 million inhabitants" in sentences
        assert "The city is located on the Vistula River" in sentences
    
    def test_sentence_splitting_empty_text(self):
        """Test dzielenia pustego tekstu"""
        sentences = self.trace_service._split_into_sentences("")
        
        assert sentences == []
    
    def test_sentence_splitting_none_text(self):
        """Test dzielenia None tekstu"""
        sentences = self.trace_service._split_into_sentences(None)
        
        assert sentences == []


class TestTRACEMetricsIntegration:
    """Testy integracji metryk TRACe"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.trace_service = TRACEService()
    
    @patch('app.services.trace_service.SentenceTransformer')
    def test_embedding_model_initialization(self, mock_sentence_transformer):
        """Test inicjalizacji modelu embeddingów"""
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Utwórz nowy serwis
        service = TRACEService()
        
        assert service.embedding_model is not None
        mock_sentence_transformer.assert_called_once_with('all-MiniLM-L6-v2')
    
    @patch('app.services.trace_service.SentenceTransformer')
    def test_embedding_model_fallback(self, mock_sentence_transformer):
        """Test fallback gdy model embeddingów nie jest dostępny"""
        mock_sentence_transformer.side_effect = Exception("Model not available")
        
        # Utwórz nowy serwis
        service = TRACEService()
        
        assert service.embedding_model is None
    
    def test_metrics_with_embedding_model(self):
        """Test metryk z modelem embeddingów"""
        # Mock modelu embeddingów
        with patch.object(self.trace_service, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            query = "What is the capital of Poland?"
            response = "Warsaw is the capital of Poland"
            context = {"fragments": [{"content": "Warsaw is the capital of Poland"}]}
            ground_truth = ["Warsaw is the capital of Poland"]
            
            metrics = self.trace_service.calculate_metrics(query, response, context, ground_truth)
            
            assert "relevance" in metrics
            assert "utilization" in metrics
            assert "adherence" in metrics
            assert "completeness" in metrics
    
    def test_metrics_without_embedding_model(self):
        """Test metryk bez modelu embeddingów"""
        # Ustaw model na None
        self.trace_service.embedding_model = None
        
        query = "What is the capital of Poland?"
        response = "Warsaw is the capital of Poland"
        context = {"fragments": [{"content": "Warsaw is the capital of Poland"}]}
        ground_truth = ["Warsaw is the capital of Poland"]
        
        metrics = self.trace_service.calculate_metrics(query, response, context, ground_truth)
        
        assert "relevance" in metrics
        assert "utilization" in metrics
        assert "adherence" in metrics
        assert "completeness" in metrics
        
        # Sprawdź czy metryki są obliczone (fallback na tokeny)
        for metric, value in metrics.items():
            assert 0.0 <= value <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])
