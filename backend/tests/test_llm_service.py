import os
import sys
from pathlib import Path

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://localhost:3000"]')

import app.services.llm_service as llm_module


class FakeResponse:
    def __init__(self, status_code: int = 200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "HTTP error",
                request=httpx.Request("GET", "http://test"),
                response=httpx.Response(self.status_code),
            )


def build_settings(
    provider: str,
    *,
    tgi_base: str = "http://tgi:8080",
    ollama_base: str = "http://ollama:11434",
    model: str = "",
    tgi_model_id: str = "test-model",
    hf_token: str = "",
):
    class _Settings:
        LLM_PROVIDER = provider
        LLM_MODEL = model
        OLLAMA_BASE_URL = ollama_base
        TGI_BASE_URL = tgi_base
        TGI_MODEL_ID = tgi_model_id
        HF_TOKEN = hf_token

        # Attributes not used directly in tests but expected by service when
        # updating defaults on fallback.
        TGI_NUM_SHARD = 1
        TGI_MAX_BATCH_PREFILL_TOKENS = 4096
        TGI_MAX_INPUT_LENGTH = 4096
        TGI_MAX_TOTAL_TOKENS = 8192

    return _Settings()


def test_llm_service_prefers_tgi(monkeypatch):
    calls = {"health": 0, "generate": 0}

    class FakeTGIClient:
        def __init__(self, base_url, timeout, headers=None, **kwargs):
            assert base_url == "http://tgi:8080"
            self.base_url = base_url
            self.timeout = timeout
            self.headers = headers or {}

        def get(self, path):
            if path == "/health":
                calls["health"] += 1
                return FakeResponse(200)
            raise AssertionError(f"Unexpected GET {path}")

        def post(self, path, json=None, **kwargs):
            assert path == "/generate"
            calls["generate"] += 1
            return FakeResponse(
                200,
                {
                    "generated_text": "hello from tgi",
                    "details": {"prompt_tokens": 5, "generated_tokens": 3},
                },
            )

        def close(self):
            pass

    monkeypatch.setattr(llm_module, "settings", build_settings("tgi", model=""))
    monkeypatch.setattr(llm_module.httpx, "Client", lambda *args, **kwargs: FakeTGIClient(*args, **kwargs))

    service = llm_module.LLMService()

    assert service.is_enabled
    result = service.generate("Cześć", system="System prompt", temperature=0.2, max_tokens=64)
    assert result.text == "hello from tgi"
    assert result.model == "test-model"
    assert result.usage["prompt_tokens"] == 5
    assert result.usage["completion_tokens"] == 3
    assert calls == {"health": 1, "generate": 1}


def test_llm_service_falls_back_to_ollama(monkeypatch):
    calls = {"tgi_health": 0, "ollama_tags": 0, "ollama_generate": 0}

    class FailingTGIClient:
        def __init__(self, base_url, timeout, headers=None, **kwargs):
            assert base_url == "http://tgi:8080"

        def get(self, path):
            if path == "/health":
                calls["tgi_health"] += 1
                return FakeResponse(503)
            raise AssertionError(f"Unexpected GET {path}")

        def close(self):
            pass

    class OllamaClient:
        def __init__(self, base_url, timeout, headers=None, **kwargs):
            assert base_url == "http://ollama:11434"

        def get(self, path):
            if path == "/api/tags":
                calls["ollama_tags"] += 1
                return FakeResponse(200)
            raise AssertionError(f"Unexpected GET {path}")

        def post(self, path, json=None, **kwargs):
            if path == "/api/generate":
                calls["ollama_generate"] += 1
                return FakeResponse(
                    200,
                    {
                        "response": "hello from ollama",
                        "prompt_eval_count": 7,
                        "eval_count": 4,
                    },
                )
            raise AssertionError(f"Unexpected POST {path}")

        def close(self):
            pass

    def fake_client_factory(base_url, timeout, headers=None, **kwargs):
        if base_url == "http://tgi:8080":
            return FailingTGIClient(base_url, timeout, headers=headers, **kwargs)
        if base_url == "http://ollama:11434":
            return OllamaClient(base_url, timeout, headers=headers, **kwargs)
        raise AssertionError(f"Unexpected base_url {base_url}")

    monkeypatch.setattr(llm_module, "settings", build_settings("tgi", model="llama3"))
    monkeypatch.setattr(llm_module.httpx, "Client", fake_client_factory)

    service = llm_module.LLMService()

    assert service.is_enabled
    result = service.generate("Hello")
    assert result.text == "hello from ollama"
    assert result.model == "llama3"
    assert result.usage["total_tokens"] == 11
    assert calls == {"tgi_health": 1, "ollama_tags": 1, "ollama_generate": 1}
