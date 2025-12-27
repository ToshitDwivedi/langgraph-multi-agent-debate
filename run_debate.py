#!/usr/bin/env python3
"""
Multi-Agent Debate CLI Runner

This script:
1. Parses CLI arguments
2. Loads configuration
3. Builds and runs the LangGraph workflow
4. Displays round-by-round output and final verdict
"""

import argparse
import os
import sys
import yaml
import random
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangGraph imports
from langgraph.graph import StateGraph, START, END

# Local imports
from nodes.state import DebateState, create_initial_state
from nodes.user_input_node import user_input_node, get_topic_from_cli
from nodes.agent_node import agent_node
from nodes.memory_node import memory_node
from nodes.rounds_controller import rounds_controller_node, should_continue
from nodes.judge_node import judge_node
from nodes.logger_node import logger_node, print_round_output, print_judge_output


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def build_debate_graph() -> StateGraph:
    """
    Build the LangGraph state graph for the debate workflow.
    
    The graph structure:
    UserInputNode → AgentNode → MemoryNode → LoggerNode → RoundsControllerNode
                                                        ↓
                                              (should_continue?)
                                                  ↓         ↓
                                            continue      judge
                                                ↓           ↓
                                           AgentNode    JudgeNode → LoggerNode → END
    """
    # Create the state graph
    workflow = StateGraph(DebateState)
    
    # Add nodes
    workflow.add_node("user_input", user_input_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("logger", logger_node)
    workflow.add_node("controller", rounds_controller_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("final_logger", logger_node)
    
    # Define edges
    # Start → UserInput → Agent (first round)
    workflow.add_edge(START, "user_input")
    workflow.add_edge("user_input", "agent")
    
    # Agent → Memory → Logger → Controller
    workflow.add_edge("agent", "memory")
    workflow.add_edge("memory", "logger")
    workflow.add_edge("logger", "controller")
    
    # Controller → conditional edge (continue or judge)
    workflow.add_conditional_edges(
        "controller",
        should_continue,
        {
            "continue": "agent",
            "judge": "judge",
        }
    )
    
    # Judge → FinalLogger → END
    workflow.add_edge("judge", "final_logger")
    workflow.add_edge("final_logger", END)
    
    return workflow.compile()


def run_debate(
    topic: str,
    config: dict,
    seed: Optional[int] = None,
) -> dict:
    """
    Run the complete debate workflow.
    
    Args:
        topic: The debate topic
        config: Configuration dict
        seed: Optional random seed for reproducibility
        
    Returns:
        Final state dict
    """
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
    
    # Create initial state
    initial_state = create_initial_state(topic, config, seed)
    
    # Build and compile the graph
    graph = build_debate_graph()
    
    # Get persona names for display
    personas = config.get("personas", {})
    agent_a_name = personas.get("agent_a", {}).get("name", "AgentA")
    agent_b_name = personas.get("agent_b", {}).get("name", "AgentB")
    
    print(f"\nStarting debate between {agent_a_name} and {agent_b_name}...")
    print("-" * 60)
    
    # Track the last printed round to avoid duplicates
    last_printed_round = 0
    final_state = None
    
    # Run the graph with streaming to show progress
    # Set recursion_limit high enough for 8 rounds (each round = ~5 steps)
    config_run = {"recursion_limit": 100}
    for state_update in graph.stream(initial_state, config=config_run):
        # Get the latest state from the update
        for node_name, node_state in state_update.items():
            # After memory node, print the round output
            if node_name == "memory":
                turns = node_state.get("turns", [])
                if turns and len(turns) > last_printed_round:
                    latest_turn = turns[-1]
                    round_num = latest_turn.get("round", 0)
                    agent = latest_turn.get("agent", "Unknown")
                    text = latest_turn.get("text", "")
                    print(f"\n[Round {round_num}] {agent}:")
                    print(text)
                    last_printed_round = len(turns)
            
            # After judge node, store for final output
            if node_name == "judge":
                final_state = node_state
            
            # After final_logger, get log path
            if node_name == "final_logger":
                if final_state:
                    final_state.update(node_state)
                else:
                    final_state = node_state
    
    # Print final verdict
    if final_state:
        summary = final_state.get("debate_summary", "")
        winner = final_state.get("winner", "")
        verdict = final_state.get("verdict", "")
        
        winner_name = agent_a_name if winner == "AgentA" else agent_b_name
        
        print("\n" + "=" * 60)
        print("[Judge] Summary of debate:")
        print(summary)
        print("\n" + "-" * 60)
        print(f"[Judge] Winner: {winner_name}")
        print(f"Reason: {verdict}")
        print("=" * 60)
        
        # Print log file location
        log_path = final_state.get("log_path", "")
        if log_path:
            print(f"\nDebate log saved to: {log_path}")
    
    return final_state


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Debate System using LangGraph"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible agent behavior"
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        help="Custom log directory path"
    )
    parser.add_argument(
        "--persona-config",
        type=str,
        default="config.yaml",
        help="Path to persona/config YAML file"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Debate topic (if not provided, will prompt interactively)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.persona_config)
    
    # Override log path if provided
    if args.log_path:
        if "logging" not in config:
            config["logging"] = {}
        config["logging"]["log_dir"] = args.log_path
    
    # Get topic from CLI argument or prompt
    if args.topic:
        topic = args.topic
    else:
        topic = get_topic_from_cli()
    
    if not topic:
        print("Error: No topic provided. Exiting.")
        sys.exit(1)
    
    try:
        # Run the debate
        final_state = run_debate(
            topic=topic,
            config=config,
            seed=args.seed,
        )
        
        print("\nDebate completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nDebate interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during debate: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
