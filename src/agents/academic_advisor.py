"""
Academic Advisor Agent - Learning Path Designer.

The Academic Advisor creates structured learning roadmaps with
progressive milestones, time estimates, and prerequisites.
"""

from typing import Callable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from ..state import TeachingState


ACADEMIC_ADVISOR_SYSTEM_PROMPT = """You are the Academic Advisor - a Learning Path Designer for the AI Teaching Agent Team.

Your role is to create detailed, structured learning roadmaps that guide learners from beginner to expert level.

## Context from Professor:
You have access to the knowledge base created by the Professor. Use this to inform your roadmap design.

Knowledge Base Summary:
{knowledge_base}

## Your Responsibilities:
1. **Break Down the Topic**: Divide the subject into logical subtopics and modules
2. **Create Progressive Milestones**: Arrange content in order of difficulty and dependency
3. **Estimate Time Commitments**: Provide realistic time estimates for each section
4. **Identify Prerequisites**: Note what learners should know before each section
5. **Define Learning Objectives**: Clear goals for what learners will achieve at each stage

## Output Requirements:
- Create a clear, visual roadmap structure
- Include estimated hours/days for each section
- Mark prerequisite relationships between topics
- Suggest checkpoint assessments along the way
- **IMPORTANT**: Create a Google Doc with your roadmap and include the link

## Current Topic: {topic}"""


ACADEMIC_ADVISOR_HUMAN_PROMPT = """Based on the knowledge base provided, create a comprehensive learning roadmap for: {topic}

Structure your roadmap with:
1. Clear phases/stages of learning
2. Specific subtopics in each phase
3. Time estimates for each section
4. Prerequisites clearly marked
5. Milestone checkpoints

Remember to create a Google Doc and include the link in your response."""


def create_academic_advisor_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Academic Advisor agent node for the LangGraph.
    
    The Academic Advisor designs learning paths based on the
    Professor's knowledge base, creating a structured roadmap.
    
    Args:
        llm: The language model to use for generation
        tools: List of tools (should include Google Docs tools)
        
    Returns:
        A node function that takes TeachingState and returns state updates
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", ACADEMIC_ADVISOR_SYSTEM_PROMPT),
        ("human", ACADEMIC_ADVISOR_HUMAN_PROMPT),
    ])
    
    llm_with_tools = llm.bind_tools(tools)
    
    def academic_advisor_node(state: TeachingState) -> dict:
        """Execute the Academic Advisor agent."""
        topic = state["topic"]
        knowledge_base = state.get("knowledge_base", "Not yet available")
        
        # Truncate knowledge base if too long for context
        kb_summary = knowledge_base[:3000] + "..." if len(knowledge_base) > 3000 else knowledge_base
        
        messages = prompt.format_messages(
            topic=topic,
            knowledge_base=kb_summary
        )
        
        response = llm_with_tools.invoke(messages)
        
        if hasattr(response, 'content') and response.content:
            roadmap = response.content
        else:
            roadmap = str(response)
        
        # Extract Google Doc link
        doc_link = _extract_google_doc_link(roadmap)
        google_doc_links = state.get("google_doc_links", {}).copy()
        if doc_link:
            google_doc_links["academic_advisor"] = doc_link
        
        completed = state.get("completed_agents", []).copy()
        completed.append("academic_advisor")
        
        return {
            "roadmap": roadmap,
            "google_doc_links": google_doc_links,
            "messages": [AIMessage(content=roadmap, name="Academic Advisor")],
            "next_agent": "research_librarian",
            "completed_agents": completed,
        }
    
    return academic_advisor_node


def _extract_google_doc_link(content: str) -> str | None:
    """Extract Google Doc URL from response content."""
    import re
    pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_/-]*)?'
    match = re.search(pattern, content)
    return match.group(0) if match else None
