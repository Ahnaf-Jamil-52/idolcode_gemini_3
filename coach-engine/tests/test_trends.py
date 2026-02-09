"""
Tests for Trend Detection Module

Tests linear regression, slope detection, and trend analysis.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from coach_engine.trends import (
    TrendDetector, TrendAnalysis, TrendDirection,
    MultiMetricTrendAnalyzer
)


class TestTrendDetector:
    """Test cases for TrendDetector class."""
    
    def test_empty_scores_stable(self):
        """Empty scores should return stable trend."""
        detector = TrendDetector()
        trend = detector.analyze([])
        
        assert trend.direction == TrendDirection.STABLE
        assert trend.slope == 0.0
    
    def test_single_point_stable(self):
        """Single data point should return stable trend."""
        detector = TrendDetector()
        trend = detector.analyze([0.5])
        
        assert trend.direction == TrendDirection.STABLE
    
    def test_increasing_is_deteriorating(self):
        """Increasing scores should detect as deteriorating."""
        detector = TrendDetector()
        
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        trend = detector.analyze(scores)
        
        assert trend.direction == TrendDirection.DETERIORATING
        assert trend.slope > 0.1
    
    def test_decreasing_is_recovering(self):
        """Decreasing scores should detect as recovering."""
        detector = TrendDetector()
        
        scores = [0.5, 0.4, 0.3, 0.2, 0.1]
        trend = detector.analyze(scores)
        
        assert trend.direction == TrendDirection.RECOVERING
        assert trend.slope < -0.1
    
    def test_flat_is_stable(self):
        """Flat scores should detect as stable."""
        detector = TrendDetector()
        
        scores = [0.3, 0.31, 0.29, 0.30, 0.31]
        trend = detector.analyze(scores)
        
        assert trend.direction == TrendDirection.STABLE
        assert abs(trend.slope) < 0.1
    
    def test_linear_regression_accuracy(self):
        """Test linear regression calculation accuracy."""
        detector = TrendDetector()
        
        # Perfect line: y = 0.1x + 0.1
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        slope, intercept, r_squared = detector.linear_regression(scores)
        
        assert slope == pytest.approx(0.1, abs=0.01)
        assert intercept == pytest.approx(0.1, abs=0.01)
        assert r_squared == pytest.approx(1.0, abs=0.01)
    
    def test_r_squared_for_noisy_data(self):
        """R-squared should be lower for noisy data."""
        detector = TrendDetector()
        
        # Noisy increasing trend
        noisy_scores = [0.1, 0.3, 0.2, 0.4, 0.35]
        _, _, r_squared = detector.linear_regression(noisy_scores)
        
        assert r_squared < 1.0
        assert r_squared > 0.0
    
    def test_sessions_to_critical_prediction(self):
        """Test prediction of sessions to critical threshold."""
        detector = TrendDetector()
        
        # Current score 0.4, slope 0.1
        sessions = detector.predict_sessions_to_critical(0.4, 0.1, 0.7)
        
        # Need 0.3 more at 0.1 per session = 3 sessions
        assert sessions == 3
    
    def test_sessions_to_critical_already_critical(self):
        """Already critical should return None."""
        detector = TrendDetector()
        
        sessions = detector.predict_sessions_to_critical(0.75, 0.1, 0.7)
        assert sessions is None
    
    def test_sessions_to_critical_negative_slope(self):
        """Improving trend should return None for time to critical."""
        detector = TrendDetector()
        
        sessions = detector.predict_sessions_to_critical(0.4, -0.1, 0.7)
        assert sessions is None
    
    def test_window_size_effect(self):
        """Should only use window_size most recent points."""
        detector = TrendDetector(window_size=3)
        
        # Old data trending up, recent data trending down
        scores = [0.1, 0.2, 0.3, 0.5, 0.4, 0.3]
        trend = detector.analyze(scores, use_window=True)
        
        # Should only see the last 3 points: 0.5, 0.4, 0.3 (decreasing)
        assert trend.direction == TrendDirection.RECOVERING
    
    def test_predicted_next_value(self):
        """Should predict next value reasonably."""
        detector = TrendDetector()
        
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        trend = detector.analyze(scores)
        
        # Next value should be ~0.6
        assert trend.predicted_next == pytest.approx(0.6, abs=0.05)
    
    def test_quick_trend_check(self):
        """Quick trend check should return correct intervention flag."""
        detector = TrendDetector()
        
        deteriorating_scores = [0.2, 0.3, 0.4, 0.5, 0.6]
        direction, intervene = detector.quick_trend_check(deteriorating_scores)
        
        assert direction == TrendDirection.DETERIORATING
        assert intervene is True
        
        stable_scores = [0.3, 0.3, 0.31, 0.29, 0.3]
        direction, intervene = detector.quick_trend_check(stable_scores)
        
        assert direction == TrendDirection.STABLE
        assert intervene is False
    
    def test_confidence_calculation(self):
        """Confidence should increase with more data points."""
        detector = TrendDetector(window_size=5)
        
        # Few points
        few_scores = [0.1, 0.2]
        trend_few = detector.analyze(few_scores)
        
        # More points
        more_scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        trend_more = detector.analyze(more_scores)
        
        assert trend_more.confidence >= trend_few.confidence
    
    def test_is_concerning_property(self):
        """is_concerning should flag deteriorating with high confidence."""
        detector = TrendDetector()
        
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        trend = detector.analyze(scores)
        
        assert trend.is_concerning is True


class TestMultiMetricTrendAnalyzer:
    """Test cases for MultiMetricTrendAnalyzer."""
    
    def test_add_data_points(self):
        """Should add data points to all metrics."""
        analyzer = MultiMetricTrendAnalyzer()
        
        analyzer.add_data_point({
            "burnout_score": 0.3,
            "solve_rate": 0.5,
        })
        analyzer.add_data_point({
            "burnout_score": 0.4,
            "solve_rate": 0.4,
        })
        
        assert len(analyzer.metrics_history["burnout_score"]) == 2
        assert len(analyzer.metrics_history["solve_rate"]) == 2
    
    def test_analyze_all_metrics(self):
        """Should analyze all metrics with data."""
        analyzer = MultiMetricTrendAnalyzer()
        
        for i in range(5):
            analyzer.add_data_point({
                "burnout_score": 0.1 + i * 0.1,
                "solve_rate": 0.5 - i * 0.05,
            })
        
        results = analyzer.analyze_all()
        
        assert "burnout_score" in results
        assert "solve_rate" in results
        assert results["burnout_score"].direction == TrendDirection.DETERIORATING
    
    def test_composite_trend(self):
        """Composite trend should consider all metrics."""
        analyzer = MultiMetricTrendAnalyzer()
        
        # Burnout increasing, everything else decreasing = bad
        for i in range(5):
            analyzer.add_data_point({
                "burnout_score": 0.1 + i * 0.1,
                "solve_rate": 0.8 - i * 0.1,
                "session_length": 120 - i * 20,
                "ghost_win_rate": 0.6 - i * 0.1,
            })
        
        composite = analyzer.get_composite_trend()
        
        assert composite == TrendDirection.DETERIORATING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
