"""
Groq LLM service abstraction layer.
Provides a modular interface for LLM generation that can be swapped to other providers.
"""

from groq import Groq

from core.config import settings
from core.logger import logger


class GroqService:
    """Abstracted LLM provider using Groq API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or settings.GROQ_API_KEY
        self._model = model or settings.GROQ_MODEL
        if not self._api_key:
            raise ValueError("GROQ_API_KEY is not configured in .env")
        self._client = Groq(api_key=self._api_key)

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> str:
        """Generate a response from the LLM."""
        logger.debug(f"Groq request: model={self._model}, temp={temperature}")
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            logger.debug(f"Groq response: {len(content)} chars")
            return content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def generate_with_history(
        self,
        messages: list[dict],
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ) -> str:
        """Generate a response with full message history."""
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
