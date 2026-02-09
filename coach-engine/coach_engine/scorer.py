"""
Burnout Scorer Module

Calculates burnout score using Exponential Moving Average (EMA)
with recency-weighted signals. No ML needed - pure mathematical scoring.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math

from .signals import BehavioralSignal, SignalType


class BurnoutLevel(Enum):
    """Burnout severity levels with thresholds."""
    LOW = "low"           # < 0.30 - normal operation
    MODERATE = "moderate" # 0.30 - 0.49 - gentle nudges
    HIGH = "high"         # 0.50 - 0.69 - coach warns + slows ghost
    CRITICAL = "critical" # >= 0.70 - activate cooperative mode


@dataclass
class BurnoutScore:
    """Complete burnout assessment at a point in time."""
    score: float  # 0.0 - 1.0
    level: BurnoutLevel
    timestamp: datetime
    contributing_signals: List[Tuple[SignalType, float]]  # (signal, contribution)
    raw_weighted_sum: float
    ema_smoothed: float
    
    def to_dict(self) -> Dict:
        return {
            "score": round(self.score, 3),
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "contributing_signals": [
                {"signal": s.value, "contribution": round(c, 3)}
                for s, c in self.contributing_signals
            ],
            "raw_weighted_sum": round(self.raw_weighted_sum, 3),
            "ema_smoothed": round(self.ema_smoothed, 3),
        }


class BurnoutScorer:
    """
    Calculates burnout score using weighted signals and EMA smoothing.
    
    Formula:
    - Each signal contributes: weight × recency_factor
    - recency_factor = e^(-decay_rate × minutes_since_signal)
    - Final score is EMA-smoothed to prevent sudden jumps
    """
    
    def __init__(
        self,
        decay_rate: float = 0.1,
        ema_alpha: float = 0.3,
        max_score: float = 1.0
    ):
        """
        Args:
            decay_rate: How fast signal impact decays over time
            ema_alpha: EMA smoothing factor (higher = more reactive)
            max_score: Maximum possible score
        """
        self.decay_rate = decay_rate
        self.ema_alpha = ema_alpha
        self.max_score = max_score
        self._previous_ema: Optional[float] = None
        self._score_history: List[BurnoutScore] = []
    
    def calculate_recency_factor(
        self, 
        signal_time: datetime, 
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate how much a signal's impact has decayed.
        More recent signals have higher impact.
        
        Returns value between 0 and 1.
        """
        now = current_time or datetime.now()
        minutes_since = (now - signal_time).total_seconds() / 60
        
        # Exponential decay: e^(-0.1 * minutes)
        # At 0 min: factor = 1.0
        # At 10 min: factor ≈ 0.37
        # At 30 min: factor ≈ 0.05
        return math.exp(-self.decay_rate * minutes_since)
    
    def calculate_raw_score(
        self,
        signals: List[BehavioralSignal],
        current_time: Optional[datetime] = None
    ) -> Tuple[float, List[Tuple[SignalType, float]]]:
        """
        Calculate raw weighted sum of signals with recency decay.
        
        Returns:
            Tuple of (raw_score, list of (signal_type, contribution))
        """
        now = current_time or datetime.now()
        total_score = 0.0
        contributions: List[Tuple[SignalType, float]] = []
        
        for signal in signals:
            recency = self.calculate_recency_factor(signal.timestamp, now)
            contribution = signal.weight * recency
            total_score += contribution
            
            if abs(contribution) > 0.001:  # Only track meaningful contributions
                contributions.append((signal.signal_type, contribution))
        
        # Sort contributions by absolute value (most impactful first)
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return total_score, contributions
    
    def apply_ema_smoothing(self, raw_score: float) -> float:
        """
        Apply Exponential Moving Average smoothing.
        Prevents sudden score jumps from single events.
        
        EMA = α × current + (1 - α) × previous
        """
        if self._previous_ema is None:
            self._previous_ema = raw_score
            return raw_score
        
        smoothed = (self.ema_alpha * raw_score + 
                   (1 - self.ema_alpha) * self._previous_ema)
        self._previous_ema = smoothed
        
        return smoothed
    
    def normalize_score(self, score: float) -> float:
        """Clamp score to [0.0, max_score] range."""
        return max(0.0, min(self.max_score, score))
    
    def get_burnout_level(self, score: float) -> BurnoutLevel:
        """Determine burnout level from score."""
        if score >= 0.70:
            return BurnoutLevel.CRITICAL
        elif score >= 0.50:
            return BurnoutLevel.HIGH
        elif score >= 0.30:
            return BurnoutLevel.MODERATE
        else:
            return BurnoutLevel.LOW
    
    def calculate_burnout(
        self,
        signals: List[BehavioralSignal],
        current_time: Optional[datetime] = None,
        apply_smoothing: bool = True
    ) -> BurnoutScore:
        """
        Calculate complete burnout score from signals.
        
        Args:
            signals: List of behavioral signals to analyze
            current_time: Reference time (defaults to now)
            apply_smoothing: Whether to apply EMA smoothing
            
        Returns:
            BurnoutScore with complete assessment
        """
        now = current_time or datetime.now()
        
        # Calculate raw weighted score
        raw_score, contributions = self.calculate_raw_score(signals, now)
        
        # Apply EMA smoothing
        if apply_smoothing:
            smoothed = self.apply_ema_smoothing(raw_score)
        else:
            smoothed = raw_score
        
        # Normalize to valid range
        final_score = self.normalize_score(smoothed)
        
        # Determine level
        level = self.get_burnout_level(final_score)
        
        # Create score object
        burnout_score = BurnoutScore(
            score=final_score,
            level=level,
            timestamp=now,
            contributing_signals=contributions[:5],  # Top 5 contributors
            raw_weighted_sum=raw_score,
            ema_smoothed=smoothed
        )
        
        # Store in history for trend analysis
        self._score_history.append(burnout_score)
        
        return burnout_score
    
    def get_score_history(self, limit: int = 10) -> List[BurnoutScore]:
        """Get recent score history for trend analysis."""
        return self._score_history[-limit:]
    
    def get_session_scores(self, session_count: int = 5) -> List[float]:
        """
        Get one score per session for trend analysis.
        Returns the final score from each of the last N sessions.
        """
        # Group scores by session (simplified: use time gaps)
        if not self._score_history:
            return []
        
        session_scores: List[float] = []
        current_session_high = 0.0
        last_time = self._score_history[0].timestamp
        
        for score in self._score_history:
            # New session if gap > 30 minutes
            if (score.timestamp - last_time).total_seconds() > 1800:
                if current_session_high > 0:
                    session_scores.append(current_session_high)
                current_session_high = score.score
            else:
                current_session_high = max(current_session_high, score.score)
            last_time = score.timestamp
        
        # Add final session
        if current_session_high > 0:
            session_scores.append(current_session_high)
        
        return session_scores[-session_count:]
    
    def reset(self):
        """Reset scorer state (for new user or testing)."""
        self._previous_ema = None
        self._score_history.clear()


