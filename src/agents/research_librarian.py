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
from .utils import execute_agent_with_tools, save_content_to_google_docs


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

## IMPORTANT Instructions:
- Use the web_search tool to find resources
- After gathering information, compile a comprehensive resource guide
- Provide your final compiled list in your response"""


RESEARCH_LIBRARIAN_HUMAN_PROMPT = """Search for and curate high-quality learning resources for: {topic}

Use the web search tool to find current resources. After searching, compile them into a comprehensive guide organized by category.

Include: official docs, tutorials, YouTube/courses, GitHub repos, and books.

Provide your complete curated resource list."""


def create_research_librarian_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Research Librarian agent node for the LangGraph.
    
    Uses web search to find resources, then compiles and saves to Google Docs.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESEARCH_LIBRARIAN_SYSTEM_PROMPT),
        ("human", RESEARCH_LIBRARIAN_HUMAN_PROMPT),
    ])
    
    # Separate search tools from Google Docs tools
    def get_search_tools(all_tools):
        return [t for t in all_tools if 'search' in t.name.lower()]
    
    def get_docs_tools(all_tools):
        return [t for t in all_tools if 'doc' in t.name.lower()]
    
    def research_librarian_node(state: TeachingState) -> dict:
        """Execute the Research Librarian agent."""
        topic = state["topic"]
        roadmap = state.get("roadmap", "Not yet available")
        
        roadmap_summary = roadmap[:3000] + "..." if len(roadmap) > 3000 else roadmap
        
        messages = prompt.format_messages(
            topic=topic,
            roadmap=roadmap_summary
        )
        
        # Use ONLY search tools for resource gathering
        search_tools = get_search_tools(tools)
        resources = execute_agent_with_tools(llm, search_tools, messages, max_iterations=5)
        
        # Save to Google Docs
        google_doc_links = state.get("google_doc_links", {}).copy()
        docs_tools = get_docs_tools(tools)
        doc_link = save_content_to_google_docs(
            docs_tools,
            f"Learning Resources: {topic}",
            resources
        )
        if doc_link:
            google_doc_links["research_librarian"] = doc_link
            resources += f"\n\n---\n📄 **Google Doc**: [{doc_link}]({doc_link})"
        
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
