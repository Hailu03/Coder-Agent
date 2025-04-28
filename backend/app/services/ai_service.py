import os
import logging
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from openai import AsyncOpenAI

from ..core.config import settings
from ..utils import extract_json_from_text
from mcp.client.sse import sse_client
from mcp import ClientSession

# Configure logging
logger = logging.getLogger("services.ai_service")


class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    async def generate_structured_output(
        self, prompt: str, output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output from a prompt."""
        pass

    @abstractmethod
    async def generate_text_with_mcp(self, prompt: str) -> str:
        """Generate text with structured output using MCP."""
        pass


class GeminiService(AIService):
    """Google Gemini AI service using google-genai SDK."""

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")

        self.model_name = model or settings.GEMINI_MODEL

        # Initialize the google-genai client
        self.client = genai.Client(api_key=self.api_key)

        logger.info(f"Initialized GeminiService with model: {self.model_name}")

    async def generate_text(self, prompt: str) -> str:
        try:
            # Use async client for non-streaming generation
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            # Extract text from first candidate
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return f"Error generating text: {e}"

    async def generate_text_with_mcp(self, prompt: str) -> str:
        try:
            # Connect to MCP server via SSE transport
            async with sse_client(
                url=settings.MCP_URL,
                headers=None
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    mcp_tools = await session.list_tools()
                    # Map to google-genai Tool objects
                    tools = [
                        types.Tool(
                            function_declarations=[
                                {
                                    "name": t.name,
                                    "description": t.description,
                                    "parameters": {
                                        k: v for k, v in t.inputSchema.items()
                                        if k not in ["additionalProperties", "$schema"]
                                    },
                                }
                            ]
                        )
                        for t in mcp_tools.tools
                    ]
                    # Request with tools
                    response = await self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.6,
                            tools=tools,
                        ),
                    )
                    content = response.candidates[0].content.parts[0]
                    if content.function_call:
                        fc = content.function_call
                        result = await session.call_tool(fc.name, arguments=fc.args)
                        # Build after-function call conversation
                        user_parts = [types.Part.from_text(prompt)]
                        func_call_part = types.Part(function_call=fc)
                        func_resp_part = types.Part.from_function_response(
                            name=fc.name, response={"result": result}
                        )
                        conv = [
                            types.Content(role="user", parts=user_parts),
                            types.Content(role="model", parts=[func_call_part]),
                            types.Content(role="function", parts=[func_resp_part]),
                        ]
                        follow = await self.client.aio.models.generate_content(
                            model=self.model_name,
                            contents=conv,
                            config=types.GenerateContentConfig(temperature=0.6),
                        )
                        return follow.candidates[0].content.parts[0].text
                    return content.text
        except Exception as e:
            logger.error(f"Error in generate_text_with_mcp: {e}")
            return f"Error generating text with MCP: {e}"

    async def generate_structured_output(
        self, prompt: str, output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        schema_str = json.dumps(output_schema, indent=2)
        full_prompt = (
            f"{prompt}\nPlease respond ONLY with JSON matching schema:\n{schema_str}"
        )
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(temperature=0.7),
                )
                text = response.candidates[0].content.parts[0].text
                data = extract_json_from_text(text)
                if data or attempt == max_retries:
                    return data
                logger.warning(
                    f"JSON extraction failed, retry {attempt + 1}/{max_retries}"
                )
            except Exception as e:
                logger.error(f"Attempt {attempt+1} error: {e}")
        return {}


class OpenAIService(AIService):
    """OpenAI service."""

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.model_name = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAIService with model: {self.model_name}")

    async def generate_text(self, prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return f"Error generating text: {e}"

    async def generate_structured_output(
        self, prompt: str, output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content or "{}")
        except Exception as e:
            logger.error(f"Error generating structured output with OpenAI: {e}")
            return {}


def get_ai_service() -> AIService:
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini":
        return GeminiService()
    if provider == "openai":
        return OpenAIService()
    logger.warning("Unknown AI provider, defaulting to Gemini.")
    return GeminiService()
