"""
Tavily Search API service integration.
Fetches real-time web search results for research topics and trends.
"""

import httpx
from core.config import settings
from core.logger import logger

class TavilyService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Executes a search query using Tavily API.
        Returns a list of structured results: [{"title": ..., "url": ..., "content": ...}]
        """
        if not self.api_key:
            logger.warning("Tavily API key not configured. Web search skipped.")
            return []

        logger.info(f"Querying Tavily for: '{query}'")
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": max_results
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.base_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    return [
                        {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", "")
                        }
                        for r in results
                    ]
                else:
                    logger.error(f"Tavily API error: Status {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Tavily request failed: {e}")
            return []
