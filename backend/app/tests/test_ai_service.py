import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from ..services.ai_service import GeminiService

@pytest.mark.asyncio
async def test_generate_text_with_mcp():
    # Mock settings
    mock_settings = {
        "MCP_URL": "http://mock-mcp-server",
        "GEMINI_API_KEY": "mock-api-key",
        "GEMINI_MODEL": "mock-model",
    }

    # Patch settings and dependencies
    with patch("..services.ai_service.settings", mock_settings), \
         patch("..services.ai_service.sse_client") as mock_sse_client, \
         patch("..services.ai_service.ClientSession") as mock_client_session, \
         patch("..services.ai_service.genai.Client") as mock_genai_client:

        # Mock SSE client and session
        mock_read_stream = AsyncMock()
        mock_write_stream = AsyncMock()
        mock_sse_client.return_value.__aenter__.return_value = (mock_read_stream, mock_write_stream)

        mock_session = AsyncMock()
        mock_client_session.return_value.__aenter__.return_value = mock_session

        # Mock genai client
        mock_genai_instance = mock_genai_client.return_value
        mock_genai_instance.aio.models.generate_content.return_value = AsyncMock(
            candidates=[
                AsyncMock(
                    content=AsyncMock(
                        parts=[
                            AsyncMock(text="Generated text from MCP")
                        ]
                    )
                )
            ]
        )

        # Initialize GeminiService
        service = GeminiService()

        # Call the method
        result = await service.generate_text_with_mcp("Test prompt")

        # Assertions
        assert result == "Generated text from MCP"
        mock_sse_client.assert_called_once_with(
            url="http://mock-mcp-server",
            headers={
                "Authorization": "Bearer mock-api-key",
                "Content-Type": "application/json",
            },
        )
        mock_genai_instance.aio.models.generate_content.assert_called()
        mock_session.initialize.assert_called_once()
        mock_session.list_tools.assert_called_once()