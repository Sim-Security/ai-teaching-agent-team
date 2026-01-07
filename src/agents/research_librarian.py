"""
Research Librarian Agent - Learning Resource Specialist.

The Research Librarian curates high-quality learning resources
including documentation, tutorials, courses, and GitHub repositories.
"""

from typing import Callable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from ..state import TeachingState


RESEARCH_LIBRARIAN_SYSTEM_PROMPT = """You are the Research Librarian - a Learning Resource Specialist for the AI Teaching Agent Team.

Your role is to curate high-quality, current learning resources that support the learning roadmap.

## Context:
- Topic: {topic}
- Learning Roadmap Summary: {roadmap}

## Your Responsibilities:
1. **Search for Current Resources**: Use the web search tool to find up-to-date materials
2. **Curate Diverse Resource Types**: Include documentation, tutorials, videos, courses, and repos
3. **Assess Quality**: Evaluate and rate each resource for quality and relevance
4. **Match to Roadmap**: Align resources with the phases in the learning roadmap
5. **Provide Descriptions**: Explain what each resource offers and who it's best for

## Resource Categories to Include:
- 📚 Official Documentation
- 📝 Technical Blogs & Articles
- 🎥 Video Tutorials & Courses
- 💻 GitHub Repositories & Code Examples
- 📖 Books & eBooks
- 🎓 Online Courses (free and paid)
- 🔧 Tools & Utilities

## Output Requirements:
- Organize resources by roadmap phase or category
- Include direct URLs when available
- Rate resources (Beginner/Intermediate/Advanced)
- Note if resources are free or paid
- **IMPORTANT**: Create a Google Doc with your curated list and include the link"""


RESEARCH_LIBRARIAN_HUMAN_PROMPT = """Search for and curate high-quality learning resources for: {topic}

Use the web search tool to find current and relevant materials. Then organize them into a comprehensive resource guide that aligns with the learning roadmap.

Remember to create a Google Doc and include the link in your response."""


def create_research_librarian_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Research Librarian agent node for the LangGraph.
    
    The Research Librarian searches for and curates learning resources,
    using web search to find current materials.
    
    Args:
        llm: The language model to use for generation
        tools: List of tools (should include search and Google Docs tools)
        
    Returns:
        A node function that takes TeachingState and returns state updates
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCH_LIBRARIAN_SYSTEM_PROMPT),
        ("human", RESEARCH_LIBRARIAN_HUMAN_PROMPT),
    ])
    
    llm_with_tools = llm.bind_tools(tools)
    
    def research_librarian_node(state: TeachingState) -> dict:
        """Execute the Research Librarian agent."""
        topic = state["topic"]
        roadmap = state.get("roadmap", "Not yet available")
        
        # Truncate roadmap if too long
        roadmap_summary = roadmap[:2000] + "..." if len(roadmap) > 2000 else roadmap
        
        messages = prompt.format_messages(
            topic=topic,
            roadmap=roadmap_summary
        )
        
        response = llm_with_tools.invoke(messages)
        
        if hasattr(response, 'content') and response.content:
            resources = response.content
        else:
            resources = str(response)
        
        # Extract Google Doc link
        doc_link = _extract_google_doc_link(resources)
        google_doc_links = state.get("google_doc_links", {}).copy()
        if doc_link:
            google_doc_links["research_librarian"] = doc_link
        
        completed = state.get("completed_agents", []).copy()
        completed.append("research_librarian")
        
        return {
            "resources": resources,
            "google_doc_links": google_doc_links,
            "messages": [AIMessage(content=resources, name="Research Librarian")],
            "next_agent": "teaching_assistant",
            "completed_agents": completed,
        }
    
    return research_librarian_node


def _extract_google_doc_link(content: str) -> str | None:
    """Extract Google Doc URL from response content."""
    import re
    pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_/-]*)?'
    match = re.search(pattern, content)
    return match.group(0) if match else None
