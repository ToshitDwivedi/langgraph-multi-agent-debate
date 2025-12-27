"""
Tests for memory updates in the debate system.

These tests verify that:
1. New turn entries are added correctly
2. Summaries are generated and updated
3. Memory slices contain correct information
4. State updates are returned properly
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.memory_node import (
    create_turn_entry,
    generate_summary,
    extract_agent_memory,
    memory_node,
)


class TestTurnEntryCreation:
    """Test suite for turn entry creation."""
    
    def test_basic_turn_entry(self):
        """Test creating a basic turn entry."""
        entry = create_turn_entry(
            round_num=1,
            agent_id="AgentA",
            agent_name="Scientist",
            text="This is a test argument.",
        )
        
        assert entry["round"] == 1
        assert entry["agent_id"] == "AgentA"
        assert entry["agent"] == "Scientist"
        assert entry["text"] == "This is a test argument."
        assert "timestamp" in entry["meta"]
        assert entry["meta"]["word_count"] == 5
    
    def test_turn_entry_preserves_text(self):
        """Test that turn entry preserves full argument text."""
        long_text = "This is a longer argument. " * 20
        entry = create_turn_entry(
            round_num=3,
            agent_id="AgentB",
            agent_name="Philosopher",
            text=long_text,
        )
        
        assert entry["text"] == long_text


class TestSummaryGeneration:
    """Test suite for summary generation."""
    
    @pytest.fixture
    def sample_turns(self):
        """Sample turns for testing."""
        return [
            {
                "round": 1,
                "agent": "Scientist",
                "agent_id": "AgentA",
                "text": "AI regulation is essential. It protects the public from harm.",
            },
            {
                "round": 2,
                "agent": "Philosopher",
                "agent_id": "AgentB",
                "text": "Freedom of innovation is paramount. We must not stifle progress.",
            },
        ]
    
    def test_summary_includes_topic(self, sample_turns):
        """Summary should include the debate topic."""
        summary = generate_summary(sample_turns, "AI Regulation")
        assert "AI Regulation" in summary
    
    def test_summary_includes_agent_points(self, sample_turns):
        """Summary should include key points from each agent."""
        summary = generate_summary(sample_turns, "AI Regulation")
        assert "Scientist" in summary or "AI regulation" in summary
    
    def test_empty_turns_returns_empty_summary(self):
        """Empty turns should return empty summary."""
        summary = generate_summary([], "Some Topic")
        assert summary == ""


class TestMemoryExtraction:
    """Test suite for memory slice extraction."""
    
    @pytest.fixture
    def full_transcript(self):
        """Full debate transcript for testing."""
        return [
            {"round": 1, "agent_id": "AgentA", "agent": "Scientist", "text": "Point 1"},
            {"round": 2, "agent_id": "AgentB", "agent": "Philosopher", "text": "Point 2"},
            {"round": 3, "agent_id": "AgentA", "agent": "Scientist", "text": "Point 3"},
            {"round": 4, "agent_id": "AgentB", "agent": "Philosopher", "text": "Point 4"},
        ]
    
    def test_agent_a_memory_extraction(self, full_transcript):
        """Test memory extraction for AgentA."""
        memory = extract_agent_memory(full_transcript, "AgentA")
        # Currently returns all turns for context
        assert len(memory) == len(full_transcript)
    
    def test_agent_b_memory_extraction(self, full_transcript):
        """Test memory extraction for AgentB."""
        memory = extract_agent_memory(full_transcript, "AgentB")
        assert len(memory) == len(full_transcript)


class TestMemoryNode:
    """Test suite for the memory node."""
    
    @pytest.fixture
    def base_state(self):
        """Create a base state for testing."""
        return {
            "topic": "Should AI be regulated?",
            "current_round": 1,
            "current_agent": "AgentA",
            "current_argument": "This is the new argument being added.",
            "turns": [],
            "summary": "",
            "agent_a_memory": [],
            "agent_b_memory": [],
            "log_entries": [],
            "config": {
                "personas": {
                    "agent_a": {"name": "Scientist"},
                    "agent_b": {"name": "Philosopher"},
                }
            },
        }
    
    def test_memory_node_adds_turn(self, base_state):
        """Memory node should add new turn to transcript."""
        result = memory_node(base_state)
        
        assert len(result["turns"]) == 1
        assert result["turns"][0]["round"] == 1
        assert result["turns"][0]["agent"] == "Scientist"
        assert result["turns"][0]["text"] == "This is the new argument being added."
    
    def test_memory_node_updates_summary(self, base_state):
        """Memory node should update the summary."""
        result = memory_node(base_state)
        
        assert result["summary"] != ""
        assert "Should AI be regulated?" in result["summary"]
    
    def test_memory_node_clears_current_argument(self, base_state):
        """Memory node should clear current_argument after storing."""
        result = memory_node(base_state)
        
        assert result["current_argument"] is None
    
    def test_memory_node_preserves_existing_turns(self, base_state):
        """Memory node should preserve existing turns."""
        base_state["turns"] = [{
            "round": 1,
            "agent": "Scientist",
            "agent_id": "AgentA",
            "text": "Previous argument.",
        }]
        base_state["current_round"] = 2
        base_state["current_agent"] = "AgentB"
        
        result = memory_node(base_state)
        
        assert len(result["turns"]) == 2
        assert result["turns"][0]["text"] == "Previous argument."
        assert result["turns"][1]["text"] == "This is the new argument being added."
    
    def test_memory_node_adds_log_entries(self, base_state):
        """Memory node should add log entries."""
        result = memory_node(base_state)
        
        assert len(result["log_entries"]) >= 1
        # Should have memory_updated and memory_snapshot events
        events = [e["event"] for e in result["log_entries"]]
        assert "memory_updated" in events


class TestMemoryIntegrity:
    """Tests for memory integrity across multiple rounds."""
    
    def test_memory_accumulation(self):
        """Test that memory accumulates correctly across rounds."""
        state = {
            "topic": "Test Topic",
            "current_round": 1,
            "current_agent": "AgentA",
            "current_argument": "Argument 1",
            "turns": [],
            "summary": "",
            "agent_a_memory": [],
            "agent_b_memory": [],
            "log_entries": [],
            "config": {
                "personas": {
                    "agent_a": {"name": "Scientist"},
                    "agent_b": {"name": "Philosopher"},
                }
            },
        }
        
        # Simulate 4 rounds
        for round_num in range(1, 5):
            agent = "AgentA" if round_num % 2 == 1 else "AgentB"
            state["current_round"] = round_num
            state["current_agent"] = agent
            state["current_argument"] = f"Argument {round_num}"
            
            result = memory_node(state)
            state["turns"] = result["turns"]
            state["summary"] = result["summary"]
        
        # Verify all 4 turns are present
        assert len(state["turns"]) == 4
        for i, turn in enumerate(state["turns"]):
            assert turn["round"] == i + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
