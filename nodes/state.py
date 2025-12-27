"""
State Schema for Multi-Agent Debate DAG

Defines the TypedDict state structure that flows through all LangGraph nodes.
"""

from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json


@dataclass
class TurnEntry:
    """Represents a single turn in the debate."""
    round: int
    agent: str  # "Scientist" or "Philosopher"
    agent_id: str  # "AgentA" or "AgentB"
    text: str
    meta: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TurnEntry":
        return cls(**data)


class DebateState(TypedDict):
    """
    Main state schema for the debate workflow.
    
    This TypedDict defines all state that flows through the LangGraph.
    Each node receives and returns updates to this state.
    """
    # Core debate information
    topic: str                          # The debate topic from user input
    
    # Round tracking
    current_round: int                  # Current round number (1-8)
    current_agent: str                  # "AgentA" or "AgentB"
    total_rounds: int                   # Total rounds (default 8)
    
    # Debate transcript
    turns: List[dict]                   # List of TurnEntry dicts
    
    # Memory management
    summary: str                        # Running summary of the debate
    agent_a_memory: List[dict]          # Memory slice for AgentA
    agent_b_memory: List[dict]          # Memory slice for AgentB
    
    # Validation tracking
    coherence_issues: List[str]         # Detected coherence issues
    duplicate_warnings: List[str]       # Duplicate argument warnings
    
    # Completion state
    is_complete: bool                   # Whether debate is finished
    
    # Judge output
    winner: Optional[str]               # "AgentA" or "AgentB"
    verdict: Optional[str]              # Judge's full verdict
    debate_summary: Optional[str]       # Final debate summary
    
    # Logging
    log_entries: List[dict]             # All logged events
    
    # Configuration
    config: dict                        # Runtime configuration
    seed: Optional[int]                 # Random seed for reproducibility
    
    # Current argument (temporary, for passing between nodes)
    current_argument: Optional[str]     # The argument just generated


def create_initial_state(topic: str, config: dict, seed: Optional[int] = None) -> DebateState:
    """Create the initial state for a new debate."""
    return DebateState(
        topic=topic,
        current_round=1,
        current_agent="AgentA",
        total_rounds=config.get("settings", {}).get("total_rounds", 8),
        turns=[],
        summary="",
        agent_a_memory=[],
        agent_b_memory=[],
        coherence_issues=[],
        duplicate_warnings=[],
        is_complete=False,
        winner=None,
        verdict=None,
        debate_summary=None,
        log_entries=[],
        config=config,
        seed=seed,
        current_argument=None,
    )


def state_to_json(state: DebateState) -> str:
    """Convert state to JSON string for logging."""
    return json.dumps(dict(state), indent=2, default=str)
