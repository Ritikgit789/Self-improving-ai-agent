"""
Web Search Tool using DuckDuckGo
"""
from typing import List
from ddgs import DDGS
from schemas import SearchResult
import config


def search_web(query: str, max_results: int = None) -> List[SearchResult]:
    """
    Search the web using DuckDuckGo
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of SearchResult objects containing title, snippet, and URL
    """
    if max_results is None:
        max_results = config.WEB_SEARCH_MAX_RESULTS
    
    try:
        results = []
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append(SearchResult(
                    title=result.get('title', 'No title'),
                    snippet=result.get('body', 'No snippet'),
                    url=result.get('href', '')
                ))
        
        return results
    
    except Exception as e:
        print(f"⚠️  Web search error: {e}")
        return []


def format_search_results(results: List[SearchResult]) -> str:
    """
    Format search results into a readable string
    
    Args:
        results: List of SearchResult objects
        
    Returns:
        Formatted string with all results
    """
    if not results:
        return "No search results found."
    
    formatted = f"Found {len(results)} search results:\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.title}\n"
        formatted += f"   {result.snippet}\n"
        formatted += f"   Source: {result.url}\n\n"
    
    return formatted
