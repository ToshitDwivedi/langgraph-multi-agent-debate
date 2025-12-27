"""
Tests for JudgeNode output format.

These tests verify that:
1. Verdict parsing works correctly
2. Required fields are present
3. Winner is one of AgentA/AgentB
4. Justification is provided
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.judge_node import (
    parse_verdict,
    format_transcript,
    format_coherence_report,
)


class TestVerdictParsing:
    """Test suite for verdict parsing."""
    
    def test_parse_complete_verdict(self):
        """Test parsing a complete verdict response."""
        response = """SUMMARY:
This was a thoughtful debate on AI regulation. The Scientist focused on safety concerns while the Philosopher emphasized innovation.

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION:
The Scientist presented more concrete evidence and practical considerations for regulation."""
        
        result = parse_verdict(response)
        
        assert "debate" in result["summary"].lower() or "thoughtful" in result["summary"].lower()
        assert result["winner"] == "AgentA"
        assert result["winner_name"] == "Scientist"
        assert "evidence" in result["justification"].lower() or "concrete" in result["justification"].lower()
    
    def test_parse_agentb_winner(self):
        """Test parsing when AgentB wins."""
        response = """SUMMARY:
A fierce debate ensued.

WINNER: AgentB

WINNER_NAME: Philosopher

JUSTIFICATION:
The Philosopher's ethical arguments were more compelling."""
        
        result = parse_verdict(response)
        
        assert result["winner"] == "AgentB"
        assert result["winner_name"] == "Philosopher"
    
    def test_parse_multiline_summary(self):
        """Test parsing multi-line summary."""
        response = """SUMMARY:
Line 1 of the summary.
Line 2 of the summary.
Line 3 with more details.

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION:
The reasoning here."""
        
        result = parse_verdict(response)
        
        assert "Line 1" in result["summary"]
        assert "Line 2" in result["summary"]
    
    def test_parse_multiline_justification(self):
        """Test parsing multi-line justification."""
        response = """SUMMARY:
Brief summary.

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION:
First reason for the decision.
Second reason with more detail.
Third concluding remark."""
        
        result = parse_verdict(response)
        
        assert "First reason" in result["justification"]
        assert "Third" in result["justification"]


class TestTranscriptFormatting:
    """Test suite for transcript formatting."""
    
    def test_format_transcript(self):
        """Test basic transcript formatting."""
        turns = [
            {"round": 1, "agent": "Scientist", "text": "First argument."},
            {"round": 2, "agent": "Philosopher", "text": "Counter argument."},
        ]
        
        result = format_transcript(turns, "AI Regulation")
        
        assert "AI Regulation" in result
        assert "[Round 1] Scientist" in result
        assert "[Round 2] Philosopher" in result
        assert "First argument." in result
        assert "Counter argument." in result
    
    def test_format_empty_transcript(self):
        """Test formatting empty transcript."""
        result = format_transcript([], "Some Topic")
        
        assert "Some Topic" in result


class TestCoherenceReportFormatting:
    """Test suite for coherence report formatting."""
    
    def test_format_with_issues(self):
        """Test formatting with coherence issues."""
        issues = ["Round 2: Topic drift detected"]
        warnings = ["Round 3: Similar to previous argument"]
        
        result = format_coherence_report(issues, warnings)
        
        assert "Coherence Issues" in result
        assert "Topic drift" in result
        assert "Duplicate" in result
        assert "Similar" in result
    
    def test_format_no_issues(self):
        """Test formatting with no issues."""
        result = format_coherence_report([], [])
        
        assert "No coherence issues" in result


class TestJudgeOutputFormat:
    """Test suite for complete judge output format validation."""
    
    def test_required_fields_present(self):
        """Test that all required fields are in parsed verdict."""
        response = """SUMMARY:
A complete debate.

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION:
Good arguments were made."""
        
        result = parse_verdict(response)
        
        # All required fields should be present
        assert "summary" in result
        assert "winner" in result
        assert "winner_name" in result
        assert "justification" in result
    
    def test_winner_is_valid_agent(self):
        """Test that winner is either AgentA or AgentB."""
        response_a = """SUMMARY: Test

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION: Test"""
        
        response_b = """SUMMARY: Test

WINNER: AgentB

WINNER_NAME: Philosopher

JUSTIFICATION: Test"""
        
        result_a = parse_verdict(response_a)
        result_b = parse_verdict(response_b)
        
        assert result_a["winner"] in ["AgentA", "AgentB"]
        assert result_b["winner"] in ["AgentA", "AgentB"]
    
    def test_justification_not_empty(self):
        """Test that justification is provided."""
        response = """SUMMARY: Brief

WINNER: AgentA

WINNER_NAME: Scientist

JUSTIFICATION:
The Scientist provided more concrete examples and evidence-based reasoning."""
        
        result = parse_verdict(response)
        
        assert len(result["justification"]) > 10  # Should have substantial content


class TestEdgeCases:
    """Test edge cases in verdict parsing."""
    
    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        response = """  SUMMARY:  
  Debate summary with spaces.  

WINNER:   AgentA  

WINNER_NAME:   Scientist  

JUSTIFICATION:  
  Reasoning with whitespace.  """
        
        result = parse_verdict(response)
        
        # Should still parse correctly
        assert result["winner"] == "AgentA"
    
    def test_case_variations(self):
        """Test handling of case variations in winner."""
        response = """SUMMARY: Test

WINNER: AGENTA

WINNER_NAME: Scientist

JUSTIFICATION: Test"""
        
        result = parse_verdict(response)
        assert result["winner"] == "AgentA"
        
        response2 = """SUMMARY: Test

WINNER: agentb

WINNER_NAME: Philosopher

JUSTIFICATION: Test"""
        
        result2 = parse_verdict(response2)
        assert result2["winner"] == "AgentB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
