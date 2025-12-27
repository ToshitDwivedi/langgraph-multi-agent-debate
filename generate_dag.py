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
    Generate and save the DAG diagram as PNG and SVG.
    
    Args:
        output_dir: Directory to save the output files
    """
    # Always save DOT file first
    dot_content = create_dag_diagram()
    dot_path = Path(output_dir) / "dag.dot"
    with open(dot_path, 'w') as f:
        f.write(dot_content)
    print(f"DOT source saved to: {dot_path}")
    
    # Also create a Mermaid diagram as fallback
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
    
    if not HAS_GRAPHVIZ:
        print("\nNote: graphviz Python package not installed.")
        print("Install with: pip install graphviz")
        print("You can render the DOT file manually or use the Mermaid diagram.")
        return
    
    try:
        # Create Graph object
        graph = graphviz.Source(dot_content)
        
        # Save as PNG
        png_path = Path(output_dir) / "dag"
        graph.render(png_path, format='png', cleanup=True)
        print(f"PNG saved to: {png_path}.png")
        
        # Save as SVG
        svg_path = Path(output_dir) / "dag"
        graph.render(svg_path, format='svg', cleanup=True)
        print(f"SVG saved to: {svg_path}.svg")
        
    except Exception as e:
        print(f"\nCould not render PNG/SVG: {e}")
        print("The Graphviz 'dot' executable may not be installed.")
        print("Install Graphviz from: https://graphviz.org/download/")
        print("Or use the Mermaid diagram in dag.md")



def generate_langgraph_diagram():
    """
    Alternative: Use LangGraph's built-in visualization if available.
    """
    try:
        from run_debate import build_debate_graph
        
        graph = build_debate_graph()
        
        # Try to get the graph visualization
        if hasattr(graph, 'get_graph'):
            mermaid_graph = graph.get_graph().draw_mermaid()
            
            mermaid_path = Path(".") / "dag_langgraph.md"
            with open(mermaid_path, 'w') as f:
                f.write("```mermaid\n")
                f.write(mermaid_graph)
                f.write("\n```")
            print(f"LangGraph Mermaid diagram saved to: {mermaid_path}")
            return True
    except Exception as e:
        print(f"Could not generate LangGraph diagram: {e}")
        return False


def main():
    """Main entry point."""
    print("Generating DAG visualization...")
    print("-" * 40)
    
    # Generate static Graphviz diagram
    save_dag_files(".")
    
    print("-" * 40)
    
    # Try LangGraph's built-in visualization
    print("\nAttempting LangGraph native visualization...")
    generate_langgraph_diagram()
    
    print("\nDone!")


if __name__ == "__main__":
    main()
