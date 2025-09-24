import re
from typing import Dict, List, Tuple
from enum import Enum

class PolicyType(str, Enum):
    TEXT = "text"
    FACTS = "facts"
    GRAPH = "graph"

class PolicySelector:
    """Serwis do automatycznego wyboru polityki RAG na podstawie analizy zapytania"""
    
    def __init__(self):
        # Słowa kluczowe dla różnych typów zapytań
        self.fact_keywords = [
            # Pytania o fakty
            "co to jest", "czym jest", "kim jest", "gdzie", "kiedy", "ile", "jak dużo",
            "definicja", "znaczenie", "data", "rok", "liczba", "wartość", "procent",
            "statystyka", "fakt", "prawda", "czy prawda", "czy to prawda",
            
            # Pytania o konkretne informacje
            "jaka jest", "jaki jest", "jakie są", "które", "który", "która",
            "nazwa", "tytuł", "autor", "twórca", "założyciel", "prezes", "dyrektor",
            "stolica", "powierzchnia", "populacja", "mieszkańcy", "ludność",
            
            # Pytania weryfikacyjne
            "czy", "prawda czy fałsz", "tak czy nie", "potwierdź", "sprawdź"
        ]
        
        self.graph_keywords = [
            # Pytania o relacje
            "związek", "relacja", "powiązanie", "połączenie", "zależność",
            "wpływ", "oddziaływanie", "skutek", "przyczyna", "konsekwencja",
            "między", "pomiędzy", "a", "oraz", "i", "razem z", "w kontekście",
            
            # Pytania o struktury i hierarchie
            "struktura", "organizacja", "hierarchia", "podział", "klasyfikacja",
            "kategoria", "typ", "rodzaj", "grupa", "klasa", "zespół",
            
            # Pytania porównawcze
            "porównaj", "różnica", "podobieństwo", "kontrast", "zestawienie",
            "lepszy", "gorszy", "większy", "mniejszy", "szybszy", "wolniejszy",
            
            # Pytania o ścieżki i połączenia
            "jak dojść", "droga", "ścieżka", "połączenie", "link", "most",
            "jak się łączy", "jak wpływa", "jak oddziałuje"
        ]
        
        self.text_keywords = [
            # Pytania opisowe
            "opisz", "wyjaśnij", "przedstaw", "scharakteryzuj", "omów",
            "jak działa", "jak funkcjonuje", "jak przebiega", "mechanizm",
            "proces", "procedura", "sposób", "metoda", "technika",
            
            # Pytania o kontekst
            "kontekst", "tło", "historia", "rozwój", "ewolucja", "geneza",
            "pochodzenie", "źródło", "podstawa", "fundament",
            
            # Pytania otwarte
            "dlaczego", "po co", "w jakim celu", "cel", "powód", "motyw",
            "znaczenie", "rola", "funkcja", "zadanie", "misja"
        ]
    
    def analyze_query(self, query: str) -> Dict[str, float]:
        """Analizuje zapytanie i zwraca prawdopodobieństwa dla każdej polityki"""
        query_lower = query.lower()
        
        # Inicjalizacja wyników
        scores = {
            PolicyType.TEXT: 0.0,
            PolicyType.FACTS: 0.0,
            PolicyType.GRAPH: 0.0
        }
        
        # Analiza słów kluczowych
        fact_score = self._calculate_keyword_score(query_lower, self.fact_keywords)
        graph_score = self._calculate_keyword_score(query_lower, self.graph_keywords)
        text_score = self._calculate_keyword_score(query_lower, self.text_keywords)
        
        # Analiza struktury pytania
        structure_scores = self._analyze_question_structure(query_lower)
        
        # Kombinacja wyników
        scores[PolicyType.FACTS] = fact_score * 0.7 + structure_scores['facts'] * 0.3
        scores[PolicyType.GRAPH] = graph_score * 0.7 + structure_scores['graph'] * 0.3
        scores[PolicyType.TEXT] = text_score * 0.7 + structure_scores['text'] * 0.3
        
        # Normalizacja wyników
        total_score = sum(scores.values())
        if total_score > 0:
            for policy in scores:
                scores[policy] = scores[policy] / total_score
        else:
            # Domyślnie TekstRAG jeśli nie ma jasnych wskaźników
            scores[PolicyType.TEXT] = 1.0
        
        return scores
    
    def _calculate_keyword_score(self, query: str, keywords: List[str]) -> float:
        """Oblicza wynik na podstawie występowania słów kluczowych"""
        score = 0.0
        query_words = query.split()
        
        for keyword in keywords:
            if keyword in query:
                # Bonus za dokładne dopasowanie frazy
                score += 2.0
            else:
                # Sprawdź czy słowa z frazy występują w zapytaniu
                keyword_words = keyword.split()
                matches = sum(1 for word in keyword_words if word in query_words)
                if matches > 0:
                    score += matches / len(keyword_words)
        
        return score
    
    def _analyze_question_structure(self, query: str) -> Dict[str, float]:
        """Analizuje strukturę pytania"""
        scores = {'facts': 0.0, 'graph': 0.0, 'text': 0.0}
        
        # Pytania zamknięte (tak/nie) -> FaktRAG
        if re.search(r'\bczy\b.*\?', query) or query.startswith('czy '):
            scores['facts'] += 1.0
        
        # Pytania o konkretne wartości -> FaktRAG
        if re.search(r'\b(ile|jak dużo|jak długo|jak wysoko)\b', query):
            scores['facts'] += 1.0
        
        # Pytania z "między", "a" -> GrafRAG
        if re.search(r'\b(między|pomiędzy).*\ba\b', query):
            scores['graph'] += 1.5
        
        # Pytania porównawcze -> GrafRAG
        if re.search(r'\b(porównaj|różnica|podobieństwo)\b', query):
            scores['graph'] += 1.0
        
        # Pytania opisowe -> TekstRAG
        if re.search(r'\b(opisz|wyjaśnij|jak działa|dlaczego)\b', query):
            scores['text'] += 1.0
        
        # Długie pytania -> TekstRAG
        if len(query.split()) > 10:
            scores['text'] += 0.5
        
        return scores
    
    def select_policy(self, query: str, confidence_threshold: float = 0.6) -> Tuple[str, float, Dict[str, float]]:
        """
        Wybiera najlepszą politykę dla zapytania
        
        Args:
            query: Zapytanie użytkownika
            confidence_threshold: Próg pewności dla automatycznego wyboru
            
        Returns:
            Tuple zawierający (wybraną_politykę, pewność, wszystkie_wyniki)
        """
        scores = self.analyze_query(query)
        
        # Znajdź politykę z najwyższym wynikiem
        best_policy = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_policy]
        
        # Jeśli pewność jest niska, domyślnie wybierz TekstRAG
        if confidence < confidence_threshold:
            best_policy = PolicyType.TEXT
            confidence = scores[PolicyType.TEXT]
        
        return best_policy, confidence, scores
    
    def get_policy_explanation(self, selected_policy: str, confidence: float, all_scores: Dict[str, float]) -> str:
        """Generuje wyjaśnienie wyboru polityki"""
        
        policy_names = {
            "text": "TekstRAG",
            "facts": "FaktRAG", 
            "graph": "GrafRAG"
        }
        
        selected_name = policy_names.get(selected_policy, selected_policy)
        
        if confidence >= 0.8:
            confidence_desc = "bardzo wysoką"
        elif confidence >= 0.6:
            confidence_desc = "wysoką"
        elif confidence >= 0.4:
            confidence_desc = "średnią"
        else:
            confidence_desc = "niską"
            
        # Znajdź drugą najlepszą politykę
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        second_best = sorted_scores[1] if len(sorted_scores) > 1 else None
        
        explanation = f"Wybrano {selected_name} z {confidence_desc} pewnością ({confidence:.1%})."
        
        if second_best and confidence - second_best[1] < 0.2:
            second_name = policy_names.get(second_best[0], second_best[0])
            explanation += f" {second_name} była bliska alternatywą ({second_best[1]:.1%})."
        
        return explanation