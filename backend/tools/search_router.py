"""
Smart Search Router
Determines which search sources to use based on the query
"""

from typing import Dict, List
from .web_search import search_web, format_web_results_for_ai
from .arxiv_search import search_arxiv, format_arxiv_results_for_ai


def analyze_query_type(query: str) -> Dict[str, bool]:
    """
    Analyze query to determine which search sources to use

    Args:
        query: User's research question

    Returns:
        Dict indicating which sources to search
    """
    query_lower = query.lower()

    pure_academic_keywords = [
        "proof of",
        "theorem",
        "mathematical proof",
        "formal verification",
        "equation derivation",
        "theoretical framework",
    ]

    pure_web_keywords = [
        "price",
        "cost",
        "buy",
        "download",
        "tutorial",
        "how to install",
        "stock market",
        "weather",
        "sports score",
    ]

    only_arxiv = any(keyword in query_lower for keyword in pure_academic_keywords)

    only_web = any(keyword in query_lower for keyword in pure_web_keywords)

    needs_arxiv = True if not only_web else False
    needs_web = True if not only_arxiv else False

    return {"search_arxiv": needs_arxiv, "search_web": needs_web, "reason": get_search_reason(needs_arxiv, needs_web)}


def get_search_reason(arxiv: bool, web: bool) -> str:
    """Get human-readable reason for search strategy"""
    if arxiv and web:
        return "Searching both academic papers and web for comprehensive research"
    elif arxiv:
        return "Searching academic papers for technical/research content"
    elif web:
        return "Searching web for current news and information"
    else:
        return "No search needed"


def search_all(query: str, max_results_per_source: int = 5) -> Dict:
    """
    Smart search across multiple sources

    Args:
        query: Research question
        max_results_per_source: Max results per source

    Returns:
        Dict with results from all searched sources
    """

    strategy = analyze_query_type(query)

    results = {"query": query, "strategy": strategy, "web_results": [], "arxiv_results": [], "combined_context": ""}

    if strategy["search_arxiv"]:
        arxiv_response = search_arxiv(query, max_results_per_source)
        if arxiv_response["success"]:
            results["arxiv_results"] = arxiv_response["results"]

    if strategy["search_web"]:
        web_response = search_web(query, max_results_per_source)
        if web_response["success"]:
            results["web_results"] = web_response["results"]

    context_parts = []

    if results["arxiv_results"]:
        context_parts.append(format_arxiv_results_for_ai(results["arxiv_results"]))

    if results["web_results"]:
        context_parts.append(format_web_results_for_ai(results["web_results"]))

    results["combined_context"] = "\n\n".join(context_parts)

    return results
