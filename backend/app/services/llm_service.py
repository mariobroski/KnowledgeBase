from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str
    model: str
    usage: Dict[str, Any]
    raw: Dict[str, Any]


class LLMService:
    """Minimalny klient LLM z obsługą Ollama.

    Zaprojektowany tak, aby był bezpieczny: jeśli brak konfiguracji,
    serwis pozostaje nieaktywny i zwraca fallback na poziomie wyższych warstw.
    """

    def __init__(self) -> None:
        self.provider = (settings.LLM_PROVIDER or "").strip().lower()
        self.model = (settings.LLM_MODEL or "").strip()
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/") if settings.OLLAMA_BASE_URL else ""
        self.tgi_base_url = settings.TGI_BASE_URL.rstrip("/") if settings.TGI_BASE_URL else ""
        self.hf_token = settings.HF_TOKEN
        self._client: Optional[httpx.Client] = None
        self._enabled = False
        self._active_provider: Optional[str] = None
        self._init_client()

    def _init_client(self) -> None:
        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        preferred_provider = self.provider or "tgi"
        providers_to_try = [preferred_provider]
        if preferred_provider != "tgi":
            providers_to_try.append("tgi")
        if preferred_provider != "ollama":
            providers_to_try.append("ollama")

        self._enabled = False
        for candidate in providers_to_try:
            if candidate == "tgi" and self.tgi_base_url:
                if self._try_init_tgi(headers):
                    self._active_provider = "tgi"
                    self.model = self.model or settings.TGI_MODEL_ID or "tgi-model"
                    return
            if candidate == "ollama" and self.ollama_base_url and (self.model or settings.LLM_MODEL):
                if self._try_init_ollama():
                    self._active_provider = "ollama"
                    self.model = self.model or settings.LLM_MODEL or ""
                    return

        self._enabled = False
        if self._client:
            self._client.close()
        self._client = None
        self._active_provider = None

    def _try_init_ollama(self) -> bool:
        client: Optional[httpx.Client] = None
        try:
            client = httpx.Client(base_url=self.ollama_base_url, timeout=30.0)
            resp = client.get("/api/tags")
            if resp.status_code < 500:
                self._client = client
                self._enabled = True
                logger.info("LLMService: Ollama detected at %s (model=%s)", self.ollama_base_url, self.model or settings.LLM_MODEL)
                return True
        except Exception as exc:
            logger.warning("LLMService init failed (Ollama): %s", exc)
        finally:
            if not self._enabled and client:
                client.close()
        return False

    def _try_init_tgi(self, headers: Dict[str, str]) -> bool:
        client: Optional[httpx.Client] = None
        try:
            client = httpx.Client(base_url=self.tgi_base_url, timeout=60.0, headers=headers)
            resp = client.get("/health")
            if resp.status_code == 200:
                self._client = client
                self._enabled = True
                logger.info("LLMService: TGI detected at %s (%s)", self.tgi_base_url, self.model or settings.TGI_MODEL_ID)
                return True
        except Exception as exc:
            logger.warning("LLMService init failed (TGI): %s", exc)
        finally:
            if not self._enabled and client:
                client.close()
        return False

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResult:
        if not self.is_enabled or not self._client:
            raise RuntimeError("LLMService disabled")

        provider = self._active_provider or self.provider

        if provider == "ollama":
            payload: Dict[str, Any] = {
                "model": self.model,
                "prompt": self._build_prompt(system, prompt),
                "stream": False,
                "options": {
                    "temperature": float(temperature),
                    # Ollama używa parametru `num_predict` zamiast `max_tokens`
                    "num_predict": int(max_tokens),
                },
            }
            resp = self._client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "").strip()
            usage = {
                "prompt_tokens": data.get("prompt_eval_count"),
                "completion_tokens": data.get("eval_count"),
                "total_tokens": None,
            }
            if usage["prompt_tokens"] is not None and usage["completion_tokens"] is not None:
                usage["total_tokens"] = int(usage["prompt_tokens"]) + int(usage["completion_tokens"])
            return LLMResult(text=text, model=self.model, usage=usage, raw=data)

        if provider == "tgi":
            # TGI expects the combined prompt in "inputs"
            payload = {
                "inputs": self._build_prompt(system, prompt),
                "parameters": {
                    "temperature": float(temperature),
                    "max_new_tokens": int(max_tokens),
                },
            }
            resp = self._client.post("/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = (data.get("generated_text") or "").strip()
            details = data.get("details", {})
            usage = {
                "prompt_tokens": details.get("prompt_tokens"),
                "completion_tokens": details.get("generated_tokens"),
                "total_tokens": None,
            }
            if usage["prompt_tokens"] is not None and usage["completion_tokens"] is not None:
                usage["total_tokens"] = int(usage["prompt_tokens"]) + int(usage["completion_tokens"])
            model_name = self.model or settings.TGI_MODEL_ID or "tgi-model"
            return LLMResult(text=text, model=model_name, usage=usage, raw=data)

        raise RuntimeError(f"Unsupported provider: {provider}")

    @staticmethod
    def _build_prompt(system: Optional[str], user: str) -> str:
        if system:
            return f"System: {system}\n\nUser: {user}\nAssistant:"
        return user


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService()
