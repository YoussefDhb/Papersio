"""
Web Search Tool using DuckDuckGo
Searches the web for current information, news, articles, etc.
No API key needed - completely free!
"""

import os
import re
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

try:
    from ddgs import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    print("DuckDuckGo search not available. Install with: pip install duckduckgo-search")


def search_web(query: str, max_results: int = 5) -> Dict:
    """
    Search the web using DuckDuckGo (free, no API key needed!)
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Dict with:
        - results: List of search results
        - query: Original query
        - success: Whether search was successful
    """
    
    if not SEARCH_AVAILABLE:
        return {
            "success": False,
            "error": "DuckDuckGo search not installed. Install with: pip install ddgs",
            "results": [],
            "query": query
        }
    
    try:
        ddgs = DDGS()
        
        search_results = ddgs.text(
            query=query,  # Changed from 'keywords' to 'query'
            max_results=max_results
        )
        
        results = []
        for item in search_results:
            results.append({
                "title": item.get('title', ''),
                "url": item.get('href', ''),
                "content": item.get('body', ''),
                "score": 1.0,
                "source": "web"
            })

        results = _filter_results(query, results, 0.12)
        
        return {
            "success": True,
            "results": results,
            "query": query,
            "count": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "query": query
        }


def format_web_results_for_ai(results: List[Dict]) -> str:
    """
    Format web search results into a readable string for AI
    
    Args:
        results: List of web search results
        
    Returns:
        Formatted string with numbered results
    """
    if not results:
        return "No web results found."
    
    formatted = "WEB SEARCH RESULTS:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"[{i}] {result['title']}\n"
        formatted += f"    URL: {result['url']}\n"
        formatted += f"    Content: {result['content'][:300]}...\n\n"
    
    return formatted


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _relevance_score(query: str, title: str, content: str, url: str) -> float:
    query_tokens = [t for t in _tokenize(query) if len(t) > 2]
    if not query_tokens:
        return 1.0
    haystack = " ".join([title or "", content or "", url or ""]).lower()
    if query.lower() in haystack:
        return 1.0
    hits = sum(1 for t in query_tokens if t in haystack)
    return hits / max(len(query_tokens), 1)


def _filter_results(query: str, results: List[Dict], min_relevance: float) -> List[Dict]:
    scored = []
    for item in results:
        score = _relevance_score(query, item.get("title", ""), item.get("content", ""), item.get("url", ""))
        item["relevance"] = score
        item["score"] = score
        scored.append(item)
    filtered = [r for r in scored if r.get("relevance", 0) >= min_relevance]
    if filtered:
        return filtered
    scored.sort(key=lambda r: r.get("relevance", 0), reverse=True)
    return scored[: max(1, min(3, len(scored)))]
