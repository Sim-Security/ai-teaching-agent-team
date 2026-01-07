"""
Shared state schema for the AI Teaching Agent Team.

This module defines the TypedDict that flows through the LangGraph StateGraph,
enabling all agents to read from and write to a common state.
"""

from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TeachingState(TypedDict):
    """
    Shared state for the teaching agent team.
    
    This state flows through the LangGraph and is updated by each agent node.
    All agents can read the current state and contribute their outputs.
    
    Attributes:
        topic: The learning topic provided by the user
        knowledge_base: Professor's comprehensive knowledge base content
        roadmap: Academic Advisor's structured learning path
        resources: Research Librarian's curated resource list
        practice_materials: Teaching Assistant's exercises and projects
        google_doc_links: URLs to created Google Docs (keyed by agent name)
        messages: Conversation history with automatic message accumulation
        next_agent: Routing control for the supervisor to determine next step
        completed_agents: List of agents that have completed their tasks
    """
    topic: str
    knowledge_base: str
    roadmap: str
    resources: str
    practice_materials: str
    google_doc_links: dict[str, str]
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    completed_agents: list[str]


def create_initial_state(topic: str) -> TeachingState:
    """
    Create the initial state for a new teaching session.
    
    Args:
        topic: The learning topic provided by the user
        
    Returns:
        A TeachingState with the topic set and all other fields initialized
    """
    return TeachingState(
        topic=topic,
        knowledge_base="",
        roadmap="",
        resources="",
        practice_materials="",
        google_doc_links={},
        messages=[],
        next_agent="professor",
        completed_agents=[],
    )
