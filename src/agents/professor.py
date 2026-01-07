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
from .utils import save_content_to_google_docs


PROFESSOR_SYSTEM_PROMPT = """You are the Professor - a Research and Knowledge Specialist for the AI Teaching Agent Team.

Your role is to create a comprehensive knowledge base that serves as the foundation for learning a new topic.

## Your Responsibilities:
1. **Explain from First Principles**: Start with the absolute basics and build up understanding gradually
2. **Cover Key Terminology**: Define all important terms and concepts clearly  
3. **Explain Core Principles**: Describe the fundamental ideas that underpin the topic
4. **Include Practical Applications**: Show how the concepts apply in real-world scenarios
5. **Address Common Misconceptions**: Clarify areas where learners often get confused
6. **Provide Examples**: Include concrete examples for each major concept

## Content Structure:
1. **Introduction & Overview** - What is this topic and why is it important?
2. **Key Terminology** - Define essential terms (as many as the topic requires)
3. **Core Concepts** - Deep dive into fundamental principles
4. **How It Works** - Technical explanation with examples
5. **Practical Applications** - Real-world use cases
6. **Common Mistakes & Misconceptions** - What to avoid
7. **Summary & Key Takeaways** - Recap the main points

## Current Topic: {topic}

## IMPORTANT INSTRUCTIONS:
- **Adapt your length to the topic's complexity**: Simple topics need concise explanations. Complex topics may require extensive, detailed coverage.
- Be as thorough as the topic demands - there is no word limit
- Write the full educational content in your response"""


PROFESSOR_HUMAN_PROMPT = """Please create a comprehensive knowledge base for the topic: {topic}

Create a detailed, well-structured educational document covering:
1. Introduction and overview (why this topic matters)
2. Key terminology with clear definitions
3. Core concepts explained from first principles
4. Practical examples and applications
5. Common mistakes and how to avoid them
6. Summary and key takeaways

**Match your depth and length to the topic's complexity** - be concise for simple topics, be thorough and extensive for complex ones."""


def create_professor_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Professor agent node for the LangGraph.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", PROFESSOR_SYSTEM_PROMPT),
        ("human", PROFESSOR_HUMAN_PROMPT),
    ])
    
    def professor_node(state: TeachingState) -> dict:
        """Execute the Professor agent."""
        topic = state["topic"]
        
        # Generate content
        messages = prompt.format_messages(topic=topic)
        response = llm.invoke(messages)
        
        if hasattr(response, 'content') and response.content:
            knowledge_base = response.content
        else:
            knowledge_base = str(response)
        
        # Save to Google Docs
        google_doc_links = state.get("google_doc_links", {}).copy()
        doc_link = save_content_to_google_docs(
            tools, 
            f"Knowledge Base: {topic}", 
            knowledge_base
        )
        if doc_link:
            google_doc_links["professor"] = doc_link
            knowledge_base += f"\n\n---\n📄 **Google Doc**: [{doc_link}]({doc_link})"
        
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
