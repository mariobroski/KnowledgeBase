"""
Testy integracyjne RAGBench + TRACe metryki
"""

import pytest
from unittest.mock import Mock, patch
from app.services.ragbench_service import RAGBenchService, RAGBenchQuery, RAGBenchResult
from app.services.trace_service import TRACEService


class TestRAGBenchTRACEIntegration:
    """Testy integracji RAGBench z metrykami TRACe"""
    
    def setup_method(self):
        """Przygotowanie testów"""
        self.ragbench_service = RAGBenchService()
        self.trace_service = TRACEService()
    
    def test_ragbench_query_structure(self):
        """Test struktury zapytań RAGBench"""
        query = RAGBenchQuery(
            query_id="test_1",
            query="What is the capital of Poland?",
            domain="FinQA",
            ground_truth=["Warsaw is the capital of Poland"],
            context=[],
            expected_answer="Warsaw",
            metadata={"difficulty": "easy"}
        )
        
        assert query.query_id == "test_1"
        assert query.query == "What is the capital of Poland?"
        assert query.domain == "FinQA"
        assert query.ground_truth == ["Warsaw is the capital of Poland"]
        assert query.expected_answer == "Warsaw"
        assert query.metadata["difficulty"] == "easy"
    
    def test_ragbench_result_structure(self):
        """Test struktury wyników RAGBench"""
        result = RAGBenchResult(
            query_id="test_1",
            strategy="text",
            response="Warsaw is the capital of Poland",
            context_used=["Warsaw is the capital of Poland since 1596"],
            metrics={
                "relevance": 0.9,
                "utilization": 0.8,
                "adherence": 0.85,
                "completeness": 0.9
            },
            latency=1500.0,
            tokens=150,
            cost=0.003,
            timestamp="2024-01-15T10:30:00Z"
        )
        
        assert result.query_id == "test_1"
        assert result.strategy == "text"
        assert result.response == "Warsaw is the capital of Poland"
        assert len(result.context_used) == 1
        assert result.metrics["relevance"] == 0.9
        assert result.latency == 1500.0
        assert result.tokens == 150
        assert result.cost == 0.003
    
    def test_trace_metrics_integration(self):
        """Test integracji metryk TRACe z RAGBench"""
        query = "What is the capital of Poland?"
        response = "Warsaw is the capital of Poland"
        context = {
            "fragments": [
                {"content": "Warsaw is the capital of Poland since 1596"},
                {"content": "Poland is a country in Central Europe"}
            ]
        }
        ground_truth = ["Warsaw is the capital of Poland"]
        
        # Oblicz metryki TRACe
        metrics = self.trace_service.calculate_metrics(query, response, context, ground_truth)
        
        # Sprawdź czy wszystkie metryki są obecne
        assert "relevance" in metrics
        assert "utilization" in metrics
        assert "adherence" in metrics
        assert "completeness" in metrics
        
        # Sprawdź czy wartości są w odpowiednim zakresie
        for metric, value in metrics.items():
            assert 0.0 <= value <= 1.0
    
    def test_ragbench_evaluation_workflow(self):
        """Test workflow ewaluacji RAGBench"""
        # Przygotuj zapytania testowe
        queries = [
            RAGBenchQuery(
                query_id="test_1",
                query="What is the capital of Poland?",
                domain="FinQA",
                ground_truth=["Warsaw is the capital of Poland"],
                context=[],
                expected_answer="Warsaw",
                metadata={}
            ),
            RAGBenchQuery(
                query_id="test_2",
                query="What is the population of Warsaw?",
                domain="FinQA",
                ground_truth=["Warsaw has about 1.8 million inhabitants"],
                context=[],
                expected_answer="1.8 million",
                metadata={}
            )
        ]
        
        # Mock SearchService
        with patch('app.services.ragbench_service.SearchService') as mock_search_service:
            mock_service = Mock()
            mock_search_service.return_value = mock_service
            
            # Mock wyników wyszukiwania
            mock_service.search.side_effect = [
                {
                    "response": "Warsaw is the capital of Poland",
                    "context": {
                        "fragments": [{"content": "Warsaw is the capital of Poland since 1596"}]
                    },
                    "tokens_used": 150
                },
                {
                    "response": "Warsaw has about 1.8 million inhabitants",
                    "context": {
                        "fragments": [{"content": "Warsaw has about 1.8 million inhabitants"}]
                    },
                    "tokens_used": 200
                }
            ]
            
            # Wykonaj ewaluację
            results = self.ragbench_service.evaluate_strategy("FinQA", "text", queries)
            
            assert len(results) == 2
            assert results[0].query_id == "test_1"
            assert results[1].query_id == "test_2"
            assert results[0].strategy == "text"
            assert results[1].strategy == "text"
    
    def test_ragbench_comparison_report(self):
        """Test generowania raportu porównawczego"""
        # Przygotuj wyniki testów
        results = {
            "FinQA": {
                "text": [
                    RAGBenchResult(
                        query_id="test_1",
                        strategy="text",
                        response="Warsaw is the capital of Poland",
                        context_used=["Warsaw is the capital of Poland since 1596"],
                        metrics={"relevance": 0.9, "utilization": 0.8, "adherence": 0.85, "completeness": 0.9},
                        latency=1500.0,
                        tokens=150,
                        cost=0.003,
                        timestamp="2024-01-15T10:30:00Z"
                    )
                ],
                "facts": [
                    RAGBenchResult(
                        query_id="test_1",
                        strategy="facts",
                        response="Warsaw is the capital of Poland",
                        context_used=["Warsaw is the capital of Poland since 1596"],
                        metrics={"relevance": 0.95, "utilization": 0.85, "adherence": 0.9, "completeness": 0.95},
                        latency=1800.0,
                        tokens=120,
                        cost=0.002,
                        timestamp="2024-01-15T10:30:00Z"
                    )
                ],
                "graph": [
                    RAGBenchResult(
                        query_id="test_1",
                        strategy="graph",
                        response="Warsaw is the capital of Poland",
                        context_used=["Warsaw is the capital of Poland since 1596"],
                        metrics={"relevance": 0.98, "utilization": 0.9, "adherence": 0.95, "completeness": 0.98},
                        latency=2200.0,
                        tokens=100,
                        cost=0.001,
                        timestamp="2024-01-15T10:30:00Z"
                    )
                ]
            }
        }
        
        # Generuj raport
        report = self.ragbench_service.generate_comparison_report(results)
        
        # Sprawdź strukturę raportu
        assert "domains" in report
        assert "FinQA" in report["domains"]
        assert "text" in report["domains"]["FinQA"]
        assert "facts" in report["domains"]["FinQA"]
        assert "graph" in report["domains"]["FinQA"]
        
        # Sprawdź metryki dla każdej strategii
        finqa_stats = report["domains"]["FinQA"]
        
        for strategy in ["text", "facts", "graph"]:
            assert "adherence" in finqa_stats[strategy]
            assert "completeness" in finqa_stats[strategy]
            assert "utilization" in finqa_stats[strategy]
            assert "relevance" in finqa_stats[strategy]
            assert "p95_latency" in finqa_stats[strategy]
            assert "avg_tokens" in finqa_stats[strategy]
            assert "avg_cost" in finqa_stats[strategy]
            assert "total_queries" in finqa_stats[strategy]
    
    def test_ragbench_metrics_calculation(self):
        """Test obliczania metryk RAGBench"""
        # Przygotuj wyniki testów
        results = [
            RAGBenchResult(
                query_id="test_1",
                strategy="text",
                response="Warsaw is the capital of Poland",
                context_used=["Warsaw is the capital of Poland since 1596"],
                metrics={"relevance": 0.9, "utilization": 0.8, "adherence": 0.85, "completeness": 0.9},
                latency=1500.0,
                tokens=150,
                cost=0.003,
                timestamp="2024-01-15T10:30:00Z"
            ),
            RAGBenchResult(
                query_id="test_2",
                strategy="text",
                response="Warsaw has about 1.8 million inhabitants",
                context_used=["Warsaw has about 1.8 million inhabitants"],
                metrics={"relevance": 0.85, "utilization": 0.75, "adherence": 0.8, "completeness": 0.85},
                latency=1800.0,
                tokens=200,
                cost=0.004,
                timestamp="2024-01-15T10:30:00Z"
            )
        ]
        
        # Oblicz średnie metryki
        avg_metrics = self.ragbench_service._calculate_average_metrics(results)
        
        assert "adherence" in avg_metrics
        assert "completeness" in avg_metrics
        assert "utilization" in avg_metrics
        assert "relevance" in avg_metrics
        assert "tokens" in avg_metrics
        assert "cost" in avg_metrics
        
        # Sprawdź czy średnie są logiczne
        assert 0.0 <= avg_metrics["adherence"] <= 1.0
        assert 0.0 <= avg_metrics["completeness"] <= 1.0
        assert 0.0 <= avg_metrics["utilization"] <= 1.0
        assert 0.0 <= avg_metrics["relevance"] <= 1.0
        assert avg_metrics["tokens"] > 0
        assert avg_metrics["cost"] > 0
    
    def test_ragbench_p95_latency_calculation(self):
        """Test obliczania 95 percentyla latencji"""
        # Przygotuj wyniki z różnymi latencjami
        results = [
            RAGBenchResult(
                query_id="test_1",
                strategy="text",
                response="Response 1",
                context_used=[],
                metrics={},
                latency=1000.0,
                tokens=100,
                cost=0.002,
                timestamp="2024-01-15T10:30:00Z"
            ),
            RAGBenchResult(
                query_id="test_2",
                strategy="text",
                response="Response 2",
                context_used=[],
                metrics={},
                latency=2000.0,
                tokens=200,
                cost=0.004,
                timestamp="2024-01-15T10:30:00Z"
            ),
            RAGBenchResult(
                query_id="test_3",
                strategy="text",
                response="Response 3",
                context_used=[],
                metrics={},
                latency=3000.0,
                tokens=300,
                cost=0.006,
                timestamp="2024-01-15T10:30:00Z"
            )
        ]
        
        # Oblicz P95 latencji
        p95_latency = self.ragbench_service._calculate_p95_latency(results)
        
        assert p95_latency > 0
        assert p95_latency >= 2000.0  # P95 powinien być >= 2000ms
    
    def test_ragbench_recommendations_generation(self):
        """Test generowania rekomendacji"""
        # Przygotuj statystyki domen
        domains_stats = {
            "FinQA": {
                "text": {
                    "adherence": 0.75,
                    "avg_tokens": 500,
                    "p95_latency": 2000
                },
                "graph": {
                    "adherence": 0.88,
                    "avg_tokens": 280,
                    "p95_latency": 2200
                }
            }
        }
        
        # Generuj rekomendacje
        recommendations = self.ragbench_service._generate_recommendations(domains_stats)
        
        assert len(recommendations) > 0
        
        # Sprawdź czy rekomendacje zawierają oczekiwane informacje
        recommendation_text = " ".join(recommendations)
        assert "GraphRAG" in recommendation_text
        assert "adherence" in recommendation_text.lower()
        assert "tokens" in recommendation_text.lower()
    
    def test_ragbench_cost_calculation(self):
        """Test obliczania kosztów"""
        # Test kosztów dla różnych strategii
        text_cost = self.ragbench_service._calculate_cost(1000, "text")
        facts_cost = self.ragbench_service._calculate_cost(1000, "facts")
        graph_cost = self.ragbench_service._calculate_cost(1000, "graph")
        
        assert text_cost > 0
        assert facts_cost > 0
        assert graph_cost > 0
        
        # Sprawdź czy koszty są w odpowiedniej relacji
        assert facts_cost < text_cost  # Facts powinien być tańszy
        assert graph_cost < text_cost  # Graph powinien być tańszy
        assert graph_cost < facts_cost  # Graph powinien być najtańszy
    
    def test_ragbench_error_handling(self):
        """Test obsługi błędów w RAGBench"""
        # Test z nieprawidłowymi danymi
        with patch('app.services.ragbench_service.SearchService') as mock_search_service:
            mock_service = Mock()
            mock_search_service.return_value = mock_service
            mock_service.search.side_effect = Exception("Search error")
            
            queries = [
                RAGBenchQuery(
                    query_id="test_1",
                    query="Test query",
                    domain="FinQA",
                    ground_truth=["Test answer"],
                    context=[],
                    expected_answer="Test answer",
                    metadata={}
                )
            ]
            
            # Wykonaj ewaluację (powinna obsłużyć błąd)
            results = self.ragbench_service.evaluate_strategy("FinQA", "text", queries)
            
            # Sprawdź czy błąd został obsłużony
            assert len(results) == 0  # Brak wyników z powodu błędu


if __name__ == "__main__":
    pytest.main([__file__])
