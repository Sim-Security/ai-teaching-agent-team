"""
Google Docs tool integration using Composio.

This module wraps the Composio LangChain integration to provide
Google Docs creation and update capabilities for the teaching agents.
"""

from typing import Optional
from langchain_core.tools import BaseTool


def get_google_docs_tools(api_key: str) -> list[BaseTool]:
    """
    Initialize Google Docs tools using Composio LangChain integration.
    
    Args:
        api_key: Composio API key for authentication
        
    Returns:
        List of LangChain-compatible tools for Google Docs operations
        
    Raises:
        ImportError: If composio-langchain is not installed
        Exception: If Composio initialization fails
    """
    try:
        from composio_langchain import ComposioToolSet, Action
    except ImportError:
        raise ImportError(
            "composio-langchain is required for Google Docs integration. "
            "Install it with: pip install composio-langchain"
        )
    
    toolset = ComposioToolSet(api_key=api_key)
    
    # Get both create and update document actions
    tools = toolset.get_tools(actions=[
        Action.GOOGLEDOCS_CREATE_DOCUMENT,
        Action.GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT,
    ])
    
    return tools


def get_google_docs_create_tool(api_key: str) -> Optional[BaseTool]:
    """
    Get only the Google Docs create document tool.
    
    Args:
        api_key: Composio API key for authentication
        
    Returns:
        The create document tool, or None if not found
    """
    tools = get_google_docs_tools(api_key)
    for tool in tools:
        if "create" in tool.name.lower():
            return tool
    return tools[0] if tools else None
