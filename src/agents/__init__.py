# Agent implementations
from .professor import create_professor_node
from .academic_advisor import create_academic_advisor_node
from .research_librarian import create_research_librarian_node
from .teaching_assistant import create_teaching_assistant_node

__all__ = [
    "create_professor_node",
    "create_academic_advisor_node", 
    "create_research_librarian_node",
    "create_teaching_assistant_node",
]
