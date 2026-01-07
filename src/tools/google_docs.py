"""
Google Docs integration using Composio MCP (Model Context Protocol).

This module uses the industry-standard MCP approach for reliable tool execution.
No fallback - MCP is the only supported method.
"""

import os
from typing import Optional
from langchain_core.tools import BaseTool


def get_google_docs_tools(
    api_key: str,
    user_id: str = "default",
    mcp_config_id: Optional[str] = None
) -> list[BaseTool]:
    """
    Get Google Docs tools via Composio MCP.
    
    Args:
        api_key: Composio API key
        user_id: User identifier
        mcp_config_id: MCP config ID (REQUIRED for tool access)
        
    Returns:
        List of LangChain-compatible tools
        
    Raises:
        ValueError: If mcp_config_id is not provided
    """
    if not mcp_config_id:
        import warnings
        warnings.warn(
            "COMPOSIO_MCP_CONFIG_ID is required for Google Docs integration. "
            "Set it in your .env file. Get it from https://platform.composio.dev/mcp-configs"
        )
        return []
    
    # Set API key in environment
    os.environ["COMPOSIO_API_KEY"] = api_key
    
    # Apply nest_asyncio to allow nested event loops (required for Streamlit)
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        import warnings
        warnings.warn("nest-asyncio not installed. Run: pip install nest-asyncio")
        return []
    
    import asyncio
    
    async def get_mcp_tools():
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # Construct the Composio MCP server URL
        # Format: https://backend.composio.dev/v3/mcp/{config_id}/mcp?user_id={user_id}
        mcp_url = (
            f"https://backend.composio.dev/v3/mcp/{mcp_config_id}/mcp"
            f"?user_id={user_id}"
        )
        
        print(f"[MCP] Connecting to: {mcp_url}")
        
        client = MultiServerMCPClient({
            "googledocs": {
                "transport": "http",
                "url": mcp_url,
                "headers": {
                    "x-api-key": api_key,
                }
            }
        })
        
        tools = await client.get_tools()
        print(f"[MCP] Loaded {len(tools)} tools")
        for tool in tools:
            print(f"[MCP]   - {tool.name}")
        
        return tools
    
    try:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tools = loop.run_until_complete(get_mcp_tools())
        return tools
        
    except Exception as e:
        import warnings
        import traceback
        print(f"[MCP] ERROR: {e}")
        traceback.print_exc()
        warnings.warn(
            f"Failed to connect to Composio MCP server: {e}. "
            "Check your MCP config at https://platform.composio.dev/mcp-configs"
        )
        return []
