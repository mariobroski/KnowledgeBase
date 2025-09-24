#!/usr/bin/env python3
"""
System analizy trendów i wzorców w wynikach ewaluacji
- Analiza wydajności w czasie
- Wykrywanie wzorców w danych
- Predykcja trendów
- Analiza korelacji
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import json

logger = logging.getLogger(__name__)


@dataclass
class TrendPoint:
    """Punkt trendu"""
    timestamp: datetime
    metric: str
    value: float
    policy: str
    domain: str


@dataclass
class TrendAnalysis:
    """Analiza trendu"""
    metric: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    correlation: float
    prediction: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class PatternAnalysis:
    """Analiza wzorców"""
    pattern_type: str
    description: str
    confidence: float
    affected_metrics: List[str]
    recommendations: List[str]


class TrendAnalyzer:
    """Analizator trendów i wzorców"""
    
    def __init__(self):
        self.trend_data = []
        self.patterns = []
        
        # Konfiguracja analizy
        self.trend_thresholds = {
            "strong_increase": 0.1,
            "moderate_increase": 0.05,
            "stable": 0.02,
            "moderate_decrease": -0.05,
            "strong_decrease": -0.1
        }
    
    def add_data_point(
        self, 
        timestamp: datetime, 
        metric: str, 
        value: float, 
        policy: str, 
        domain: str
    ):
        """Dodaje punkt danych do analizy"""
        self.trend_data.append(TrendPoint(
            timestamp=timestamp,
            metric=metric,
            value=value,
            policy=policy,
            domain=domain
        ))
    
    def analyze_trends(self, metric: str, policy: str = None, domain: str = None) -> List[TrendAnalysis]:
        """
        Analizuje trendy dla danej metryki
        
        Args:
            metric: Nazwa metryki
            policy: Polityka (opcjonalnie)
            domain: Domena (opcjonalnie)
            
        Returns:
            Lista analiz trendów
        """
        # Filtruj dane
        filtered_data = [
            point for point in self.trend_data
            if point.metric == metric
            and (policy is None or point.policy == policy)
            and (domain is None or point.domain == domain)
        ]
        
        if len(filtered_data) < 3:
            logger.warning(f"Za mało danych do analizy trendu dla {metric}")
            return []
        
        # Sortuj według czasu
        filtered_data.sort(key=lambda x: x.timestamp)
        
        # Analizuj trendy
        trend_analyses = []
        
        # Trend ogólny
        overall_trend = self._analyze_single_trend(filtered_data, metric)
        if overall_trend:
            trend_analyses.append(overall_trend)
        
        # Trendy dla każdej polityki
        if policy is None:
            policies = set(point.policy for point in filtered_data)
            for pol in policies:
                policy_data = [p for p in filtered_data if p.policy == pol]
                if len(policy_data) >= 3:
                    trend = self._analyze_single_trend(policy_data, f"{metric}_{pol}")
                    if trend:
                        trend_analyses.append(trend)
        
        # Trendy dla każdej domeny
        if domain is None:
            domains = set(point.domain for point in filtered_data)
            for dom in domains:
                domain_data = [p for p in filtered_data if p.domain == dom]
                if len(domain_data) >= 3:
                    trend = self._analyze_single_trend(domain_data, f"{metric}_{dom}")
                    if trend:
                        trend_analyses.append(trend)
        
        return trend_analyses
    
    def _analyze_single_trend(self, data: List[TrendPoint], metric_name: str) -> Optional[TrendAnalysis]:
        """Analizuje pojedynczy trend"""
        if len(data) < 3:
            return None
        
        # Przygotuj dane
        timestamps = [point.timestamp for point in data]
        values = [point.value for point in data]
        
        # Konwertuj timestamps na liczby
        time_numeric = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]  # godziny
        
        # Regresja liniowa
        X = np.array(time_numeric).reshape(-1, 1)
        y = np.array(values)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Oblicz trend
        slope = model.coef_[0]
        r_squared = model.score(X, y)
        
        # Określ kierunek trendu
        if slope > self.trend_thresholds["strong_increase"]:
            direction = "strong_increase"
        elif slope > self.trend_thresholds["moderate_increase"]:
            direction = "moderate_increase"
        elif slope > self.trend_thresholds["stable"]:
            direction = "stable"
        elif slope > self.trend_thresholds["moderate_decrease"]:
            direction = "moderate_decrease"
        else:
            direction = "strong_decrease"
        
        # Siła trendu
        strength = abs(slope) / (np.std(values) + 1e-8)
        strength = min(1.0, strength)
        
        # Predykcja
        if len(data) >= 5:
            # Predykcja na następny punkt
            next_time = time_numeric[-1] + (time_numeric[-1] - time_numeric[-2])
            prediction = model.predict([[next_time]])[0]
            confidence = r_squared
        else:
            prediction = None
            confidence = None
        
        return TrendAnalysis(
            metric=metric_name,
            trend_direction=direction,
            trend_strength=strength,
            correlation=r_squared,
            prediction=prediction,
            confidence=confidence
        )
    
    def detect_patterns(self) -> List[PatternAnalysis]:
        """Wykrywa wzorce w danych"""
        if len(self.trend_data) < 10:
            logger.warning("Za mało danych do wykrywania wzorców")
            return []
        
        # Konwertuj dane na DataFrame
        df = pd.DataFrame([
            {
                "timestamp": point.timestamp,
                "metric": point.metric,
                "value": point.value,
                "policy": point.policy,
                "domain": point.domain
            }
            for point in self.trend_data
        ])
        
        patterns = []
        
        # Wzorzec 1: Korelacja między metrykami
        correlation_pattern = self._detect_correlation_patterns(df)
        if correlation_pattern:
            patterns.append(correlation_pattern)
        
        # Wzorzec 2: Wzorce czasowe
        temporal_pattern = self._detect_temporal_patterns(df)
        if temporal_pattern:
            patterns.append(temporal_pattern)
        
        # Wzorzec 3: Wzorce domenowe
        domain_pattern = self._detect_domain_patterns(df)
        if domain_pattern:
            patterns.append(domain_pattern)
        
        # Wzorzec 4: Wzorce polityk
        policy_pattern = self._detect_policy_patterns(df)
        if policy_pattern:
            patterns.append(policy_pattern)
        
        return patterns
    
    def _detect_correlation_patterns(self, df: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Wykrywa wzorce korelacji"""
        # Pivot tabela dla metryk
        pivot_df = df.pivot_table(
            index=['timestamp', 'policy', 'domain'],
            columns='metric',
            values='value',
            aggfunc='mean'
        ).reset_index()
        
        # Oblicz korelacje
        numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return None
        
        correlation_matrix = pivot_df[numeric_cols].corr()
        
        # Znajdź silne korelacje
        strong_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr = correlation_matrix.iloc[i, j]
                if abs(corr) > 0.7:
                    strong_correlations.append({
                        "metric1": correlation_matrix.columns[i],
                        "metric2": correlation_matrix.columns[j],
                        "correlation": corr
                    })
        
        if not strong_correlations:
            return None
        
        # Generuj opis
        descriptions = []
        for corr in strong_correlations:
            if corr["correlation"] > 0.7:
                descriptions.append(f"Silna pozytywna korelacja między {corr['metric1']} i {corr['metric2']}")
            elif corr["correlation"] < -0.7:
                descriptions.append(f"Silna negatywna korelacja między {corr['metric1']} i {corr['metric2']}")
        
        return PatternAnalysis(
            pattern_type="correlation",
            description="; ".join(descriptions),
            confidence=0.8,
            affected_metrics=[corr["metric1"] for corr in strong_correlations] + 
                            [corr["metric2"] for corr in strong_correlations],
            recommendations=[
                "Rozważ optymalizację metryk o silnej korelacji",
                "Sprawdź czy korelacja jest przyczynowa czy przypadkowa"
            ]
        )
    
    def _detect_temporal_patterns(self, df: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Wykrywa wzorce czasowe"""
        # Grupuj według godzin
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby(['hour', 'metric'])['value'].mean().reset_index()
        
        # Sprawdź czy są różnice w wydajności w różnych godzinach
        hour_variance = hourly_avg.groupby('metric')['value'].var()
        high_variance_metrics = hour_variance[hour_variance > hour_variance.quantile(0.8)].index.tolist()
        
        if not high_variance_metrics:
            return None
        
        return PatternAnalysis(
            pattern_type="temporal",
            description=f"Wydajność zmienia się w zależności od pory dnia dla metryk: {', '.join(high_variance_metrics)}",
            confidence=0.7,
            affected_metrics=high_variance_metrics,
            recommendations=[
                "Rozważ optymalizację systemu dla różnych pór dnia",
                "Sprawdź czy różnice są związane z obciążeniem systemu"
            ]
        )
    
    def _detect_domain_patterns(self, df: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Wykrywa wzorce domenowe"""
        # Grupuj według domen
        domain_avg = df.groupby(['domain', 'metric'])['value'].mean().reset_index()
        
        # Sprawdź czy są różnice między domenami
        domain_variance = domain_avg.groupby('metric')['value'].var()
        high_variance_metrics = domain_variance[domain_variance > domain_variance.quantile(0.8)].index.tolist()
        
        if not high_variance_metrics:
            return None
        
        # Znajdź najlepsze i najgorsze domeny
        domain_performance = domain_avg.groupby('domain')['value'].mean().sort_values(ascending=False)
        best_domain = domain_performance.index[0]
        worst_domain = domain_performance.index[-1]
        
        return PatternAnalysis(
            pattern_type="domain",
            description=f"Wydajność różni się między domenami. Najlepsza: {best_domain}, najgorsza: {worst_domain}",
            confidence=0.8,
            affected_metrics=high_variance_metrics,
            recommendations=[
                f"Rozważ optymalizację dla domeny {worst_domain}",
                f"Przeanalizuj co czyni domenę {best_domain} bardziej efektywną"
            ]
        )
    
    def _detect_policy_patterns(self, df: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Wykrywa wzorce polityk"""
        # Grupuj według polityk
        policy_avg = df.groupby(['policy', 'metric'])['value'].mean().reset_index()
        
        # Sprawdź czy są różnice między politykami
        policy_variance = policy_avg.groupby('metric')['value'].var()
        high_variance_metrics = policy_variance[policy_variance > policy_variance.quantile(0.8)].index.tolist()
        
        if not high_variance_metrics:
            return None
        
        # Znajdź najlepsze i najgorsze polityki
        policy_performance = policy_avg.groupby('policy')['value'].mean().sort_values(ascending=False)
        best_policy = policy_performance.index[0]
        worst_policy = policy_performance.index[-1]
        
        return PatternAnalysis(
            pattern_type="policy",
            description=f"Wydajność różni się między politykami. Najlepsza: {best_policy}, najgorsza: {worst_policy}",
            confidence=0.8,
            affected_metrics=high_variance_metrics,
            recommendations=[
                f"Rozważ zwiększenie wykorzystania {best_policy}",
                f"Przeanalizuj dlaczego {worst_policy} osiąga gorsze wyniki"
            ]
        )
    
    def generate_trend_report(self) -> Dict[str, Any]:
        """Generuje raport trendów"""
        report = {
            "trends": {},
            "patterns": [],
            "summary": {},
            "generated_at": datetime.now().isoformat()
        }
        
        # Analizuj trendy dla każdej metryki
        metrics = set(point.metric for point in self.trend_data)
        for metric in metrics:
            trend_analyses = self.analyze_trends(metric)
            if trend_analyses:
                report["trends"][metric] = [
                    {
                        "trend_direction": trend.trend_direction,
                        "trend_strength": trend.trend_strength,
                        "correlation": trend.correlation,
                        "prediction": trend.prediction,
                        "confidence": trend.confidence
                    }
                    for trend in trend_analyses
                ]
        
        # Wykryj wzorce
        patterns = self.detect_patterns()
        report["patterns"] = [
            {
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "affected_metrics": pattern.affected_metrics,
                "recommendations": pattern.recommendations
            }
            for pattern in patterns
        ]
        
        # Podsumowanie
        report["summary"] = {
            "total_data_points": len(self.trend_data),
            "metrics_analyzed": len(metrics),
            "patterns_detected": len(patterns),
            "date_range": {
                "start": min(point.timestamp for point in self.trend_data).isoformat(),
                "end": max(point.timestamp for point in self.trend_data).isoformat()
            }
        }
        
        return report
    
    def save_trend_report(self, filename: str = "trend_analysis_report.json"):
        """Zapisuje raport trendów"""
        report = self.generate_trend_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raport trendów zapisany do {filename}")
    
    def plot_trends(self, metric: str, save_path: str = None):
        """Tworzy wykres trendów"""
        # Filtruj dane
        filtered_data = [point for point in self.trend_data if point.metric == metric]
        
        if not filtered_data:
            logger.warning(f"Brak danych dla metryki {metric}")
            return
        
        # Przygotuj dane
        df = pd.DataFrame([
            {
                "timestamp": point.timestamp,
                "value": point.value,
                "policy": point.policy,
                "domain": point.domain
            }
            for point in filtered_data
        ])
        
        # Stwórz wykres
        plt.figure(figsize=(12, 8))
        
        # Wykres dla każdej polityki
        for policy in df['policy'].unique():
            policy_data = df[df['policy'] == policy]
            plt.plot(policy_data['timestamp'], policy_data['value'], 
                    marker='o', label=policy, linewidth=2)
        
        plt.title(f'Trend dla metryki: {metric}')
        plt.xlabel('Czas')
        plt.ylabel('Wartość')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Wykres trendów zapisany do {save_path}")
        else:
            plt.show()
        
        plt.close()


# Global instance
trend_analyzer = TrendAnalyzer()
