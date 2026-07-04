"""
Research Trend Analyzer.
Fetches academic papers and web trends from arXiv and Tavily,
and synthesizes them using Groq into a structured JSON output.
"""

import json
from core.logger import logger
from services.arxiv_service import ArxivService
from services.tavily_service import TavilyService
from services.groq_service import GroqService
from professor_mode.schemas import TrendAnalysisOutput

class TrendAnalyzer:
    def __init__(self):
        self.arxiv = ArxivService()
        self.tavily = TavilyService()
        self.llm = GroqService()

    def analyze(self, topic: str) -> TrendAnalysisOutput:
        logger.info(f"[TrendAnalyzer] Analyzing trends for topic: '{topic}'")
        
        # 1. Fetch arXiv papers (fallback to empty list on error)
        try:
            arxiv_raw = self.arxiv.search_papers(topic, max_results=4)
        except Exception as e:
            logger.error(f"[TrendAnalyzer] arXiv search failed: {e}")
            arxiv_raw = []

        # 2. Fetch Tavily web results (fallback to empty list on error)
        try:
            tavily_raw = self.tavily.search(topic, max_results=4)
        except Exception as e:
            logger.error(f"[TrendAnalyzer] Tavily search failed: {e}")
            tavily_raw = []

        # 3. Format external data context
        context_items = []
        for paper in arxiv_raw:
            title = paper.get("title", "Untitled")
            summary = paper.get("summary", "")
            context_items.append(f"Source: arXiv\nTitle: {title}\nSummary: {summary}\n")
        
        for web in tavily_raw:
            title = web.get("title", "Untitled Web Result")
            content = web.get("content", "")
            context_items.append(f"Source: Tavily\nTitle: {title}\nSummary: {content}\n")

        context_str = "\n---\n".join(context_items) if context_items else "No external results retrieved."

        # 4. Generate structured analysis using Groq JSON Mode
        system_prompt = (
            "You are a Senior Research Director. Analyze the provided academic search context and identify the "
            "main research trends and emerging areas for the specified topic.\n\n"
            "CRITICAL: You must output ONLY a valid JSON object matching the schema below. Do not include any markdown "
            "fencing, surrounding explanation, or extra characters. Simply output the raw JSON object.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            '  "topic": "string",\n'
            '  "trends": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "summary": "string",\n'
            '      "source": "tavily|arxiv",\n'
            '      "confidence": float (between 0.0 and 1.0)\n'
            "    }\n"
            "  ],\n"
            '  "emerging_areas": ["string"]\n'
            "}"
        )

        user_prompt = f"""Topic: {topic}

Search Context:
{context_str}

Synthesize the data above into the requested JSON schema. Include at least 2-3 detailed trends and 2-3 emerging areas."""

        logger.info("[TrendAnalyzer] Calling Groq structured completion...")
        raw_json = self.llm.generate_json(user_prompt=user_prompt, system_prompt=system_prompt)
        
        # Clean JSON in case LLM added markdown backticks
        clean_json = raw_json.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:-1]
            clean_json = "\n".join(lines).strip()

        # Parse and validate with Pydantic
        try:
            parsed = json.loads(clean_json)
            # Ensure topic matches input
            parsed["topic"] = topic
            validated = TrendAnalysisOutput(**parsed)
            logger.info("[TrendAnalyzer] Trend analysis completed and validated successfully.")
            return validated
        except Exception as e:
            logger.error(f"[TrendAnalyzer] JSON Validation failed: {e}. Raw response: {raw_json}")
            # Fallback output in case of parsing failures
            return TrendAnalysisOutput(
                topic=topic,
                trends=[
                    {
                        "title": f"General trends in {topic}",
                        "summary": "Academic and web results show active development, but structure could not be fully parsed.",
                        "source": "arxiv",
                        "confidence": 0.5
                    }
                ],
                emerging_areas=[f"Advanced {topic}"]
            )
