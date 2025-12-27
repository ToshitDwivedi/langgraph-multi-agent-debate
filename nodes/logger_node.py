"""
LoggerNode - Persistent logging of all events

This node:
1. Writes all node messages and state transitions to a log file
2. Includes timestamps for every event
3. Writes memory snapshots periodically
4. Outputs the final verdict
"""

import json
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path


def ensure_log_directory(log_dir: str) -> Path:
    """Ensure the log directory exists."""
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_log_filename(log_dir: str) -> str:
    """Generate a timestamped log filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path(log_dir) / f"debate_log_{timestamp}.json")


def write_log_file(log_path: str, log_entries: list, state: Dict[str, Any]):
    """
    Write the complete log file.
    
    Args:
        log_path: Path to the log file
        log_entries: List of log entry dicts
        state: Current state for final summary
    """
    config = state.get("config", {})
    personas_config = config.get("personas", {})
    
    log_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "topic": state.get("topic", ""),
            "total_rounds": state.get("total_rounds", 8),
            "agent_a": personas_config.get("agent_a", {}).get("name", "AgentA"),
            "agent_b": personas_config.get("agent_b", {}).get("name", "AgentB"),
            "seed": state.get("seed"),
        },
        "events": log_entries,
        "final_state": {
            "turns": state.get("turns", []),
            "summary": state.get("summary", ""),
            "winner": state.get("winner"),
            "verdict": state.get("verdict"),
            "debate_summary": state.get("debate_summary"),
            "coherence_issues": state.get("coherence_issues", []),
            "duplicate_warnings": state.get("duplicate_warnings", []),
        }
    }
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)


def logger_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for logging.
    
    This node is called after each major state transition to:
    1. Record the current state of the debate
    2. Log any issues or warnings
    
    For the final call (after JudgeNode), it writes the complete log file.
    
    Args:
        state: Current state dict
        
    Returns:
        Updated state (minimal changes, mainly for log file path)
    """
    config = state.get("config", {})
    logging_config = config.get("logging", {})
    
    log_dir = logging_config.get("log_dir", "logs")
    is_complete = state.get("is_complete", False)
    has_verdict = state.get("winner") is not None
    
    log_entries = state.get("log_entries", [])
    
    # Add logger node event
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "LoggerNode",
        "event": "state_logged",
        "data": {
            "current_round": state.get("current_round", 1),
            "is_complete": is_complete,
            "has_verdict": has_verdict,
            "total_events": len(log_entries),
        }
    }
    log_entries = log_entries + [log_entry]
    
    # Write log file if debate is complete and verdict is available
    if is_complete and has_verdict:
        ensure_log_directory(log_dir)
        log_path = generate_log_filename(log_dir)
        
        # Update state with log entries before writing
        state_with_logs = dict(state)
        state_with_logs["log_entries"] = log_entries
        
        write_log_file(log_path, log_entries, state_with_logs)
        
        # Add final log write event
        final_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "node": "LoggerNode",
            "event": "log_file_written",
            "data": {
                "log_path": log_path,
            }
        }
        log_entries = log_entries + [final_log_entry]
        
        return {
            "log_entries": log_entries,
            "log_path": log_path,
        }
    
    return {
        "log_entries": log_entries,
    }


def print_round_output(state: Dict[str, Any]):
    """Print the latest round output to CLI."""
    turns = state.get("turns", [])
    if not turns:
        return
    
    latest_turn = turns[-1]
    round_num = latest_turn.get("round", "?")
    agent = latest_turn.get("agent", "Unknown")
    text = latest_turn.get("text", "")
    
    print(f"\n[Round {round_num}] {agent}:")
    print(text)


def print_judge_output(state: Dict[str, Any]):
    """Print the judge's verdict to CLI."""
    summary = state.get("debate_summary", "")
    winner = state.get("winner", "")
    winner_name = ""
    verdict = state.get("verdict", "")
    
    config = state.get("config", {})
    personas_config = config.get("personas", {})
    
    if winner == "AgentA":
        winner_name = personas_config.get("agent_a", {}).get("name", "AgentA")
    else:
        winner_name = personas_config.get("agent_b", {}).get("name", "AgentB")
    
    print("\n" + "=" * 60)
    print("[Judge] Summary of debate:")
    print(summary)
    print("\n" + "-" * 60)
    print(f"[Judge] Winner: {winner_name}")
    print(f"Reason: {verdict}")
    print("=" * 60)
