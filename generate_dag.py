#!/usr/bin/env python3
"""
DAG Visualization Generator

Generates a visual representation of the Multi-Agent Debate workflow
as a PNG and SVG file using Graphviz.
"""

import os
from pathlib import Path

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False
    print("Warning: graphviz package not installed. Install with: pip install graphviz")


def create_dag_diagram() -> str:
    """
    Create the DOT representation of the debate DAG.
    
    Returns:
        DOT format string
    """
    dot_content = '''
digraph DebateDAG {
    // Graph settings
    rankdir=TB;
    splines=ortho;
    nodesep=0.8;
    ranksep=1.0;
    
    // Node styles
    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=12];
    
    // Start and End nodes
    START [label="START", shape=circle, fillcolor="#4CAF50", fontcolor="white"];
    END [label="END", shape=doublecircle, fillcolor="#f44336", fontcolor="white"];
    
    // Input node
    UserInput [label="UserInputNode\\n(Topic Validation)", fillcolor="#2196F3", fontcolor="white"];
    
    // Agent nodes
    AgentA [label="AgentNode\\n(Scientist)", fillcolor="#FF9800", fontcolor="white"];
    AgentB [label="AgentNode\\n(Philosopher)", fillcolor="#9C27B0", fontcolor="white"];
    
    // Processing nodes
    Memory [label="MemoryNode\\n(Transcript & Summary)", fillcolor="#00BCD4", fontcolor="white"];
    Logger [label="LoggerNode\\n(Event Logging)", fillcolor="#607D8B", fontcolor="white"];
    Controller [label="RoundsControllerNode\\n(Turn Enforcement)", fillcolor="#795548", fontcolor="white"];
    
    // Judge node
    Judge [label="JudgeNode\\n(Verdict & Summary)", fillcolor="#E91E63", fontcolor="white"];
    FinalLogger [label="LoggerNode\\n(Final Log Write)", fillcolor="#607D8B", fontcolor="white"];
    
    // Decision node
    Decision [label="Round < 8?", shape=diamond, fillcolor="#FFC107", fontcolor="black"];
    
    // Edges
    START -> UserInput;
    UserInput -> AgentA [label="Round 1"];
    
    // Odd rounds (1, 3, 5, 7) - AgentA
    AgentA -> Memory;
    
    // Even rounds (2, 4, 6, 8) - AgentB
    AgentB -> Memory;
    
    Memory -> Logger;
    Logger -> Controller;
    Controller -> Decision;
    
    Decision -> AgentB [label="Yes (odd round done)"];
    Decision -> AgentA [label="Yes (even round done)"];
    Decision -> Judge [label="No (Round 8 done)"];
    
    Judge -> FinalLogger;
    FinalLogger -> END;
    
    // Subgraph for debate loop
    subgraph cluster_debate_loop {
        label = "Debate Loop (8 Rounds)";
        style = dashed;
        color = "#9E9E9E";
        AgentA;
        AgentB;
        Memory;
        Logger;
        Controller;
        Decision;
    }
}
'''
    return dot_content


def save_dag_files(output_dir: str = "."):
    """
    Generate and save the DAG diagram as a Mermaid markdown file.
    
    Args:
        output_dir: Directory to save the output files
    """
    # Create a Mermaid diagram
    mermaid_content = """```mermaid
flowchart TD
    START([START]) --> UI[UserInputNode<br/>Topic Validation]
    UI --> AGENT[AgentNode<br/>Scientist/Philosopher]
    AGENT --> MEM[MemoryNode<br/>Transcript & Summary]
    MEM --> LOG[LoggerNode<br/>Event Logging]
    LOG --> CTRL[RoundsControllerNode<br/>Turn Enforcement]
    CTRL --> |Round < 8| AGENT
    CTRL --> |Round = 8| JUDGE[JudgeNode<br/>Verdict & Summary]
    JUDGE --> FLOG[LoggerNode<br/>Final Log Write]
    FLOG --> END([END])
    
    subgraph debate_loop[Debate Loop - 8 Rounds]
        AGENT
        MEM
        LOG
        CTRL
    end
```"""
    mermaid_path = Path(output_dir) / "dag.md"
    with open(mermaid_path, 'w') as f:
        f.write("# Multi-Agent Debate DAG Diagram\n\n")
        f.write(mermaid_content)
    print(f"Mermaid diagram saved to: {mermaid_path}")



def main():
    """Main entry point."""
    print("Generating DAG visualization...")
    print("-" * 40)
    
    # Generate static Graphviz diagram
    save_dag_files(".")
    
    print("-" * 40)
    print("\nDone!")


if __name__ == "__main__":
    main()
