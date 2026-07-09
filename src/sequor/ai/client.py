"""LLM clients — local (Ollama) and cloud (MiniMax) generation + embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from sequor.config import settings

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------


class OllamaClient:
    """Client for Ollama local AI service.

    Handles both LLM generation and embedding generation using Ollama's API.
    Falls back gracefully when Ollama is not available.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.llm_model
        self.embedding_model = embedding_model or settings.embedding_model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text using the LLM."""
        client = await self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        logger.info("ollama.generate.start", model=self.model, prompt_length=len(prompt))

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            logger.info(
                "ollama.generate.ok",
                model=self.model,
                response_length=len(content),
            )
            return content
        except httpx.HTTPStatusError as e:
            logger.error("ollama.generate.error", status=e.response.status_code)
            raise
        except httpx.ConnectError:
            logger.warning("ollama.generate.unavailable", base_url=self.base_url)
            raise RuntimeError(
                f"Ollama service unavailable at {self.base_url}. Please ensure Ollama is running."
            ) from None

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings. Tries Ollama first, falls back to OpenAI."""
        try:
            return await self._generate_ollama_embeddings(texts)
        except (httpx.ConnectError, RuntimeError):
            logger.warning("ollama.embedding.unavailable, falling back to OpenAI")
            return await self._generate_openai_embeddings(texts)

    async def _generate_ollama_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Ollama. Raises on failure."""
        client = await self._get_client()
        embeddings = []
        for text in texts:
            payload = {"model": self.embedding_model, "prompt": text}
            logger.debug(
                "ollama.embedding.start", model=self.embedding_model, text_length=len(text)
            )
            try:
                response = await client.post("/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                embeddings.append(embedding)
            except httpx.HTTPStatusError as e:
                logger.error(
                    "ollama.embedding.error", status=e.response.status_code, text_length=len(text)
                )
                raise
            except httpx.ConnectError:
                logger.warning("ollama.embedding.unreachable", base_url=self.base_url)
                raise
        logger.info("ollama.embedding.ok", model=self.embedding_model, text_count=len(texts))
        return embeddings

    async def _generate_openai_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via OpenAI API."""
        if not settings.openai_api_key:
            logger.warning("openai.embedding.skipped", reason="OPENAI_API_KEY not set")
            raise RuntimeError("OpenAI API key not configured")
        import openai

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        embeddings = []
        for text in texts:
            logger.debug(
                "openai.embedding.start",
                model=settings.openai_embedding_model,
                text_length=len(text),
            )
            try:
                resp = await client.embeddings.create(
                    model=settings.openai_embedding_model,
                    input=text,
                )
                embedding = resp.data[0].embedding
                embeddings.append(embedding)
            except Exception as e:
                logger.warning("openai.embedding.failed", error=str(e))
                raise RuntimeError(f"OpenAI embedding failed: {e}") from e
        logger.info(
            "openai.embedding.ok", model=settings.openai_embedding_model, text_count=len(texts)
        )
        return embeddings

    async def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# MiniMax provider (OpenAI-compatible cloud API)
# ---------------------------------------------------------------------------


class MiniMaxClient:
    """Client for MiniMax cloud LLM service.

    MiniMax provides an OpenAI-compatible chat completions API.
    Embeddings are delegated to OpenAI (MiniMax does not currently offer embeddings).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.minimax_api_key
        self.model = model or settings.minimax_model
        self.base_url = base_url or settings.minimax_base_url
        self.embedding_model = embedding_model or settings.embedding_model
        self._client: Any = None  # openai.AsyncOpenAI

    def _get_client(self) -> Any:
        """Get or create the OpenAI-compatible client pointed at MiniMax."""
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text via MiniMax chat completions API."""
        client = self._get_client()

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        logger.info("minimax.generate.start", model=self.model, prompt_length=len(prompt))

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            logger.info(
                "minimax.generate.ok",
                model=self.model,
                response_length=len(content),
            )
            return content
        except Exception as e:
            logger.error("minimax.generate.error", error=str(e))
            raise RuntimeError(f"MiniMax generation failed: {e}") from e

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via OpenAI (MiniMax does not offer embeddings).

        Falls back to Ollama if OpenAI is not configured.
        """
        # Try OpenAI first
        if settings.openai_api_key:
            import openai

            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            embeddings: list[list[float]] = []
            for text in texts:
                logger.debug(
                    "openai.embedding.start",
                    model=settings.openai_embedding_model,
                    text_length=len(text),
                )
                try:
                    resp = await client.embeddings.create(
                        model=settings.openai_embedding_model,
                        input=text,
                    )
                    embeddings.append(resp.data[0].embedding)
                except Exception as e:
                    logger.warning("openai.embedding.failed", error=str(e))
                    raise RuntimeError(f"OpenAI embedding failed: {e}") from e
            logger.info(
                "openai.embedding.ok",
                model=settings.openai_embedding_model,
                text_count=len(texts),
            )
            return embeddings

        # Fall back to Ollama for embeddings
        logger.warning("minimax.embedding.fallback_to_ollama")
        ollama = OllamaClient(embedding_model=self.embedding_model)
        return await ollama._generate_ollama_embeddings(texts)

    async def is_available(self) -> bool:
        """Check if MiniMax API is reachable."""
        try:
            client = self._get_client()
            # Lightweight probe — list models (or just check connectivity)
            await client.models.list()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Global client factory
# ---------------------------------------------------------------------------

_client: OllamaClient | MiniMaxClient | None = None


def get_llm_client() -> OllamaClient | MiniMaxClient:
    """Get or create the LLM client based on settings.llm_provider."""
    global _client
    if _client is None:
        if settings.llm_provider == "minimax":
            logger.info("llm.client.init", provider="minimax", model=settings.minimax_model)
            _client = MiniMaxClient()
        else:
            logger.info("llm.client.init", provider="ollama", model=settings.llm_model)
            _client = OllamaClient()
    return _client


# Backward-compatible alias — used throughout the codebase
get_ollama_client = get_llm_client


# ---------------------------------------------------------------------------
# Safe generation helper
# ---------------------------------------------------------------------------


@dataclass
class LLMResult:
    """Result from LLM generation with escalation routing signal."""

    content: str
    should_escalate: bool
    error: str | None = None


async def safe_generate(
    client: OllamaClient | MiniMaxClient,
    prompt: str,
    system: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> LLMResult:
    """Generate text with graceful fallback to escalation on LLM failure.

    Returns an LLMResult with should_escalate=True when the LLM fails,
    allowing callers to route to escalation without try/except at every call site.
    """
    try:
        content = await client.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResult(content=content, should_escalate=False)
    except (RuntimeError, httpx.HTTPStatusError, httpx.ConnectError) as e:
        logger.warning(
            "llm.generate.failed_routing_to_escalation",
            error=str(e),
            error_type=type(e).__name__,
        )
        return LLMResult(content="", should_escalate=True, error=str(e))
    except Exception as e:
        logger.error(
            "llm.generate.unexpected_error_routing_to_escalation",
            error=str(e),
            error_type=type(e).__name__,
        )
        return LLMResult(content="", should_escalate=True, error=str(e))
