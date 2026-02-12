"""
Quick test script to verify search functionality works
Run this to test your search tools before using the full app
"""

from tools.web_search import search_web
from tools.arxiv_search import search_arxiv
from tools.search_router import search_all

def test_web_search():
    """Test web search"""
    print("Testing Web Search...")
    print("-" * 50)
    
    result = search_web("latest AI news", max_results=3)
    
    if result["success"]:
        print(f"Found {result['count']} web results")
        for i, item in enumerate(result["results"], 1):
            print(f"\n[{i}] {item['title']}")
            print(f"    {item['url']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n")


def test_arxiv_search():
    """Test ArXiv search"""
    print("Testing ArXiv Search...")
    print("-" * 50)
    
    result = search_arxiv("transformer neural networks", max_results=3)
    
    if result["success"]:
        print(f"Found {result['count']} papers")
        for i, paper in enumerate(result["results"], 1):
            authors = ", ".join(paper["authors"][:2])
            if len(paper["authors"]) > 2:
                authors += " et al."
            print(f"\n[{i}] {paper['title']}")
            print(f"    Authors: {authors}")
            print(f"    {paper['arxiv_url']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n")


def test_smart_search():
    """Test smart search router"""
    print("Testing Smart Search Router...")
    print("-" * 50)
    
    queries = [
        "How do transformers work?",
        "Latest AI news January 2026",
        "What is quantum computing?"
    ]
    
    for query in queries:
        print(f"\nQuery: \"{query}\"")
        result = search_all(query, max_results_per_source=2)
        
        strategy = result["strategy"]
        print(f"Strategy: {strategy['reason']}")
        print(f"ArXiv: {len(result['arxiv_results'])} papers")
        print(f"Web: {len(result['web_results'])} articles")
        print("-" * 30)
    
    print("\n")


if __name__ == "__main__":
    print("=" * 50)
    print("PAPERSIO - SEARCH TOOLS TEST")
    print("=" * 50)
    print()
    
    try:
        test_web_search()
        test_arxiv_search()
        test_smart_search()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
        print("\nIf all tests passed, your search system is working!")
        print("   Start the backend: python main.py")
        print("   Then open: frontend/index.html")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has TAVILY_API_KEY")
        print("2. Make sure you ran: pip install -r requirements.txt")
        print("3. Check your internet connection")
