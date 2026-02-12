"""Search tools for Papersio"""

from .web_search import search_web
from .arxiv_search import search_arxiv
from .search_router import search_all
from .pdf_extractor import extract_paper_content, format_paper_for_ai
from .embeddings import search_similar_queries, search_similar_papers
from .research_memory import (
    save_research,
    get_research_context,
    save_paper_content,
    get_paper_content,
    get_research_stats
)
from .pdf_generator import generate_research_pdf, LaTeXPaperGenerator

__all__ = [
    "search_web",
    "search_arxiv",
    "search_all",
    "extract_paper_content",
    "format_paper_for_ai",
    "search_similar_queries",
    "search_similar_papers",
    "save_research",
    "get_research_context",
    "save_paper_content",
    "get_paper_content",
    "get_research_stats",
    "generate_research_pdf",
    "LaTeXPaperGenerator"
]
