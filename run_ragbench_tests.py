#!/usr/bin/env python3
"""
Skrypt uruchamiający testy RAGBench i TRACe metryki
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Dodaj ścieżkę do backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_tests():
    """Uruchamia testy RAGBench i TRACe"""
    
    print("🧪 Uruchamianie testów RAGBench i TRACe metryki")
    print("=" * 60)
    
    # Lista testów do uruchomienia
    test_files = [
        "tests/test_ragbench_import.py",
        "tests/test_trace_metrics.py", 
        "tests/test_ragbench_trace_integration.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\n📋 Uruchamianie testów: {test_file}")
        print("-" * 40)
        
        try:
            # Uruchom testy
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short"
            ], 
            cwd=backend_path,
            capture_output=True,
            text=True
            )
            
            # Sprawdź wynik
            if result.returncode == 0:
                print(f"✅ {test_file} - WSZYSTKIE TESTY PRZESZŁY")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} - BŁĘDY W TESTACH")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results[test_file] = "FAILED"
                
        except Exception as e:
            print(f"💥 Błąd uruchamiania testów {test_file}: {e}")
            results[test_file] = "ERROR"
    
    # Podsumowanie wyników
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE WYNIKÓW")
    print("=" * 60)
    
    passed = sum(1 for status in results.values() if status == "PASSED")
    failed = sum(1 for status in results.values() if status == "FAILED")
    errors = sum(1 for status in results.values() if status == "ERROR")
    
    print(f"✅ Przeszły: {passed}")
    print(f"❌ Nie przeszły: {failed}")
    print(f"💥 Błędy: {errors}")
    print(f"📈 Łącznie: {len(results)}")
    
    # Szczegóły wyników
    print("\n📋 SZCZEGÓŁY:")
    for test_file, status in results.items():
        status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "💥"
        print(f"{status_icon} {test_file}: {status}")
    
    # Zwróć kod wyjścia
    if failed > 0 or errors > 0:
        print(f"\n💥 Testy zakończone z błędami!")
        return 1
    else:
        print(f"\n🎉 Wszystkie testy przeszły pomyślnie!")
        return 0


def run_specific_test(test_name: str):
    """Uruchamia konkretny test"""
    
    print(f"🎯 Uruchamianie testu: {test_name}")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_name, 
            "-v", 
            "--tb=long"
        ], 
        cwd=backend_path,
        capture_output=True,
        text=True
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode
        
    except Exception as e:
        print(f"💥 Błąd uruchamiania testu {test_name}: {e}")
        return 1


def main():
    """Główna funkcja"""
    
    if len(sys.argv) > 1:
        # Uruchom konkretny test
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        # Uruchom wszystkie testy
        return run_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
