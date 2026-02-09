"""
Trend Detection Module

Detects directional trends in burnout scores using simple linear regression.
No external libraries needed - pure Python implementation.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum
import math


class TrendDirection(Enum):
    """Direction of burnout trend."""
    DETERIORATING = "deteriorating"  # slope > 0.1 - getting worse
    STABLE = "stable"                # slope ≈ 0 - no significant change
    RECOVERING = "recovering"        # slope < -0.1 - getting better


@dataclass
class TrendAnalysis:
    """Complete trend analysis result."""
    direction: TrendDirection
    slope: float                    # Rate of change per session
    intercept: float                # Y-intercept of regression line
    r_squared: float                # Goodness of fit (0-1)
    confidence: float               # Confidence in the trend (0-1)
    data_points: int                # Number of points used
    predicted_next: float           # Predicted next score
    sessions_to_critical: Optional[int]  # Sessions until score hits 0.7 (if deteriorating)
    
    def to_dict(self) -> dict:
        return {
            "direction": self.direction.value,
            "slope": round(self.slope, 4),
            "intercept": round(self.intercept, 4),
            "r_squared": round(self.r_squared, 4),
            "confidence": round(self.confidence, 3),
            "data_points": self.data_points,
            "predicted_next": round(self.predicted_next, 3),
            "sessions_to_critical": self.sessions_to_critical,
        }
    
    @property
    def is_concerning(self) -> bool:
        """Check if trend warrants intervention."""
        return (self.direction == TrendDirection.DETERIORATING and 
                self.confidence > 0.6)


class TrendDetector:
    """
    Detects trends in burnout scores using least-squares linear regression.
    
    Uses the 5-point sliding window approach for stability.
    Pure Python implementation - no numpy/scipy needed.
    """
    
    def __init__(
        self,
        window_size: int = 5,
        deteriorating_threshold: float = 0.1,
        recovering_threshold: float = -0.1,
        min_confidence: float = 0.5
    ):
        """
        Args:
            window_size: Number of data points to use for regression
            deteriorating_threshold: Slope above this = deteriorating
            recovering_threshold: Slope below this = recovering
            min_confidence: Minimum R² to consider trend reliable
        """
        self.window_size = window_size
        self.deteriorating_threshold = deteriorating_threshold
        self.recovering_threshold = recovering_threshold
        self.min_confidence = min_confidence
    
    def linear_regression(
        self, 
        y_values: List[float]
    ) -> Tuple[float, float, float]:
        """
        Simple least-squares linear regression.
        
        Formula:
        slope = Σ((x - x̄)(y - ȳ)) / Σ((x - x̄)²)
        intercept = ȳ - slope × x̄
        
        Args:
            y_values: List of y values (x values are assumed to be 0, 1, 2, ...)
            
        Returns:
            Tuple of (slope, intercept, r_squared)
        """
        n = len(y_values)
        if n < 2:
            return 0.0, y_values[0] if y_values else 0.0, 0.0
        
        # X values are just indices: 0, 1, 2, ...
        x_values = list(range(n))
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate slope numerator and denominator
        numerator = sum((x - x_mean) * (y - y_mean) 
                       for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0, y_mean, 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R² (coefficient of determination)
        y_pred = [slope * x + intercept for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        r_squared = max(0.0, min(1.0, r_squared))  # Clamp to [0, 1]
        
        return slope, intercept, r_squared
    
    def get_trend_direction(self, slope: float) -> TrendDirection:
        """Determine trend direction from slope."""
        if slope >= self.deteriorating_threshold:
            return TrendDirection.DETERIORATING
        elif slope <= self.recovering_threshold:
            return TrendDirection.RECOVERING
        else:
            return TrendDirection.STABLE
    
    def calculate_confidence(
        self, 
        r_squared: float, 
        data_points: int
    ) -> float:
        """
        Calculate confidence in the trend.
        
        Combines R² with data point count for reliability.
        """
        # More data points = more confidence
        point_factor = min(1.0, data_points / self.window_size)
        
        # R² directly represents fit quality
        return r_squared * point_factor
    
    def predict_sessions_to_critical(
        self,
        current_score: float,
        slope: float,
        critical_threshold: float = 0.7
    ) -> Optional[int]:
        """
        Predict how many sessions until score hits critical threshold.
        
        Returns None if slope is negative or zero, or if already critical.
        """
        if slope <= 0 or current_score >= critical_threshold:
            return None
        
        gap = critical_threshold - current_score
        sessions = math.ceil(gap / slope)
        
        return max(1, sessions)
    
    def analyze(
        self, 
        scores: List[float],
        use_window: bool = True
    ) -> TrendAnalysis:
        """
        Analyze trend in burnout scores.
        
        Args:
            scores: List of burnout scores (oldest first)
            use_window: Whether to use only the last window_size points
            
        Returns:
            Complete TrendAnalysis
        """
        if not scores:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                slope=0.0,
                intercept=0.0,
                r_squared=0.0,
                confidence=0.0,
                data_points=0,
                predicted_next=0.0,
                sessions_to_critical=None
            )
        
        # Use window if specified and enough data
        if use_window and len(scores) > self.window_size:
            analysis_scores = scores[-self.window_size:]
        else:
            analysis_scores = scores
        
        # Run regression
        slope, intercept, r_squared = self.linear_regression(analysis_scores)
        
        # Determine direction
        direction = self.get_trend_direction(slope)
        
        # Calculate confidence
        confidence = self.calculate_confidence(r_squared, len(analysis_scores))
        
        # Predict next score
        next_x = len(analysis_scores)
        predicted_next = max(0.0, min(1.0, slope * next_x + intercept))
        
        # Sessions to critical (if deteriorating)
        current_score = analysis_scores[-1] if analysis_scores else 0.0
        sessions_to_critical = self.predict_sessions_to_critical(
            current_score, slope
        )
        
        return TrendAnalysis(
            direction=direction,
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            confidence=confidence,
            data_points=len(analysis_scores),
            predicted_next=predicted_next,
            sessions_to_critical=sessions_to_critical
        )
    
    def quick_trend_check(self, scores: List[float]) -> Tuple[TrendDirection, bool]:
        """
        Quick check for trend direction and whether to intervene.
        
        Returns:
            Tuple of (direction, should_intervene)
        """
        analysis = self.analyze(scores)
        should_intervene = (
            analysis.direction == TrendDirection.DETERIORATING and
            analysis.confidence >= self.min_confidence
        )
        return analysis.direction, should_intervene


class MultiMetricTrendAnalyzer:
    """
    Analyzes trends across multiple metrics for comprehensive assessment.
    """
    
    def __init__(self):
        self.detector = TrendDetector()
        self.metrics_history: dict[str, List[float]] = {
            "burnout_score": [],
            "solve_rate": [],
            "session_length": [],
            "ghost_win_rate": [],
        }
    
    def add_data_point(self, metrics: dict[str, float]):
        """Add a new data point for all metrics."""
        for key, value in metrics.items():
            if key in self.metrics_history:
                self.metrics_history[key].append(value)
    
    def analyze_all(self) -> dict[str, TrendAnalysis]:
        """Analyze trends for all tracked metrics."""
        results = {}
        for metric, values in self.metrics_history.items():
            if values:
                results[metric] = self.detector.analyze(values)
        return results
    
    def get_composite_trend(self) -> TrendDirection:
        """
        Get overall trend by combining multiple metrics.
        
        Weighting:
        - burnout_score: 50%
        - solve_rate: 20% (inverted - decreasing is bad)
        - session_length: 15% (inverted - decreasing is bad)
        - ghost_win_rate: 15% (inverted - decreasing is bad)
        """
        analyses = self.analyze_all()
        
        if not analyses:
            return TrendDirection.STABLE
        
        # Calculate weighted composite slope
        weights = {
            "burnout_score": 0.5,
            "solve_rate": -0.2,      # Negative because lower is bad
            "session_length": -0.15,  # Negative because lower is bad
            "ghost_win_rate": -0.15,  # Negative because lower is bad
        }
        
        composite_slope = 0.0
        total_weight = 0.0
        
        for metric, analysis in analyses.items():
            if metric in weights:
                composite_slope += analysis.slope * weights[metric]
                total_weight += abs(weights[metric])
        
        if total_weight > 0:
            composite_slope /= total_weight
        
        # Determine direction
        if composite_slope > 0.05:
            return TrendDirection.DETERIORATING
        elif composite_slope < -0.05:
            return TrendDirection.RECOVERING
        else:
            return TrendDirection.STABLE
