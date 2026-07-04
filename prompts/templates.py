"""
Prompt Formatting Templates.
Provides helper functions for formatting structured context into prompt inputs.
"""

def format_faculty_context(results: list[dict]) -> str:
    """Formats retrieved vector database results into a context string."""
    parts = []
    for r in results:
        meta = r.get("metadata", {})
        source = meta.get("source", "Unknown Document")
        page = meta.get("page", "?")
        parts.append(
            f"Source Document: {source} (Page {page})\n"
            f"Content:\n{r['document']}"
        )
    return "\n\n====================\n\n".join(parts)

def format_external_trends(web_results: list[dict], papers: list[dict]) -> str:
    """Formats Tavily and arXiv external results into a context string."""
    parts = []
    if papers:
        parts.append("Latest Academic Publications (arXiv):")
        for p in papers:
            authors_str = ", ".join(p.get("authors", []))
            parts.append(
                f"- Title: {p.get('title')}\n"
                f"  Authors: {authors_str}\n"
                f"  Summary: {p.get('summary')[:300]}...\n"
                f"  URL: {p.get('url')}"
            )
    if web_results:
        parts.append("\nWeb Search Results (Tavily):")
        for w in web_results:
            parts.append(
                f"- Title: {w.get('title')}\n"
                f"  Summary: {w.get('content')}\n"
                f"  URL: {w.get('url')}"
            )
    return "\n".join(parts) if parts else "No external trends available."
