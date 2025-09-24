"""
TRACe Service - implementacja metryk TRACe dla oceny systemów RAG
Metryki: Relevance, Utilization, Adherence, Completeness
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class TRACEService:
    """Serwis do obliczania metryk TRACe"""
    
    def __init__(self):
        self.embedding_model = None
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Inicjalizuje model embeddingów dla obliczania podobieństwa semantycznego"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model embeddingów zainicjalizowany dla TRACe")
        except Exception as e:
            logger.warning(f"Nie udało się załadować modelu embeddingów: {e}")
            self.embedding_model = None
    
    def calculate_metrics(self, query: str, response: str, context: Dict[str, Any], 
                         ground_truth: List[str]) -> Dict[str, float]:
        """
        Oblicza wszystkie metryki TRACe
        
        Args:
            query: Zapytanie użytkownika
            response: Wygenerowana odpowiedź
            context: Kontekst wykorzystany do generowania odpowiedzi
            ground_truth: Prawdziwe odpowiedzi (ground truth)
            
        Returns:
            Słownik z metrykami TRACe
        """
        try:
            # Relevance - trafność odpowiedzi względem pytania
            relevance = self._calculate_relevance(query, response)
            
            # Utilization - wykorzystanie kontekstu
            utilization = self._calculate_utilization(response, context)
            
            # Adherence - zgodność z kontekstem (faithfulness)
            adherence = self._calculate_adherence(response, context)
            
            # Completeness - kompletność odpowiedzi
            completeness = self._calculate_completeness(response, ground_truth)
            
            return {
                "relevance": relevance,
                "utilization": utilization,
                "adherence": adherence,
                "completeness": completeness
            }
            
        except Exception as e:
            logger.error(f"Błąd obliczania metryk TRACe: {e}")
            return {
                "relevance": 0.0,
                "utilization": 0.0,
                "adherence": 0.0,
                "completeness": 0.0
            }
    
    def _calculate_relevance(self, query: str, response: str) -> float:
        """
        Oblicza relevance - trafność odpowiedzi względem pytania
        
        Args:
            query: Zapytanie użytkownika
            response: Wygenerowana odpowiedź
            
        Returns:
            Wartość relevance w przedziale [0, 1]
        """
        if not query or not response:
            return 0.0
        
        try:
            if self.embedding_model:
                # Użyj embeddingów semantycznych
                query_embedding = self.embedding_model.encode([query])
                response_embedding = self.embedding_model.encode([response])
                
                similarity = cosine_similarity(query_embedding, response_embedding)[0][0]
                return float(similarity)
            else:
                # Fallback na podobieństwo tokenów
                return self._calculate_token_similarity(query, response)
                
        except Exception as e:
            logger.error(f"Błąd obliczania relevance: {e}")
            return 0.0
    
    def _calculate_utilization(self, response: str, context: Dict[str, Any]) -> float:
        """
        Oblicza utilization - wykorzystanie kontekstu w odpowiedzi
        
        Args:
            response: Wygenerowana odpowiedź
            context: Kontekst wykorzystany do generowania
            
        Returns:
            Wartość utilization w przedziale [0, 1]
        """
        if not response or not context:
            return 0.0
        
        try:
            # Pobierz fragmenty z kontekstu
            fragments = context.get("fragments", [])
            if not fragments:
                return 0.0
            
            # Połącz wszystkie fragmenty w jeden tekst
            context_text = " ".join([f.get("content", "") for f in fragments])
            
            if not context_text:
                return 0.0
            
            # Oblicz podobieństwo między odpowiedzią a kontekstem
            if self.embedding_model:
                response_embedding = self.embedding_model.encode([response])
                context_embedding = self.embedding_model.encode([context_text])
                
                similarity = cosine_similarity(response_embedding, context_embedding)[0][0]
                return float(similarity)
            else:
                return self._calculate_token_similarity(response, context_text)
                
        except Exception as e:
            logger.error(f"Błąd obliczania utilization: {e}")
            return 0.0
    
    def _calculate_adherence(self, response: str, context: Dict[str, Any]) -> float:
        """
        Oblicza adherence - zgodność odpowiedzi z kontekstem (faithfulness)
        
        Args:
            response: Wygenerowana odpowiedź
            context: Kontekst wykorzystany do generowania
            
        Returns:
            Wartość adherence w przedziale [0, 1]
        """
        if not response or not context:
            return 0.0
        
        try:
            # Pobierz fragmenty z kontekstu
            fragments = context.get("fragments", [])
            if not fragments:
                return 0.0
            
            # Sprawdź czy odpowiedź zawiera informacje z kontekstu
            context_sentences = []
            for fragment in fragments:
                content = fragment.get("content", "")
                if content:
                    # Podziel na zdania
                    sentences = self._split_into_sentences(content)
                    context_sentences.extend(sentences)
            
            if not context_sentences:
                return 0.0
            
            # Oblicz podobieństwo między odpowiedzią a każdym zdaniem z kontekstu
            similarities = []
            for sentence in context_sentences:
                if self.embedding_model:
                    response_embedding = self.embedding_model.encode([response])
                    sentence_embedding = self.embedding_model.encode([sentence])
                    
                    similarity = cosine_similarity(response_embedding, sentence_embedding)[0][0]
                    similarities.append(similarity)
                else:
                    similarity = self._calculate_token_similarity(response, sentence)
                    similarities.append(similarity)
            
            # Adherence to maksymalne podobieństwo do kontekstu
            return float(max(similarities)) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Błąd obliczania adherence: {e}")
            return 0.0
    
    def _calculate_completeness(self, response: str, ground_truth: List[str]) -> float:
        """
        Oblicza completeness - kompletność odpowiedzi względem ground truth
        
        Args:
            response: Wygenerowana odpowiedź
            ground_truth: Lista prawdziwych odpowiedzi
            
        Returns:
            Wartość completeness w przedziale [0, 1]
        """
        if not response or not ground_truth:
            return 0.0
        
        try:
            # Sprawdź czy odpowiedź zawiera informacje z ground truth
            similarities = []
            for gt in ground_truth:
                if self.embedding_model:
                    response_embedding = self.embedding_model.encode([response])
                    gt_embedding = self.embedding_model.encode([gt])
                    
                    similarity = cosine_similarity(response_embedding, gt_embedding)[0][0]
                    similarities.append(similarity)
                else:
                    similarity = self._calculate_token_similarity(response, gt)
                    similarities.append(similarity)
            
            # Completeness to maksymalne podobieństwo do ground truth
            return float(max(similarities)) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Błąd obliczania completeness: {e}")
            return 0.0
    
    def _calculate_token_similarity(self, text1: str, text2: str) -> float:
        """
        Oblicza podobieństwo na podstawie tokenów (fallback)
        
        Args:
            text1: Pierwszy tekst
            text2: Drugi tekst
            
        Returns:
            Podobieństwo w przedziale [0, 1]
        """
        if not text1 or not text2:
            return 0.0
        
        # Tokenizacja
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Dzieli tekst na zdania
        
        Args:
            text: Tekst do podziału
            
        Returns:
            Lista zdań
        """
        if not text:
            return []
        
        # Prosty podział na zdania
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def calculate_hallucination_rate(self, responses: List[str], contexts: List[Dict[str, Any]]) -> float:
        """
        Oblicza wskaźnik halucynacji dla listy odpowiedzi
        
        Args:
            responses: Lista odpowiedzi
            contexts: Lista kontekstów
            
        Returns:
            Wskaźnik halucynacji w przedziale [0, 1]
        """
        if not responses or not contexts or len(responses) != len(contexts):
            return 0.0
        
        hallucination_count = 0
        
        for response, context in zip(responses, contexts):
            adherence = self._calculate_adherence(response, context)
            
            # Jeśli adherence < 0.5, uznaj za halucynację
            if adherence < 0.5:
                hallucination_count += 1
        
        return hallucination_count / len(responses)
    
    def calculate_average_metrics(self, results: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Oblicza średnie metryki z listy wyników
        
        Args:
            results: Lista wyników metryk
            
        Returns:
            Średnie metryki
        """
        if not results:
            return {}
        
        metrics = ["relevance", "utilization", "adherence", "completeness"]
        averages = {}
        
        for metric in metrics:
            values = [r.get(metric, 0) for r in results if metric in r]
            averages[metric] = sum(values) / len(values) if values else 0.0
        
        return averages


# Global instance
trace_service = TRACEService()
