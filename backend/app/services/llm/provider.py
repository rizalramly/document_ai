"""Abstract LLM provider and Ollama implementation."""

from __future__ import annotations
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Any
from pathlib import Path

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache (upgradeable to Redis)
_llm_cache: dict[str, Any] = {}


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", images: list[str] | None = None,
                       temperature: float = 0.1) -> str:
        """Generate text completion."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts."""
        ...

    @abstractmethod
    async def chat(self, messages: list[dict], system: str = "",
                   temperature: float = 0.1) -> str:
        """Multi-turn chat completion."""
        ...


class OllamaProvider(LLMProvider):
    """Ollama HTTP API implementation."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.vision_model = settings.ollama_vision_model
        self.embed_model = settings.ollama_embed_model
        self.chat_model = settings.ollama_chat_model
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    def _cache_key(self, model: str, prompt: str, images: list | None = None) -> str:
        data = f"{model}:{prompt}:{images or ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def generate(self, prompt: str, system: str = "", images: list[str] | None = None,
                       temperature: float | None = None) -> str:
        """Generate using Ollama /api/generate."""
        temp = temperature if temperature is not None else settings.ollama_temperature
        model = self.vision_model if images else self.chat_model

        cache_key = self._cache_key(model, prompt, images)
        if cache_key in _llm_cache:
            logger.debug("LLM cache hit")
            return _llm_cache[cache_key]

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temp}
        }
        if images:
            payload["images"] = images  # base64-encoded images

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            result = resp.json().get("response", "")

        _llm_cache[cache_key] = result
        return result

    async def embed(self, text: str) -> list[float]:
        """Generate embedding using Ollama /api/embed."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/embed", json={
                "model": self.embed_model,
                "input": text
            })
            resp.raise_for_status()
            data = resp.json()
            # Ollama returns {"embeddings": [[...]]}
            embeddings = data.get("embeddings", [[]])
            return embeddings[0] if embeddings else []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed by calling embed() for each text."""
        results = []
        for text in texts:
            vec = await self.embed(text)
            results.append(vec)
        return results

    async def chat(self, messages: list[dict], system: str = "",
                   temperature: float | None = None) -> str:
        """Chat completion using Ollama /api/chat."""
        temp = temperature if temperature is not None else settings.ollama_temperature
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json={
                "model": self.chat_model,
                "messages": all_messages,
                "stream": False,
                "options": {"temperature": temp}
            })
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")

    async def health_check(self) -> bool:
        """Check Ollama connectivity."""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


# Singleton
llm_provider = OllamaProvider()
