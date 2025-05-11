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

        # Import fix helper
        try:
            from .ai_service_fix import gemini_structured_output
            self._structured_output_helper = gemini_structured_output
            logger.info("Loaded Gemini compatibility fixes")
        except ImportError:
            logger.warning("Could not load Gemini compatibility fixes")
            self._structured_output_helper = None

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
            
            # Xử lý schema để tương thích với Gemini
            # Loại bỏ additionalProperties: False để tránh lỗi validation
            cleaned_schema = self._clean_schema_for_gemini(output_schema)
            
            try:
                # Sử dụng tính năng structured output của Gemini API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        response_mime_type="application/json",
                        # Truyền schema đã làm sạch
                        response_schema=cleaned_schema
                    ),
                )
                
                # Xử lý kết quả
                if hasattr(response, 'parsed') and response.parsed is not None:
                    parsed_result = response.parsed
                    # Thêm các trường bắt buộc bị thiếu dựa trên schema
                    parsed_result = self._fix_missing_required_fields(parsed_result, output_schema)
                    return parsed_result
                elif hasattr(response, 'text') and response.text:
                    # Nếu không có parsed, thử parse từ text
                    try:
                        json_result = json.loads(response.text)
                        # Thêm các trường bắt buộc bị thiếu
                        json_result = self._fix_missing_required_fields(json_result, output_schema)
                        return json_result
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse response text as JSON, generating fallback")
                        return self._generate_fallback_response(output_schema)
            except Exception as e:
                logger.error(f"Error during Gemini API call: {e}")
                # Generate fallback response on any API error
                return self._generate_fallback_response(output_schema)
            
            # Fallback
            logger.warning("No valid structured output received, generating fallback")
            return self._generate_fallback_response(output_schema)
                
        except Exception as e:
            logger.error(f"Error generating structured output with Gemini: {e}")
            return self._generate_fallback_response(output_schema)
            
    def _generate_fallback_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback response with default values based on the schema.
        
        Args:
            schema: The output schema
            
        Returns:
            A basic valid response matching the schema
        """
        result = {}
        if not isinstance(schema, dict):
            return result
            
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])
        
        for field_name, field_schema in properties.items():
            if field_name in required_fields:
                field_type = field_schema.get("type", "")
                if field_type == "string":
                    result[field_name] = ""
                elif field_type == "array":
                    result[field_name] = []
                elif field_type == "object":
                    result[field_name] = {}
                elif field_type == "number" or field_type == "integer":
                    result[field_name] = 0
                elif field_type == "boolean":
                    result[field_name] = False
                else:
                    result[field_name] = None
                    
        return result
    
    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Remove problematic additionalProperties=False from schema for Gemini.
        
        Args:
            schema: The original JSON schema
            
        Returns:
            A cleaned schema compatible with Gemini
        """
        if not isinstance(schema, dict):
            return schema
            
        cleaned = {}
        
        for key, value in schema.items():
            # Skip additionalProperties field completely
            if key == "additionalProperties":
                continue
                
            # Recursively clean nested objects
            if isinstance(value, dict):
                cleaned[key] = self._clean_schema_for_gemini(value)
            elif isinstance(value, list):
                # Handle arrays
                cleaned[key] = [
                    self._clean_schema_for_gemini(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value
                
        return cleaned
        
    def _fix_missing_required_fields(self, result: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for any missing required fields based on the schema.
        
        Args:
            result: The API response with potentially missing fields
            schema: The schema defining the structure and required fields
            
        Returns:
            A dictionary with defaults for any missing required fields
        """
        if not isinstance(result, dict) or not isinstance(schema, dict):
            return result
            
        # Get the required fields from the schema
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Add default values for missing required fields
        for field in required_fields:
            if field not in result:
                # Add an appropriate default based on the field's type
                field_schema = properties.get(field, {})
                field_type = field_schema.get("type", "")
                
                if field_type == "string":
                    result[field] = ""
                elif field_type == "array":
                    result[field] = []
                elif field_type == "object":
                    result[field] = {}
                elif field_type == "number" or field_type == "integer":
                    result[field] = 0
                elif field_type == "boolean":
                    result[field] = False
                else:
                    # Default fallback
                    result[field] = None
                    
        # Also handle nested objects and arrays
        for key, value in result.items():
            if key in properties and isinstance(value, dict):
                field_schema = properties.get(key, {})
                if field_schema.get("type") == "object":
                    # Recursively fix nested objects
                    result[key] = self._fix_missing_required_fields(value, field_schema)
                    
        return result


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
