#!/usr/bin/env python3
"""
Test script for KnowledgeBase infrastructure
Tests all services: PostgreSQL, Qdrant, JanusGraph, Ollama, Redis
"""

import asyncio
import sys
import time
from typing import Dict, List, Tuple

import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
import redis
from gremlinpython.driver import client as gremlin_client


class InfrastructureTester:
    """Test all infrastructure components"""
    
    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.errors: Dict[str, str] = {}
    
    def test_postgres(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="postgres",
                database="rag_system"
            )
            conn.close()
            print("✅ PostgreSQL: Connected successfully")
            return True
        except Exception as e:
            print(f"❌ PostgreSQL: {e}")
            self.errors["postgres"] = str(e)
            return False
    
    def test_qdrant(self) -> bool:
        """Test Qdrant connection"""
        try:
            client = QdrantClient(host="localhost", port=6333)
            collections = client.get_collections()
            print("✅ Qdrant: Connected successfully")
            return True
        except Exception as e:
            print(f"❌ Qdrant: {e}")
            self.errors["qdrant"] = str(e)
            return False
    
    def test_janusgraph(self) -> bool:
        """Test JanusGraph connection"""
        try:
            client = gremlin_client.Client(
                'ws://localhost:8182/gremlin', 'g'
            )
            result = client.submit('g.V().limit(1)').all().result()
            client.close()
            print("✅ JanusGraph: Connected successfully")
            return True
        except Exception as e:
            print(f"❌ JanusGraph: {e}")
            self.errors["janusgraph"] = str(e)
            return False
    
    def test_redis(self) -> bool:
        """Test Redis connection"""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis: Connected successfully")
            return True
        except Exception as e:
            print(f"❌ Redis: {e}")
            self.errors["redis"] = str(e)
            return False
    
    def test_ollama(self) -> bool:
        """Test Ollama connection"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama: Connected successfully")
                return True
            else:
                print(f"❌ Ollama: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ollama: {e}")
            self.errors["ollama"] = str(e)
            return False
    
    def test_tgi(self) -> bool:
        """Test TGI connection"""
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                print("✅ TGI: Connected successfully")
                return True
            else:
                print(f"❌ TGI: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ TGI: {e}")
            self.errors["tgi"] = str(e)
            return False
    
    def test_weaviate(self) -> bool:
        """Test Weaviate connection"""
        try:
            response = requests.get("http://localhost:8080/v1/meta", timeout=5)
            if response.status_code == 200:
                print("✅ Weaviate: Connected successfully")
                return True
            else:
                print(f"❌ Weaviate: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Weaviate: {e}")
            self.errors["weaviate"] = str(e)
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all infrastructure tests"""
        print("🔍 Testing KnowledgeBase Infrastructure...")
        print("=" * 50)
        
        # Core services
        self.results["postgres"] = self.test_postgres()
        self.results["qdrant"] = self.test_qdrant()
        self.results["janusgraph"] = self.test_janusgraph()
        self.results["redis"] = self.test_redis()
        
        # LLM services
        self.results["ollama"] = self.test_ollama()
        self.results["tgi"] = self.test_tgi()
        
        # Alternative services
        self.results["weaviate"] = self.test_weaviate()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 INFRASTRUCTURE TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\n🔧 FAILED SERVICES:")
            for service, error in self.errors.items():
                print(f"  • {service}: {error}")
        
        print("\n🚀 NEXT STEPS:")
        if failed_tests == 0:
            print("  • All services are running correctly!")
            print("  • You can now start the backend and frontend")
        else:
            print("  • Start missing services with: docker-compose -f docker-compose-open-source.yml up -d")
            print("  • Check service logs: docker-compose -f docker-compose-open-source.yml logs <service>")
            print("  • Wait for services to fully initialize (especially JanusGraph and TGI)")


def main():
    """Main test function"""
    tester = InfrastructureTester()
    
    print("⏳ Waiting 5 seconds for services to initialize...")
    time.sleep(5)
    
    results = tester.run_all_tests()
    tester.print_summary()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All infrastructure tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
