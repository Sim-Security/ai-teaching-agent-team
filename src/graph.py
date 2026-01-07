"""
LangGraph StateGraph Definition.

This module constructs the main teaching agent team graph with
all nodes, edges, and conditional routing logic.
"""

from langgraph.graph import StateGraph, END, START
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .state import TeachingState
from .supervisor import create_supervisor, route_to_agent
from .agents import (
    create_professor_node,
    create_academic_advisor_node,
    create_research_librarian_node,
    create_teaching_assistant_node,
)


def create_teaching_graph(
    llm: BaseChatModel,
    google_docs_tools: list[BaseTool],
    search_tool: BaseTool,
):
    """
    Create the teaching agent team LangGraph.
    
    This graph orchestrates 4 specialized teaching agents in sequence:
    1. Professor - Creates knowledge base
    2. Academic Advisor - Designs learning roadmap
    3. Research Librarian - Curates resources
    4. Teaching Assistant - Creates practice materials
    
    The Supervisor node manages routing between agents.
    
    Args:
        llm: The language model for all agents
        google_docs_tools: Composio Google Docs tools
        search_tool: Web search tool (DuckDuckGo or SerpAPI)
        
    Returns:
        Compiled LangGraph ready for execution
        
    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4o-mini")
        >>> graph = create_teaching_graph(llm, docs_tools, search_tool)
        >>> result = graph.invoke({"topic": "Machine Learning"})
    """
    # Combine tools for agents that need both
    all_tools = google_docs_tools + [search_tool]
    
    # Initialize the StateGraph with our state schema
    graph = StateGraph(TeachingState)
    
    # Add the Supervisor node
    graph.add_node("supervisor", create_supervisor(llm))
    
    # Add agent nodes
    graph.add_node(
        "professor",
        create_professor_node(llm, google_docs_tools)
    )
    graph.add_node(
        "academic_advisor",
        create_academic_advisor_node(llm, google_docs_tools)
    )
    graph.add_node(
        "research_librarian",
        create_research_librarian_node(llm, all_tools)
    )
    graph.add_node(
        "teaching_assistant",
        create_teaching_assistant_node(llm, all_tools)
    )
    
    # Define the entry point - start with supervisor
    graph.add_edge(START, "supervisor")
    
    # Add conditional edges from supervisor to agents
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "professor": "professor",
            "academic_advisor": "academic_advisor",
            "research_librarian": "research_librarian",
            "teaching_assistant": "teaching_assistant",
            "FINISH": END,
        }
    )
    
    # All agents return to supervisor after completing
    graph.add_edge("professor", "supervisor")
    graph.add_edge("academic_advisor", "supervisor")
    graph.add_edge("research_librarian", "supervisor")
    graph.add_edge("teaching_assistant", "supervisor")
    
    # Compile and return the graph
    return graph.compile()


def get_graph_visualization(graph) -> str:
    """
    Get a Mermaid diagram representation of the graph.
    
    Useful for documentation and debugging.
    
    Args:
        graph: Compiled LangGraph
        
    Returns:
        Mermaid diagram string
    """
    try:
        return graph.get_graph().draw_mermaid()
    except Exception:
        return "Graph visualization not available"
