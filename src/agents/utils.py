"""
Agent utilities for proper tool execution.

This module provides helper functions for executing tools
when the LLM returns tool calls instead of direct content.
"""

from typing import List
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool


def execute_agent_with_tools(
    llm: BaseChatModel,
    tools: List[BaseTool],
    messages: List[BaseMessage],
    max_iterations: int = 5,
) -> str:
    """
    Execute an LLM with tools, handling tool calls iteratively.
    
    When the LLM responds with tool_calls, this function executes
    those tools and continues the conversation until the LLM
    provides a final text response.
    
    Args:
        llm: The language model (with tools already bound)
        tools: List of available tools
        messages: Initial messages to send
        max_iterations: Maximum number of tool execution rounds
        
    Returns:
        The final text content from the LLM
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
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call.get('name', '')
                tool_args = tool_call.get('args', {})
                tool_id = tool_call.get('id', f'call_{iteration}')
                
                if tool_name in tool_dict:
                    try:
                        # Execute the tool
                        tool_result = tool_dict[tool_name].invoke(tool_args)
                        result_str = str(tool_result)
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
    # Ask LLM to summarize what it's learned
    current_messages.append(
        AIMessage(content="Please provide your final comprehensive response based on all the information gathered.")
    )
    final_response = llm_with_tools.invoke(current_messages)
    
    if hasattr(final_response, 'content') and final_response.content:
        return final_response.content
    return "Agent completed but could not generate final response."
