"""
Text Chunking Engine.
Splits large text blocks into overlapping segments matching model window limits while preserving word boundaries.
"""

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        """
        Splits a text string into chunks of chunk_size characters with chunk_overlap overlap.
        Respects space and newline breaks to avoid split words.
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If we aren't at the end of the text, try to find a natural word break
            if end < text_len:
                # Look backwards for a space or newline within the last 50 characters
                last_space = text.rfind(' ', end - 50, end)
                last_newline = text.rfind('\n', end - 50, end)
                best_break = max(last_space, last_newline)
                if best_break != -1:
                    end = best_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_len:
                break

            # Move starting cursor back by the overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loops in case overlap is larger than chunk size
            if start >= end:
                start = end

        return chunks
