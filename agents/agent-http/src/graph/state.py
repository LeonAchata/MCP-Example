"""State definition for LangGraph workflow."""

from typing import List, Optional, TypedDict, Annotated
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for the agent workflow."""
    
    messages: Annotated[List, add_messages]  # Message history with reducer
    user_input: str  # Original user input
    final_answer: Optional[str]  # Final response
    steps: List[dict]  # Execution steps for debugging
