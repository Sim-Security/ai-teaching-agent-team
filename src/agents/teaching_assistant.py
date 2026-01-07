"""
Teaching Assistant Agent - Exercise Creator.

The Teaching Assistant creates comprehensive practice materials
including exercises, quizzes, projects, and real-world applications.
"""

from typing import Callable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from ..state import TeachingState
from .utils import execute_agent_with_tools


TEACHING_ASSISTANT_SYSTEM_PROMPT = """You are the Teaching Assistant - an Exercise Creator for the AI Teaching Agent Team.

Your role is to create comprehensive practice materials that help learners apply and reinforce their knowledge.

## Context:
- Topic: {topic}
- Knowledge Base Summary: {knowledge_base}
- Learning Roadmap Summary: {roadmap}

## Your Responsibilities:
1. **Create Progressive Exercises**: Start simple and increase complexity
2. **Design Quizzes**: Test understanding of key concepts
3. **Develop Hands-on Projects**: Real-world application scenarios
4. **Provide Solutions**: Detailed explanations for all exercises
5. **Align with Roadmap**: Match exercises to roadmap phases

## Exercise Types to Include:
- 🎯 Concept Check Questions (multiple choice, true/false)
- ✍️ Short Answer Exercises
- 💻 Coding Challenges (if applicable)
- 🔨 Mini Projects
- 🏆 Capstone Project Ideas
- 🧩 Problem-Solving Scenarios

## Output Requirements:
- Organize exercises by difficulty level (Beginner → Intermediate → Advanced)
- Include clear instructions for each exercise
- Provide complete solutions with explanations
- Estimate time needed for each exercise

## IMPORTANT Instructions:
- You may use web_search to find example problems if helpful
- Focus on creating original, practical exercises
- Provide your complete practice materials in your final response"""


TEACHING_ASSISTANT_HUMAN_PROMPT = """Create comprehensive practice materials for: {topic}

Design exercises, quizzes, and projects that align with the learning roadmap and help reinforce the knowledge base concepts.

Provide your complete practice materials including exercises and solutions in your response."""


def create_teaching_assistant_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Teaching Assistant agent node for the LangGraph.
    
    The Teaching Assistant creates practice materials aligned
    with the knowledge base and roadmap from previous agents.
    
    Args:
        llm: The language model to use for generation
        tools: List of tools (should include search and Google Docs tools)
        
    Returns:
        A node function that takes TeachingState and returns state updates
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", TEACHING_ASSISTANT_SYSTEM_PROMPT),
        ("human", TEACHING_ASSISTANT_HUMAN_PROMPT),
    ])
    
    def teaching_assistant_node(state: TeachingState) -> dict:
        """Execute the Teaching Assistant agent."""
        topic = state["topic"]
        knowledge_base = state.get("knowledge_base", "Not yet available")
        roadmap = state.get("roadmap", "Not yet available")
        
        # Truncate for context limits
        kb_summary = knowledge_base[:2000] + "..." if len(knowledge_base) > 2000 else knowledge_base
        roadmap_summary = roadmap[:2000] + "..." if len(roadmap) > 2000 else roadmap
        
        messages = prompt.format_messages(
            topic=topic,
            knowledge_base=kb_summary,
            roadmap=roadmap_summary
        )
        
        # Execute with proper tool handling
        practice_materials = execute_agent_with_tools(llm, tools, messages, max_iterations=5)
        
        # Extract Google Doc link if present
        doc_link = _extract_google_doc_link(practice_materials)
        google_doc_links = state.get("google_doc_links", {}).copy()
        if doc_link:
            google_doc_links["teaching_assistant"] = doc_link
        
        completed = state.get("completed_agents", []).copy()
        completed.append("teaching_assistant")
        
        return {
            "practice_materials": practice_materials,
            "google_doc_links": google_doc_links,
            "messages": [AIMessage(content=practice_materials, name="Teaching Assistant")],
            "next_agent": "FINISH",  # Last agent - signal completion
            "completed_agents": completed,
        }
    
    return teaching_assistant_node


def _extract_google_doc_link(content: str) -> str | None:
    """Extract Google Doc URL from response content."""
    import re
    pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_/-]*)?'
    match = re.search(pattern, content)
    return match.group(0) if match else None
