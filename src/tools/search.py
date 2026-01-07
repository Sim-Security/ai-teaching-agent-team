"""
Web search tool implementations.

Provides DuckDuckGo search as default (free, no API key required)
and SerpAPI for production use cases requiring higher reliability.
"""

from typing import Optional
from langchain_core.tools import BaseTool, Tool


def get_search_tool(
    use_production: bool = False,
    serpapi_key: Optional[str] = None
) -> BaseTool:
    """
    Get a web search tool for finding learning resources.
    
    Uses DuckDuckGo by default (free, no API key needed).
    For production environments, SerpAPI can be enabled for better reliability.
    
    Args:
        use_production: If True and serpapi_key is provided, use SerpAPI
        serpapi_key: SerpAPI key for production search
        
    Returns:
        A LangChain-compatible search tool
        
    Examples:
        >>> # Development/testing - free DuckDuckGo
        >>> tool = get_search_tool()
        
        >>> # Production - SerpAPI
        >>> tool = get_search_tool(use_production=True, serpapi_key="your-key")
    """
    if use_production and serpapi_key:
        return _get_serpapi_tool(serpapi_key)
    return _get_duckduckgo_tool()


def _get_duckduckgo_tool() -> BaseTool:
    """Get DuckDuckGo search tool (free, no API key required)."""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
    except ImportError:
        raise ImportError(
            "DuckDuckGo search is required. "
            "Install it with: pip install -U duckduckgo-search"
        )
    
    return DuckDuckGoSearchRun(
        name="web_search",
        description=(
            "Search the web for current information about learning resources, "
            "tutorials, documentation, and educational content. "
            "Input should be a search query string."
        ),
    )


def _get_serpapi_tool(api_key: str) -> BaseTool:
    """Get SerpAPI search tool for production use."""
    try:
        from langchain_community.utilities import SerpAPIWrapper
    except ImportError:
        raise ImportError(
            "google-search-results is required for SerpAPI. "
            "Install it with: pip install google-search-results"
        )
    
    search = SerpAPIWrapper(serpapi_api_key=api_key)
    
    return Tool(
        name="web_search",
        description=(
            "Search the web for current information about learning resources, "
            "tutorials, documentation, and educational content. "
            "Input should be a search query string."
        ),
        func=search.run,
    )
