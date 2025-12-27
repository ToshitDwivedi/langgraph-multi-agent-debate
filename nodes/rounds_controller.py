"""
RoundsControllerNode - Turn sequencing and enforcement

This node:
1. Enforces the 8-round limit (4 turns per agent)
2. Validates turn order (AgentA odd rounds, AgentB even rounds)
3. Checks for duplicate arguments
4. Detects topic drift via keyword analysis
"""

import difflib
import re
from typing import Dict, Any, List, Literal
from datetime import datetime


def extract_keywords(text: str) -> set:
    """
    Extract significant keywords from text.
    
    Removes common stop words and returns unique keywords.
    """
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    }
    
    # Extract words, lowercase, filter
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return {w for w in words if w not in stop_words}


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate string similarity between two texts.
    
    Uses difflib's SequenceMatcher for similarity ratio.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def check_duplicate_argument(
    new_argument: str,
    previous_turns: List[dict],
    agent_id: str,
    threshold: float = 0.85,
) -> tuple[bool, str]:
    """
    Check if the new argument is too similar to previous ones.
    
    Args:
        new_argument: The new argument to check
        previous_turns: List of previous turn entries
        agent_id: The agent making the argument
        threshold: Similarity threshold for duplicate detection
        
    Returns:
        Tuple of (is_duplicate, warning_message)
    """
    # Only check against the same agent's previous arguments
    agent_turns = [t for t in previous_turns if t.get("agent_id") == agent_id]
    
    for turn in agent_turns:
        prev_text = turn.get("text", "")
        similarity = calculate_similarity(new_argument, prev_text)
        
        if similarity >= threshold:
            round_num = turn.get("round", "?")
            return True, f"Argument too similar to Round {round_num} (similarity: {similarity:.2%})"
    
    return False, ""


def check_topic_drift(
    argument: str,
    topic: str,
    threshold: float = 0.3,
) -> tuple[bool, str]:
    """
    Check if the argument has drifted from the main topic.
    
    Uses keyword overlap to measure relevance.
    
    Args:
        argument: The argument to check
        topic: The original debate topic
        threshold: Minimum keyword overlap ratio
        
    Returns:
        Tuple of (has_drifted, warning_message)
    """
    topic_keywords = extract_keywords(topic)
    argument_keywords = extract_keywords(argument)
    
    if not topic_keywords:
        return False, ""
    
    # Calculate overlap
    overlap = topic_keywords & argument_keywords
    overlap_ratio = len(overlap) / len(topic_keywords) if topic_keywords else 1.0
    
    if overlap_ratio < threshold:
        return True, f"Possible topic drift detected (keyword overlap: {overlap_ratio:.2%})"
    
    return False, ""


def validate_turn_order(current_round: int, current_agent: str) -> tuple[bool, str]:
    """
    Validate that the correct agent is speaking.
    
    AgentA speaks on odd rounds (1, 3, 5, 7)
    AgentB speaks on even rounds (2, 4, 6, 8)
    
    Args:
        current_round: The current round number
        current_agent: The agent attempting to speak
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    expected_agent = "AgentA" if current_round % 2 == 1 else "AgentB"
    
    if current_agent != expected_agent:
        return False, f"Turn order violation: Expected {expected_agent} for round {current_round}"
    
    return True, ""


def rounds_controller_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for round control and validation.
    
    Called after MemoryNode to:
    1. Check for argument duplicates
    2. Detect coherence issues
    3. Advance to next round or complete debate
    
    Args:
        state: Current state dict
        
    Returns:
        Updated state with validation results
    """
    config = state.get("config", {})
    settings = config.get("settings", {})
    
    current_round = state.get("current_round", 1)
    current_agent = state.get("current_agent", "AgentA")
    total_rounds = state.get("total_rounds", 8)
    topic = state.get("topic", "")
    turns = state.get("turns", [])
    
    similarity_threshold = settings.get("similarity_threshold", 0.85)
    drift_threshold = settings.get("topic_drift_threshold", 0.3)
    
    coherence_issues = state.get("coherence_issues", []).copy()
    duplicate_warnings = state.get("duplicate_warnings", []).copy()
    
    # Get the latest argument
    latest_turn = turns[-1] if turns else None
    latest_argument = latest_turn.get("text", "") if latest_turn else ""
    
    # Check for duplicates (against previous turns, not including current)
    previous_turns = turns[:-1] if len(turns) > 1 else []
    is_duplicate, dup_warning = check_duplicate_argument(
        latest_argument, previous_turns, current_agent, similarity_threshold
    )
    if is_duplicate:
        duplicate_warnings.append(f"Round {current_round}: {dup_warning}")
    
    # Check for topic drift
    has_drifted, drift_warning = check_topic_drift(
        latest_argument, topic, drift_threshold
    )
    if has_drifted:
        coherence_issues.append(f"Round {current_round}: {drift_warning}")
    
    # Determine next state
    is_complete = current_round >= total_rounds
    next_round = current_round + 1 if not is_complete else current_round
    next_agent = "AgentB" if current_agent == "AgentA" else "AgentA"
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "RoundsControllerNode",
        "event": "round_completed",
        "data": {
            "completed_round": current_round,
            "agent": current_agent,
            "is_complete": is_complete,
            "next_round": next_round,
            "next_agent": next_agent if not is_complete else None,
            "duplicate_detected": is_duplicate,
            "topic_drift_detected": has_drifted,
        }
    }
    
    return {
        "current_round": next_round,
        "current_agent": next_agent,
        "is_complete": is_complete,
        "coherence_issues": coherence_issues,
        "duplicate_warnings": duplicate_warnings,
        "log_entries": state.get("log_entries", []) + [log_entry],
    }


def should_continue(state: Dict[str, Any]) -> Literal["continue", "judge"]:
    """
    Conditional edge function to determine next node.
    
    Args:
        state: Current state dict
        
    Returns:
        "continue" to continue debate, "judge" to go to JudgeNode
    """
    if state.get("is_complete", False):
        return "judge"
    return "continue"
