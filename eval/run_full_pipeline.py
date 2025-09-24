#!/usr/bin/env python3
"""
Pełny pipeline ewaluacji RAGBench + FinanceBench
Uruchamia import, ewaluację i generowanie raportów
"""

import os
import sys
import json
import logging
import subprocess
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from advanced_metrics import AdvancedEvaluator
from literature_comparison import LiteratureComparator
from trend_analysis import TrendAnalyzer

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullPipelineRunner:
    """Runner pełnego pipeline'u ewaluacji"""
    
    def __init__(self):
        self.eval_dir = Path(__file__).parent
        self.results_dir = self.eval_dir / "results"
        self.reports_dir = self.eval_dir / "reports"
        
        # Konfiguracja domen
        self.ragbench_domains = ["FinQA", "TAT-QA", "TechQA", "CUAD", "EManual"]
        self.financebench_domains = ["FinanceBench", "FinancialQA", "FinNLP"]
        
        # Konfiguracja polityk
        self.policies = ["text", "facts", "graph", "hybrid"]
        
        # Konfiguracja API
        self.api_base_url = "http://localhost:8000"
        
        # Nowe komponenty
        self.advanced_evaluator = AdvancedEvaluator()
        self.literature_comparator = LiteratureComparator()
        self.trend_analyzer = TrendAnalyzer()
        
    def run_full_pipeline(self, domains: List[str] = None, policies: List[str] = None):
        """
        Uruchamia pełny pipeline ewaluacji
        
        Args:
            domains: Lista domen do testowania
            policies: Lista polityk do testowania
        """
        if domains is None:
            domains = self.ragbench_domains + self.financebench_domains
        
        if policies is None:
            policies = self.policies
        
        logger.info(f"Rozpoczynanie pełnego pipeline'u ewaluacji")
        logger.info(f"Domeny: {domains}")
        logger.info(f"Polityki: {policies}")
        
        start_time = datetime.now()
        
        try:
            # Krok 1: Sprawdź dostępność API
            if not self._check_api_availability():
                logger.error("API nie jest dostępne. Uruchom backend przed kontynuowaniem.")
                return False
            
            # Krok 2: Import korpusów
            import_results = self._import_corpus(domains)
            if not import_results:
                logger.error("Błąd importu korpusów")
                return False
            
            # Krok 3: Ewaluacja
            eval_results = self._run_evaluation(domains, policies)
            if not eval_results:
                logger.error("Błąd ewaluacji")
                return False
            
            # Krok 4: Generowanie raportów
            report_results = self._generate_reports(domains)
            if not report_results:
                logger.error("Błąd generowania raportów")
                return False
            
            # Krok 5: Zaawansowana analiza
            advanced_results = self._run_advanced_analysis(domains, policies)
            if not advanced_results:
                logger.warning("Błąd zaawansowanej analizy")
            
            # Krok 6: Porównanie z literaturą
            literature_results = self._run_literature_comparison(domains, policies)
            if not literature_results:
                logger.warning("Błąd porównania z literaturą")
            
            # Krok 7: Analiza trendów
            trend_results = self._run_trend_analysis(domains, policies)
            if not trend_results:
                logger.warning("Błąd analizy trendów")
            
            # Krok 8: Podsumowanie
            self._generate_summary(domains, policies, start_time)
            
            logger.info("✅ Pełny pipeline ewaluacji zakończony pomyślnie")
            return True
            
        except Exception as e:
            logger.error(f"Błąd w pełnym pipeline'u: {e}")
            return False
    
    def _check_api_availability(self) -> bool:
        """Sprawdza dostępność API"""
        logger.info("Sprawdzanie dostępności API...")
        
        try:
            import requests
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ API jest dostępne")
                return True
            else:
                logger.error(f"❌ API zwróciło status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Błąd połączenia z API: {e}")
            return False
    
    def _import_corpus(self, domains: List[str]) -> bool:
        """Importuje korpusy"""
        logger.info("Rozpoczynanie importu korpusów...")
        
        success_count = 0
        
        for domain in domains:
            logger.info(f"Import korpusu {domain}...")
            
            try:
                if domain in self.ragbench_domains:
                    # Import RAGBench
                    result = subprocess.run([
                        sys.executable, 
                        str(self.eval_dir / "ingest_ragbench.py"),
                        domain
                    ], capture_output=True, text=True, timeout=300)
                elif domain in self.financebench_domains:
                    # Import FinanceBench
                    result = subprocess.run([
                        sys.executable,
                        str(self.eval_dir / "ingest_financebench.py"),
                        domain
                    ], capture_output=True, text=True, timeout=300)
                else:
                    logger.warning(f"Nieznana domena: {domain}")
                    continue
                
                if result.returncode == 0:
                    logger.info(f"✅ Import korpusu {domain} zakończony pomyślnie")
                    success_count += 1
                else:
                    logger.error(f"❌ Błąd importu korpusu {domain}: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                logger.error(f"⏰ Timeout importu korpusu {domain}")
            except Exception as e:
                logger.error(f"💥 Błąd importu korpusu {domain}: {e}")
        
        logger.info(f"Import zakończony: {success_count}/{len(domains)} korpusów")
        return success_count > 0
    
    def _run_evaluation(self, domains: List[str], policies: List[str]) -> bool:
        """Uruchamia ewaluację"""
        logger.info("Rozpoczynanie ewaluacji...")
        
        success_count = 0
        
        for domain in domains:
            logger.info(f"Ewaluacja domeny {domain}...")
            
            try:
                # Uruchom ewaluację dla domeny
                result = subprocess.run([
                    sys.executable,
                    str(self.eval_dir / "run_eval.py"),
                    domain,
                    ",".join(policies)
                ], capture_output=True, text=True, timeout=1800)  # 30 minut timeout
                
                if result.returncode == 0:
                    logger.info(f"✅ Ewaluacja domeny {domain} zakończona pomyślnie")
                    success_count += 1
                else:
                    logger.error(f"❌ Błąd ewaluacji domeny {domain}: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                logger.error(f"⏰ Timeout ewaluacji domeny {domain}")
            except Exception as e:
                logger.error(f"💥 Błąd ewaluacji domeny {domain}: {e}")
        
        logger.info(f"Ewaluacja zakończona: {success_count}/{len(domains)} domen")
        return success_count > 0
    
    def _generate_reports(self, domains: List[str]) -> bool:
        """Generuje raporty"""
        logger.info("Rozpoczynanie generowania raportów...")
        
        try:
            # Generuj raporty dla każdej domeny
            for domain in domains:
                logger.info(f"Generowanie raportu dla domeny {domain}...")
                
                result = subprocess.run([
                    sys.executable,
                    str(self.eval_dir / "generate_report.py"),
                    domain
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"✅ Raport dla domeny {domain} wygenerowany")
                else:
                    logger.error(f"❌ Błąd generowania raportu dla domeny {domain}: {result.stderr}")
            
            # Generuj zbiorczy raport
            logger.info("Generowanie zbiorczego raportu...")
            
            result = subprocess.run([
                sys.executable,
                str(self.eval_dir / "generate_report.py"),
                ",".join(domains),
                "--combined"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Zbiorczy raport wygenerowany")
                return True
            else:
                logger.error(f"❌ Błąd generowania zbiorczego raportu: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Błąd generowania raportów: {e}")
            return False
    
    def _generate_summary(self, domains: List[str], policies: List[str], start_time: datetime):
        """Generuje podsumowanie"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("📊 PODSUMOWANIE PEŁNEGO PIPELINE'U EWALUACJI")
        logger.info("=" * 60)
        logger.info(f"⏰ Czas trwania: {duration}")
        logger.info(f"📋 Domeny: {', '.join(domains)}")
        logger.info(f"🔧 Polityki: {', '.join(policies)}")
        logger.info(f"📁 Wyniki: {self.results_dir}")
        logger.info(f"📊 Raporty: {self.reports_dir}")
        
        # Sprawdź pliki wyników
        result_files = list(self.results_dir.glob("*.csv"))
        report_files = list(self.reports_dir.glob("*.json"))
        
        logger.info(f"📄 Pliki wyników: {len(result_files)}")
        logger.info(f"📊 Pliki raportów: {len(report_files)}")
        
        # Wyświetl najważniejsze pliki
        if result_files:
            logger.info("📄 Najważniejsze pliki wyników:")
            for file in result_files[:5]:  # Pokaż pierwsze 5
                logger.info(f"  - {file.name}")
        
        if report_files:
            logger.info("📊 Najważniejsze pliki raportów:")
            for file in report_files[:5]:  # Pokaż pierwsze 5
                logger.info(f"  - {file.name}")
        
        logger.info("=" * 60)
    
    def _run_advanced_analysis(self, domains: List[str], policies: List[str]) -> bool:
        """Uruchamia zaawansowaną analizę metryk"""
        logger.info("Rozpoczynanie zaawansowanej analizy...")
        
        try:
            # Załaduj wyniki ewaluacji
            for domain in domains:
                csv_files = list(self.results_dir.glob(f"{domain}_results_*.csv"))
                
                if not csv_files:
                    logger.warning(f"Brak wyników dla domeny {domain}")
                    continue
                
                # Załaduj najnowszy plik
                latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file)
                
                # Analizuj zaawansowane metryki
                for _, row in df.iterrows():
                    advanced_metrics = self.advanced_evaluator.calculate_advanced_metrics(
                        query=row['query'],
                        response=row['response'],
                        context=json.loads(row.get('context', '{}')),
                        ground_truth=json.loads(row.get('ground_truth', '[]'))
                    )
                    
                    # Generuj raport jakości
                    quality_report = self.advanced_evaluator.generate_quality_report(advanced_metrics)
                    
                    # Zapisz wyniki
                    advanced_file = self.results_dir / f"{domain}_advanced_metrics.json"
                    with open(advanced_file, 'w', encoding='utf-8') as f:
                        json.dump(quality_report, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Zaawansowana analiza zakończona")
            return True
            
        except Exception as e:
            logger.error(f"Błąd zaawansowanej analizy: {e}")
            return False
    
    def _run_literature_comparison(self, domains: List[str], policies: List[str]) -> bool:
        """Uruchamia porównanie z literaturą"""
        logger.info("Rozpoczynanie porównania z literaturą...")
        
        try:
            comparison_results = []
            
            for domain in domains:
                # Załaduj wyniki
                csv_files = list(self.results_dir.glob(f"{domain}_results_*.csv"))
                
                if not csv_files:
                    continue
                
                latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file)
                
                # Przygotuj wyniki dla porównania
                our_results = {}
                for policy in policies:
                    policy_data = df[df['policy'] == policy]
                    if not policy_data.empty:
                        our_results[policy] = {
                            "relevance": policy_data['relevance'].mean(),
                            "utilization": policy_data['utilization'].mean(),
                            "adherence": policy_data['adherence'].mean(),
                            "completeness": policy_data['completeness'].mean()
                        }
                
                # Porównaj z literaturą
                comparison_result = self.literature_comparator.compare_with_literature(
                    our_results=our_results,
                    benchmark="RAGBench" if domain in self.ragbench_domains else "FinanceBench",
                    domain=domain
                )
                
                comparison_results.append(comparison_result)
            
            # Generuj raport porównawczy
            if comparison_results:
                report = self.literature_comparator.generate_comparison_report(comparison_results)
                self.literature_comparator.save_comparison_report(
                    report, 
                    str(self.reports_dir / "literature_comparison_report.json")
                )
            
            logger.info("✅ Porównanie z literaturą zakończone")
            return True
            
        except Exception as e:
            logger.error(f"Błąd porównania z literaturą: {e}")
            return False
    
    def _run_trend_analysis(self, domains: List[str], policies: List[str]) -> bool:
        """Uruchamia analizę trendów"""
        logger.info("Rozpoczynanie analizy trendów...")
        
        try:
            # Załaduj dane historyczne
            for domain in domains:
                csv_files = list(self.results_dir.glob(f"{domain}_results_*.csv"))
                
                for csv_file in csv_files:
                    df = pd.read_csv(csv_file)
                    
                    # Dodaj punkty danych do analizatora
                    for _, row in df.iterrows():
                        timestamp = datetime.now()  # W rzeczywistości z pliku
                        
                        # Dodaj różne metryki
                        for metric in ['relevance', 'utilization', 'adherence', 'completeness']:
                            if metric in row:
                                self.trend_analyzer.add_data_point(
                                    timestamp=timestamp,
                                    metric=metric,
                                    value=row[metric],
                                    policy=row['policy'],
                                    domain=domain
                                )
            
            # Wykonaj analizę trendów
            trend_report = self.trend_analyzer.generate_trend_report()
            
            # Zapisz raport
            with open(self.reports_dir / "trend_analysis_report.json", 'w', encoding='utf-8') as f:
                json.dump(trend_report, f, indent=2, ensure_ascii=False)
            
            # Stwórz wykresy
            for metric in ['relevance', 'utilization', 'adherence', 'completeness']:
                self.trend_analyzer.plot_trends(
                    metric=metric,
                    save_path=str(self.reports_dir / f"trend_{metric}.png")
                )
            
            logger.info("✅ Analiza trendów zakończona")
            return True
            
        except Exception as e:
            logger.error(f"Błąd analizy trendów: {e}")
            return False
    
    def run_quick_test(self, domain: str = "FinQA", policy: str = "text"):
        """
        Uruchamia szybki test dla jednej domeny i polityki
        
        Args:
            domain: Domena do testowania
            policy: Polityka do testowania
        """
        logger.info(f"Rozpoczynanie szybkiego testu: {domain} + {policy}")
        
        try:
            # Sprawdź API
            if not self._check_api_availability():
                return False
            
            # Import korpusu
            logger.info(f"Import korpusu {domain}...")
            if domain in self.ragbench_domains:
                result = subprocess.run([
                    sys.executable,
                    str(self.eval_dir / "ingest_ragbench.py"),
                    domain
                ], capture_output=True, text=True, timeout=300)
            elif domain in self.financebench_domains:
                result = subprocess.run([
                    sys.executable,
                    str(self.eval_dir / "ingest_financebench.py"),
                    domain
                ], capture_output=True, text=True, timeout=300)
            else:
                logger.error(f"Nieznana domena: {domain}")
                return False
            
            if result.returncode != 0:
                logger.error(f"Błąd importu: {result.stderr}")
                return False
            
            # Ewaluacja
            logger.info(f"Ewaluacja {domain} + {policy}...")
            result = subprocess.run([
                sys.executable,
                str(self.eval_dir / "run_eval.py"),
                domain,
                policy
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"Błąd ewaluacji: {result.stderr}")
                return False
            
            # Raport
            logger.info(f"Generowanie raportu...")
            result = subprocess.run([
                sys.executable,
                str(self.eval_dir / "generate_report.py"),
                domain
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Błąd generowania raportu: {result.stderr}")
                return False
            
            logger.info("✅ Szybki test zakończony pomyślnie")
            return True
            
        except Exception as e:
            logger.error(f"💥 Błąd w szybkim teście: {e}")
            return False


def main():
    """Główna funkcja"""
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python run_full_pipeline.py --full [domains] [policies]")
        print("  python run_full_pipeline.py --quick [domain] [policy]")
        print("  python run_full_pipeline.py --domains")
        print("")
        print("Przykłady:")
        print("  python run_full_pipeline.py --full")
        print("  python run_full_pipeline.py --full FinQA,TAT-QA text,facts")
        print("  python run_full_pipeline.py --quick FinQA text")
        print("  python run_full_pipeline.py --domains")
        sys.exit(1)
    
    runner = FullPipelineRunner()
    
    if sys.argv[1] == "--full":
        # Pełny pipeline
        domains = sys.argv[2].split(",") if len(sys.argv) > 2 else None
        policies = sys.argv[3].split(",") if len(sys.argv) > 3 else None
        
        success = runner.run_full_pipeline(domains, policies)
        sys.exit(0 if success else 1)
        
    elif sys.argv[1] == "--quick":
        # Szybki test
        domain = sys.argv[2] if len(sys.argv) > 2 else "FinQA"
        policy = sys.argv[3] if len(sys.argv) > 3 else "text"
        
        success = runner.run_quick_test(domain, policy)
        sys.exit(0 if success else 1)
        
    elif sys.argv[1] == "--domains":
        # Wyświetl dostępne domeny
        print("Dostępne domeny RAGBench:")
        for domain in runner.ragbench_domains:
            print(f"  - {domain}")
        
        print("\nDostępne domeny FinanceBench:")
        for domain in runner.financebench_domains:
            print(f"  - {domain}")
        
        print(f"\nDostępne polityki: {', '.join(runner.policies)}")
        
    else:
        print("Nieznana opcja. Użyj --help dla pomocy.")
        sys.exit(1)


if __name__ == "__main__":
    main()
