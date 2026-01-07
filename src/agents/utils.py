"""
Agent utilities for proper tool execution.

This module provides helper functions for executing tools
when the LLM returns tool calls instead of direct content.
"""

import asyncio
import re
from typing import List, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

# Apply nest_asyncio to allow nested event loops (required for Streamlit)
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass


def execute_agent_with_tools(
    llm: BaseChatModel,
    tools: List[BaseTool],
    messages: List[BaseMessage],
    max_iterations: int = 5,
) -> str:
    """
    Execute an LLM with tools, handling tool calls iteratively.
    Uses async tool invocation for MCP compatibility.
    """
    # Create tool lookup
    tool_dict = {tool.name: tool for tool in tools}
    
    # Bind tools to LLM if not already bound
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    
    current_messages = list(messages)
    
    for iteration in range(max_iterations):
        # Get LLM response
        response = llm_with_tools.invoke(current_messages)
        
        # Check if response has tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Add AI message to conversation
            current_messages.append(response)
            
            # Execute each tool call using async
            for tool_call in response.tool_calls:
                tool_name = tool_call.get('name', '')
                tool_args = tool_call.get('args', {})
                tool_id = tool_call.get('id', f'call_{iteration}')
                
                if tool_name in tool_dict:
                    try:
                        # Execute the tool with async support
                        result_str = _invoke_tool_async(tool_dict[tool_name], tool_args)
                    except Exception as e:
                        result_str = f"Error executing tool {tool_name}: {str(e)}"
                else:
                    result_str = f"Tool '{tool_name}' not found"
                
                # Add tool result to conversation
                current_messages.append(
                    ToolMessage(content=result_str, tool_call_id=tool_id)
                )
        else:
            # No tool calls - return the content
            if hasattr(response, 'content') and response.content:
                return response.content
            else:
                return str(response)
    
    # Max iterations reached - try to get a final response
    current_messages.append(
        HumanMessage(content="Please provide your final comprehensive response based on all the information gathered.")
    )
    final_response = llm_with_tools.invoke(current_messages)
    
    if hasattr(final_response, 'content') and final_response.content:
        return final_response.content
    return "Agent completed but could not generate final response."


def _invoke_tool_async(tool: BaseTool, args: dict) -> str:
    """Invoke a tool with async support for MCP tools."""
    async def _ainvoke():
        result = await tool.ainvoke(args)
        return str(result)
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_ainvoke())
    except Exception:
        # Fallback to sync if async fails
        try:
            return str(tool.invoke(args))
        except Exception as e:
            return f"Error: {e}"


def save_content_to_google_docs(
    tools: List[BaseTool],
    title: str,
    content: str
) -> Optional[str]:
    """
    Save content to Google Docs using available tools.
    Supports both sync and async (MCP) tools.
    
    Args:
        tools: List of available tools
        title: Document title
        content: Content to save
        
    Returns:
        Document URL if successful, None otherwise
    """
    if not tools:
        print("[DOCS] No Google Docs tools available")
        return None
    
    # Find the create document tool
    create_tool = None
    for tool in tools:
        tool_name_lower = tool.name.lower()
        if 'create' in tool_name_lower and 'document' in tool_name_lower:
            if 'markdown' not in tool_name_lower:  # Prefer non-markdown version
                create_tool = tool
                break
    
    # Fallback to any create doc tool
    if not create_tool:
        for tool in tools:
            if 'create' in tool.name.lower() and 'doc' in tool.name.lower():
                create_tool = tool
                break
    
    if not create_tool:
        print("[DOCS] No suitable create document tool found")
        return None
    
    print(f"[DOCS] Using tool: {create_tool.name}")
    print(f"[DOCS] Creating document: {title} ({len(content)} chars)")
    
    # Invoke the tool with async support
    try:
        result_str = _invoke_tool_async(create_tool, {
            "title": title,
            "text": content,
        })
        
        print(f"[DOCS] Result: {result_str[:300]}...")
        
        # Extract document URL
        doc_link = _extract_google_doc_link(result_str)
        
        if doc_link:
            print(f"[DOCS] SUCCESS: {doc_link}")
        else:
            print("[DOCS] No document URL found in result")
        
        return doc_link
        
    except Exception as e:
        print(f"[DOCS] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def _extract_google_doc_link(content: str) -> Optional[str]:
    """Extract Google Doc URL from response content or construct from documentId."""
    
    # First try to find a full URL
    url_pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_/-]*)?'
    match = re.search(url_pattern, content)
    if match:
        return match.group(0)
    
    # If no URL, try to extract documentId and construct URL
    doc_id_pattern = r'"documentId"\s*:\s*"([a-zA-Z0-9_-]+)"'
    match = re.search(doc_id_pattern, content)
    if match:
        doc_id = match.group(1)
        return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    return None
