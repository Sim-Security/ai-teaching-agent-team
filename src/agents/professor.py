"""
Professor Agent - Research and Knowledge Specialist.

The Professor agent creates comprehensive knowledge bases covering
fundamental concepts, advanced topics, and current developments.
"""

from typing import Callable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage

from ..state import TeachingState


PROFESSOR_SYSTEM_PROMPT = """You are the Professor - a Research and Knowledge Specialist for the AI Teaching Agent Team.

Your role is to create a comprehensive knowledge base that serves as the foundation for learning a new topic.

## Your Responsibilities:
1. **Explain from First Principles**: Start with the absolute basics and build up understanding gradually
2. **Cover Key Terminology**: Define all important terms and concepts clearly
3. **Explain Core Principles**: Describe the fundamental ideas that underpin the topic
4. **Include Practical Applications**: Show how the concepts apply in real-world scenarios
5. **Address Common Misconceptions**: Clarify areas where learners often get confused

## Output Requirements:
- Format your response as a well-structured educational document
- Use clear headings and subheadings for organization
- Include examples where helpful
- Make content accessible to beginners while still being comprehensive
- **IMPORTANT**: Create a Google Doc with your knowledge base content

## Current Topic: {topic}

Create a comprehensive knowledge base that anyone starting out can read and gain maximum value from."""


PROFESSOR_HUMAN_PROMPT = """Please create a comprehensive knowledge base for the topic: {topic}

Remember to:
1. Explain concepts from first principles
2. Include key terminology and definitions
3. Cover core principles and practical applications
4. Format for readability and understanding
5. Create a Google Doc with your findings and include the link in your response"""


def create_professor_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Professor agent node for the LangGraph.
    
    The Professor researches the topic and creates a comprehensive
    knowledge base document, saving it to Google Docs.
    
    Args:
        llm: The language model to use for generation
        tools: List of tools (should include Google Docs tools)
        
    Returns:
        A node function that takes TeachingState and returns state updates
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROFESSOR_SYSTEM_PROMPT),
        ("human", PROFESSOR_HUMAN_PROMPT),
    ])
    
    # Bind tools to LLM for function calling
    llm_with_tools = llm.bind_tools(tools)
    
    def professor_node(state: TeachingState) -> dict:
        """Execute the Professor agent."""
        topic = state["topic"]
        
        # Format the prompt
        messages = prompt.format_messages(topic=topic)
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(messages)
        
        # Extract content - handle both direct response and tool calls
        if hasattr(response, 'content') and response.content:
            knowledge_base = response.content
        else:
            knowledge_base = str(response)
        
        # Extract Google Doc link if present
        doc_link = _extract_google_doc_link(knowledge_base)
        google_doc_links = state.get("google_doc_links", {}).copy()
        if doc_link:
            google_doc_links["professor"] = doc_link
        
        # Update completed agents list
        completed = state.get("completed_agents", []).copy()
        completed.append("professor")
        
        return {
            "knowledge_base": knowledge_base,
            "google_doc_links": google_doc_links,
            "messages": [AIMessage(content=knowledge_base, name="Professor")],
            "next_agent": "academic_advisor",
            "completed_agents": completed,
        }
    
    return professor_node


def _extract_google_doc_link(content: str) -> str | None:
    """Extract Google Doc URL from response content."""
    import re
    
    # Match Google Docs URLs
    pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_/-]*)?'
    match = re.search(pattern, content)
    
    return match.group(0) if match else None
