from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional

Confidence = float

logger = logging.getLogger(__name__)


@dataclass
class FactCandidate:
    text: str
    subject: str
    relation: str
    object: str
    subject_type: Optional[str] = None
    object_type: Optional[str] = None
    confidence: Confidence = 0.6


class FactExtractor:
    """Ekstrakcja faktów i encji z fragmentu tekstu.

    Preferuje spaCy (jeśli zainstalowany i dostępny model), w przeciwnym razie używa
    prostych heurystyk tokenowych."""

    def __init__(self) -> None:
        self._nlp = None
        self._lang = "pl"
        try:  # pragma: no cover - zależne od środowiska
            import spacy

            for model in ("pl_core_news_sm", "pl_core_news_lg", "en_core_web_sm"):
                try:
                    self._nlp = spacy.load(model)
                    self._lang = "pl" if model.startswith("pl_") else "en"
                    logger.info("Załadowano model spaCy: %s", model)
                    break
                except Exception:
                    continue
            if self._nlp is None:
                logger.warning("Nie udało się załadować żadnego modelu spaCy – użyję heurystyk.")
        except Exception as exc:  # pragma: no cover
            logger.warning("spaCy niedostępne (%s) – użyję heurystyk.", exc)

    def extract(self, text: str) -> List[FactCandidate]:
        text = text.strip()
        if not text:
            return []
        if self._nlp is None:
            return self._extract_with_heuristics(text)
        return self._extract_with_spacy(text)

    # --- spaCy pipeline ---

    def _extract_with_spacy(self, text: str) -> List[FactCandidate]:
        doc = self._nlp(text)
        candidates: List[FactCandidate] = []
        for sent in doc.sents:
            sentence = sent.text.strip()
            if len(sentence) < 20:
                continue

            subject = self._first_entity(sent)
            obj = self._second_entity(sent)
            relation = sent.root.lemma_.lower() if sent.root else "powiązany"

            if not subject:
                subject = self._noun_chunk(sent)
            if not obj:
                obj = self._noun_chunk(sent, skip_first=True)
            if not subject or not obj:
                continue

            confidence = 0.6
            if len(sentence) > 40:
                confidence += 0.1
            if self._has_numeric(sent):
                confidence += 0.1
            confidence = min(confidence, 0.95)

            subj_type = self._map_label_to_type(getattr(subject, "label_", None))
            obj_type = self._map_label_to_type(getattr(obj, "label_", None))
            # Jeśli nie rozpoznano typu, spróbuj heurystyki liczby/daty
            if not subj_type and self._looks_like_number(subject.text):
                subj_type = "liczba"
            if not obj_type and self._looks_like_number(obj.text):
                obj_type = "liczba"

            candidates.append(
                FactCandidate(
                    text=sentence,
                    subject=subject.text.strip(),
                    subject_type=subj_type,
                    relation=relation or "powiązany",
                    object=obj.text.strip(),
                    object_type=obj_type,
                    confidence=confidence,
                )
            )
        if not candidates:
            return self._extract_with_heuristics(text)
        return candidates

    def _first_entity(self, sent):
        for ent in sent.ents:
            if ent.text.strip():
                return ent
        return None

    def _second_entity(self, sent):
        ents = [ent for ent in sent.ents if ent.text.strip()]
        if len(ents) >= 2:
            return ents[1]
        return None

    def _noun_chunk(self, sent, skip_first: bool = False):
        try:
            chunks = [chunk for chunk in sent.noun_chunks if chunk.text.strip()]
        except Exception:
            return None
        if skip_first and len(chunks) >= 2:
            return chunks[1]
        return chunks[0] if chunks else None

    def _has_numeric(self, sent) -> bool:
        return any(token.like_num for token in sent)

    def _map_label_to_type(self, label: Optional[str]) -> Optional[str]:
        if not label:
            return None
        label_low = label.lower()
        mapping = {
            # English
            "person": "osoba",
            "org": "organizacja",
            "gpe": "miejsce",
            "loc": "miejsce",
            "date": "data",
            "time": "data",
            "cardinal": "liczba",
            "quantity": "liczba",
            "ordinal": "liczba",
            "percent": "liczba",
            "money": "liczba",
            # Common uppercase spaCy
            "person".upper(): "osoba",
            "org".upper(): "organizacja",
            "gpe".upper(): "miejsce",
            "loc".upper(): "miejsce",
            "date".upper(): "data",
            "time".upper(): "data",
            "cardinal".upper(): "liczba",
            "quantity".upper(): "liczba",
            "ordinal".upper(): "liczba",
            "percent".upper(): "liczba",
            "money".upper(): "liczba",
            # Possible Polish models
            "persname": "osoba",
            "orgname": "organizacja",
            "geogname": "miejsce",
            "placename": "miejsce",
            "num": "liczba",
        }
        # Try exact
        if label in mapping:
            return mapping[label]
        if label_low in mapping:
            return mapping[label_low]
        return None

    def _looks_like_number(self, text: str) -> bool:
        t = text.strip()
        if not t:
            return False
        if any(ch.isdigit() for ch in t):
            return True
        # simple patterns like 12%, 3.14, 1/2
        import re
        return bool(re.match(r"^[0-9]+([\.,][0-9]+)?(%|/[0-9]+)?$", t))

    # --- Heurystyczna wersja fallback ---

    def _extract_with_heuristics(self, text: str) -> List[FactCandidate]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        candidates: List[FactCandidate] = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
            parts = re.split(r"\bjest\b|\bsą\b|\bto\b", sentence, maxsplit=1, flags=re.IGNORECASE)
            if len(parts) == 2:
                subject, rest = parts
                subject = subject.strip(" ,:;-")
                rest = rest.strip()
                object_part = rest.split(",")[0].strip()
                if not subject or not object_part:
                    continue
                candidates.append(
                    FactCandidate(
                        text=sentence,
                        subject=subject,
                        relation="jest",
                        object=object_part,
                        confidence=0.55,
                    )
                )
        return candidates


@lru_cache(maxsize=1)
def get_fact_extractor() -> FactExtractor:
    return FactExtractor()
