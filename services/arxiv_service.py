"""
arXiv API service integration.
Queries the academic arXiv repository to fetch latest papers on research topics.
"""

import xml.etree.ElementTree as ET
import httpx
from core.logger import logger

class ArxivService:
    def __init__(self):
        self.base_url = "https://export.arxiv.org/api/query"

    def search_papers(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Queries arXiv API for papers matching the given query.
        Returns a list of papers: [{"title": ..., "summary": ..., "authors": ..., "url": ...}]
        """
        # Ensure query is a string
        if isinstance(query, list):
            query = " ".join(query)
            
        logger.info(f"Querying arXiv for papers matching: '{query}'")
        
        # Simple sanitization of query parameters
        formatted_query = str(query).replace(" ", "+")
        params = {
            "search_query": f"all:{formatted_query}",
            "start": 0,
            "max_results": max_results
        }
        
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(self.base_url, params=params)
                if response.status_code != 200:
                    logger.error(f"arXiv API error: Status {response.status_code}")
                    return []
                
                # Parse atom XML response
                root = ET.fromstring(response.content)
                papers = []
                
                # Namespaces map
                ns = {
                    "atom": "http://www.w3.org/2005/Atom",
                    "opensearch": "http://a9.com/-/spec/opensearch/1.1/"
                }
                
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    id_url = entry.find("atom:id", ns)
                    
                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name = author.find("atom:name", ns)
                        if name is not None and name.text:
                            authors.append(name.text.strip())
                            
                    title_text = title.text.strip().replace("\n", " ") if title is not None and title.text else "No Title"
                    summary_text = summary.text.strip().replace("\n", " ") if summary is not None and summary.text else "No Summary"
                    url_text = id_url.text.strip() if id_url is not None and id_url.text else ""
                    
                    papers.append({
                        "title": title_text,
                        "summary": summary_text,
                        "authors": authors,
                        "url": url_text
                    })
                    
                return papers
                
        except Exception as e:
            logger.error(f"arXiv search request failed: {e}")
            return []
