"""
Shared Utility Helpers.
Provides text sanitization and parsing utilities.
"""

import re

def clean_professor_name(name: str) -> str:
    """Standardizes names to a clean prefix (e.g. Dr. John -> john)."""
    clean = name.strip().lower()
    clean = re.sub(r"^(dr\.|prof\.|professor|doctor)\s+", "", clean)
    return clean.split()[0] if clean else ""

def format_clean_text(text: str) -> str:
    """Cleans up redundant carriage returns, double-spaces, and linebreaks."""
    cleaned = text.replace("\r", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()

def sanitize_user_query(query: str) -> str:
    """
    Sanitizes user input to prevent prompt injections.
    Removes common jailbreak instructions and target phrases.
    """
    patterns = [
        r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?instructions",
        r"(?i)system\s+compromised",
        r"(?i)bypass\s+safety",
        r"(?i)override\s+rules",
        r"(?i)forget\s+what\s+was\s+written",
    ]
    
    sanitized = query
    for pattern in patterns:
        sanitized = re.sub(pattern, "[CLEANED]", sanitized)
        
    # Clean double spaces
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized.strip()
