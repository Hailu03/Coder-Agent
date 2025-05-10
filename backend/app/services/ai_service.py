import os
import logging
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from openai import OpenAI

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

class GeminiService(AIService):
    """Google Gemini AI service using google-genai SDK."""

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY 
        if not self.api_key:
            raise ValueError("Gemini API key is required")

        self.model_name = model or settings.GEMINI_MODEL
        if self.model_name is None:
            logger.warning("No Gemini model specified, using default model: gemini-2.0-flash")
            self.model_name = "gemini-2.0-flash"

        # Initialize the google-genai client
        self.client = genai.Client(api_key=self.api_key)

        logger.info(f"Initialized GeminiService with model: {self.model_name}")

    async def generate_text(self, prompt: str) -> str:
        try:
            # Use async client for non-streaming generation
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            # Extract text from first candidate
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            return f"Error generating text: {e}"

    async def generate_structured_output(
        self, prompt: str, output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Kiểm tra tất cả các giá trị đầu vào
            if prompt is None:
                logger.error("Prompt cannot be None in generate_structured_output")
                return {}

            if self.model_name is None:
                logger.error("Model name cannot be None in generate_structured_output")
                return {}
            
            # Sử dụng tính năng structured output của Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                    # Truyền schema dưới dạng dictionary
                    response_schema=output_schema
                ),
            )
            
            # Xử lý kết quả
            if hasattr(response, 'parsed') and response.parsed is not None:
                # Trả về kết quả đã phân tích
                return response.parsed
            elif hasattr(response, 'text') and response.text:
                # Nếu không có parsed, thử parse từ text
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse response text as JSON, returning text")
                    return {"result": response.text}
            
            # Fallback
            logger.warning("No valid structured output received, returning empty dict")
            return {}
            
        except Exception as e:
            logger.error(f"Error generating structured output with Gemini: {e}")
            return {}

class OpenAIService(AIService):
    """OpenAI service."""

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.model_name = model or settings.OPENAI_MODEL
        
        # Only pass the required parameters to avoid issues with proxies or other parameters
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAIService with model: {self.model_name}")

    async def generate_text(self, prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model_name,
                input=prompt
            )

            return response.output_text
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return f"Error generating text: {e}"

    async def generate_structured_output(
        self, prompt: str, output_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            response = self.client.responses.parse(
                model=self.model_name,
                input=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}    
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "structured_output",
                        "schema": output_schema,
                        "strict": True
                    }
                }
            )

            if response and hasattr(response, 'output_text'):
                # Try to parse the output text as JSON
                try:
                    return json.loads(response.output_text)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse response text as JSON, returning text")
                    return {"result": response.output_text}
            elif response and hasattr(response, 'text'):
                # If no valid structured output, try to parse from text
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse response text as JSON, returning text")
                    return {"result": response.text}
            else:
                logger.warning("No valid structured output received, returning empty dict")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return {}            
        except Exception as e:
            logger.error(f"Error generating structured output with OpenAI: {e}")
            return {}


def get_ai_service() -> AIService:
    """Get the appropriate AI service based on configuration.
    
    This function prioritizes the environment variable AI_PROVIDER over
    the settings.AI_PROVIDER to ensure the most recent configuration is used.
    
    Returns:
        An instance of the appropriate AIService implementation
    """
    # Đọc trực tiếp từ biến môi trường để đảm bảo lấy giá trị mới nhất
    provider = os.environ.get("AI_PROVIDER", "").lower()
    
    # Nếu không có trong biến môi trường, sử dụng giá trị từ settings
    if not provider:
        provider = settings.AI_PROVIDER.lower()
    
    logger.info(f"Using AI provider: {provider}")
    
    # Khởi tạo service phù hợp dựa trên provider
    if provider == "openai":
        # Sử dụng OpenAI
        return OpenAIService()
    elif provider == "gemini":
        # Sử dụng Gemini
        return GeminiService()
    else:
        # Provider không hợp lệ, sử dụng OpenAI làm mặc định
        logger.warning(f"Unknown AI provider '{provider}', defaulting to OpenAI")
        return OpenAIService()
