#!/usr/bin/env python3
"""
Zaawansowane metryki ewaluacji RAG
- Hallucination Detection
- Factual Accuracy
- Context Utilization Analysis
- Response Quality Scoring
"""

import logging
import re
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from collections import Counter
import json

logger = logging.getLogger(__name__)


@dataclass
class AdvancedMetrics:
    """Zaawansowane metryki ewaluacji"""
    hallucination_score: float
    factual_accuracy: float
    context_utilization: float
    response_quality: float
    coherence_score: float
    fluency_score: float
    specificity_score: float
    completeness_score: float


class AdvancedEvaluator:
    """Zaawansowany ewaluator metryk RAG"""
    
    def __init__(self):
        self.embedding_model = None
        self.nlp = None
        self._initialize_models()
        
        # Słowniki do wykrywania halucynacji
        self.hallucination_indicators = [
            "nie wiem", "nie jestem pewien", "prawdopodobnie", "może",
            "wydaje mi się", "być może", "nie mam pewności"
        ]
        
        # Wzorce halucynacji
        self.hallucination_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # Daty
            r"\$\d+",  # Kwoty
            r"\d+%",  # Procenty
            r"\d+\.\d+",  # Liczby dziesiętne
        ]
    
    def _initialize_models(self):
        """Inicjalizuje modele NLP"""
        try:
            # Model embeddingów
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model embeddingów zainicjalizowany")
        except Exception as e:
            logger.warning(f"Nie udało się załadować modelu embeddingów: {e}")
        
        try:
            # Model spaCy
            self.nlp = spacy.load("pl_core_news_sm")
            logger.info("Model spaCy zainicjalizowany")
        except Exception as e:
            logger.warning(f"Nie udało się załadować modelu spaCy: {e}")
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Model spaCy (en) zainicjalizowany")
            except Exception as e2:
                logger.warning(f"Nie udało się załadować modelu spaCy (en): {e2}")
    
    def calculate_advanced_metrics(
        self, 
        query: str, 
        response: str, 
        context: Dict[str, Any], 
        ground_truth: List[str]
    ) -> AdvancedMetrics:
        """
        Oblicza zaawansowane metryki ewaluacji
        
        Args:
            query: Zapytanie użytkownika
            response: Wygenerowana odpowiedź
            context: Kontekst wykorzystany
            ground_truth: Prawdziwe odpowiedzi
            
        Returns:
            Zaawansowane metryki
        """
        try:
            # Wykrywanie halucynacji
            hallucination_score = self._detect_hallucinations(response, context)
            
            # Dokładność faktyczna
            factual_accuracy = self._calculate_factual_accuracy(response, ground_truth)
            
            # Wykorzystanie kontekstu
            context_utilization = self._calculate_context_utilization(response, context)
            
            # Jakość odpowiedzi
            response_quality = self._calculate_response_quality(response)
            
            # Spójność
            coherence_score = self._calculate_coherence(response)
            
            # Płynność
            fluency_score = self._calculate_fluency(response)
            
            # Specyficzność
            specificity_score = self._calculate_specificity(response, query)
            
            # Kompletność
            completeness_score = self._calculate_completeness(response, ground_truth)
            
            return AdvancedMetrics(
                hallucination_score=hallucination_score,
                factual_accuracy=factual_accuracy,
                context_utilization=context_utilization,
                response_quality=response_quality,
                coherence_score=coherence_score,
                fluency_score=fluency_score,
                specificity_score=specificity_score,
                completeness_score=completeness_score
            )
            
        except Exception as e:
            logger.error(f"Błąd obliczania zaawansowanych metryk: {e}")
            return AdvancedMetrics(
                hallucination_score=0.0,
                factual_accuracy=0.0,
                context_utilization=0.0,
                response_quality=0.0,
                coherence_score=0.0,
                fluency_score=0.0,
                specificity_score=0.0,
                completeness_score=0.0
            )
    
    def _detect_hallucinations(self, response: str, context: Dict[str, Any]) -> float:
        """
        Wykrywa halucynacje w odpowiedzi
        
        Args:
            response: Odpowiedź do analizy
            context: Kontekst wykorzystany
            
        Returns:
            Wskaźnik halucynacji (0-1, gdzie 1 = brak halucynacji)
        """
        if not response or not context:
            return 0.0
        
        # Pobierz fragmenty z kontekstu
        fragments = context.get("fragments", [])
        if not fragments:
            return 0.0
        
        # Połącz kontekst
        context_text = " ".join([f.get("content", "") for f in fragments])
        
        # Sprawdź podobieństwo semantyczne
        if self.embedding_model:
            try:
                response_embedding = self.embedding_model.encode([response])
                context_embedding = self.embedding_model.encode([context_text])
                
                similarity = cosine_similarity(response_embedding, context_embedding)[0][0]
                
                # Sprawdź wskaźniki halucynacji
                hallucination_indicators = sum(1 for indicator in self.hallucination_indicators 
                                             if indicator.lower() in response.lower())
                
                # Sprawdź wzorce halucynacji
                hallucination_patterns = sum(1 for pattern in self.hallucination_patterns 
                                          if re.search(pattern, response))
                
                # Oblicz wskaźnik halucynacji
                hallucination_score = similarity * (1 - hallucination_indicators * 0.1) * (1 - hallucination_patterns * 0.05)
                
                return max(0.0, min(1.0, hallucination_score))
                
            except Exception as e:
                logger.error(f"Błąd wykrywania halucynacji: {e}")
                return 0.0
        
        # Fallback na podobieństwo tokenów
        return self._calculate_token_similarity(response, context_text)
    
    def _calculate_factual_accuracy(self, response: str, ground_truth: List[str]) -> float:
        """
        Oblicza dokładność faktyczną
        
        Args:
            response: Odpowiedź do analizy
            ground_truth: Prawdziwe odpowiedzi
            
        Returns:
            Dokładność faktyczna (0-1)
        """
        if not response or not ground_truth:
            return 0.0
        
        # Sprawdź czy odpowiedź zawiera informacje z ground truth
        max_similarity = 0.0
        
        for gt in ground_truth:
            if self.embedding_model:
                try:
                    response_embedding = self.embedding_model.encode([response])
                    gt_embedding = self.embedding_model.encode([gt])
                    
                    similarity = cosine_similarity(response_embedding, gt_embedding)[0][0]
                    max_similarity = max(max_similarity, similarity)
                except Exception:
                    similarity = self._calculate_token_similarity(response, gt)
                    max_similarity = max(max_similarity, similarity)
            else:
                similarity = self._calculate_token_similarity(response, gt)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _calculate_context_utilization(self, response: str, context: Dict[str, Any]) -> float:
        """
        Oblicza wykorzystanie kontekstu
        
        Args:
            response: Odpowiedź do analizy
            context: Kontekst wykorzystany
            
        Returns:
            Wykorzystanie kontekstu (0-1)
        """
        if not response or not context:
            return 0.0
        
        # Pobierz fragmenty z kontekstu
        fragments = context.get("fragments", [])
        if not fragments:
            return 0.0
        
        # Sprawdź ile fragmentów jest wykorzystanych
        utilized_fragments = 0
        
        for fragment in fragments:
            content = fragment.get("content", "")
            if content:
                # Sprawdź czy fragment jest wykorzystany w odpowiedzi
                if self._is_fragment_utilized(response, content):
                    utilized_fragments += 1
        
        return utilized_fragments / len(fragments) if fragments else 0.0
    
    def _is_fragment_utilized(self, response: str, fragment: str) -> bool:
        """Sprawdza czy fragment jest wykorzystany w odpowiedzi"""
        if not response or not fragment:
            return False
        
        # Sprawdź podobieństwo semantyczne
        if self.embedding_model:
            try:
                response_embedding = self.embedding_model.encode([response])
                fragment_embedding = self.embedding_model.encode([fragment])
                
                similarity = cosine_similarity(response_embedding, fragment_embedding)[0][0]
                return similarity > 0.7  # Próg wykorzystania
            except Exception:
                pass
        
        # Fallback na podobieństwo tokenów
        similarity = self._calculate_token_similarity(response, fragment)
        return similarity > 0.5
    
    def _calculate_response_quality(self, response: str) -> float:
        """
        Oblicza jakość odpowiedzi
        
        Args:
            response: Odpowiedź do analizy
            
        Returns:
            Jakość odpowiedzi (0-1)
        """
        if not response:
            return 0.0
        
        # Sprawdź długość odpowiedzi
        length_score = min(1.0, len(response.split()) / 50)  # Optymalna długość ~50 słów
        
        # Sprawdź strukturę odpowiedzi
        structure_score = self._analyze_response_structure(response)
        
        # Sprawdź czytelność
        readability_score = self._calculate_readability(response)
        
        # Średnia ważona
        quality_score = (length_score * 0.3 + structure_score * 0.4 + readability_score * 0.3)
        
        return max(0.0, min(1.0, quality_score))
    
    def _analyze_response_structure(self, response: str) -> float:
        """Analizuje strukturę odpowiedzi"""
        if not response:
            return 0.0
        
        # Sprawdź czy odpowiedź ma strukturę
        has_intro = any(word in response.lower() for word in ["odpowiedź", "wynik", "rezultat"])
        has_conclusion = any(word in response.lower() for word in ["podsumowując", "wniosek", "zakończenie"])
        has_details = len(response.split()) > 10
        
        structure_score = sum([has_intro, has_conclusion, has_details]) / 3
        return structure_score
    
    def _calculate_readability(self, response: str) -> float:
        """Oblicza czytelność odpowiedzi"""
        if not response:
            return 0.0
        
        # Prosta metryka czytelności
        words = response.split()
        sentences = response.count('.') + response.count('!') + response.count('?')
        
        if sentences == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Optymalna liczba słów na zdanie: 15-20
        if 15 <= avg_words_per_sentence <= 20:
            return 1.0
        elif 10 <= avg_words_per_sentence <= 25:
            return 0.8
        elif 5 <= avg_words_per_sentence <= 30:
            return 0.6
        else:
            return 0.4
    
    def _calculate_coherence(self, response: str) -> float:
        """Oblicza spójność odpowiedzi"""
        if not response or not self.nlp:
            return 0.0
        
        try:
            doc = self.nlp(response)
            
            # Sprawdź spójność semantyczną
            sentences = [sent.text for sent in doc.sents]
            if len(sentences) < 2:
                return 1.0
            
            # Oblicz podobieństwo między zdaniami
            similarities = []
            for i in range(len(sentences) - 1):
                if self.embedding_model:
                    try:
                        sent1_embedding = self.embedding_model.encode([sentences[i]])
                        sent2_embedding = self.embedding_model.encode([sentences[i + 1]])
                        
                        similarity = cosine_similarity(sent1_embedding, sent2_embedding)[0][0]
                        similarities.append(similarity)
                    except Exception:
                        similarity = self._calculate_token_similarity(sentences[i], sentences[i + 1])
                        similarities.append(similarity)
                else:
                    similarity = self._calculate_token_similarity(sentences[i], sentences[i + 1])
                    similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Błąd obliczania spójności: {e}")
            return 0.0
    
    def _calculate_fluency(self, response: str) -> float:
        """Oblicza płynność odpowiedzi"""
        if not response:
            return 0.0
        
        # Sprawdź płynność na podstawie wzorców językowych
        fluency_indicators = [
            r'\b(ale|jednak|ponadto|dodatkowo|więc|zatem)\b',  # Spójniki
            r'\b(przede wszystkim|po pierwsze|po drugie)\b',  # Struktura
            r'\b(na przykład|na przykład|czyli)\b',  # Przykłady
        ]
        
        fluency_score = 0.0
        for pattern in fluency_indicators:
            matches = len(re.findall(pattern, response, re.IGNORECASE))
            fluency_score += min(1.0, matches / 3)  # Normalizacja
        
        return min(1.0, fluency_score / len(fluency_indicators))
    
    def _calculate_specificity(self, response: str, query: str) -> float:
        """Oblicza specyficzność odpowiedzi względem zapytania"""
        if not response or not query:
            return 0.0
        
        # Sprawdź czy odpowiedź jest specyficzna dla zapytania
        if self.embedding_model:
            try:
                response_embedding = self.embedding_model.encode([response])
                query_embedding = self.embedding_model.encode([query])
                
                similarity = cosine_similarity(response_embedding, query_embedding)[0][0]
                return similarity
            except Exception:
                pass
        
        # Fallback na podobieństwo tokenów
        return self._calculate_token_similarity(response, query)
    
    def _calculate_completeness(self, response: str, ground_truth: List[str]) -> float:
        """Oblicza kompletność odpowiedzi"""
        if not response or not ground_truth:
            return 0.0
        
        # Sprawdź czy odpowiedź pokrywa wszystkie aspekty ground truth
        coverage_scores = []
        
        for gt in ground_truth:
            if self.embedding_model:
                try:
                    response_embedding = self.embedding_model.encode([response])
                    gt_embedding = self.embedding_model.encode([gt])
                    
                    similarity = cosine_similarity(response_embedding, gt_embedding)[0][0]
                    coverage_scores.append(similarity)
                except Exception:
                    similarity = self._calculate_token_similarity(response, gt)
                    coverage_scores.append(similarity)
            else:
                similarity = self._calculate_token_similarity(response, gt)
                coverage_scores.append(similarity)
        
        return np.mean(coverage_scores) if coverage_scores else 0.0
    
    def _calculate_token_similarity(self, text1: str, text2: str) -> float:
        """Oblicza podobieństwo na podstawie tokenów"""
        if not text1 or not text2:
            return 0.0
        
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def generate_quality_report(self, metrics: AdvancedMetrics) -> Dict[str, Any]:
        """
        Generuje raport jakości na podstawie metryk
        
        Args:
            metrics: Zaawansowane metryki
            
        Returns:
            Raport jakości
        """
        # Ocena jakości
        quality_level = "Excellent"
        if metrics.hallucination_score < 0.8:
            quality_level = "Good"
        if metrics.hallucination_score < 0.6:
            quality_level = "Fair"
        if metrics.hallucination_score < 0.4:
            quality_level = "Poor"
        
        # Rekomendacje
        recommendations = []
        
        if metrics.hallucination_score < 0.7:
            recommendations.append("Zwiększ weryfikację faktów w odpowiedzi")
        
        if metrics.context_utilization < 0.6:
            recommendations.append("Lepiej wykorzystuj dostępny kontekst")
        
        if metrics.coherence_score < 0.7:
            recommendations.append("Popraw spójność odpowiedzi")
        
        if metrics.fluency_score < 0.6:
            recommendations.append("Popraw płynność językową")
        
        return {
            "quality_level": quality_level,
            "overall_score": np.mean([
                metrics.hallucination_score,
                metrics.factual_accuracy,
                metrics.context_utilization,
                metrics.response_quality,
                metrics.coherence_score,
                metrics.fluency_score,
                metrics.specificity_score,
                metrics.completeness_score
            ]),
            "recommendations": recommendations,
            "detailed_metrics": {
                "hallucination_score": metrics.hallucination_score,
                "factual_accuracy": metrics.factual_accuracy,
                "context_utilization": metrics.context_utilization,
                "response_quality": metrics.response_quality,
                "coherence_score": metrics.coherence_score,
                "fluency_score": metrics.fluency_score,
                "specificity_score": metrics.specificity_score,
                "completeness_score": metrics.completeness_score
            }
        }


# Global instance
advanced_evaluator = AdvancedEvaluator()
