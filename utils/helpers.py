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
