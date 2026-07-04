"""
Central configuration loader.
Reads all settings from .env and exposes them as typed attributes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Application settings loaded from environment variables."""

    # --- ChromaDB ---
    CHROMA_API_KEY: str = os.getenv("CHROMA_API_KEY", "")
    CHROMA_TENANT: str = os.getenv("CHROMA_TENANT", "")
    CHROMA_DATABASE: str = os.getenv("CHROMA_DATABASE", "")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "pdf_documents")

    # --- Groq LLM ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- Tavily (optional) ---
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_PROJECT_ROOT / 'faculty_rag.db'}")

    # --- Paths ---
    PROJECT_ROOT: Path = _PROJECT_ROOT
    LOGS_DIR: Path = _PROJECT_ROOT / "logs"

    # --- RAG tuning ---
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "8"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "1.2"))

    def __init__(self):
        self.LOGS_DIR.mkdir(exist_ok=True)

    @property
    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def has_chroma(self) -> bool:
        return bool(self.CHROMA_API_KEY and self.CHROMA_TENANT and self.CHROMA_DATABASE)

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY)


settings = Settings()
