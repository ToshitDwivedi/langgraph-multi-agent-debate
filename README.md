# Multi-Agent Debate DAG System

A LangGraph-based workflow that simulates structured debates between two AI agents with memory management, turn control, and automated judging.

## Features

- **8-Round Debates**: Exactly 4 turns per agent, strictly alternating
- **Persona-Based Agents**: Configurable personas (Scientist vs Philosopher)
- **Memory Management**: Structured transcript with agent-specific memory slices
- **Turn Control**: Programmatic enforcement of turn order
- **Duplicate Detection**: String similarity checks to prevent repeated arguments
- **Topic Drift Detection**: Keyword-based coherence validation
- **Automated Judging**: LLM-powered verdict with reasoned justification
- **Comprehensive Logging**: JSON logs with timestamps for all events
- **DAG Visualization**: Graphviz-generated workflow diagram

## Project Structure

```
Assignment1/
├── run_debate.py              # CLI launcher
├── generate_dag.py            # DAG visualization generator
├── config.yaml                # Configuration (personas, settings)
├── requirements.txt           # Dependencies
├── .env.example               # Environment variables template
│
├── nodes/                     # LangGraph node implementations
│   ├── __init__.py
│   ├── state.py               # State schema (DebateState)
│   ├── user_input_node.py     # Topic input validation
│   ├── agent_node.py          # Debate agents (AgentA/AgentB)
│   ├── memory_node.py         # Memory management
│   ├── rounds_controller.py   # Turn sequencing
│   ├── judge_node.py          # Final verdict
│   └── logger_node.py         # Event logging
│
├── persona_templates/         # Agent persona prompts
│   ├── scientist.txt
│   └── philosopher.txt
│
├── tests/                     # Unit/integration tests
│   ├── test_turn_enforcement.py
│   ├── test_duplicate_detection.py
│   ├── test_memory_updates.py
│   └── test_judge_output.py
│
└── logs/                      # Generated log files
```

## Installation

1. **Clone the repository**:
   ```bash
   cd Assignment1
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API key**:
   ```bash
   copy .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Usage

### Basic Debate

```bash
python run_debate.py
```

You'll be prompted to enter a debate topic:

```
============================================================
  MULTI-AGENT DEBATE SYSTEM
============================================================

Enter topic for debate: Should AI be regulated like medicine?
```

### CLI Flags

```bash
# With reproducible random seed
python run_debate.py --seed 42

# Custom log directory
python run_debate.py --log-path ./my_logs

# Custom config file
python run_debate.py --persona-config custom_config.yaml

# Non-interactive (provide topic directly)
python run_debate.py --topic "Should AI be regulated like medicine?"
```

### Example Output

```
Starting debate between Scientist and Philosopher...
------------------------------------------------------------

[Round 1] Scientist:
AI regulation is essential because of the high-risk applications in healthcare
and autonomous systems. Research indicates that unregulated AI deployments have
led to biased outcomes in 67% of cases studied...

[Round 2] Philosopher:
From an ethical standpoint, we must consider the philosophical implications of
restricting innovation. History teaches us that excessive regulation often
stifles human progress...

...

[Round 8] Philosopher:
In conclusion, while oversight has value, we must balance safety with the 
freedom to explore new frontiers of knowledge...

============================================================
[Judge] Summary of debate:
This debate explored the tension between AI safety and innovation freedom.
The Scientist emphasized empirical evidence for regulation, while the
Philosopher argued for balanced, innovation-friendly approaches.

------------------------------------------------------------
[Judge] Winner: Scientist
Reason: Presented grounded, risk-based arguments aligned with public safety
principles, with concrete evidence supporting regulatory frameworks.
============================================================

Debate log saved to: logs/debate_log_20251226_235800.json
```

## DAG Structure

```
START → UserInputNode → AgentNode → MemoryNode → LoggerNode → RoundsController
                           ↑                                        ↓
                           └──────────── (if round < 8) ←──────────┘
                                                                    ↓
                                              (if round = 8) → JudgeNode → END
```

### Generate DAG Diagram

```bash
python generate_dag.py
```

This creates:
- `dag.png` - PNG visualization
- `dag.svg` - SVG visualization
- `dag.dot` - GraphViz source file

## Configuration

Edit `config.yaml` to customize:

```yaml
personas:
  agent_a:
    name: "Scientist"
    prompt_file: "persona_templates/scientist.txt"
  agent_b:
    name: "Philosopher"
    prompt_file: "persona_templates/philosopher.txt"

settings:
  total_rounds: 8
  similarity_threshold: 0.85  # Duplicate detection
  topic_drift_threshold: 0.3  # Coherence check

llm:
  provider: "openai"  # or "google"
  model: "gpt-4o-mini"
  temperature: 0.7
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_turn_enforcement.py -v

# Run with coverage
python -m pytest tests/ --cov=nodes
```

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_turn_enforcement.py` | Turn order validation, round advancement |
| `test_duplicate_detection.py` | Similarity calculation, duplicate flagging |
| `test_memory_updates.py` | Turn entries, summary generation |
| `test_judge_output.py` | Verdict parsing, output format |

## Log Format

Logs are saved as JSON with the following structure:

```json
{
  "metadata": {
    "created_at": "2025-12-26T23:58:00",
    "topic": "Should AI be regulated?",
    "agent_a": "Scientist",
    "agent_b": "Philosopher"
  },
  "events": [
    {
      "timestamp": "...",
      "node": "UserInputNode",
      "event": "topic_validated",
      "data": {...}
    }
  ],
  "final_state": {
    "turns": [...],
    "winner": "AgentA",
    "verdict": "...",
    "debate_summary": "..."
  }
}
```

## Reproducibility

For deterministic output (useful for testing):

```bash
python run_debate.py --seed 42 --topic "Should AI be regulated?"
```

The seed controls:
- LLM temperature reduction for consistency
- Random state for any randomized operations

## Requirements

- Python 3.10+
- OpenAI API key (or Google API key for Gemini)
- Graphviz (optional, for DAG visualization)

## License

MIT License

## Demo Video

See `demo_video.mp4` for a walkthrough showing:
1. How to run the CLI
2. A debate session excerpt
3. Judge summary and log file
4. Code structure overview
