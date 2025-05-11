"""
Gemini API Schema Compatibility Module

This module provides helper functions to make JSON schemas compatible with Google's Gemini API.
It helps address issues with the 'additionalProperties: False' constraint that causes validation failures.
"""

import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
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
            cleaned[key] = clean_schema_for_gemini(value)
        elif isinstance(value, list):
            # Handle arrays
            cleaned[key] = [
                clean_schema_for_gemini(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value
            
    return cleaned
    
def create_default_response(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Create a default response that matches the schema's required fields.
    
    This is helpful when the AI provider fails to generate a valid structured response.
    
    Args:
        schema: The JSON schema
        
    Returns:
        A dictionary with default values matching the required schema
    """
    result = {}
    
    # If schema is invalid, return empty dict
    if not isinstance(schema, dict):
        return result
        
    # Get properties and required fields
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Add default values for each required field
    for field in required_fields:
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get("type", "")
            
            if field_type == "string":
                result[field] = ""
            elif field_type == "array":
                result[field] = []
            elif field_type == "object":
                nested_schema = field_schema
                result[field] = create_default_response(nested_schema)
            elif field_type in ["number", "integer"]:
                result[field] = 0
            elif field_type == "boolean":
                result[field] = False
            else:
                result[field] = None
        else:
            # Field is required but not in properties
            result[field] = None
            
    return result
    
def ensure_required_fields(response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required fields are present in the response.
    
    Args:
        response: The response from the AI provider
        schema: The expected schema
        
    Returns:
        A response with all required fields
    """
    if not isinstance(response, dict) or not isinstance(schema, dict):
        return response
        
    # Get the required fields from the schema
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Add missing required fields with default values
    for field in required_fields:
        if field not in response:
            field_schema = properties.get(field, {})
            field_type = field_schema.get("type", "")
            
            if field_type == "string":
                response[field] = ""
            elif field_type == "array":
                response[field] = []
            elif field_type == "object":
                response[field] = create_default_response(field_schema)
            elif field_type in ["number", "integer"]:
                response[field] = 0
            elif field_type == "boolean":
                response[field] = False
            else:
                response[field] = None
    
    # Handle nested objects recursively
    for field, value in response.items():
        if field in properties and isinstance(value, dict):
            field_schema = properties[field]
            if field_schema.get("type") == "object":
                response[field] = ensure_required_fields(value, field_schema)
                
    return response
