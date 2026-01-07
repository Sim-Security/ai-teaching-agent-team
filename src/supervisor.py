"""
Supervisor Agent - Orchestrator for the Teaching Team.

The Supervisor routes tasks to specialized agents and manages
the overall workflow through the teaching process.
"""

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from .state import TeachingState


# Agent routing options
AGENTS = ["professor", "academic_advisor", "research_librarian", "teaching_assistant"]
ROUTING_OPTIONS = Literal["professor", "academic_advisor", "research_librarian", "teaching_assistant", "FINISH"]


SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor - the orchestrator of the AI Teaching Agent Team.

Your role is to manage the workflow and route tasks to the appropriate specialized agents.

## Your Team:
1. **Professor** - Creates comprehensive knowledge bases (first step)
2. **Academic Advisor** - Designs learning roadmaps (needs knowledge base)
3. **Research Librarian** - Curates learning resources (needs roadmap)
4. **Teaching Assistant** - Creates practice materials (needs knowledge + roadmap)

## Workflow Rules:
- The Professor should ALWAYS go first to establish the knowledge base
- Academic Advisor should follow to create the learning path
- Research Librarian curates resources aligned with the roadmap
- Teaching Assistant creates exercises based on all previous work
- After all agents complete, respond with FINISH

## Current State:
- Topic: {topic}
- Completed Agents: {completed_agents}

Based on the current state, determine which agent should work next, or if we're done."""


def create_supervisor(llm: BaseChatModel):
    """
    Create the Supervisor node that orchestrates the agent workflow.
    
    The Supervisor determines which agent should run next based on
    the current state and completed work.
    
    Args:
        llm: The language model (used for complex routing decisions if needed)
        
    Returns:
        A node function for routing decisions
    """
    def supervisor_node(state: TeachingState) -> dict:
        """
        Determine the next agent to run based on workflow rules.
        
        Uses a simple rule-based approach for reliable orchestration:
        Professor → Academic Advisor → Research Librarian → Teaching Assistant → FINISH
        """
        completed = state.get("completed_agents", [])
        
        # Follow the sequential workflow
        if "professor" not in completed:
            next_agent = "professor"
        elif "academic_advisor" not in completed:
            next_agent = "academic_advisor"
        elif "research_librarian" not in completed:
            next_agent = "research_librarian"
        elif "teaching_assistant" not in completed:
            next_agent = "teaching_assistant"
        else:
            next_agent = "FINISH"
        
        return {
            "next_agent": next_agent,
        }
    
    return supervisor_node


def route_to_agent(state: TeachingState) -> ROUTING_OPTIONS:
    """
    Conditional edge function to route to the appropriate agent.
    
    This is used by LangGraph to determine which node to visit next.
    
    Args:
        state: Current teaching state
        
    Returns:
        The name of the next agent node or "FINISH"
    """
    return state.get("next_agent", "FINISH")
