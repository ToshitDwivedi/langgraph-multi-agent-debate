"""
AgentNode - Debate agents with persona-based argument generation

This node handles both AgentA (Scientist) and AgentB (Philosopher).
Each agent:
1. Receives their persona prompt from config
2. Gets agent-specific memory (not full state)
3. Generates arguments using the LLM
4. Avoids repeating previous arguments
"""

import os
import random
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# LLM imports - supporting multiple providers
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

from langchain_core.messages import HumanMessage, SystemMessage


def load_persona(persona_file: str, base_path: str = ".") -> str:
    """Load persona prompt from file."""
    path = Path(base_path) / persona_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Fallback to default prompts
    return "You are a debate participant. Present thoughtful arguments."


def get_llm(config: dict, seed: Optional[int] = None):
    """
    Initialize the LLM based on configuration.
    
    Args:
        config: Configuration dict with LLM settings
        seed: Optional random seed for reproducibility
        
    Returns:
        LLM instance
    """
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "groq")
    model = llm_config.get("model", "llama-3.3-70b-versatile")
    temperature = llm_config.get("temperature", 0.7)
    max_tokens = llm_config.get("max_tokens", 500)
    
    if seed is not None:
        random.seed(seed)
        # Reduce temperature for more deterministic output
        temperature = min(temperature, 0.3)
    
    if provider == "groq" and ChatGroq:
        return ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "openai" and ChatOpenAI:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "google" and ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Available: groq, openai, google")


def format_memory_for_agent(state: Dict[str, Any], agent_id: str) -> str:
    """
    Format the relevant memory slice for an agent.
    
    Each agent sees:
    - All opponent's previous arguments
    - Their own previous arguments
    - A summary of the debate so far
    
    Args:
        state: Current state dict
        agent_id: "AgentA" or "AgentB"
        
    Returns:
        Formatted memory string for the prompt
    """
    turns = state.get("turns", [])
    summary = state.get("summary", "")
    
    if not turns:
        return "This is the opening round. No prior arguments have been made."
    
    memory_parts = []
    
    # Add debate summary if available
    if summary:
        memory_parts.append(f"**Debate Summary So Far:**\n{summary}\n")
    
    # Format previous turns
    memory_parts.append("**Previous Arguments:**")
    for turn in turns:
        speaker = turn.get("agent", "Unknown")
        text = turn.get("text", "")
        round_num = turn.get("round", 0)
        memory_parts.append(f"\n[Round {round_num}] {speaker}:\n{text}")
    
    return "\n".join(memory_parts)


def build_agent_prompt(
    topic: str,
    persona: str,
    memory: str,
    agent_name: str,
    current_round: int,
    total_rounds: int,
) -> list:
    """
    Build the prompt messages for the agent.
    
    Args:
        topic: The debate topic
        persona: The agent's persona prompt
        memory: Formatted memory of previous turns
        agent_name: "Scientist" or "Philosopher"
        current_round: Current round number
        total_rounds: Total rounds in debate
        
    Returns:
        List of messages for the LLM
    """
    system_prompt = f"""{persona}

**Current Debate Context:**
- Topic: {topic}
- You are: {agent_name}
- Current Round: {current_round} of {total_rounds}

**Instructions:**
1. Present a clear, compelling argument on your position
2. Address points made by your opponent (if any)
3. DO NOT repeat arguments you've already made
4. Keep your response focused and under 150 words
5. Stay on topic and maintain logical coherence

{memory}
"""

    user_prompt = f"""Present your argument for Round {current_round} on the topic: "{topic}"

Remember: You must present a NEW argument or perspective. Do not repeat previous points."""

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]


def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for agent argument generation.
    
    This node:
    1. Determines which agent should speak
    2. Loads the appropriate persona
    3. Prepares agent-specific memory
    4. Generates the argument via LLM
    
    Args:
        state: Current state dict
        
    Returns:
        Updated state with the new argument
    """
    config = state.get("config", {})
    current_agent = state.get("current_agent", "AgentA")
    current_round = state.get("current_round", 1)
    total_rounds = state.get("total_rounds", 8)
    topic = state.get("topic", "")
    seed = state.get("seed")
    
    # Get persona config
    personas_config = config.get("personas", {})
    
    if current_agent == "AgentA":
        persona_config = personas_config.get("agent_a", {})
    else:
        persona_config = personas_config.get("agent_b", {})
    
    agent_name = persona_config.get("name", current_agent)
    persona_file = persona_config.get("prompt_file", "")
    
    # Load persona prompt
    persona = load_persona(persona_file)
    
    # Get agent-specific memory
    memory = format_memory_for_agent(state, current_agent)
    
    # Build prompt
    messages = build_agent_prompt(
        topic=topic,
        persona=persona,
        memory=memory,
        agent_name=agent_name,
        current_round=current_round,
        total_rounds=total_rounds,
    )
    
    # Generate argument
    llm = get_llm(config, seed)
    response = llm.invoke(messages)
    argument = response.content.strip()
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "AgentNode",
        "event": "argument_generated",
        "data": {
            "agent": current_agent,
            "agent_name": agent_name,
            "round": current_round,
            "argument_length": len(argument),
        }
    }
    
    return {
        "current_argument": argument,
        "log_entries": state.get("log_entries", []) + [log_entry],
    }
