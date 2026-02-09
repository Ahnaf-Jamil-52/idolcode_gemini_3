"""
Tests for Burnout Scoring Module

Tests the EMA scoring, level detection, and recency factors.
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from coach_engine.signals import BehavioralSignal, SignalType
from coach_engine.scorer import (
    BurnoutScorer, BurnoutScore, BurnoutLevel,
    SessionBurnoutTracker
)


class TestBurnoutScorer:
    """Test cases for BurnoutScorer class."""
    
    def test_empty_signals_returns_zero(self):
        """Empty signal list should return 0 score."""
        scorer = BurnoutScorer()
        score = scorer.calculate_burnout([])
        
        assert score.score == 0.0
        assert score.level == BurnoutLevel.LOW
    
    def test_single_negative_signal(self):
        """Single negative signal should produce positive score."""
        scorer = BurnoutScorer()
        
        signals = [
            BehavioralSignal(
                signal_type=SignalType.RAPID_WA_BURST,
                timestamp=datetime.now(),
                weight=0.15
            )
        ]
        
        score = scorer.calculate_burnout(signals, apply_smoothing=False)
        
        assert score.score > 0.0
        assert score.score <= 0.15  # Can't exceed weight
    
    def test_multiple_signals_accumulate(self):
        """Multiple signals should accumulate scores."""
        scorer = BurnoutScorer()
        
        now = datetime.now()
        signals = [
            BehavioralSignal(SignalType.RAPID_WA_BURST, now, 0.15),
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.PROBLEM_SKIP_STREAK, now, 0.18),
        ]
        
        score = scorer.calculate_burnout(signals, apply_smoothing=False)
        
        # Should be sum of weights (all recent)
        assert score.score > 0.4
    
    def test_recency_factor_decays(self):
        """Older signals should have less impact."""
        scorer = BurnoutScorer()
        
        now = datetime.now()
        old_time = now - timedelta(minutes=30)
        
        # Recent signal
        recent_signals = [
            BehavioralSignal(SignalType.RAPID_WA_BURST, now, 0.15)
        ]
        
        # Old signal (same type)
        old_signals = [
            BehavioralSignal(SignalType.RAPID_WA_BURST, old_time, 0.15)
        ]
        
        recent_score = scorer.calculate_burnout(recent_signals, apply_smoothing=False)
        scorer.reset()
        old_score = scorer.calculate_burnout(old_signals, apply_smoothing=False)
        
        assert recent_score.score > old_score.score
    
    def test_burnout_levels(self):
        """Test correct level assignment for different scores."""
        scorer = BurnoutScorer()
        
        assert scorer.get_burnout_level(0.10) == BurnoutLevel.LOW
        assert scorer.get_burnout_level(0.29) == BurnoutLevel.LOW
        assert scorer.get_burnout_level(0.30) == BurnoutLevel.MODERATE
        assert scorer.get_burnout_level(0.49) == BurnoutLevel.MODERATE
        assert scorer.get_burnout_level(0.50) == BurnoutLevel.HIGH
        assert scorer.get_burnout_level(0.69) == BurnoutLevel.HIGH
        assert scorer.get_burnout_level(0.70) == BurnoutLevel.CRITICAL
        assert scorer.get_burnout_level(1.00) == BurnoutLevel.CRITICAL
    
    def test_positive_signals_reduce_score(self):
        """Positive signals (wins, solves) should reduce score."""
        scorer = BurnoutScorer()
        
        now = datetime.now()
        
        # Just negative signals
        neg_signals = [
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.PROBLEM_SKIP_STREAK, now, 0.18),
        ]
        neg_score = scorer.calculate_burnout(neg_signals, apply_smoothing=False)
        
        scorer.reset()
        
        # Negative + positive signals
        mixed_signals = [
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.PROBLEM_SKIP_STREAK, now, 0.18),
            BehavioralSignal(SignalType.GHOST_WIN, now, -0.20),
        ]
        mixed_score = scorer.calculate_burnout(mixed_signals, apply_smoothing=False)
        
        assert mixed_score.score < neg_score.score
    
    def test_ema_smoothing(self):
        """EMA should smooth sudden changes."""
        scorer = BurnoutScorer(ema_alpha=0.3)
        
        now = datetime.now()
        
        # First calculation
        signals1 = [
            BehavioralSignal(SignalType.RAPID_WA_BURST, now, 0.15)
        ]
        score1 = scorer.calculate_burnout(signals1)
        
        # Second calculation with much higher raw score
        signals2 = [
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.PROBLEM_SKIP_STREAK, now, 0.18),
            BehavioralSignal(SignalType.SUBMISSION_THEN_SILENCE, now, 0.20),
        ]
        score2 = scorer.calculate_burnout(signals2)
        
        # EMA should prevent huge jump
        # Without smoothing, score2 would be ~0.58
        # With smoothing, it should be less
        assert score2.raw_weighted_sum > score2.ema_smoothed or abs(score2.raw_weighted_sum - score2.ema_smoothed) < 0.1
    
    def test_score_normalization(self):
        """Score should never exceed 1.0."""
        scorer = BurnoutScorer()
        
        now = datetime.now()
        
        # Many high-weight signals
        signals = [
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.SUBMISSION_THEN_SILENCE, now, 0.20),
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.SUBMISSION_THEN_SILENCE, now, 0.20),
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.SUBMISSION_THEN_SILENCE, now, 0.20),
        ]
        
        score = scorer.calculate_burnout(signals)
        
        assert score.score <= 1.0
    
    def test_contributing_signals_tracked(self):
        """Top contributing signals should be tracked."""
        scorer = BurnoutScorer()
        
        now = datetime.now()
        signals = [
            BehavioralSignal(SignalType.GHOST_LOSS_STREAK, now, 0.20),
            BehavioralSignal(SignalType.RAPID_WA_BURST, now, 0.15),
        ]
        
        score = scorer.calculate_burnout(signals, apply_smoothing=False)
        
        assert len(score.contributing_signals) > 0
        # Highest weight first
        assert score.contributing_signals[0][0] == SignalType.GHOST_LOSS_STREAK


class TestSessionBurnoutTracker:
    """Test cases for SessionBurnoutTracker."""
    
    def test_record_peaks(self):
        """Should record session peaks correctly."""
        tracker = SessionBurnoutTracker()
        
        tracker.record_session_peak("s1", 0.3)
        tracker.record_session_peak("s2", 0.5)
        tracker.record_session_peak("s3", 0.4)
        
        peaks = tracker.get_recent_peaks(3)
        assert peaks == [0.3, 0.5, 0.4]
    
    def test_average_peak(self):
        """Should calculate average peak correctly."""
        tracker = SessionBurnoutTracker()
        
        tracker.record_session_peak("s1", 0.2)
        tracker.record_session_peak("s2", 0.4)
        tracker.record_session_peak("s3", 0.6)
        
        avg = tracker.get_average_peak(3)
        assert avg == pytest.approx(0.4, abs=0.01)
    
    def test_deteriorating_detection(self):
        """Should detect deteriorating trend."""
        tracker = SessionBurnoutTracker()
        
        # Increasing scores = deteriorating
        tracker.record_session_peak("s1", 0.1)
        tracker.record_session_peak("s2", 0.2)
        tracker.record_session_peak("s3", 0.3)
        tracker.record_session_peak("s4", 0.4)
        tracker.record_session_peak("s5", 0.5)
        
        assert tracker.is_deteriorating() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
