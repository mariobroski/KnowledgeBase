#!/usr/bin/env python3
"""
Generator raportów - tworzy tabele porównawcze i wykresy trendów
Porównuje wyniki RAGBench + FinanceBench z wnioskami
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generator raportów porównawczych"""
    
    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Konfiguracja stylów
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def load_results(self, domain: str) -> Dict[str, pd.DataFrame]:
        """
        Ładuje wyniki z plików CSV
        
        Args:
            domain: Nazwa domeny
            
        Returns:
            Słownik z DataFrame dla każdej polityki
        """
        results = {}
        
        # Znajdź pliki wyników dla danej domeny
        csv_files = list(self.results_dir.glob(f"{domain}_results_*.csv"))
        
        if not csv_files:
            logger.error(f"Brak plików wyników dla domeny {domain}")
            return {}
        
        # Załaduj najnowszy plik
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Ładowanie wyników z {latest_file}")
        
        df = pd.read_csv(latest_file)
        
        # Podziel według polityk
        for policy in df['policy'].unique():
            policy_df = df[df['policy'] == policy].copy()
            results[policy] = policy_df
        
        return results
    
    def generate_domain_report(self, domain: str) -> Dict[str, Any]:
        """
        Generuje raport dla danej domeny
        
        Args:
            domain: Nazwa domeny
            
        Returns:
            Raport domeny
        """
        logger.info(f"Generowanie raportu dla domeny {domain}")
        
        # Załaduj wyniki
        results = self.load_results(domain)
        if not results:
            return {}
        
        # Oblicz statystyki dla każdej polityki
        domain_stats = {}
        
        for policy, df in results.items():
            stats = self._calculate_policy_stats(df)
            domain_stats[policy] = stats
        
        # Generuj wykresy
        self._generate_domain_plots(domain, results)
        
        # Generuj tabele porównawcze
        comparison_table = self._generate_comparison_table(domain_stats)
        
        # Generuj wnioski
        conclusions = self._generate_domain_conclusions(domain_stats)
        
        report = {
            "domain": domain,
            "statistics": domain_stats,
            "comparison_table": comparison_table,
            "conclusions": conclusions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Zapisz raport
        self._save_domain_report(domain, report)
        
        return report
    
    def _calculate_policy_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Oblicza statystyki dla polityki"""
        stats = {}
        
        # Metryki TRACe
        trace_metrics = ["relevance", "utilization", "adherence", "completeness"]
        for metric in trace_metrics:
            if metric in df.columns:
                values = df[metric].dropna()
                stats[metric] = {
                    "mean": values.mean(),
                    "std": values.std(),
                    "min": values.min(),
                    "max": values.max(),
                    "p50": values.median(),
                    "p95": values.quantile(0.95)
                }
        
        # Metryki RAGAS
        ragas_metrics = ["faithfulness", "answer_relevance", "context_precision", "context_recall"]
        for metric in ragas_metrics:
            if metric in df.columns:
                values = df[metric].dropna()
                stats[metric] = {
                    "mean": values.mean(),
                    "std": values.std(),
                    "min": values.min(),
                    "max": values.max(),
                    "p50": values.median(),
                    "p95": values.quantile(0.95)
                }
        
        # Metryki operacyjne
        if "total_time" in df.columns:
            times = df["total_time"].dropna()
            stats["latency"] = {
                "mean": times.mean(),
                "std": times.std(),
                "p50": times.median(),
                "p95": times.quantile(0.95)
            }
        
        if "tokens_used" in df.columns:
            tokens = df["tokens_used"].dropna()
            stats["tokens"] = {
                "mean": tokens.mean(),
                "std": tokens.std(),
                "min": tokens.min(),
                "max": tokens.max()
            }
        
        if "cost" in df.columns:
            costs = df["cost"].dropna()
            stats["cost"] = {
                "mean": costs.mean(),
                "std": costs.std(),
                "min": costs.min(),
                "max": costs.max()
            }
        
        # Liczba zapytań
        stats["total_queries"] = len(df)
        
        return stats
    
    def _generate_domain_plots(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Generuje wykresy dla domeny"""
        
        # Wykres 1: Porównanie metryk TRACe
        self._plot_trace_metrics(domain, results)
        
        # Wykres 2: Porównanie metryk RAGAS
        self._plot_ragas_metrics(domain, results)
        
        # Wykres 3: Porównanie latencji
        self._plot_latency_comparison(domain, results)
        
        # Wykres 4: Porównanie kosztów
        self._plot_cost_comparison(domain, results)
        
        # Wykres 5: Heatmapa korelacji
        self._plot_correlation_heatmap(domain, results)
    
    def _plot_trace_metrics(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Wykres metryk TRACe"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'TRACe Metrics Comparison - {domain}', fontsize=16)
        
        metrics = ["relevance", "utilization", "adherence", "completeness"]
        titles = ["Relevance", "Utilization", "Adherence", "Completeness"]
        
        for i, (metric, title) in enumerate(zip(metrics, titles)):
            ax = axes[i//2, i%2]
            
            data = []
            labels = []
            
            for policy, df in results.items():
                if metric in df.columns:
                    values = df[metric].dropna()
                    data.append(values)
                    labels.append(policy)
            
            if data:
                ax.boxplot(data, labels=labels)
                ax.set_title(title)
                ax.set_ylabel('Score')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"{domain}_trace_metrics.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_ragas_metrics(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Wykres metryk RAGAS"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'RAGAS Metrics Comparison - {domain}', fontsize=16)
        
        metrics = ["faithfulness", "answer_relevance", "context_precision", "context_recall"]
        titles = ["Faithfulness", "Answer Relevance", "Context Precision", "Context Recall"]
        
        for i, (metric, title) in enumerate(zip(metrics, titles)):
            ax = axes[i//2, i%2]
            
            data = []
            labels = []
            
            for policy, df in results.items():
                if metric in df.columns:
                    values = df[metric].dropna()
                    data.append(values)
                    labels.append(policy)
            
            if data:
                ax.boxplot(data, labels=labels)
                ax.set_title(title)
                ax.set_ylabel('Score')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"{domain}_ragas_metrics.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_latency_comparison(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Wykres porównania latencji"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        data = []
        labels = []
        
        for policy, df in results.items():
            if "total_time" in df.columns:
                times = df["total_time"].dropna()
                data.append(times)
                labels.append(policy)
        
        if data:
            ax.boxplot(data, labels=labels)
            ax.set_title(f'Latency Comparison - {domain}')
            ax.set_ylabel('Time (ms)')
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"{domain}_latency.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_cost_comparison(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Wykres porównania kosztów"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        data = []
        labels = []
        
        for policy, df in results.items():
            if "cost" in df.columns:
                costs = df["cost"].dropna()
                data.append(costs)
                labels.append(policy)
        
        if data:
            ax.boxplot(data, labels=labels)
            ax.set_title(f'Cost Comparison - {domain}')
            ax.set_ylabel('Cost ($)')
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"{domain}_cost.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_correlation_heatmap(self, domain: str, results: Dict[str, pd.DataFrame]):
        """Heatmapa korelacji metryk"""
        # Połącz wszystkie dane
        all_data = []
        for policy, df in results.items():
            df_copy = df.copy()
            df_copy['policy'] = policy
            all_data.append(df_copy)
        
        if not all_data:
            return
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Wybierz kolumny numeryczne
        numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
        correlation_matrix = combined_df[numeric_cols].corr()
        
        # Generuj heatmapę
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                    square=True, ax=ax)
        ax.set_title(f'Metrics Correlation Heatmap - {domain}')
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"{domain}_correlation.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_comparison_table(self, domain_stats: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Generuje tabelę porównawczą"""
        comparison_data = []
        
        for policy, stats in domain_stats.items():
            row = {"Policy": policy}
            
            # Dodaj metryki TRACe
            for metric in ["relevance", "utilization", "adherence", "completeness"]:
                if metric in stats:
                    row[f"{metric}_mean"] = round(stats[metric]["mean"], 3)
                    row[f"{metric}_std"] = round(stats[metric]["std"], 3)
            
            # Dodaj metryki RAGAS
            for metric in ["faithfulness", "answer_relevance", "context_precision", "context_recall"]:
                if metric in stats:
                    row[f"{metric}_mean"] = round(stats[metric]["mean"], 3)
                    row[f"{metric}_std"] = round(stats[metric]["std"], 3)
            
            # Dodaj metryki operacyjne
            if "latency" in stats:
                row["latency_p50"] = round(stats["latency"]["p50"], 1)
                row["latency_p95"] = round(stats["latency"]["p95"], 1)
            
            if "tokens" in stats:
                row["tokens_mean"] = round(stats["tokens"]["mean"], 1)
            
            if "cost" in stats:
                row["cost_mean"] = round(stats["cost"]["mean"], 6)
            
            row["total_queries"] = stats.get("total_queries", 0)
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def _generate_domain_conclusions(self, domain_stats: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generuje wnioski dla domeny"""
        conclusions = []
        
        # Znajdź najlepszą politykę dla każdej metryki
        best_policies = {}
        
        for metric in ["relevance", "utilization", "adherence", "completeness"]:
            best_policy = None
            best_score = 0
            
            for policy, stats in domain_stats.items():
                if metric in stats:
                    score = stats[metric]["mean"]
                    if score > best_score:
                        best_score = score
                        best_policy = policy
            
            if best_policy:
                best_policies[metric] = best_policy
                conclusions.append(f"Polityka {best_policy} osiąga najlepszą {metric} ({best_score:.3f})")
        
        # Analiza latencji
        if "latency" in domain_stats.get("text", {}):
            text_latency = domain_stats["text"]["latency"]["p95"]
            graph_latency = domain_stats.get("graph", {}).get("latency", {}).get("p95", 0)
            
            if graph_latency > 0:
                latency_ratio = graph_latency / text_latency
                conclusions.append(f"GraphRAG jest {latency_ratio:.1f}x wolniejszy od TextRAG")
        
        # Analiza kosztów
        if "cost" in domain_stats.get("text", {}):
            text_cost = domain_stats["text"]["cost"]["mean"]
            graph_cost = domain_stats.get("graph", {}).get("cost", {}).get("mean", 0)
            
            if graph_cost > 0:
                cost_ratio = text_cost / graph_cost
                conclusions.append(f"GraphRAG jest {cost_ratio:.1f}x tańszy od TextRAG")
        
        return conclusions
    
    def _save_domain_report(self, domain: str, report: Dict[str, Any]):
        """Zapisuje raport domeny"""
        report_file = self.reports_dir / f"{domain}_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Zapisz tabelę porównawczą
        if "comparison_table" in report:
            table_file = self.reports_dir / f"{domain}_comparison.csv"
            report["comparison_table"].to_csv(table_file, index=False)
        
        logger.info(f"Raport domeny {domain} zapisany do {report_file}")
    
    def generate_combined_report(self, domains: List[str]) -> Dict[str, Any]:
        """
        Generuje zbiorczy raport dla wszystkich domen
        
        Args:
            domains: Lista domen
            
        Returns:
            Zbiorczy raport
        """
        logger.info("Generowanie zbiorczego raportu")
        
        combined_stats = {}
        all_comparisons = []
        
        # Załaduj statystyki dla każdej domeny
        for domain in domains:
            domain_report = self.generate_domain_report(domain)
            if domain_report:
                combined_stats[domain] = domain_report["statistics"]
                
                # Dodaj domenę do tabeli porównawczej
                comparison_df = domain_report["comparison_table"].copy()
                comparison_df["domain"] = domain
                all_comparisons.append(comparison_df)
        
        # Połącz wszystkie tabele porównawcze
        if all_comparisons:
            combined_comparison = pd.concat(all_comparisons, ignore_index=True)
        else:
            combined_comparison = pd.DataFrame()
        
        # Generuj wykresy zbiorcze
        self._generate_combined_plots(combined_stats)
        
        # Generuj wnioski zbiorcze
        combined_conclusions = self._generate_combined_conclusions(combined_stats)
        
        combined_report = {
            "domains": domains,
            "statistics": combined_stats,
            "comparison_table": combined_comparison,
            "conclusions": combined_conclusions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Zapisz zbiorczy raport
        self._save_combined_report(combined_report)
        
        return combined_report
    
    def _generate_combined_plots(self, combined_stats: Dict[str, Dict[str, Dict[str, Any]]]):
        """Generuje wykresy zbiorcze"""
        
        # Wykres 1: Porównanie metryk TRACe między domenami
        self._plot_domain_comparison(combined_stats, "relevance", "Relevance")
        self._plot_domain_comparison(combined_stats, "adherence", "Adherence")
        self._plot_domain_comparison(combined_stats, "utilization", "Utilization")
        self._plot_domain_comparison(combined_stats, "completeness", "Completeness")
        
        # Wykres 2: Porównanie latencji między domenami
        self._plot_domain_latency_comparison(combined_stats)
        
        # Wykres 3: Porównanie kosztów między domenami
        self._plot_domain_cost_comparison(combined_stats)
    
    def _plot_domain_comparison(self, combined_stats: Dict[str, Dict[str, Dict[str, Any]]], 
                               metric: str, title: str):
        """Wykres porównania metryki między domenami"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        domains = list(combined_stats.keys())
        policies = ["text", "facts", "graph", "hybrid"]
        
        x = np.arange(len(domains))
        width = 0.2
        
        for i, policy in enumerate(policies):
            values = []
            for domain in domains:
                if policy in combined_stats[domain] and metric in combined_stats[domain][policy]:
                    values.append(combined_stats[domain][policy][metric]["mean"])
                else:
                    values.append(0)
            
            ax.bar(x + i * width, values, width, label=policy)
        
        ax.set_xlabel('Domain')
        ax.set_ylabel(f'{title} Score')
        ax.set_title(f'{title} Comparison Across Domains')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(domains)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / f"combined_{metric.lower()}_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_domain_latency_comparison(self, combined_stats: Dict[str, Dict[str, Dict[str, Any]]]):
        """Wykres porównania latencji między domenami"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        domains = list(combined_stats.keys())
        policies = ["text", "facts", "graph", "hybrid"]
        
        x = np.arange(len(domains))
        width = 0.2
        
        for i, policy in enumerate(policies):
            values = []
            for domain in domains:
                if policy in combined_stats[domain] and "latency" in combined_stats[domain][policy]:
                    values.append(combined_stats[domain][policy]["latency"]["p95"])
                else:
                    values.append(0)
            
            ax.bar(x + i * width, values, width, label=policy)
        
        ax.set_xlabel('Domain')
        ax.set_ylabel('Latency (ms)')
        ax.set_title('Latency Comparison Across Domains')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(domains)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / "combined_latency_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_domain_cost_comparison(self, combined_stats: Dict[str, Dict[str, Dict[str, Any]]]):
        """Wykres porównania kosztów między domenami"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        domains = list(combined_stats.keys())
        policies = ["text", "facts", "graph", "hybrid"]
        
        x = np.arange(len(domains))
        width = 0.2
        
        for i, policy in enumerate(policies):
            values = []
            for domain in domains:
                if policy in combined_stats[domain] and "cost" in combined_stats[domain][policy]:
                    values.append(combined_stats[domain][policy]["cost"]["mean"])
                else:
                    values.append(0)
            
            ax.bar(x + i * width, values, width, label=policy)
        
        ax.set_xlabel('Domain')
        ax.set_ylabel('Cost ($)')
        ax.set_title('Cost Comparison Across Domains')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(domains)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / "combined_cost_comparison.png", 
                   dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_combined_conclusions(self, combined_stats: Dict[str, Dict[str, Dict[str, Any]]]) -> List[str]:
        """Generuje wnioski zbiorcze"""
        conclusions = []
        
        # Analiza trendów między domenami
        domain_performance = {}
        
        for domain, stats in combined_stats.items():
            domain_scores = {}
            for policy, policy_stats in stats.items():
                if "adherence" in policy_stats:
                    domain_scores[policy] = policy_stats["adherence"]["mean"]
            
            if domain_scores:
                best_policy = max(domain_scores, key=domain_scores.get)
                domain_performance[domain] = {
                    "best_policy": best_policy,
                    "best_score": domain_scores[best_policy]
                }
        
        # Wnioski o najlepszych politykach
        policy_wins = {}
        for domain, perf in domain_performance.items():
            policy = perf["best_policy"]
            if policy not in policy_wins:
                policy_wins[policy] = 0
            policy_wins[policy] += 1
        
        if policy_wins:
            best_overall_policy = max(policy_wins, key=policy_wins.get)
            conclusions.append(f"Polityka {best_overall_policy} wygrywa w {policy_wins[best_overall_policy]} domenach")
        
        # Analiza różnic między domenami
        adherence_scores = []
        for domain, stats in combined_stats.items():
            for policy, policy_stats in stats.items():
                if "adherence" in policy_stats:
                    adherence_scores.append(policy_stats["adherence"]["mean"])
        
        if adherence_scores:
            score_std = np.std(adherence_scores)
            conclusions.append(f"Odchylenie standardowe adherence: {score_std:.3f}")
        
        # Wnioski o wydajności
        latency_analysis = []
        for domain, stats in combined_stats.items():
            for policy, policy_stats in stats.items():
                if "latency" in policy_stats:
                    latency_analysis.append({
                        "domain": domain,
                        "policy": policy,
                        "p95": policy_stats["latency"]["p95"]
                    })
        
        if latency_analysis:
            fastest = min(latency_analysis, key=lambda x: x["p95"])
            conclusions.append(f"Najszybsza polityka: {fastest['policy']} w domenie {fastest['domain']} ({fastest['p95']:.1f}ms)")
        
        return conclusions
    
    def _save_combined_report(self, combined_report: Dict[str, Any]):
        """Zapisuje zbiorczy raport"""
        report_file = self.reports_dir / "combined_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(combined_report, f, indent=2, ensure_ascii=False)
        
        # Zapisz tabelę porównawczą
        if "comparison_table" in combined_report and not combined_report["comparison_table"].empty:
            table_file = self.reports_dir / "combined_comparison.csv"
            combined_report["comparison_table"].to_csv(table_file, index=False)
        
        logger.info(f"Zbiorczy raport zapisany do {report_file}")


def main():
    """Główna funkcja"""
    if len(sys.argv) < 2:
        print("Użycie: python generate_report.py <domain1,domain2,...> [--combined]")
        print("Dostępne domeny: FinQA, TAT-QA, TechQA, CUAD, EManual, FinanceBench, FinancialQA, FinNLP")
        sys.exit(1)
    
    domains = sys.argv[1].split(",")
    combined = "--combined" in sys.argv
    
    generator = ReportGenerator()
    
    if combined:
        # Generuj zbiorczy raport
        report = generator.generate_combined_report(domains)
        print(f"✅ Zbiorczy raport wygenerowany dla domen: {domains}")
    else:
        # Generuj raporty dla każdej domeny
        for domain in domains:
            report = generator.generate_domain_report(domain)
            if report:
                print(f"✅ Raport wygenerowany dla domeny {domain}")
            else:
                print(f"❌ Błąd generowania raportu dla domeny {domain}")
    
    print(f"📊 Raporty zapisane do {generator.reports_dir}")


if __name__ == "__main__":
    main()
