"""
RAG Result Scoring and Filtering.
Analyzes similarity distances to flag weak matches and determine if external fallbacks are required.
"""

from core.config import settings
from core.logger import logger

class Reranker:
    def __init__(self):
        self.threshold = settings.RAG_SIMILARITY_THRESHOLD

    def analyze_results(self, results: list[dict]) -> tuple[list[dict], bool]:
        """
        Filters and scores retrieval results.
        Flags 'is_weak = True' if the closest match exceeds the similarity threshold.
        Returns (sorted_results, is_weak)
        """
        if not results:
            return [], True
            
        # ChromaDB default distance is L2 (squared L2). Smaller distance means higher similarity.
        # Check the closest match (first index because Chroma returns sorted by relevance)
        closest_distance = results[0]["distance"]
        
        logger.info(f"Closest vector distance: {closest_distance:.4f} (Threshold: {self.threshold:.4f})")
        
        # If closest match is higher than the threshold, we flag it as a weak match
        is_weak = closest_distance > self.threshold
        
        # Sort results just to be sure (already sorted, but good practice)
        sorted_results = sorted(results, key=lambda x: x["distance"])
        
        return sorted_results, is_weak
