"""
ArXiv Search Tool
Searches academic papers on ArXiv for research questions
Supports full PDF content extraction for deep analysis
"""

import arxiv
import re
from typing import List, Dict
from tools.research_memory import save_paper_content, get_paper_content


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _relevance_score(query: str, title: str, summary: str, categories: List[str]) -> float:
    query_tokens = [t for t in _tokenize(query) if len(t) > 2]
    if not query_tokens:
        return 1.0
    haystack = " ".join([title or "", summary or "", " ".join(categories or [])]).lower()
    if query.lower() in haystack:
        return 1.0
    hits = sum(1 for t in query_tokens if t in haystack)
    return hits / max(len(query_tokens), 1)


def _filter_results(query: str, results: List[Dict], min_relevance: float) -> List[Dict]:
    scored = []
    for item in results:
        score = _relevance_score(query, item.get("title", ""), item.get("summary", ""), item.get("categories", []))
        item["relevance"] = score
        scored.append(item)
    filtered = [r for r in scored if r.get("relevance", 0) >= min_relevance]
    if filtered:
        return filtered
    scored.sort(key=lambda r: r.get("relevance", 0), reverse=True)
    return scored[: max(1, min(3, len(scored)))]


def search_arxiv(
    query: str,
    max_results: int = 5,
    extract_full_content: bool = False,
    filter_relevance: bool = True,
    min_relevance: float = 0.12
) -> Dict:
    """
    Search ArXiv for academic papers
    
    Args:
        query: Search query string
        max_results: Maximum number of papers to return
        extract_full_content: If True, download and extract PDF content
        
    Returns:
        Dict with:
        - results: List of paper results (with full_text if extracted)
        - query: Original query
        - success: Whether search was successful
    """
    
    try:
        client = arxiv.Client()
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in client.results(search):
            arxiv_id = paper.entry_id.split('/abs/')[-1]
            
            paper_data = {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.strftime("%Y-%m-%d"),
                "pdf_url": paper.pdf_url,
                "arxiv_url": paper.entry_id,
                "arxiv_id": arxiv_id,
                "categories": paper.categories,
                "source": "arxiv"
            }
            
            if extract_full_content:
                existing_content = get_paper_content(arxiv_id)
                if existing_content and existing_content['full_text']:
                    paper_data['full_text'] = existing_content['full_text']
                    paper_data['tables'] = existing_content['tables']
                    print(f"Using cached content for {arxiv_id}")
                else:
                    print(f"Extracting content for: {paper.title[:50]}...")
                    save_result = save_paper_content(
                        arxiv_id=arxiv_id,
                        title=paper.title,
                        authors=[author.name for author in paper.authors],
                        abstract=paper.summary,
                        pdf_url=paper.pdf_url,
                        published_date=paper.published.strftime("%Y-%m-%d"),
                        extract_full_content=True
                    )
                    
                    if save_result['success'] and save_result.get('extraction_status') == 'success':
                        content = get_paper_content(arxiv_id)
                        if content:
                            paper_data['full_text'] = content['full_text']
                            paper_data['tables'] = content['tables']
            
            results.append(paper_data)
        
        if filter_relevance:
            results = _filter_results(query, results, min_relevance)

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


def format_arxiv_results_for_ai(results: List[Dict], include_full_text: bool = False) -> str:
    """
    Format ArXiv search results into a readable string for AI
    
    Args:
        results: List of ArXiv paper results
        include_full_text: Whether to include full extracted text
        
    Returns:
        Formatted string with numbered results
    """
    if not results:
        return "No ArXiv papers found."
    
    formatted = "ARXIV PAPERS:\n\n"
    for i, result in enumerate(results, 1):
        authors = ", ".join(result['authors'][:3])  # First 3 authors
        if len(result['authors']) > 3:
            authors += " et al."
        
        formatted += f"[{i}] {result['title']}\n"
        formatted += f"    Authors: {authors}\n"
        formatted += f"    Published: {result['published']}\n"
        
        if include_full_text and result.get('full_text'):
            formatted += f"    Full Paper Content:\n{result['full_text'][:3000]}...\n"
            
            if result.get('tables') and len(result['tables']) > 0:
                formatted += f"    Tables Found: {len(result['tables'])}\n"
                if result['tables'][0].get('markdown'):
                    formatted += f"\n    Example Table:\n{result['tables'][0]['markdown']}\n"
        else:
            formatted += f"    Summary: {result['summary'][:300]}...\n"
        
        formatted += f"    PDF: {result['pdf_url']}\n\n"
    
    return formatted
