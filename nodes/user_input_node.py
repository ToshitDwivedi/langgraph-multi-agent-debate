"""
UserInputNode - Handles CLI topic input and validation

This node:
1. Accepts the debate topic at runtime via CLI input
2. Validates topic length (10-500 characters)
3. Sanitizes content (removes HTML, special chars)
4. Initializes state with the validated topic
"""

import re
import html
from typing import Dict, Any
from datetime import datetime


def sanitize_topic(topic: str) -> str:
    """
    Sanitize the debate topic by removing HTML tags and special characters.
    
    Args:
        topic: Raw topic string from user input
        
    Returns:
        Cleaned topic string
    """
    # Remove HTML tags
    topic = html.unescape(topic)
    topic = re.sub(r'<[^>]+>', '', topic)
    
    # Remove control characters but keep basic punctuation
    topic = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', topic)
    
    # Normalize whitespace
    topic = ' '.join(topic.split())
    
    return topic.strip()


def validate_topic(topic: str, min_length: int = 10, max_length: int = 500) -> tuple[bool, str]:
    """
    Validate the debate topic.
    
    Args:
        topic: The sanitized topic string
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not topic:
        return False, "Topic cannot be empty."
    
    if len(topic) < min_length:
        return False, f"Topic too short. Minimum {min_length} characters required."
    
    if len(topic) > max_length:
        return False, f"Topic too long. Maximum {max_length} characters allowed."
    
    # Check for meaningful content (at least 2 words)
    words = topic.split()
    if len(words) < 2:
        return False, "Topic must contain at least 2 words."
    
    return True, ""


def user_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for processing user input.
    
    This node is called at the start of the workflow to validate
    and process the debate topic provided by the user.
    
    Args:
        state: Current state dict containing the topic
        
    Returns:
        Updated state with validated topic and log entry
    """
    config = state.get("config", {})
    settings = config.get("settings", {})
    
    min_length = settings.get("min_topic_length", 10)
    max_length = settings.get("max_topic_length", 500)
    
    # Sanitize topic
    raw_topic = state.get("topic", "")
    sanitized_topic = sanitize_topic(raw_topic)
    
    # Validate topic
    is_valid, error_message = validate_topic(sanitized_topic, min_length, max_length)
    
    if not is_valid:
        raise ValueError(f"Invalid topic: {error_message}")
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "UserInputNode",
        "event": "topic_validated",
        "data": {
            "original_topic": raw_topic,
            "sanitized_topic": sanitized_topic,
            "topic_length": len(sanitized_topic),
        }
    }
    
    # Return state updates
    return {
        "topic": sanitized_topic,
        "log_entries": state.get("log_entries", []) + [log_entry],
    }


def get_topic_from_cli() -> str:
    """
    Get the debate topic from CLI input.
    
    Returns:
        The user-provided topic string
    """
    print("\n" + "=" * 60)
    print("  MULTI-AGENT DEBATE SYSTEM")
    print("=" * 60)
    topic = input("\nEnter topic for debate: ").strip()
    return topic
