from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    provider_name = "abstract"
    model_name = "unknown"
    is_real_llm = False

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 90) -> dict[str, Any]:
    """HTTP helper kept for local providers such as Ollama.

    Groq deliberately does NOT use urllib. The academic demo uses the official
    Groq Python SDK so the provider is isolated behind a stable interface.
    """
    body = json.dumps(payload).encode("utf-8")
    safe_headers = {
        "Accept": "application/json",
        "User-Agent": "CorePulse-IA/373",
        **headers,
    }
    request = urllib.request.Request(url, data=body, headers=safe_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"HTTP {exc.code}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"No fue posible contactar al proveedor: {exc}") from exc


class MockProvider(LLMProvider):
    """Proveedor determinista para tests y dry-run. No cuenta como demo LLM real."""

    provider_name = "mock"
    model_name = "deterministic-test-provider"
    is_real_llm = False

    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "measured_data": {},
                "interpretation": "La interpretación requiere considerar únicamente los datos medidos y las fuentes recuperadas.",
                "retrieved_information": ["Se recuperó información técnica controlada [S1]."],
                "recommendations": ["Verificar condiciones de carga y refrigeración antes de aplicar cambios [S1]."],
                "sources": [],
            },
            ensure_ascii=False,
        )


class GroqProvider(LLMProvider):
    """Proveedor Groq real mediante el SDK oficial `groq`.

    La API key se lee exclusivamente desde GROQ_API_KEY/.env. Nunca se imprime
    ni se incorpora a la evidencia generada.
    """

    provider_name = "groq"
    is_real_llm = True

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model_name = model or os.getenv("GROQ_MODEL", "")
        if not self.api_key:
            raise ProviderError("Falta GROQ_API_KEY.")
        if not self.model_name:
            raise ProviderError("Falta GROQ_MODEL.")

        try:
            from groq import Groq
        except ImportError as exc:  # pragma: no cover - depende del entorno del usuario
            raise ProviderError(
                "Falta el SDK oficial de Groq. Ejecuta 01_PREPARAR_ENTORNO.bat "
                "o instala requirements-isy0101.txt."
            ) from exc
        self._client_cls = Groq

    @staticmethod
    def _safe_provider_error(exc: Exception) -> str:
        status = getattr(exc, "status_code", None)
        body = getattr(exc, "body", None)
        if status is not None:
            detail = ""
            if isinstance(body, dict):
                err = body.get("error", body)
                if isinstance(err, dict):
                    detail = str(err.get("message", ""))
                else:
                    detail = str(err)
            if not detail:
                detail = str(exc)
            detail = detail.replace("\n", " ")[:500]
            return f"Groq HTTP {status}: {detail}"
        return f"Error del proveedor Groq ({type(exc).__name__}): {str(exc)[:500]}"

    def generate(self, prompt: str) -> str:
        try:
            client = self._client_cls(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Responde exclusivamente JSON válido."},
                    {"role": "user", "content": prompt},
                ],
            )
            content = completion.choices[0].message.content
            if not content:
                raise ProviderError("Groq devolvió una respuesta vacía.")
            return str(content)
        except ProviderError:
            raise
        except Exception as exc:  # pragma: no cover - requiere proveedor externo real
            raise ProviderError(self._safe_provider_error(exc)) from exc


class OllamaProvider(LLMProvider):
    provider_name = "ollama"
    is_real_llm = True

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model or os.getenv("OLLAMA_MODEL", "")
        if not self.model_name:
            raise ProviderError("Falta OLLAMA_MODEL.")

    def generate(self, prompt: str) -> str:
        data = _post_json(
            f"{self.base_url}/api/generate",
            {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
            },
            {"Content-Type": "application/json"},
        )
        return str(data["response"])
