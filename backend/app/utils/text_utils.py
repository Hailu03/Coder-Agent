"""Text utility functions.

This module contains utility functions for text processing.
"""

import json
import re
from typing import Any, Dict, Optional, List

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from text that might contain other content.
    
    Args:
        text: The text containing JSON
        
    Returns:
        Extracted JSON as a dictionary, or empty dict if no valid JSON found
    """
    # First try to extract from markdown JSON code blocks
    json_code_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    code_matches = re.findall(json_code_pattern, text)
    
    # Try each code block match
    for json_str in code_matches:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON object with balanced brackets
    json_candidate = extract_balanced_json(text)
    if json_candidate:
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
    
    # Try a more aggressive approach - find anything between the outermost braces
    json_pattern = r'(\{[\s\S]*\})'
    match = re.search(json_pattern, text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            # Sometimes there's extra text at beginning or end
            json_str = match.group(1)
            # Clean up the JSON string
            json_str = cleanup_json_string(json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    
    # Try to fix common JSON syntax errors and try again
    fixed_text = fix_common_json_errors(text)
    try:
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        pass
    
    # Last resort: try extracting line by line
    lines = text.split('\n')
    for i in range(len(lines)):
        for j in range(i+1, len(lines)+1):
            candidate = '\n'.join(lines[i:j])
            if candidate.strip().startswith('{') and candidate.strip().endswith('}'):
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    
    # Return empty dict if all attempts fail
    return {}

def extract_balanced_json(text: str) -> Optional[str]:
    """Extract a balanced JSON object from text.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        Extracted JSON string or None if no balanced JSON found
    """
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
                return text[start_index:i+1]
    
    return None

def cleanup_json_string(json_str: str) -> str:
    """Clean up common issues in JSON strings.
    
    Args:
        json_str: The JSON string to clean
        
    Returns:
        Cleaned JSON string
    """
    # Remove any trailing commas before closing brackets or braces
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix unquoted property names
    json_str = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', json_str)
    
    # Fix single quotes to double quotes (careful with apostrophes in text)
    # This is a simplified approach and might not catch all cases correctly
    json_str = re.sub(r':\s*\'([^\']*?)\'', r': "\1"', json_str)
    
    return json_str

def fix_common_json_errors(text: str) -> str:
    """Attempt to fix common JSON syntax errors.
    
    Args:
        text: The text to fix
        
    Returns:
        Fixed JSON string
    """
    # Extract what looks most like a JSON object
    json_pattern = r'(\{[\s\S]*\})'
    match = re.search(json_pattern, text)
    
    if not match:
        return text
    
    json_str = match.group(1)
    
    # Fix missing quotes around property names
    json_str = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', json_str)
    
    # Fix single quotes
    json_str = json_str.replace("'", '"')
    
    # Fix trailing commas
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix missing quotes around string values (more complex, less reliable)
    json_str = re.sub(r':\s*([a-zA-Z0-9_]+)(\s*[,}])', r': "\1"\2', json_str)
    
    # Fix newlines and tabs in strings
    json_str = json_str.replace('\\n', '\\\\n')
    json_str = json_str.replace('\\t', '\\\\t')
    
    return json_str

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