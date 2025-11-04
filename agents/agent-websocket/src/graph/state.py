"""Agent state definition."""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for the agent workflow."""
    
    messages: Annotated[List[BaseMessage], add_messages]  # Message history with reducer
    user_input: str
    steps: List[Dict[str, Any]]
    final_answer: Optional[str]
