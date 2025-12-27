"""
JudgeNode - Final verdict and summary generation

This node:
1. Aggregates the full debate transcript
2. Analyzes argument quality and coherence
3. Produces a structured verdict with winner and justification
"""

from typing import Dict, Any
from datetime import datetime

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None
    raise ImportError("langchain-groq not installed")

from langchain_core.messages import HumanMessage, SystemMessage


def get_llm(config: dict):
    """Initialize Groq LLM based on configuration."""
    llm_config = config.get("llm", {})
    model = llm_config.get("model", "llama-3.3-70b-versatile")
    temperature = 0.3  # Lower temperature for more consistent judging
    max_tokens = 1000
    
    return ChatGroq(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def format_transcript(turns: list, topic: str) -> str:
    """Format the full debate transcript for the judge."""
    lines = [f"**Debate Topic:** {topic}\n"]
    lines.append("**Full Transcript:**\n")
    
    for turn in turns:
        round_num = turn.get("round", "?")
        agent = turn.get("agent", "Unknown")
        text = turn.get("text", "")
        lines.append(f"\n[Round {round_num}] {agent}:\n{text}\n")
    
    return "\n".join(lines)


def format_coherence_report(coherence_issues: list, duplicate_warnings: list) -> str:
    """Format coherence and duplicate issues for the judge."""
    lines = []
    
    if coherence_issues:
        lines.append("**Coherence Issues Detected:**")
        for issue in coherence_issues:
            lines.append(f"- {issue}")
    
    if duplicate_warnings:
        lines.append("\n**Duplicate Argument Warnings:**")
        for warning in duplicate_warnings:
            lines.append(f"- {warning}")
    
    if not lines:
        lines.append("No coherence issues or duplicate arguments detected.")
    
    return "\n".join(lines)


def build_judge_prompt(
    transcript: str,
    coherence_report: str,
    agent_a_name: str,
    agent_b_name: str,
) -> list:
    """Build the prompt messages for the judge."""
    system_prompt = f"""You are an impartial debate judge with expertise in logical reasoning and rhetorical analysis.

Your task is to:
1. Review the complete debate transcript
2. Evaluate the quality of arguments from both sides
3. Consider logical coherence, evidence quality, and persuasiveness
4. Declare a winner with clear justification

**Participants:**
- AgentA: {agent_a_name}
- AgentB: {agent_b_name}

**Evaluation Criteria:**
- Clarity and structure of arguments
- Quality of evidence and reasoning
- Responsiveness to opponent's points
- Logical consistency
- Persuasiveness

You MUST respond in the following exact format:

SUMMARY:
[Provide a concise 2-3 paragraph summary of the debate, highlighting key arguments from each side]

WINNER: [AgentA or AgentB]

WINNER_NAME: [{agent_a_name} or {agent_b_name}]

JUSTIFICATION:
[Provide a detailed explanation of why the winner was chosen, referencing specific arguments]
"""

    user_prompt = f"""{transcript}

---

{coherence_report}

---

Please analyze this debate and provide your verdict following the exact format specified."""

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]


def parse_verdict(response_text: str) -> dict:
    """Parse the judge's response into structured components."""
    result = {
        "summary": "",
        "winner": "",
        "winner_name": "",
        "justification": "",
    }
    
    lines = response_text.strip().split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line_upper = line.strip().upper()
        
        if line_upper.startswith("SUMMARY:"):
            if current_section and current_content:
                result[current_section] = '\n'.join(current_content).strip()
            current_section = "summary"
            remaining = line.split(":", 1)[1].strip() if ":" in line else ""
            current_content = [remaining] if remaining else []
        elif line_upper.startswith("WINNER:"):
            if current_section and current_content:
                result[current_section] = '\n'.join(current_content).strip()
            winner_text = line.split(":", 1)[1].strip() if ":" in line else ""
            result["winner"] = "AgentA" if "AGENTA" in winner_text.upper() else "AgentB"
            current_section = None
            current_content = []
        elif line_upper.startswith("WINNER_NAME:"):
            result["winner_name"] = line.split(":", 1)[1].strip() if ":" in line else ""
        elif line_upper.startswith("JUSTIFICATION:"):
            if current_section and current_content:
                result[current_section] = '\n'.join(current_content).strip()
            current_section = "justification"
            remaining = line.split(":", 1)[1].strip() if ":" in line else ""
            current_content = [remaining] if remaining else []
        elif current_section:
            current_content.append(line)
    
    # Handle last section
    if current_section and current_content:
        result[current_section] = '\n'.join(current_content).strip()
    
    return result


def judge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for final judgment.
    
    Called after all 8 rounds to:
    1. Review the complete debate
    2. Analyze argument quality
    3. Declare a winner with justification
    
    Args:
        state: Current state dict
        
    Returns:
        Updated state with verdict
    """
    config = state.get("config", {})
    personas_config = config.get("personas", {})
    
    topic = state.get("topic", "")
    turns = state.get("turns", [])
    coherence_issues = state.get("coherence_issues", [])
    duplicate_warnings = state.get("duplicate_warnings", [])
    
    agent_a_name = personas_config.get("agent_a", {}).get("name", "AgentA")
    agent_b_name = personas_config.get("agent_b", {}).get("name", "AgentB")
    
    # Format inputs
    transcript = format_transcript(turns, topic)
    coherence_report = format_coherence_report(coherence_issues, duplicate_warnings)
    
    # Build prompt and get LLM response
    messages = build_judge_prompt(
        transcript=transcript,
        coherence_report=coherence_report,
        agent_a_name=agent_a_name,
        agent_b_name=agent_b_name,
    )
    
    llm = get_llm(config)
    response = llm.invoke(messages)
    verdict_text = response.content.strip()
    
    # Parse the verdict
    parsed_verdict = parse_verdict(verdict_text)
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "node": "JudgeNode",
        "event": "verdict_generated",
        "data": {
            "winner": parsed_verdict["winner"],
            "winner_name": parsed_verdict["winner_name"],
            "total_rounds": len(turns),
            "coherence_issues_count": len(coherence_issues),
            "duplicate_warnings_count": len(duplicate_warnings),
        }
    }
    
    # Final verdict log entry
    final_verdict = {
        "timestamp": datetime.now().isoformat(),
        "node": "JudgeNode",
        "event": "final_verdict",
        "data": {
            "topic": topic,
            "summary": parsed_verdict["summary"],
            "winner": parsed_verdict["winner"],
            "winner_name": parsed_verdict["winner_name"],
            "justification": parsed_verdict["justification"],
            "full_response": verdict_text,
        }
    }
    
    return {
        "winner": parsed_verdict["winner"],
        "verdict": parsed_verdict["justification"],
        "debate_summary": parsed_verdict["summary"],
        "log_entries": state.get("log_entries", []) + [log_entry, final_verdict],
    }
