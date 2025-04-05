"""AI Service module for interacting with AI models.

This module provides services for interacting with different AI models
like Gemini and OpenAI.
"""

import os
import logging
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import aiohttp
import google.generativeai as genai
from openai import AsyncOpenAI

from ..core.config import settings
from ..utils import extract_json_from_text

# Configure logging
logger = logging.getLogger("services.ai_service")


class AIService(ABC):
    """Abstract base class for AI services."""
    
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    async def generate_structured_output(self, prompt: str, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output from a prompt.
        
        Args:
            prompt: The input prompt
            output_schema: The expected output schema
            
        Returns:
            Structured output as a dictionary
        """
        pass


class GeminiService(AIService):
    """Google Gemini AI service."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the Gemini service.
        
        Args:
            api_key: Gemini API key
            model: Gemini model name
        """
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.model_name = model or settings.GEMINI_MODEL
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Get the generative model
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Gemini service with model: {self.model_name}")
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt using Gemini.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text
        """
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def generate_structured_output(self, prompt: str, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output from a prompt using Gemini.
        
        Args:
            prompt: The input prompt
            output_schema: The expected output schema
            
        Returns:
            Structured output as a dictionary
        """
        schema_description = json.dumps(output_schema, indent=2)
        
        # Reformulated prompt with clear instructions for valid JSON
        full_prompt = f"""
        {prompt}
        
        Please provide your response as a JSON object with the following schema:
        {schema_description}
        
        IMPORTANT INSTRUCTIONS:
        1. Return ONLY valid, complete JSON, no additional text or explanation
        2. Make sure all strings are properly escaped and quoted
        3. Make sure to close all brackets and braces properly
        4. Do not include code blocks or markdown formatting in your JSON
        5. Do not truncate the JSON object
        
        RETURN FORMAT:
        {{
          "key1": "value1",
          "key2": "value2",
          ...
        }}
        """
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = await self.model.generate_content_async(full_prompt)
                result_text = response.text
                
                # Try to extract valid JSON from the response
                result_dict = extract_json_from_text(result_text)
                
                # If we got an empty dictionary, the extraction failed
                if not result_dict and attempt < max_retries:
                    logger.warning(f"JSON extraction failed on attempt {attempt + 1}, retrying...")
                    continue
                
                return result_dict
                
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1} generating structured output with Gemini: {str(e)}")
                if attempt < max_retries:
                    logger.info("Retrying with simplified prompt...")
                    # Simplify the schema if we're retrying
                    output_schema = self._simplify_schema(output_schema)
                    schema_description = json.dumps(output_schema, indent=2)
                else:
                    return {}
    
    def _simplify_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify a complex schema for retry attempts.
        
        Args:
            schema: The original schema
            
        Returns:
            A simplified version of the schema
        """
        simplified = {}
        
        # Process top-level fields
        for key, value in schema.items():
            if isinstance(value, dict):
                # Recursively simplify nested objects
                simplified[key] = self._simplify_schema(value)
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                # For arrays of objects, just include one example
                simplified[key] = [self._simplify_schema(value[0])]
            else:
                # Keep primitive values as-is
                simplified[key] = value
                
        return simplified


class OpenAIService(AIService):
    """OpenAI service."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the OpenAI service.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model name
        """
        self.api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model_name = model or settings.OPENAI_MODEL
        
        # Initialize the OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI service with model: {self.model_name}")
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text from a prompt using OpenAI.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def generate_structured_output(self, prompt: str, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output from a prompt using OpenAI.
        
        Args:
            prompt: The input prompt
            output_schema: The expected output schema
            
        Returns:
            Structured output as a dictionary
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            result_text = response.choices[0].message.content or "{}"
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Error generating structured output with OpenAI: {str(e)}")
            return {}


def get_ai_service() -> AIService:
    """Factory function to get the appropriate AI service based on settings.
    
    Returns:
        An instance of AIService
    """
    provider = settings.AI_PROVIDER.lower()
    
    if provider == "gemini":
        return GeminiService()
    elif provider == "openai":
        return OpenAIService()
    else:
        logger.warning(f"Unknown AI provider: {provider}. Defaulting to Gemini.")
        return GeminiService()