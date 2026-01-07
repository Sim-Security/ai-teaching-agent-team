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
from .utils import execute_agent_with_tools, save_content_to_google_docs


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

## IMPORTANT:
- Focus on creating original, practical exercises
- Adapt quantity and complexity to the topic
- Write your complete practice materials in your response"""


TEACHING_ASSISTANT_HUMAN_PROMPT = """Create comprehensive practice materials for: {topic}

Design exercises, quizzes, and projects that:
1. Align with the learning roadmap phases
2. Reinforce knowledge base concepts
3. Progress from beginner to advanced
4. Include solutions and explanations

Provide your complete practice materials with exercises and solutions."""


def create_teaching_assistant_node(
    llm: BaseChatModel,
    tools: list[BaseTool],
) -> Callable[[TeachingState], dict]:
    """
    Create the Teaching Assistant agent node for the LangGraph.
    
    Creates practice materials, optionally using search for examples.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", TEACHING_ASSISTANT_SYSTEM_PROMPT),
        ("human", TEACHING_ASSISTANT_HUMAN_PROMPT),
    ])
    
    def get_search_tools(all_tools):
        return [t for t in all_tools if 'search' in t.name.lower()]
    
    def get_docs_tools(all_tools):
        return [t for t in all_tools if 'doc' in t.name.lower()]
    
    def teaching_assistant_node(state: TeachingState) -> dict:
        """Execute the Teaching Assistant agent."""
        topic = state["topic"]
        knowledge_base = state.get("knowledge_base", "Not yet available")
        roadmap = state.get("roadmap", "Not yet available")
        
        kb_summary = knowledge_base[:3000] + "..." if len(knowledge_base) > 3000 else knowledge_base
        roadmap_summary = roadmap[:3000] + "..." if len(roadmap) > 3000 else roadmap
        
        messages = prompt.format_messages(
            topic=topic,
            knowledge_base=kb_summary,
            roadmap=roadmap_summary
        )
        
        # Use search tools if available for finding example problems
        search_tools = get_search_tools(tools)
        if search_tools:
            practice_materials = execute_agent_with_tools(llm, search_tools, messages, max_iterations=3)
        else:
            # No search tools - generate directly
            response = llm.invoke(messages)
            practice_materials = response.content if hasattr(response, 'content') else str(response)
        
        # Save to Google Docs
        google_doc_links = state.get("google_doc_links", {}).copy()
        docs_tools = get_docs_tools(tools)
        doc_link = save_content_to_google_docs(
            docs_tools,
            f"Practice Materials: {topic}",
            practice_materials
        )
        if doc_link:
            google_doc_links["teaching_assistant"] = doc_link
            practice_materials += f"\n\n---\n📄 **Google Doc**: [{doc_link}]({doc_link})"
        
        completed = state.get("completed_agents", []).copy()
        completed.append("teaching_assistant")
        
        return {
            "practice_materials": practice_materials,
            "google_doc_links": google_doc_links,
            "messages": [AIMessage(content=practice_materials, name="Teaching Assistant")],
            "next_agent": "FINISH",
            "completed_agents": completed,
        }
    
    return teaching_assistant_node
