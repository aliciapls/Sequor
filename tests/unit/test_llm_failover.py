"""Unit tests for LLM failover to escalation."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from sequor.ai.client import OllamaClient, safe_generate


class TestSafeGenerate:
    @pytest.mark.asyncio
    async def test_returns_content_on_success(self):
        client = AsyncMock(spec=OllamaClient)
        client.generate = AsyncMock(return_value="This is a FAQ about pricing.")

        result = await safe_generate(client, "Classify this message...")

        assert result.content == "This is a FAQ about pricing."
        assert result.should_escalate is False
        assert result.error is None

    @pytest.mark.asyncio
    async def test_routes_to_escalation_on_runtime_error(self):
        client = AsyncMock(spec=OllamaClient)
        client.generate = AsyncMock(
            side_effect=RuntimeError("Ollama service unavailable")
        )

        result = await safe_generate(client, "Classify this message...")

        assert result.content == ""
        assert result.should_escalate is True
        assert "Ollama service unavailable" in result.error

    @pytest.mark.asyncio
    async def test_routes_to_escalation_on_connect_error(self):
        client = AsyncMock(spec=OllamaClient)
        client.generate = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await safe_generate(client, "Classify this message...")

        assert result.content == ""
        assert result.should_escalate is True
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_routes_to_escalation_on_http_error(self):
        client = AsyncMock(spec=OllamaClient)
        request = MagicMock()
        response = MagicMock()
        response.status_code = 500
        client.generate = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server error", request=request, response=response
            )
        )

        result = await safe_generate(client, "Classify this message...")

        assert result.content == ""
        assert result.should_escalate is True

    @pytest.mark.asyncio
    async def test_routes_to_escalation_on_unexpected_error(self):
        client = AsyncMock(spec=OllamaClient)
        client.generate = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        result = await safe_generate(client, "Classify this message...")

        assert result.content == ""
        assert result.should_escalate is True
