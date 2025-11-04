"""Agent state definition."""

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State for the agent workflow."""
    
    messages: List[BaseMessage]
    user_input: str
    steps: List[Dict[str, Any]]
    final_answer: Optional[str]
