"""Text utility functions.

This module contains utility functions for text processing.
"""

import json
import re
from typing import Any, Dict, Optional

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from text that might contain other content.
    
    Args:
        text: The text containing JSON
        
    Returns:
        Extracted JSON as a dictionary, or None if no valid JSON found
    """
    # Try to find JSON block using regex
    json_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)
    
    if match:
        # Extract from code block
        json_str = match.group(1)
    else:
        # Try to find JSON object using brackets
        json_pattern = r'(\{[\s\S]*\})'
        match = re.search(json_pattern, text)
        if match:
            json_str = match.group(1)
        else:
            # Use the entire text as fallback
            json_str = text
    
    # Try to parse the JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If direct parsing fails, try to find the first valid JSON object
        bracket_count = 0
        start_index = -1
        
        for i, char in enumerate(text):
            if char == '{' and bracket_count == 0:
                start_index = i
                bracket_count += 1
            elif char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                
                if bracket_count == 0 and start_index != -1:
                    try:
                        json_str = text[start_index:i+1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        start_index = -1
        
        return None

def clean_language_name(language: str) -> str:
    """Normalize programming language names for consistent use.
    
    Args:
        language: The programming language name to clean
        
    Returns:
        A normalized version of the language name
    """
    language = language.lower().strip()
    
    # Map of common language variations to standard names
    language_map = {
        # JavaScript variants
        "javascript": "javascript",
        "js": "javascript",
        "node": "javascript",
        "nodejs": "javascript",
        "node.js": "javascript",
        
        # TypeScript variants
        "typescript": "typescript",
        "ts": "typescript",
        
        # Python variants
        "python": "python",
        "py": "python",
        "python3": "python",
        
        # Java variants
        "java": "java",
        
        # C# variants
        "c#": "csharp",
        "csharp": "csharp",
        "c-sharp": "csharp",
        
        # C++ variants
        "c++": "cpp",
        "cpp": "cpp",
        
        # C variants
        "c": "c",
        
        # Go variants
        "go": "go",
        "golang": "go",
        
        # Ruby variants
        "ruby": "ruby",
        "rb": "ruby",
        
        # PHP variants
        "php": "php",
        
        # Rust variants
        "rust": "rust",
        "rs": "rust",
        
        # Swift variants
        "swift": "swift",
        
        # Kotlin variants
        "kotlin": "kotlin",
        "kt": "kotlin",
    }
    
    return language_map.get(language, language)

def format_code_with_language(code: str, language: str) -> str:
    """Format code with appropriate language markdown.
    
    Args:
        code: The code to format
        language: The programming language of the code
        
    Returns:
        Formatted code with markdown code block syntax
    """
    # Clean and normalize the language name
    clean_lang = clean_language_name(language)
    
    # Check if the code is already properly formatted with the correct language
    code_block_pattern = r'^```([\w]*)\n([\s\S]*?)\n```$'
    match = re.match(code_block_pattern, code.strip())
    
    if match:
        lang_tag, code_content = match.groups()
        # If the language tag matches or is missing, use the existing format but with correct language
        if not lang_tag or clean_language_name(lang_tag) == clean_lang:
            # Keep the content but ensure correct language tag
            return f"```{clean_lang}\n{code_content.strip()}\n```"
    
    # Remove any existing markdown code block formatting
    code = re.sub(r'^```[\w]*\n|```$', '', code, flags=re.MULTILINE)
    
    # Trim whitespace while preserving the code indentation
    code = code.strip()
    
    # Format with the appropriate language tag
    return f"```{clean_lang}\n{code}\n```"

def extract_code_from_markdown(text: str, default_language: str = "python") -> Dict[str, str]:
    """Extract code blocks from markdown text.
    
    Args:
        text: The markdown text containing code blocks
        default_language: Default programming language if not specified
        
    Returns:
        Dictionary with language as key and code as value
    """
    # Find all code blocks with language tags
    pattern = r'```([\w]*)\n([\s\S]*?)\n```'
    matches = re.findall(pattern, text)
    
    result = {}
    
    for lang, code in matches:
        if not lang:
            lang = default_language
        else:
            lang = clean_language_name(lang)
        
        if lang in result:
            # If we already have code for this language, append to it
            result[lang] += "\n\n" + code.strip()
        else:
            result[lang] = code.strip()
    
    # If no code blocks found, treat the entire text as code with default language
    if not result and text.strip():
        result[default_language] = text.strip()
    
    return result