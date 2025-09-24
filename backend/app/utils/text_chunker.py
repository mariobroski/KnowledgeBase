"""
Narzędzie do dzielenia tekstu na fragmenty (chunking)
"""
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


class TextChunker:
    """Klasa do dzielenia tekstu na fragmenty"""
    
    def __init__(self, max_chunk_size: Optional[int] = None, overlap: Optional[int] = None):
        """
        Inicjalizacja chunkera
        
        Args:
            max_chunk_size: Maksymalny rozmiar fragmentu w znakach (domyślnie z config)
            overlap: Nakładanie się fragmentów w znakach (domyślnie z config)
        """
        self.max_chunk_size = max_chunk_size or settings.CHUNK_SIZE
        self.overlap = overlap or settings.CHUNK_OVERLAP
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Dzieli tekst na fragmenty
        
        Args:
            text: Tekst do podzielenia
            
        Returns:
            Lista fragmentów z metadanymi
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Najpierw spróbuj podzielić po akapitach
        paragraphs = self._split_by_paragraphs(text)
        
        if len(paragraphs) <= 1:
            # Jeśli nie ma akapitów, podziel po zdaniach
            return self._chunk_by_sentences(text)
        else:
            # Podziel po akapitach, łącząc małe akapity
            return self._chunk_by_paragraphs(paragraphs)
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Dzieli tekst na akapity"""
        # Podziel po podwójnych znakach nowej linii lub po pojedynczych jeśli nie ma podwójnych
        paragraphs = re.split(r'\n\s*\n', text.strip())
        if len(paragraphs) <= 1:
            paragraphs = text.split('\n')
        
        # Usuń puste akapity
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _chunk_by_paragraphs(self, paragraphs: List[str]) -> List[Dict[str, Any]]:
        """Dzieli tekst na fragmenty na podstawie akapitów"""
        chunks = []
        current_chunk = ""
        current_start = 0
        position = 1
        
        for paragraph in paragraphs:
            # Sprawdź czy dodanie tego akapitu nie przekroczy limitu
            if len(current_chunk) + len(paragraph) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Zapisz obecny fragment jeśli nie jest pusty
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'start_position': current_start,
                        'end_position': current_start + len(current_chunk),
                        'position': position
                    })
                    position += 1
                    current_start += len(current_chunk) - self.overlap
                
                # Rozpocznij nowy fragment
                current_chunk = paragraph
        
        # Dodaj ostatni fragment
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'start_position': current_start,
                'end_position': current_start + len(current_chunk),
                'position': position
            })
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Dzieli tekst na fragmenty na podstawie zdań"""
        # Prosty podział po zdaniach
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            # Jeśli nie można podzielić po zdaniach, podziel na równe części
            return self._chunk_by_size(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        position = 1
        
        for sentence in sentences:
            # Sprawdź czy dodanie tego zdania nie przekroczy limitu
            if len(current_chunk) + len(sentence) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                # Zapisz obecny fragment jeśli nie jest pusty
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'start_position': current_start,
                        'end_position': current_start + len(current_chunk),
                        'position': position
                    })
                    position += 1
                    current_start += len(current_chunk) - self.overlap
                
                # Rozpocznij nowy fragment
                current_chunk = sentence
        
        # Dodaj ostatni fragment
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'start_position': current_start,
                'end_position': current_start + len(current_chunk),
                'position': position
            })
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[Dict[str, Any]]:
        """Dzieli tekst na fragmenty o stałym rozmiarze"""
        chunks = []
        position = 1
        
        for i in range(0, len(text), self.max_chunk_size - self.overlap):
            chunk_text = text[i:i + self.max_chunk_size]
            if chunk_text.strip():
                chunks.append({
                    'content': chunk_text.strip(),
                    'start_position': i,
                    'end_position': i + len(chunk_text),
                    'position': position
                })
                position += 1
        
        return chunks