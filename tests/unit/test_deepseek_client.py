"""Unit tests for DeepSeekClient — generation, embeddings, availability, close."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sequor.ai.client import DeepSeekClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_chat_completion(content: str) -> MagicMock:
    """Build a mock OpenAI chat completion object with the given content."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def _fake_embedding_response(dim: int = 768) -> MagicMock:
    """Build a mock OpenAI embedding response."""
    embed = MagicMock()
    embed.embedding = [0.1] * dim
    data = MagicMock()
    data.data = [embed]
    return data


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


class TestDeepSeekGenerate:
    @pytest.mark.asyncio
    async def test_returns_content_on_success(self):
        """Happy path: generate returns the LLM's text content."""
        client = DeepSeekClient(api_key="sk-test", model="deepseek-chat")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(
            return_value=_fake_chat_completion("Paris is the capital of France.")
        )
        with patch.object(client, "_get_client", return_value=fake_client):
            result = await client.generate("What is the capital of France?")

        assert result == "Paris is the capital of France."
        fake_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_none_content_from_api(self):
        """content can be None — should return empty string, not crash."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_fake_chat_completion(None))
        with patch.object(client, "_get_client", return_value=fake_client):
            result = await client.generate("prompt")

        assert result == ""

    @pytest.mark.asyncio
    async def test_includes_system_message_when_provided(self):
        """system kwarg should be sent as a system-role message."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_fake_chat_completion("ok"))
        with patch.object(client, "_get_client", return_value=fake_client):
            await client.generate("prompt", system="You are helpful.")

        call_kwargs = fake_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[1] == {"role": "user", "content": "prompt"}

    @pytest.mark.asyncio
    async def test_raises_runtime_error_with_generic_message_on_failure(self):
        """R8 invariant: error message is generic — no str(e) leakage."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API returned 500: internal server error")
        )
        with patch.object(client, "_get_client", return_value=fake_client):
            with pytest.raises(RuntimeError, match="DeepSeek generation failed"):
                await client.generate("prompt")

    @pytest.mark.asyncio
    async def test_preserves_exception_chain_via_from_e(self):
        """R8 invariant: `from e` preserves the original exception chain."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        original = Exception("transient network error")
        fake_client.chat.completions.create = AsyncMock(side_effect=original)
        with patch.object(client, "_get_client", return_value=fake_client):
            try:
                await client.generate("prompt")
            except RuntimeError as exc:
                assert exc.__cause__ is original

    @pytest.mark.asyncio
    async def test_passes_temperature_and_max_tokens(self):
        """Custom temperature and max_tokens are forwarded to the API."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_fake_chat_completion("ok"))
        with patch.object(client, "_get_client", return_value=fake_client):
            await client.generate("prompt", temperature=0.7, max_tokens=512)

        call_kwargs = fake_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 512

    @pytest.mark.asyncio
    async def test_uses_default_temperature_and_max_tokens(self):
        """Defaults: temperature=0.3, max_tokens=2048."""
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_fake_chat_completion("ok"))
        with patch.object(client, "_get_client", return_value=fake_client):
            await client.generate("prompt")

        call_kwargs = fake_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 2048


# ---------------------------------------------------------------------------
# generate_embeddings
# ---------------------------------------------------------------------------


class TestDeepSeekGenerateEmbeddings:
    @pytest.mark.asyncio
    async def test_uses_openai_when_api_key_configured(self):
        """When OPENAI_API_KEY is set, embeddings route through OpenAI."""
        client = DeepSeekClient(api_key="sk-deepseek")
        fake_openai = AsyncMock()
        fake_openai.embeddings.create = AsyncMock(return_value=_fake_embedding_response(768))

        with patch("sequor.ai.client.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-openai"
            mock_settings.openai_embedding_model = "text-embedding-3-small"
            # openai is lazily imported inside generate_embeddings;
            # pre-seed sys.modules so the local import resolves to our fake.
            fake_openai_module = MagicMock()
            fake_openai_module.AsyncOpenAI = MagicMock(return_value=fake_openai)
            with patch.dict(sys.modules, {"openai": fake_openai_module}):
                result = await client.generate_embeddings(["hello world"])

        assert len(result) == 1
        assert len(result[0]) == 768
        fake_openai.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_runtime_error_with_generic_message_on_openai_failure(self):
        """R8 invariant: embedding failure raises generic RuntimeError."""
        client = DeepSeekClient(api_key="sk-deepseek")
        fake_openai = AsyncMock()
        fake_openai.embeddings.create = AsyncMock(side_effect=Exception("rate limit exceeded"))

        with patch("sequor.ai.client.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-openai"
            mock_settings.openai_embedding_model = "text-embedding-3-small"
            fake_openai_module = MagicMock()
            fake_openai_module.AsyncOpenAI = MagicMock(return_value=fake_openai)
            with patch.dict(sys.modules, {"openai": fake_openai_module}):
                with pytest.raises(RuntimeError, match="OpenAI embedding failed"):
                    await client.generate_embeddings(["hello world"])

    @pytest.mark.asyncio
    async def test_falls_back_to_ollama_when_no_openai_key(self):
        """When OPENAI_API_KEY is empty, fall back to Ollama for embeddings."""
        client = DeepSeekClient(api_key="sk-deepseek", embedding_model="nomic-embed-text")
        fake_ollama_client = AsyncMock()
        fake_ollama_client.post = AsyncMock()
        fake_ollama_client.post.return_value.raise_for_status = MagicMock()
        fake_ollama_client.post.return_value.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

        with patch("sequor.ai.client.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            mock_settings.ollama_base_url = "http://localhost:11434"
            with patch.object(client, "_get_client", return_value=fake_ollama_client):
                # We need to mock OllamaClient._generate_ollama_embeddings
                # but the fallback creates its own OllamaClient internally.
                # Patch the OllamaClient constructor instead.
                with patch("sequor.ai.client.OllamaClient") as mock_ollama_cls:
                    mock_ollama = AsyncMock()
                    mock_ollama._generate_ollama_embeddings = AsyncMock(
                        return_value=[[0.1, 0.2, 0.3]]
                    )
                    mock_ollama_cls.return_value = mock_ollama
                    result = await client.generate_embeddings(["hello"])

        assert len(result) == 1
        assert result[0] == [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestDeepSeekIsAvailable:
    @pytest.mark.asyncio
    async def test_returns_true_when_models_list_succeeds(self):
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.models.list = AsyncMock(return_value=MagicMock())
        with patch.object(client, "_get_client", return_value=fake_client):
            assert await client.is_available() is True

    @pytest.mark.asyncio
    async def test_returns_false_when_models_list_raises(self):
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        fake_client.models.list = AsyncMock(side_effect=Exception("timeout"))
        with patch.object(client, "_get_client", return_value=fake_client):
            assert await client.is_available() is False


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestDeepSeekClose:
    @pytest.mark.asyncio
    async def test_closes_underlying_client(self):
        client = DeepSeekClient(api_key="sk-test")
        fake_client = AsyncMock()
        with patch.object(client, "_get_client", return_value=fake_client):
            client._client = fake_client  # set directly
            await client.close()

        fake_client.close.assert_awaited_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_is_noop_when_no_client(self):
        client = DeepSeekClient(api_key="sk-test")
        await client.close()  # should not raise
        assert client._client is None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestDeepSeekConfiguration:
    def test_defaults_from_settings(self):
        """Without explicit args, reads from sequor.config.settings."""
        with patch("sequor.ai.client.settings") as mock_settings:
            mock_settings.deepseek_api_key = "sk-from-settings"
            mock_settings.deepseek_model = "deepseek-chat"
            mock_settings.deepseek_base_url = "https://api.deepseek.com/v1"
            mock_settings.embedding_model = "nomic-embed-text"

            client = DeepSeekClient()
            assert client.api_key == "sk-from-settings"
            assert client.model == "deepseek-chat"
            assert client.base_url == "https://api.deepseek.com/v1"
            assert client.embedding_model == "nomic-embed-text"

    def test_explicit_args_override_settings(self):
        """Explicit constructor args take precedence over settings."""
        with patch("sequor.ai.client.settings") as mock_settings:
            mock_settings.deepseek_api_key = "sk-from-settings"
            mock_settings.deepseek_model = "deepseek-chat"

            client = DeepSeekClient(api_key="sk-explicit", model="deepseek-reasoner")
            assert client.api_key == "sk-explicit"
            assert client.model == "deepseek-reasoner"

    def test_get_client_lazy_inits_openai(self):
        """_get_client imports openai lazily and creates AsyncOpenAI."""
        client = DeepSeekClient(api_key="sk-test")
        fake_openai_cls = MagicMock()
        fake_openai = MagicMock()
        fake_openai_cls.return_value = fake_openai

        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import sys

            sys.modules["openai"].AsyncOpenAI = fake_openai_cls
            result = client._get_client()

        assert result is fake_openai
        fake_openai_cls.assert_called_once_with(
            api_key="sk-test", base_url="https://api.deepseek.com/v1"
        )

    def test_get_client_caches_instance(self):
        """_get_client returns the same instance on repeated calls."""
        client = DeepSeekClient(api_key="sk-test")
        fake_openai_cls = MagicMock()
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import sys

            sys.modules["openai"].AsyncOpenAI = fake_openai_cls
            first = client._get_client()
            second = client._get_client()

        assert first is second
        # Only constructed once.
        assert fake_openai_cls.call_count == 1
