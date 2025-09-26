from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import numpy as np

try:  # pragma: no cover - zależne od środowiska
    import joblib
except Exception as exc:  # pragma: no cover
    joblib = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class MLPolicyRouter:
    """Wybór polityki RAG z wykorzystaniem wytrenowanego modelu ML."""

    def __init__(self, model_path: str) -> None:
        if joblib is None:
            raise RuntimeError("joblib is required to load the policy router model")

        resolved = Path(model_path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Brak pliku modelu polityki RAG: {resolved}")

        payload: Dict[str, Any] = joblib.load(resolved)

        self.vectorizer = payload.get("vectorizer")
        self.model = payload.get("model")
        self.label_encoder = payload.get("label_encoder")
        self.labels: Optional[Iterable[str]] = payload.get("labels")

        if self.vectorizer is None or self.model is None:
            raise ValueError("Plik modelu musi zawierać klucze 'vectorizer' i 'model'")

        if not hasattr(self.model, "predict"):
            raise ValueError("Obiekt modelu musi implementować metodę predict/predict_proba")

        logger.info("Załadowano model ML policy routera z %s", resolved)

    def predict_proba(self, query: str) -> Dict[str, float]:
        """Zwraca rozkład prawdopodobieństw polityk RAG dla zapytania."""
        features = self.vectorizer.transform([query])

        if hasattr(self.model, "predict_proba"):
            raw_probs = self.model.predict_proba(features)[0]
        else:  # pragma: no cover - fallback dla modeli bez predict_proba
            decision = self.model.decision_function(features)
            if decision.ndim == 1:
                decision = np.vstack([-decision, decision])
            raw_probs = _softmax(decision)[0]

        label_names = self._get_label_names()
        probs: Dict[str, float] = {label: 0.0 for label in label_names}

        for label, prob in zip(self._model_classes(), raw_probs):
            label_str = str(label)
            probs[label_str] = float(prob)

        # Normalizacja do sumy 1 (zabezpieczenie przed błędami zaokrągleń)
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}

        return probs

    def predict(self, query: str) -> str:
        label = self.model.predict(self.vectorizer.transform([query]))[0]
        return str(label)

    def _get_label_names(self) -> Iterable[str]:
        if self.labels:
            return list(self.labels)
        if self.label_encoder is not None and hasattr(self.label_encoder, "classes_"):
            return [str(c) for c in self.label_encoder.classes_]
        if hasattr(self.model, "classes_"):
            return [str(c) for c in self.model.classes_]
        return ["text", "facts", "graph"]

    def _model_classes(self) -> Iterable[str]:
        if hasattr(self.model, "classes_"):
            return [str(c) for c in self.model.classes_]
        if self.label_encoder is not None and hasattr(self.label_encoder, "classes_"):
            return [str(c) for c in self.label_encoder.classes_]
        if self.labels:
            return list(self.labels)
        raise ValueError("Model nie udostępnia informacji o klasach")


def _softmax(x: np.ndarray) -> np.ndarray:
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / e_x.sum(axis=-1, keepdims=True)

