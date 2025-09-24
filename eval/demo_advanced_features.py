#!/usr/bin/env python3
"""
Demonstracja zaawansowanych funkcjonalności systemu ewaluacji
- Zaawansowane metryki
- Porównanie z literaturą
- Analiza trendów
- Wizualizacje
"""

import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from advanced_metrics import AdvancedEvaluator
from literature_comparison import LiteratureComparator
from trend_analysis import TrendAnalyzer

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedFeaturesDemo:
    """Demonstracja zaawansowanych funkcjonalności"""
    
    def __init__(self):
        self.advanced_evaluator = AdvancedEvaluator()
        self.literature_comparator = LiteratureComparator()
        self.trend_analyzer = TrendAnalyzer()
        
        # Przykładowe dane
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self) -> dict:
        """Generuje przykładowe dane do demonstracji"""
        return {
            "queries": [
                {
                    "query": "What was Company XYZ's revenue in Q3 2023?",
                    "response": "Company XYZ reported revenue of $1.2M in Q3 2023, representing a 15% increase from Q2.",
                    "context": {
                        "fragments": [
                            {"content": "Company XYZ reported revenue of $1.2M in Q3 2023, representing a 15% increase from Q2."},
                            {"content": "The company's net profit was $200K, up 25% from previous quarter."}
                        ]
                    },
                    "ground_truth": ["Company XYZ reported revenue of $1.2M in Q3 2023"]
                },
                {
                    "query": "What is the current ratio for Company ABC?",
                    "response": "The current ratio for Company ABC is 2.0, indicating strong liquidity position.",
                    "context": {
                        "fragments": [
                            {"content": "The company's total assets increased from $500M to $600M in 2023."},
                            {"content": "Current ratio improved from 1.5 to 2.0, indicating better liquidity position."}
                        ]
                    },
                    "ground_truth": ["Current ratio improved from 1.5 to 2.0"]
                }
            ]
        }
    
    def demo_advanced_metrics(self):
        """Demonstracja zaawansowanych metryk"""
        logger.info("🎯 Demonstracja zaawansowanych metryk")
        
        print("\n" + "="*60)
        print("📊 ZAAWANSOWANE METRYKI EWALUACJI")
        print("="*60)
        
        for i, query_data in enumerate(self.sample_data["queries"], 1):
            print(f"\n📋 Zapytanie {i}: {query_data['query']}")
            print(f"💬 Odpowiedź: {query_data['response']}")
            
            # Oblicz zaawansowane metryki
            advanced_metrics = self.advanced_evaluator.calculate_advanced_metrics(
                query=query_data["query"],
                response=query_data["response"],
                context=query_data["context"],
                ground_truth=query_data["ground_truth"]
            )
            
            # Wyświetl metryki
            print(f"\n📈 Metryki zaawansowane:")
            print(f"  🎯 Hallucination Score: {advanced_metrics.hallucination_score:.3f}")
            print(f"  ✅ Factual Accuracy: {advanced_metrics.factual_accuracy:.3f}")
            print(f"  🔗 Context Utilization: {advanced_metrics.context_utilization:.3f}")
            print(f"  ⭐ Response Quality: {advanced_metrics.response_quality:.3f}")
            print(f"  🔄 Coherence Score: {advanced_metrics.coherence_score:.3f}")
            print(f"  💬 Fluency Score: {advanced_metrics.fluency_score:.3f}")
            print(f"  🎯 Specificity Score: {advanced_metrics.specificity_score:.3f}")
            print(f"  📝 Completeness Score: {advanced_metrics.completeness_score:.3f}")
            
            # Generuj raport jakości
            quality_report = self.advanced_evaluator.generate_quality_report(advanced_metrics)
            print(f"\n📊 Raport jakości:")
            print(f"  🏆 Poziom jakości: {quality_report['quality_level']}")
            print(f"  📈 Ogólny wynik: {quality_report['overall_score']:.3f}")
            print(f"  💡 Rekomendacje: {', '.join(quality_report['recommendations'])}")
    
    def demo_literature_comparison(self):
        """Demonstracja porównania z literaturą"""
        logger.info("📚 Demonstracja porównania z literaturą")
        
        print("\n" + "="*60)
        print("📚 PORÓWNANIE Z LITERATURĄ NAUKOWĄ")
        print("="*60)
        
        # Przykładowe wyniki naszego systemu
        our_results = {
            "TextRAG": {
                "relevance": 0.82,
                "utilization": 0.75,
                "adherence": 0.78,
                "completeness": 0.80
            },
            "FactRAG": {
                "relevance": 0.85,
                "utilization": 0.80,
                "adherence": 0.82,
                "completeness": 0.83
            },
            "GraphRAG": {
                "relevance": 0.88,
                "utilization": 0.85,
                "adherence": 0.90,
                "completeness": 0.87
            }
        }
        
        # Porównaj z literaturą
        comparison_result = self.literature_comparator.compare_with_literature(
            our_results=our_results,
            benchmark="RAGBench",
            domain="FinQA"
        )
        
        print(f"\n📊 Nasze wyniki vs literatura:")
        for policy, metrics in our_results.items():
            print(f"\n🔧 {policy}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value:.3f}")
        
        print(f"\n📈 Porównanie z literaturą:")
        for policy, deltas in comparison_result.comparison_metrics.items():
            print(f"\n🔧 {policy}:")
            for metric, delta in deltas.items():
                direction = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
                print(f"  {metric}: {delta:+.1f}% {direction}")
        
        print(f"\n💡 Wnioski:")
        for insight in comparison_result.insights:
            print(f"  • {insight}")
        
        print(f"\n🎯 Rekomendacje:")
        for recommendation in comparison_result.recommendations:
            print(f"  • {recommendation}")
    
    def demo_trend_analysis(self):
        """Demonstracja analizy trendów"""
        logger.info("📈 Demonstracja analizy trendów")
        
        print("\n" + "="*60)
        print("📈 ANALIZA TRENDÓW I WZORCÓW")
        print("="*60)
        
        # Generuj przykładowe dane czasowe
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            timestamp = base_time + timedelta(days=i)
            
            # Symuluj trendy
            for metric in ['relevance', 'utilization', 'adherence', 'completeness']:
                # Trend wzrostowy z szumem
                base_value = 0.7 + (i / 30) * 0.2  # Wzrost od 0.7 do 0.9
                noise = np.random.normal(0, 0.05)
                value = max(0, min(1, base_value + noise))
                
                self.trend_analyzer.add_data_point(
                    timestamp=timestamp,
                    metric=metric,
                    value=value,
                    policy="GraphRAG",
                    domain="FinQA"
                )
        
        # Analizuj trendy
        print(f"\n📊 Analiza trendów:")
        for metric in ['relevance', 'utilization', 'adherence', 'completeness']:
            trends = self.trend_analyzer.analyze_trends(metric, policy="GraphRAG", domain="FinQA")
            
            if trends:
                trend = trends[0]
                direction_emoji = {
                    "strong_increase": "📈📈",
                    "moderate_increase": "📈",
                    "stable": "➡️",
                    "moderate_decrease": "📉",
                    "strong_decrease": "📉📉"
                }
                
                print(f"\n🔧 {metric}:")
                print(f"  Kierunek: {direction_emoji.get(trend.trend_direction, '❓')} {trend.trend_direction}")
                print(f"  Siła: {trend.trend_strength:.3f}")
                print(f"  Korelacja: {trend.correlation:.3f}")
                if trend.prediction:
                    print(f"  Predykcja: {trend.prediction:.3f}")
                if trend.confidence:
                    print(f"  Pewność: {trend.confidence:.3f}")
        
        # Wykryj wzorce
        patterns = self.trend_analyzer.detect_patterns()
        
        print(f"\n🔍 Wykryte wzorce:")
        for pattern in patterns:
            print(f"\n📋 {pattern.pattern_type.upper()}:")
            print(f"  Opis: {pattern.description}")
            print(f"  Pewność: {pattern.confidence:.3f}")
            print(f"  Metryki: {', '.join(pattern.affected_metrics)}")
            print(f"  Rekomendacje: {', '.join(pattern.recommendations)}")
        
        # Generuj raport
        trend_report = self.trend_analyzer.generate_trend_report()
        
        print(f"\n📊 Podsumowanie raportu trendów:")
        print(f"  Punkty danych: {trend_report['summary']['total_data_points']}")
        print(f"  Metryki: {trend_report['summary']['metrics_analyzed']}")
        print(f"  Wzorce: {trend_report['summary']['patterns_detected']}")
    
    def demo_visualizations(self):
        """Demonstracja wizualizacji"""
        logger.info("📊 Demonstracja wizualizacji")
        
        print("\n" + "="*60)
        print("📊 WIZUALIZACJE I WYKRESY")
        print("="*60)
        
        # Generuj przykładowe dane
        np.random.seed(42)
        
        # Dane dla różnych polityk
        policies = ['TextRAG', 'FactRAG', 'GraphRAG', 'HybridRAG']
        metrics = ['relevance', 'utilization', 'adherence', 'completeness']
        
        data = []
        for policy in policies:
            for metric in metrics:
                # Symuluj różne wydajności
                if policy == 'GraphRAG':
                    base_value = 0.85
                elif policy == 'FactRAG':
                    base_value = 0.80
                elif policy == 'TextRAG':
                    base_value = 0.75
                else:
                    base_value = 0.78
                
                value = base_value + np.random.normal(0, 0.05)
                value = max(0, min(1, value))
                
                data.append({
                    'policy': policy,
                    'metric': metric,
                    'value': value
                })
        
        df = pd.DataFrame(data)
        
        # Wykres 1: Porównanie polityk
        plt.figure(figsize=(12, 8))
        pivot_df = df.pivot(index='metric', columns='policy', values='value')
        
        ax = pivot_df.plot(kind='bar', figsize=(12, 8))
        plt.title('Porównanie wydajności polityk RAG', fontsize=16, fontweight='bold')
        plt.xlabel('Metryki', fontsize=12)
        plt.ylabel('Wartość', fontsize=12)
        plt.legend(title='Polityka', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('policy_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Wykres porównania polityk zapisany jako 'policy_comparison.png'")
        
        # Wykres 2: Heatmapa korelacji
        plt.figure(figsize=(10, 8))
        correlation_matrix = pivot_df.corr()
        
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, fmt='.3f')
        plt.title('Korelacja między politykami RAG', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Heatmapa korelacji zapisana jako 'correlation_heatmap.png'")
        
        # Wykres 3: Rozkład metryk
        plt.figure(figsize=(12, 8))
        
        for i, metric in enumerate(metrics, 1):
            plt.subplot(2, 2, i)
            metric_data = df[df['metric'] == metric]
            
            for policy in policies:
                policy_data = metric_data[metric_data['policy'] == policy]['value']
                plt.hist(policy_data, alpha=0.7, label=policy, bins=10)
            
            plt.title(f'Rozkład {metric}', fontweight='bold')
            plt.xlabel('Wartość')
            plt.ylabel('Częstość')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        plt.suptitle('Rozkład metryk dla różnych polityk', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('metrics_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Rozkład metryk zapisany jako 'metrics_distribution.png'")
    
    def run_full_demo(self):
        """Uruchamia pełną demonstrację"""
        logger.info("🚀 Rozpoczynanie pełnej demonstracji zaawansowanych funkcjonalności")
        
        print("\n" + "🎯" * 30)
        print("🚀 DEMONSTRACJA ZAAWANSOWANYCH FUNKCJONALNOŚCI")
        print("🎯" * 30)
        
        try:
            # Demonstracja zaawansowanych metryk
            self.demo_advanced_metrics()
            
            # Demonstracja porównania z literaturą
            self.demo_literature_comparison()
            
            # Demonstracja analizy trendów
            self.demo_trend_analysis()
            
            # Demonstracja wizualizacji
            self.demo_visualizations()
            
            print("\n" + "🎉" * 30)
            print("✅ DEMONSTRACJA ZAKOŃCZONA POMYŚLNIE!")
            print("🎉" * 30)
            
            print("\n📁 Wygenerowane pliki:")
            print("  📊 policy_comparison.png - Porównanie polityk")
            print("  🔥 correlation_heatmap.png - Heatmapa korelacji")
            print("  📈 metrics_distribution.png - Rozkład metryk")
            
        except Exception as e:
            logger.error(f"Błąd w demonstracji: {e}")
            print(f"\n❌ Błąd w demonstracji: {e}")


def main():
    """Główna funkcja"""
    demo = AdvancedFeaturesDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()