class SessionBurnoutTracker:
    """
    Tracks burnout across multiple sessions.
    Maintains per-session peak scores for trend analysis.
    """
    
    def __init__(self):
        self.session_peaks: List[Tuple[str, float, datetime]] = []  # (session_id, peak_score, timestamp)
    
    def record_session_peak(
        self, 
        session_id: str, 
        peak_score: float, 
        timestamp: Optional[datetime] = None
    ):
        """Record the peak burnout score for a session."""
        self.session_peaks.append((
            session_id,
            peak_score,
            timestamp or datetime.now()
        ))
    
    def get_recent_peaks(self, count: int = 5) -> List[float]:
        """Get peak scores from recent sessions."""
        return [p[1] for p in self.session_peaks[-count:]]
    
    def get_average_peak(self, count: int = 5) -> float:
        """Get average peak score across recent sessions."""
        peaks = self.get_recent_peaks(count)
        if not peaks:
            return 0.0
        return sum(peaks) / len(peaks)
    
    def is_deteriorating(self, threshold: float = 0.1) -> bool:
        """Check if burnout is getting worse over sessions."""
        peaks = self.get_recent_peaks(5)
        if len(peaks) < 3:
            return False
        
        # Simple check: is the trend upward?
        avg_first_half = sum(peaks[:len(peaks)//2]) / (len(peaks)//2)
        avg_second_half = sum(peaks[len(peaks)//2:]) / (len(peaks) - len(peaks)//2)
        
        return (avg_second_half - avg_first_half) > threshold
