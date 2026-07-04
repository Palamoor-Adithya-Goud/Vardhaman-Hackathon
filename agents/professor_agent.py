"""
Professor Mode Agent.
Compares local faculty expertise against global research trends to identify gaps and suggest opportunities.
"""

from services.groq_service import GroqService
from services.tavily_service import TavilyService
from services.arxiv_service import ArxivService
from rag.retriever import ChromaRetriever
from prompts.system_prompts import PROFESSOR_MODE_SYSTEM, PROFESSOR_MODE_USER_TEMPLATE
from core.logger import logger

class ProfessorAgent:
    def __init__(self):
        self.llm = GroqService()
        self.tavily = TavilyService()
        self.arxiv = ArxivService()
        self.retriever = ChromaRetriever()

    def analyze_gaps(self, research_topic: str) -> dict:
        """
        Runs Professor Mode gap analysis:
        1. Query internal ChromaDB to represent local faculty expertise.
        2. Query Tavily + arXiv to represent global research trends on the topic.
        3. Use Groq to analyze gaps and suggest project opportunities.
        """
        logger.info(f"Running Professor Mode Gap Analysis for: '{research_topic}'")
        
        # 1. Retrieve local expertise
        local_results = self.retriever.retrieve(research_topic, n_results=6)
        local_texts = []
        for r in local_results:
            source = r["metadata"].get("source", "Unknown Document")
            local_texts.append(f"[Faculty Source: {source}]\n{r['document']}")
        local_context = "\n\n".join(local_texts) if local_texts else "No local faculty profiles found for this topic."

        # 2. Retrieve global trends
        global_papers = self.arxiv.search_papers(research_topic, max_results=3)
        global_web = self.tavily.search(research_topic, max_results=3)
        
        trend_parts = []
        if global_papers:
            trend_parts.append("Latest papers from arXiv:")
            for p in global_papers:
                trend_parts.append(f"- {p['title']} by {', '.join(p['authors'])}")
        if global_web:
            trend_parts.append("Web research trends (Tavily):")
            for w in global_web:
                trend_parts.append(f"- {w['title']}: {w['content']}")
                
        global_context = "\n".join(trend_parts) if trend_parts else "No global trends could be fetched."

        # 3. Call Groq
        user_prompt = PROFESSOR_MODE_USER_TEMPLATE.format(
            faculty_expertise=local_context,
            global_trends=global_context
        )
        
        analysis = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=PROFESSOR_MODE_SYSTEM,
            temperature=0.3
        )
        
        return {
            "topic": research_topic,
            "local_context": local_context,
            "global_trends": global_context,
            "analysis": analysis
        }
