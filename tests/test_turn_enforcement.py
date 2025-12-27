"""
Tests for turn enforcement in the debate system.

These tests verify that:
1. Turn order is correctly enforced (AgentA on odd, AgentB on even)
2. Out-of-order calls are rejected
3. Round counter advances correctly
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.rounds_controller import (
    validate_turn_order,
    rounds_controller_node,
    should_continue,
)


class TestTurnOrderValidation:
    """Test suite for turn order validation."""
    
    def test_agent_a_on_odd_rounds(self):
        """AgentA should be valid on rounds 1, 3, 5, 7."""
        for round_num in [1, 3, 5, 7]:
            is_valid, error = validate_turn_order(round_num, "AgentA")
            assert is_valid, f"AgentA should be valid on round {round_num}: {error}"
    
    def test_agent_b_on_even_rounds(self):
        """AgentB should be valid on rounds 2, 4, 6, 8."""
        for round_num in [2, 4, 6, 8]:
            is_valid, error = validate_turn_order(round_num, "AgentB")
            assert is_valid, f"AgentB should be valid on round {round_num}: {error}"
    
    def test_agent_a_rejected_on_even_rounds(self):
        """AgentA should be rejected on even rounds."""
        for round_num in [2, 4, 6, 8]:
            is_valid, error = validate_turn_order(round_num, "AgentA")
            assert not is_valid, f"AgentA should be rejected on round {round_num}"
            assert "Turn order violation" in error
    
    def test_agent_b_rejected_on_odd_rounds(self):
        """AgentB should be rejected on odd rounds."""
        for round_num in [1, 3, 5, 7]:
            is_valid, error = validate_turn_order(round_num, "AgentB")
            assert not is_valid, f"AgentB should be rejected on round {round_num}"
            assert "Turn order violation" in error


class TestRoundsController:
    """Test suite for the rounds controller node."""
    
    @pytest.fixture
    def base_state(self):
        """Create a base state for testing."""
        return {
            "topic": "Should AI be regulated?",
            "current_round": 1,
            "current_agent": "AgentA",
            "total_rounds": 8,
            "turns": [{
                "round": 1,
                "agent": "Scientist",
                "agent_id": "AgentA",
                "text": "AI regulation is necessary for safety.",
            }],
            "summary": "",
            "coherence_issues": [],
            "duplicate_warnings": [],
            "log_entries": [],
            "config": {"settings": {"similarity_threshold": 0.85}},
        }
    
    def test_round_advancement(self, base_state):
        """Test that rounds advance correctly."""
        result = rounds_controller_node(base_state)
        assert result["current_round"] == 2
        assert result["current_agent"] == "AgentB"
        assert result["is_complete"] == False
    
    def test_debate_completion(self, base_state):
        """Test that debate completes after 8 rounds."""
        base_state["current_round"] = 8
        base_state["current_agent"] = "AgentB"
        
        result = rounds_controller_node(base_state)
        assert result["is_complete"] == True
    
    def test_should_continue_returns_continue(self, base_state):
        """Test should_continue returns 'continue' when not complete."""
        base_state["is_complete"] = False
        result = should_continue(base_state)
        assert result == "continue"
    
    def test_should_continue_returns_judge(self, base_state):
        """Test should_continue returns 'judge' when complete."""
        base_state["is_complete"] = True
        result = should_continue(base_state)
        assert result == "judge"


class TestAlternation:
    """Test suite for agent alternation."""
    
    def test_agent_alternation_sequence(self):
        """Test full sequence of agent alternation through 8 rounds."""
        expected_sequence = [
            (1, "AgentA"),
            (2, "AgentB"),
            (3, "AgentA"),
            (4, "AgentB"),
            (5, "AgentA"),
            (6, "AgentB"),
            (7, "AgentA"),
            (8, "AgentB"),
        ]
        
        for round_num, expected_agent in expected_sequence:
            is_valid, _ = validate_turn_order(round_num, expected_agent)
            assert is_valid, f"Round {round_num} should have {expected_agent}"
            
            # Also verify the other agent is rejected
            other_agent = "AgentB" if expected_agent == "AgentA" else "AgentA"
            is_invalid, _ = validate_turn_order(round_num, other_agent)
            assert not is_invalid, f"Round {round_num} should reject {other_agent}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
