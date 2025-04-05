"""Models for utility functions.

This module contains models and enums for utility functions.
"""

from enum import Enum
from typing import Dict, Any, List, Optional

class LanguageExtensions:
    """Mapping of programming languages to file extensions."""
    
    extensions: Dict[str, str] = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "c#": "cs",
        "c++": "cpp",
        "c": "c",
        "go": "go",
        "ruby": "rb",
        "php": "php",
        "swift": "swift",
        "kotlin": "kt",
        "rust": "rs",
        "scala": "scala"
    }
    
    @classmethod
    def get_extension(cls, language: str) -> str:
        """Get the file extension for a given language.
        
        Args:
            language: Programming language name
            
        Returns:
            File extension for the language
        """
        return cls.extensions.get(language.lower(), "txt")