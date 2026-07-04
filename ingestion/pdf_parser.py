"""
Faculty PDF Parser.
Extracts faculty biography and profile data, strips inline citations, and removes reference sections.
"""

import re
from pathlib import Path
import pypdf
from core.logger import logger
from services.groq_service import GroqService
from prompts.system_prompts import PDF_CLEANING_SYSTEM

class FacultyPDFParser:
    def __init__(self):
        try:
            self.llm = GroqService()
        except Exception:
            self.llm = None
            logger.warning("Groq not initialized for PDF cleaning. Will fallback to regex cleaning.")

    def clean_text_regex(self, text: str) -> str:
        """
        Uses regular expressions to strip inline citations and truncate reference lists.
        """
        # 1. Truncate references/bibliography
        ref_patterns = [
            r"(?i)\nREFERENCES\b", 
            r"(?i)\nBIBLIOGRAPHY\b", 
            r"(?i)\nLITERATURE CITED\b",
            r"(?i)\nWORKS CITED\b"
        ]
        
        cleaned_text = text
        for pattern in ref_patterns:
            matches = list(re.finditer(pattern, cleaned_text))
            if matches:
                # Truncate at the first occurrence of references heading near the end
                # (usually references are in the last 30% of the document)
                match = matches[-1]
                if match.start() > len(cleaned_text) * 0.5:
                    logger.info(f"Truncated reference list at character position {match.start()}")
                    cleaned_text = cleaned_text[:match.start()]
                    break

        # 2. Remove inline citation markers e.g. [1], [12, 15], [3-7], (Smith, 2020)
        # Remove bracket citations: [1], [1, 2], [1-5]
        cleaned_text = re.sub(r"\[\d+(?:,\s*\d+)*\]", "", cleaned_text)
        cleaned_text = re.sub(r"\[\d+\s*-\s*\d+\]", "", cleaned_text)
        
        # Remove parenthetical author-year citations: (Author, 2020), (Author et al., 2019)
        cleaned_text = re.sub(r"\([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?,\s*\d{4}\)", "", cleaned_text)
        
        # Clean double spaces or broken formatting
        cleaned_text = re.sub(r" {2,}", " ", cleaned_text)
        
        return cleaned_text.strip()

    def parse_faculty_profile(self, pdf_path: str) -> list[dict]:
        """
        Parses a PDF document, extracts biography text from first/last pages,
        strips citations, and returns cleaned page text chunks.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        logger.info(f"Parsing faculty PDF: {path.name}")
        reader = pypdf.PdfReader(path)
        total_pages = len(reader.pages)
        
        pages_content = []
        
        for idx in range(total_pages):
            page_num = idx + 1
            text = reader.pages[idx].extract_text()
            if not text or not text.strip():
                continue
                
            # Perform regex cleaning to strip citations/references
            cleaned_text = self.clean_text_regex(text)
            
            # If the text is empty after cleaning, skip it
            if not cleaned_text.strip():
                continue
                
            # For page 1, 2 and the last page, we can run them through the LLM to get a clean bio profile
            # if we have the LLM service available.
            is_bio_page = (page_num == 1) or (page_num == 2) or (page_num == total_pages)
            
            if is_bio_page and self.llm:
                try:
                    logger.info(f"Running LLM cleaning on bio-critical Page {page_num} of {path.name}")
                    cleaned_text = self.llm.generate(
                        user_prompt=f"Clean the following page text to extract only faculty profile info:\n\n{cleaned_text}",
                        system_prompt=PDF_CLEANING_SYSTEM,
                        temperature=0.1
                    )
                except Exception as e:
                    logger.warning(f"LLM cleaning failed on Page {page_num}, falling back to regex: {e}")
            
            pages_content.append({
                "page_number": page_num,
                "text": cleaned_text,
                "source": path.name
            })
            
        return pages_content
