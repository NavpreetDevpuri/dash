from typing import Any
from langgraph.types import PregelTask


def safely_check_interrupts(agent_graph: Any, config: dict) -> bool:
    """
    Safely checks if there's an ongoing PregelTask that needs user input.
    
    Args:
        agent_graph: The agent graph to check state from
        config: Configuration dictionary for the agent graph
        
    Returns:
        bool: True if there's an ongoing PregelTask with interrupts, False otherwise
    """
    try:
        current_state = agent_graph.get_state(config)
        return (current_state and 
                isinstance(current_state[-1], (list, tuple)) and 
                isinstance(current_state[-1][0], PregelTask) and 
                hasattr(current_state[-1][0], 'interrupts') and 
                bool(current_state[-1][0].interrupts[0]))
    except Exception:
        return False

