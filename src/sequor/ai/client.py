"""Ollama client for local LLM and embedding generation."""

import httpx
import structlog

from sequor.config import settings

logger = structlog.get_logger()


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
        """Generate text using the LLM.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
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
        """Generate embeddings for texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        client = await self._get_client()

        embeddings = []
        for text in texts:
            payload = {
                "model": self.embedding_model,
                "prompt": text,
            }

            logger.debug(
                "ollama.embedding.start",
                model=self.embedding_model,
                text_length=len(text),
            )

            try:
                response = await client.post("/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                embeddings.append(embedding)
            except httpx.HTTPStatusError as e:
                logger.error(
                    "ollama.embedding.error",
                    status=e.response.status_code,
                    text_length=len(text),
                )
                raise
            except httpx.ConnectError:
                logger.warning("ollama.embedding.unavailable", base_url=self.base_url)
                raise RuntimeError(
                    f"Ollama service unavailable at {self.base_url}. "
                    "Please ensure Ollama is running."
                ) from None

        logger.info(
            "ollama.embedding.ok",
            model=self.embedding_model,
            text_count=len(texts),
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


# Global client instance
_ollama_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    """Get or create the global Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
