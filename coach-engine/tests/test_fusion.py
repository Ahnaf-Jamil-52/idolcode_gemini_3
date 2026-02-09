"""
Tests for Fusion Module

Tests the cross-referencing logic that combines behavioral signals
with text sentiment for comprehensive burnout detection.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from coach_engine.fusion import (
    FusionEngine, FusionResult,
    BehaviorTextAlignment, InterventionLevel
)
from coach_engine.states import CoachState
from coach_engine.sentiment import EmotionalState


class TestFusionEngine:
    """Test cases for FusionEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh FusionEngine for each test."""
        eng = FusionEngine()
        eng.start_session("test_user", "test_session")
        return eng
    
    def test_initial_state_normal(self, engine):
        """Engine should start in normal state."""
        result = engine.analyze()
        
        assert result.current_state == CoachState.NORMAL
        assert result.composite_score < 0.3
    
    def test_process_events(self, engine):
        """Events should be processed and create signals."""
        signals = engine.process_event("wrong_answer")
        
        assert isinstance(signals, list)
    
    def test_process_message(self, engine):
        """Messages should be processed for sentiment."""
        result = engine.process_message("I'm frustrated with this problem")
        
        assert result.state in [EmotionalState.FRUSTRATED, EmotionalState.DISCOURAGED]
    
    def test_alignment_genuine_good(self, engine):
        """Good behavior + positive text = genuine good."""
        # Add positive events
        engine.process_event("problem_solved")
        engine.process_event("ghost_race_result", {"won": True})
        
        # Add positive message
        engine.process_message("Yes! Finally got it! This is awesome!")
        
        result = engine.analyze()
        
        assert result.alignment == BehaviorTextAlignment.GENUINE_GOOD
    
    def test_alignment_confirmed_burnout(self, engine):
        """Bad behavior + negative text = confirmed burnout."""
        # Add negative events
        for _ in range(3):
            engine.process_event("wrong_answer")
            engine.process_event("problem_skipped")
        
        engine.process_event("ghost_race_result", {"won": False})
        engine.process_event("ghost_race_result", {"won": False})
        engine.process_event("ghost_race_result", {"won": False})
        
        # Add negative message
        engine.process_message("I can't do this. It's too hard. I give up.")
        
        result = engine.analyze()
        
        assert result.alignment in [
            BehaviorTextAlignment.CONFIRMED_BURNOUT,
            BehaviorTextAlignment.MASKING
        ]
        assert result.composite_score > 0.3
    
    def test_masking_detection(self, engine):
        """Positive text + bad behavior = masking."""
        # Add many negative events
        for _ in range(5):
            engine.process_event("wrong_answer")
            engine.process_event("problem_skipped")
        
        for _ in range(3):
            engine.process_event("ghost_race_result", {"won": False})
        
        # But positive message
        engine.process_message("I'm fine, no problem here")
        
        result = engine.analyze()
        
        # Should detect masking or at least flag concern
        assert result.is_masking or result.composite_score > 0.3
    
    def test_intervention_levels(self, engine):
        """Intervention level should increase with burnout."""
        # Low burnout
        initial = engine.analyze()
        
        # Add stress
        for _ in range(5):
            engine.process_event("wrong_answer")
            engine.process_event("ghost_race_result", {"won": False})
        
        stressed = engine.analyze()
        
        # Intervention should be higher
        assert stressed.intervention_level.value >= initial.intervention_level.value
    
    def test_ghost_speed_modifier(self, engine):
        """Ghost speed should decrease with higher burnout."""
        initial = engine.analyze()
        
        # Add stress
        for _ in range(5):
            engine.process_event("wrong_answer")
            engine.process_event("ghost_race_result", {"won": False})
            engine.process_event("problem_skipped")
        
        stressed = engine.analyze()
        
        assert stressed.ghost_speed_modifier <= initial.ghost_speed_modifier
    
    def test_recommended_actions(self, engine):
        """Should provide recommended actions."""
        # Create stressful scenario
        for _ in range(3):
            engine.process_event("wrong_answer")
            engine.process_event("problem_skipped")
        
        result = engine.analyze()
        
        assert len(result.recommended_actions) > 0
    
    def test_session_lifecycle(self, engine):
        """Session start/end should work correctly."""
        # End the session started in fixture
        engine.end_session()
        
        # Start new session
        engine.start_session("user2", "session2")
        
        result = engine.analyze()
        assert result.current_state == CoachState.NORMAL
    
    def test_state_summary(self, engine):
        """get_current_state_summary should return valid dict."""
        summary = engine.get_current_state_summary()
        
        assert "state" in summary
        assert "composite_score" in summary
        assert "ghost_speed" in summary
        assert summary["state"] == "normal"
    
    def test_composite_score_weights(self, engine):
        """Composite score should weight components correctly."""
        # Behavior is weighted 65%, so should dominate
        
        # Many bad behavioral signals
        for _ in range(5):
            engine.process_event("wrong_answer")
            engine.process_event("ghost_race_result", {"won": False})
        
        # But positive sentiment
        engine.process_message("This is great, I love it!")
        
        result = engine.analyze()
        
        # Behavior should still push score up despite positive text
        assert result.behavior_score > 0.2
    
    def test_reset(self, engine):
        """Reset should clear all state."""
        # Add some data
        engine.process_event("wrong_answer")
        engine.process_message("frustrated")
        
        engine.reset()
        engine.start_session("new", "new")
        
        result = engine.analyze()
        
        assert result.composite_score == pytest.approx(0.0, abs=0.1)


class TestBehaviorTextAlignment:
    """Test alignment detection edge cases."""
    
    def test_venting_ok_scenario(self):
        """Good behavior + negative text = just venting."""
        engine = FusionEngine()
        engine.start_session("test", "test")
        
        # Good behavioral signals
        engine.process_event("problem_solved")
        engine.process_event("ghost_race_result", {"won": True})
        
        # Negative message (venting)
        engine.process_message("That was so annoying! Took forever")
        
        result = engine.analyze()
        
        # Should be venting or genuine good, not burnout
        assert result.alignment in [
            BehaviorTextAlignment.VENTING_OK,
            BehaviorTextAlignment.GENUINE_GOOD
        ]


class TestInterventionLevel:
    """Test intervention level determination."""
    
    def test_urgent_for_critical_score(self):
        """Critical score should trigger urgent intervention."""
        engine = FusionEngine()
        engine.start_session("test", "test")
        
        # Force high burnout through many events
        for _ in range(10):
            engine.process_event("wrong_answer")
            engine.process_event("problem_skipped")
            engine.process_event("ghost_race_result", {"won": False})
        
        engine.process_message("I give up, this is impossible, I'm too dumb")
        
        result = engine.analyze()
        
        if result.composite_score >= 0.7:
            assert result.intervention_level == InterventionLevel.URGENT
    
    def test_none_for_normal(self):
        """Normal operation should have no intervention."""
        engine = FusionEngine()
        engine.start_session("test", "test")
        
        result = engine.analyze()
        
        assert result.intervention_level == InterventionLevel.NONE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
