"""
MemoryNode - Structured debate memory management

This node:
1. Maintains the debate transcript (list of turns)
2. Updates after each agent turn
3. Generates running summaries
4. Provides agent-specific memory slices
"""

from typing import Dict, Any, List
from datetime import datetime


def create_turn_entry(
    round_num: int,
    agent_id: str,
    agent_name: str,
    text: str,
) -> dict:
    """
    Create a turn entry for the debate transcript.
    
    Args:
        round_num: The round number
        agent_id: "AgentA" or "AgentB"
        agent_name: Display name (e.g., "Scientist")
        text: The argument text
        
    Returns:
        Turn entry dict
    """
    return {
        "round": round_num,
        "agent": agent_name,
        "agent_id": agent_id,
        "text": text,
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "word_count": len(text.split()),
        }
    }


def generate_summary(turns: List[dict], topic: str) -> str:
    """
    Generate a running summary of the debate.
    
    This creates a concise summary of key points from each side.
    
    Args:
        turns: List of turn entries
        topic: The debate topic
        
    Returns:
        Summary string
    """
    if not turns:
        return ""
    
    agent_a_points = []
    agent_b_points = []
    
    for turn in turns:
        agent_id = turn.get("agent_id", "")
        text = turn.get("text", "")
        
        # Extract first sentence as key point (simple heuristic)
        sentences = text.split('.')
        key_point = sentences[0].strip()[:100] if sentences else text[:100]
        
        if agent_id == "AgentA":
            agent_a_points.append(key_point)
        else:
            agent_b_points.append(key_point)
    
    summary_parts = [f"Debate on: {topic}"]
    
    if agent_a_points:
        agent_a_name = turns[0].get("agent", "AgentA") if turns[0].get("agent_id") == "AgentA" else "AgentA"
        for i, t in enumerate(turns):
            if t.get("agent_id") == "AgentA":
                agent_a_name = t.get("agent", "AgentA")
                break
        summary_parts.append(f"\n{agent_a_name}'s key points: " + "; ".join(agent_a_points[:3]))
    
    if agent_b_points:
        agent_b_name = "AgentB"
        for t in turns:
            if t.get("agent_id") == "AgentB":
                agent_b_name = t.get("agent", "AgentB")
                break
        summary_parts.append(f"\n{agent_b_name}'s key points: " + "; ".join(agent_b_points[:3]))
    
    return "".join(summary_parts)


def extract_agent_memory(turns: List[dict], agent_id: str) -> List[dict]:
    """
    Extract memory slice relevant to a specific agent.
    
    Each agent sees all turns but organized for their context.
    
    Args:
        turns: All debate turns
        agent_id: "AgentA" or "AgentB"
        
    Returns:
        List of relevant turn entries
    """
    # For now, return all turns - agents see the full transcript
    # but formatted appropriately in agent_node
    return turns


def memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for memory management.
    
    Called after each agent turn to:
    1. Add the new argument to the transcript
    2. Update the debate summary
    3. Prepare memory slices for each agent
    
    Args:
        state: Current state dict
        
    Returns:
        Updated state with new turn and memory
    """
    config = state.get("config", {})
    personas_config = config.get("personas", {})
    
    current_agent = state.get("current_agent", "AgentA")
    current_round = state.get("current_round", 1)
    current_argument = state.get("current_argument", "")
    topic = state.get("topic", "")
    turns = state.get("turns", []).copy()
    
    # Get agent display name
    if current_agent == "AgentA":
        agent_name = personas_config.get("agent_a", {}).get("name", "AgentA")
    else:
        agent_name = personas_config.get("agent_b", {}).get("name", "AgentB")
    
    # Create and add new turn entry
    new_turn = create_turn_entry(
        round_num=current_round,
        agent_id=current_agent,
        agent_name=agent_name,
        text=current_argument,
    )
    turns.append(new_turn)
    
    # Generate updated summary
    summary = generate_summary(turns, topic)
    
    # Extract memory slices for each agent
    agent_a_memory = extract_agent_memory(turns, "AgentA")
    agent_b_memory = extract_agent_memory(turns, "AgentB")
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "MemoryNode",
        "event": "memory_updated",
        "data": {
            "total_turns": len(turns),
            "current_round": current_round,
            "summary_length": len(summary),
        }
    }
    
    # Memory snapshot for logging
    memory_snapshot = {
        "timestamp": datetime.now().isoformat(),
        "node": "MemoryNode",
        "event": "memory_snapshot",
        "data": {
            "turns": turns,
            "summary": summary,
        }
    }
    
    return {
        "turns": turns,
        "summary": summary,
        "agent_a_memory": agent_a_memory,
        "agent_b_memory": agent_b_memory,
        "current_argument": None,  # Clear after storing
        "log_entries": state.get("log_entries", []) + [log_entry, memory_snapshot],
    }
