"""
Google Docs tool integration using Composio v3 SDK.

This module wraps the Composio LangChain integration to provide
Google Docs creation and update capabilities for the teaching agents.

With Composio v3, OAuth authorization is handled programmatically
rather than via the `composio add googledocs` CLI command.
"""

import os
from typing import Optional
from langchain_core.tools import BaseTool


def check_google_docs_connection(api_key: str, user_id: str = "default") -> dict:
    """
    Check if Google Docs is connected for the given user.
    
    Args:
        api_key: Composio API key
        user_id: User identifier in your system
        
    Returns:
        dict with 'connected' bool and 'auth_url' if authorization needed
    """
    os.environ["COMPOSIO_API_KEY"] = api_key
    
    try:
        from composio import Composio
        
        composio = Composio(api_key=api_key)
        
        # Check for existing connections
        accounts = composio.connected_accounts.list(user_id=user_id)
        
        for account in accounts:
            if hasattr(account, 'toolkit') and 'googledocs' in account.toolkit.lower():
                if account.status == "ACTIVE":
                    return {"connected": True, "account_id": account.id}
        
        return {"connected": False, "message": "Google Docs not connected"}
        
    except Exception as e:
        return {"connected": False, "error": str(e)}


def initiate_google_docs_auth(api_key: str, user_id: str = "default") -> dict:
    """
    Initiate OAuth flow for Google Docs authorization.
    
    Args:
        api_key: Composio API key
        user_id: User identifier in your system
        
    Returns:
        dict with 'auth_url' to redirect user for authorization
    """
    os.environ["COMPOSIO_API_KEY"] = api_key
    
    try:
        from composio import Composio
        
        composio = Composio(api_key=api_key)
        
        # Initiate connection - this requires an auth_config_id from your dashboard
        # For Google Docs, you need to create an auth config in the Composio dashboard first
        connection_request = composio.connected_accounts.initiate(
            user_id=user_id,
            toolkit="GOOGLEDOCS",
            redirect_url="https://platform.composio.dev/callback",
        )
        
        return {
            "auth_url": connection_request.redirect_url,
            "connection_id": connection_request.id,
        }
        
    except Exception as e:
        return {"error": str(e)}


def get_google_docs_tools(api_key: str, user_id: str = "default") -> list[BaseTool]:
    """
    Initialize Google Docs tools using Composio LangChain integration.
    
    Args:
        api_key: Composio API key for authentication
        user_id: User identifier for connected account lookup
        
    Returns:
        List of LangChain-compatible tools for Google Docs operations
        
    Raises:
        ImportError: If composio-langchain is not installed
        Exception: If Composio initialization fails
    """
    # Set API key in environment for Composio
    os.environ["COMPOSIO_API_KEY"] = api_key
    
    try:
        from composio import Composio
        from composio_langchain import LangchainProvider
    except ImportError:
        raise ImportError(
            "composio-langchain is required for Google Docs integration. "
            "Install it with: pip install -U composio-langchain composio"
        )
    
    try:
        # Initialize Composio with LangChain provider
        composio = Composio(api_key=api_key, provider=LangchainProvider())
        
        # Get Google Docs tools for this user
        tools = composio.tools.get(
            user_id=user_id,
            toolkits=["GOOGLEDOCS"],
        )
        
        if not tools:
            import warnings
            warnings.warn(
                "No Google Docs tools available. "
                "Please authorize Google Docs at: https://platform.composio.dev/ "
                "Navigate to Connections > Add Connection > Google Docs"
            )
        
        return tools
        
    except Exception as e:
        # If Composio setup fails, return empty list with warning
        import warnings
        warnings.warn(
            f"Failed to initialize Composio Google Docs tools: {e}. "
            "Agents will continue without Google Docs integration. "
            "Please authorize at: https://platform.composio.dev/"
        )
        return []


def get_google_docs_create_tool(api_key: str, user_id: str = "default") -> Optional[BaseTool]:
    """
    Get only the Google Docs create document tool.
    
    Args:
        api_key: Composio API key for authentication
        user_id: User identifier for connected account lookup
        
    Returns:
        The create document tool, or None if not found
    """
    tools = get_google_docs_tools(api_key, user_id)
    for tool in tools:
        if "create" in tool.name.lower():
            return tool
    return tools[0] if tools else None
