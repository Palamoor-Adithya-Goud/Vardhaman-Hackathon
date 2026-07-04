"""
Research Gap Analyzer.
Compares local faculty expertise (from ChromaDB) against external trends,
and identifies covered areas, missing areas, and opportunity gaps.
"""

import json
from core.logger import logger
from rag.retriever import ChromaRetriever
from services.groq_service import GroqService
from professor_mode.schemas import GapAnalysisOutput, TrendAnalysisOutput

class GapAnalyzer:
    def __init__(self):
        self.retriever = ChromaRetriever()
        self.llm = GroqService()

    def analyze(self, topic: str, trends_output: TrendAnalysisOutput) -> GapAnalysisOutput:
        logger.info(f"[GapAnalyzer] Analyzing research gaps for topic: '{topic}'")
        
        # 1. Retrieve local faculty expertise chunks
        try:
            local_results = self.retriever.retrieve(topic, n_results=8)
            local_texts = []
            for r in local_results:
                source = r["metadata"].get("source", "Unknown Document")
                local_texts.append(f"[Faculty Source: {source}]\n{r['document']}")
            local_context = "\n\n".join(local_texts) if local_texts else "No local faculty profiles found in ChromaDB."
        except Exception as e:
            logger.error(f"[GapAnalyzer] ChromaDB retrieval failed: {e}")
            local_context = "No local faculty profiles retrieved due to ChromaDB error."

        # 2. Format external trends context
        trends_list = []
        for t in trends_output.trends:
            trends_list.append(f"- Trend: {t.title}\n  Summary: {t.summary} (Confidence: {t.confidence})")
        trends_str = "\n".join(trends_list)

        # 3. Call Groq JSON Mode to compare and identify gaps
        system_prompt = (
            "You are a Senior Academic Director. Compare local faculty expertise against external global research trends "
            "to identify research gaps and opportunities.\n\n"
            "CRITICAL: You must output ONLY a valid JSON object matching the schema below. Do not include any markdown "
            "fencing, surrounding explanation, or extra characters. Simply output the raw JSON object.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            '  "covered_areas": ["string"],\n'
            '  "missing_areas": ["string"],\n'
            '  "opportunity_gaps": [\n'
            "    {\n"
            '      "gap": "string",\n'
            '      "why_it_matters": "string"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"""Topic: {topic}

Local Faculty Expertise Context:
{local_context}

Global Research Trends:
{trends_str}

Perform a gap analysis. Identify which trends are already covered by our local faculty (covered_areas), which trends are missing from our faculty (missing_areas), and outline 2-3 specific opportunity_gaps that we could target."""

        logger.info("[GapAnalyzer] Calling Groq structured completion...")
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
            validated = GapAnalysisOutput(**parsed)
            logger.info("[GapAnalyzer] Gap analysis completed and validated successfully.")
            return validated
        except Exception as e:
            logger.error(f"[GapAnalyzer] JSON Validation failed: {e}. Raw response: {raw_json}")
            # Fallback output
            return GapAnalysisOutput(
                covered_areas=["General Computer Science"],
                missing_areas=[f"Advanced applications in {topic}"],
                opportunity_gaps=[
                    {
                        "gap": f"Lack of specialized research in {topic}",
                        "why_it_matters": "Global academic focus is moving rapidly, and we need specialized studies."
                    }
                ]
            )
