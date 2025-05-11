"""
Fix for Gemini API Service in GeminiService class
"""

import json
import logging
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

from ..core.config import settings
from ..utils import extract_json_from_text
from .gemini_fix import clean_schema_for_gemini, create_default_response, ensure_required_fields

logger = logging.getLogger("services.ai_service")

async def gemini_structured_output(
    client: genai.Client, 
    model_name: str, 
    prompt: str, 
    output_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate structured output from Gemini API with error handling and fallbacks.
    
    Args:
        client: The Gemini API client
        model_name: Name of the Gemini model to use
        prompt: The input prompt
        output_schema: The expected output schema
        
    Returns:
        A structured output matching the schema
    """
    try:
        # Remove additionalProperties from schema for Gemini compatibility
        cleaned_schema = clean_schema_for_gemini(output_schema)
        
        # First try: Use response_schema parameter
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                    response_schema=cleaned_schema
                ),
            )
            
            # If we have parsed content, ensure required fields exist
            if hasattr(response, 'parsed') and response.parsed is not None:
                result = ensure_required_fields(response.parsed, output_schema)
                return result
            
            # Otherwise try to extract JSON from text
            if hasattr(response, 'text') and response.text:
                try:
                    json_text = extract_json_from_text(response.text)
                    if json_text:
                        json_result = json.loads(json_text)
                        return ensure_required_fields(json_result, output_schema)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"First attempt failed with schema: {e}")
            
        # Second try: Include schema in prompt
        try:
            schema_prompt = f"{prompt}\n\nYou MUST respond with valid JSON following this exact schema:\n```json\n{json.dumps(cleaned_schema, indent=2)}\n```"
            response = client.models.generate_content(
                model=model_name,
                contents=schema_prompt,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            
            if hasattr(response, 'text') and response.text:
                json_text = extract_json_from_text(response.text)
                if json_text:
                    try:
                        json_result = json.loads(json_text)
                        return ensure_required_fields(json_result, output_schema)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Second attempt failed: {e}")
            
        # Last resort: Create default response
        logger.warning("All attempts failed, creating default response")
        return create_default_response(output_schema)
    except Exception as e:
        logger.error(f"Error in gemini_structured_output: {e}")
        # Create minimal valid structure
        return create_default_response(output_schema)
