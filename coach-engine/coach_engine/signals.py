"""
Behavioral Signal Ingestion Module

Collects and processes implicit behavioral signals from user activity.
No NLP required - purely event-based pattern detection.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import deque
from enum import Enum
import math


class SignalType(Enum):
    """Taxonomy of behavioral signals that indicate burnout."""
    RAPID_WA_BURST = "rapid_wa_burst"  # 3+ wrong answers in < 2 min
    SUBMISSION_THEN_SILENCE = "submission_then_silence"  # Submit → no activity 15+ min
    PROBLEM_SKIP_STREAK = "problem_skip_streak"  # 3+ problems opened then abandoned
    SESSION_LENGTH_DECAY = "session_length_decay"  # Sessions getting shorter over 3 days
    GHOST_LOSS_STREAK = "ghost_loss_streak"  # 3+ consecutive ghost race losses
    TIME_BETWEEN_SESSIONS_GROWTH = "time_between_sessions_growth"  # Gaps widening
    HINT_DEPENDENCY = "hint_dependency"  # Requesting hints > 60% of problems
    IDLE_ON_PROBLEM = "idle_on_problem"  # Problem open 20+ min, no submission
    COPY_PASTE_DETECTION = "copy_paste_detection"  # Code pasted from external source
    TAB_AWAY_FREQUENCY = "tab_away_frequency"  # Switching away repeatedly
    # Positive signals (for recovery detection)
    SUCCESSFUL_SOLVE = "successful_solve"
    GHOST_WIN = "ghost_win"
    HINT_DECLINED = "hint_declined"
    LONG_FOCUSED_SESSION = "long_focused_session"


# Signal weights for burnout calculation
SIGNAL_WEIGHTS: Dict[SignalType, float] = {
    SignalType.RAPID_WA_BURST: 0.15,
    SignalType.SUBMISSION_THEN_SILENCE: 0.20,
    SignalType.PROBLEM_SKIP_STREAK: 0.18,
    SignalType.SESSION_LENGTH_DECAY: 0.12,
    SignalType.GHOST_LOSS_STREAK: 0.20,
    SignalType.TIME_BETWEEN_SESSIONS_GROWTH: 0.10,
    SignalType.HINT_DEPENDENCY: 0.08,
    SignalType.IDLE_ON_PROBLEM: 0.12,
    SignalType.COPY_PASTE_DETECTION: 0.10,
    SignalType.TAB_AWAY_FREQUENCY: 0.05,
    # Negative weights for positive signals (reduce burnout)
    SignalType.SUCCESSFUL_SOLVE: -0.15,
    SignalType.GHOST_WIN: -0.20,
    SignalType.HINT_DECLINED: -0.05,
    SignalType.LONG_FOCUSED_SESSION: -0.10,
}


@dataclass
class BehavioralSignal:
    """A single behavioral event/signal."""
    signal_type: SignalType
    timestamp: datetime
    weight: float = field(default=0.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.weight == 0.0:
            self.weight = SIGNAL_WEIGHTS.get(self.signal_type, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "timestamp": self.timestamp.isoformat(),
            "weight": self.weight,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehavioralSignal":
        return cls(
            signal_type=SignalType(data["signal_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            weight=data.get("weight", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class UserSession:
    """Represents a single user session with aggregated stats."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    problems_attempted: int = 0
    problems_solved: int = 0
    ghost_races_won: int = 0
    ghost_races_lost: int = 0
    hints_requested: int = 0
    wrong_answers: int = 0
    skipped_problems: int = 0
    
    @property
    def duration_minutes(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return (datetime.now() - self.start_time).total_seconds() / 60
    
    @property
    def solve_rate(self) -> float:
        if self.problems_attempted == 0:
            return 0.0
        return self.problems_solved / self.problems_attempted
    
    @property
    def hint_dependency_rate(self) -> float:
        if self.problems_attempted == 0:
            return 0.0
        return self.hints_requested / self.problems_attempted
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "problems_attempted": self.problems_attempted,
            "problems_solved": self.problems_solved,
            "ghost_races_won": self.ghost_races_won,
            "ghost_races_lost": self.ghost_races_lost,
            "hints_requested": self.hints_requested,
            "wrong_answers": self.wrong_answers,
            "skipped_problems": self.skipped_problems,
        }


class SignalCollector:
    """
    Collects and manages behavioral signals from user activity.
    Maintains rolling windows for both events and sessions.
    """
    
    def __init__(self, max_events: int = 20, max_sessions: int = 10):
        self.max_events = max_events
        self.max_sessions = max_sessions
        self.signals: deque[BehavioralSignal] = deque(maxlen=max_events)
        self.sessions: deque[UserSession] = deque(maxlen=max_sessions)
        self.current_session: Optional[UserSession] = None
        
        # Activity tracking for pattern detection
        self._last_submission_time: Optional[datetime] = None
        self._recent_wrong_answers: deque[datetime] = deque(maxlen=10)
        self._recent_problem_opens: deque[datetime] = deque(maxlen=10)
        self._recent_problem_skips: deque[datetime] = deque(maxlen=10)
        self._consecutive_ghost_losses: int = 0
        self._tab_switches: deque[datetime] = deque(maxlen=20)
    
    def start_session(self, user_id: str, session_id: str) -> UserSession:
        """Start a new session for tracking."""
        if self.current_session:
            self.end_session()
        
        self.current_session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now()
        )
        return self.current_session
    
    def end_session(self) -> Optional[UserSession]:
        """End the current session and add to history."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.sessions.append(self.current_session)
            
            # Check for session length decay
            self._check_session_length_decay()
            
            ended_session = self.current_session
            self.current_session = None
            return ended_session
        return None
    
    def record_event(self, event_type: str, metadata: Optional[Dict[str, Any]] = None) -> List[BehavioralSignal]:
        """
        Record a raw event and detect any behavioral signals.
        Returns list of signals detected from this event.
        """
        now = datetime.now()
        detected_signals: List[BehavioralSignal] = []
        metadata = metadata or {}
        
        # Process different event types
        if event_type == "submission":
            signal = self._process_submission(now, metadata)
            if signal:
                detected_signals.append(signal)
        
        elif event_type == "wrong_answer":
            signals = self._process_wrong_answer(now, metadata)
            detected_signals.extend(signals)
        
        elif event_type == "problem_opened":
            self._recent_problem_opens.append(now)
        
        elif event_type == "problem_skipped":
            signals = self._process_problem_skip(now, metadata)
            detected_signals.extend(signals)
        
        elif event_type == "ghost_race_result":
            signals = self._process_ghost_race(now, metadata)
            detected_signals.extend(signals)
        
        elif event_type == "hint_requested":
            signal = self._process_hint_request(now, metadata)
            if signal:
                detected_signals.append(signal)
        
        elif event_type == "hint_declined":
            detected_signals.append(BehavioralSignal(
                signal_type=SignalType.HINT_DECLINED,
                timestamp=now,
                metadata=metadata
            ))
        
        elif event_type == "problem_solved":
            detected_signals.append(BehavioralSignal(
                signal_type=SignalType.SUCCESSFUL_SOLVE,
                timestamp=now,
                metadata=metadata
            ))
            if self.current_session:
                self.current_session.problems_solved += 1
        
        elif event_type == "code_paste":
            detected_signals.append(BehavioralSignal(
                signal_type=SignalType.COPY_PASTE_DETECTION,
                timestamp=now,
                metadata=metadata
            ))
        
        elif event_type == "tab_switch":
            signals = self._process_tab_switch(now, metadata)
            detected_signals.extend(signals)
        
        elif event_type == "idle_detected":
            if metadata.get("idle_minutes", 0) >= 20:
                detected_signals.append(BehavioralSignal(
                    signal_type=SignalType.IDLE_ON_PROBLEM,
                    timestamp=now,
                    metadata=metadata
                ))
        
        # Add all detected signals to the queue
        for signal in detected_signals:
            self.signals.append(signal)
        
        return detected_signals
    
    def _process_submission(self, now: datetime, metadata: Dict) -> Optional[BehavioralSignal]:
        """Check for submission_then_silence pattern."""
        self._last_submission_time = now
        if self.current_session:
            self.current_session.problems_attempted += 1
        return None
    
    def _process_wrong_answer(self, now: datetime, metadata: Dict) -> List[BehavioralSignal]:
        """Check for rapid wrong answer bursts."""
        signals = []
        self._recent_wrong_answers.append(now)
        
        if self.current_session:
            self.current_session.wrong_answers += 1
        
        # Check for 3+ wrong answers in < 2 minutes
        if len(self._recent_wrong_answers) >= 3:
            recent_3 = list(self._recent_wrong_answers)[-3:]
            time_span = (recent_3[-1] - recent_3[0]).total_seconds()
            if time_span <= 120:  # 2 minutes
                signals.append(BehavioralSignal(
                    signal_type=SignalType.RAPID_WA_BURST,
                    timestamp=now,
                    metadata={"count": 3, "time_span_seconds": time_span}
                ))
        
        return signals
    
    def _process_problem_skip(self, now: datetime, metadata: Dict) -> List[BehavioralSignal]:
        """Check for problem skip streak."""
        signals = []
        self._recent_problem_skips.append(now)
        
        if self.current_session:
            self.current_session.skipped_problems += 1
        
        # Check for 3+ skips in the recent window
        recent_skips = [s for s in self._recent_problem_skips 
                       if (now - s).total_seconds() < 600]  # Last 10 minutes
        
        if len(recent_skips) >= 3:
            signals.append(BehavioralSignal(
                signal_type=SignalType.PROBLEM_SKIP_STREAK,
                timestamp=now,
                metadata={"skip_count": len(recent_skips)}
            ))
        
        return signals
    
    def _process_ghost_race(self, now: datetime, metadata: Dict) -> List[BehavioralSignal]:
        """Check for ghost race loss streaks."""
        signals = []
        won = metadata.get("won", False)
        
        if self.current_session:
            if won:
                self.current_session.ghost_races_won += 1
            else:
                self.current_session.ghost_races_lost += 1
        
        if won:
            self._consecutive_ghost_losses = 0
            signals.append(BehavioralSignal(
                signal_type=SignalType.GHOST_WIN,
                timestamp=now,
                metadata=metadata
            ))
        else:
            self._consecutive_ghost_losses += 1
            if self._consecutive_ghost_losses >= 3:
                signals.append(BehavioralSignal(
                    signal_type=SignalType.GHOST_LOSS_STREAK,
                    timestamp=now,
                    metadata={"consecutive_losses": self._consecutive_ghost_losses}
                ))
        
        return signals
    
    def _process_hint_request(self, now: datetime, metadata: Dict) -> Optional[BehavioralSignal]:
        """Track hint dependency."""
        if self.current_session:
            self.current_session.hints_requested += 1
            
            # Check if hint dependency is > 60%
            if (self.current_session.problems_attempted >= 5 and 
                self.current_session.hint_dependency_rate > 0.6):
                return BehavioralSignal(
                    signal_type=SignalType.HINT_DEPENDENCY,
                    timestamp=now,
                    metadata={"rate": self.current_session.hint_dependency_rate}
                )
        return None
    
    def _process_tab_switch(self, now: datetime, metadata: Dict) -> List[BehavioralSignal]:
        """Detect excessive tab switching (distraction/avoidance)."""
        signals = []
        self._tab_switches.append(now)
        
        # Check for frequent tab switches in last 5 minutes
        recent_switches = [s for s in self._tab_switches 
                         if (now - s).total_seconds() < 300]
        
        if len(recent_switches) >= 10:  # 10+ switches in 5 minutes
            signals.append(BehavioralSignal(
                signal_type=SignalType.TAB_AWAY_FREQUENCY,
                timestamp=now,
                metadata={"switches_in_5min": len(recent_switches)}
            ))
        
        return signals
    
    def _check_session_length_decay(self):
        """Check if session lengths are decreasing over time."""
        if len(self.sessions) >= 3:
            recent_sessions = list(self.sessions)[-3:]
            durations = [s.duration_minutes for s in recent_sessions]
            
            # Simple check: each session shorter than previous
            if all(durations[i] > durations[i+1] for i in range(len(durations)-1)):
                decay_signal = BehavioralSignal(
                    signal_type=SignalType.SESSION_LENGTH_DECAY,
                    timestamp=datetime.now(),
                    metadata={
                        "durations": durations,
                        "decay_percentage": (durations[0] - durations[-1]) / durations[0] * 100
                    }
                )
                self.signals.append(decay_signal)
    
    def check_silence_after_submission(self, current_time: Optional[datetime] = None) -> Optional[BehavioralSignal]:
        """
        Check if there's been silence after last submission.
        Should be called periodically (e.g., every minute).
        """
        now = current_time or datetime.now()
        
        if self._last_submission_time:
            silence_duration = (now - self._last_submission_time).total_seconds() / 60
            
            if silence_duration >= 15:  # 15+ minutes of silence
                signal = BehavioralSignal(
                    signal_type=SignalType.SUBMISSION_THEN_SILENCE,
                    timestamp=now,
                    metadata={"silence_minutes": silence_duration}
                )
                self.signals.append(signal)
                self._last_submission_time = None  # Reset to avoid repeat triggers
                return signal
        
        return None
    
    def check_session_gaps(self) -> Optional[BehavioralSignal]:
        """Check if gaps between sessions are growing."""
        if len(self.sessions) < 3:
            return None
        
        recent_sessions = list(self.sessions)[-3:]
        gaps = []
        
        for i in range(len(recent_sessions) - 1):
            if recent_sessions[i].end_time and recent_sessions[i+1].start_time:
                gap = (recent_sessions[i+1].start_time - recent_sessions[i].end_time).total_seconds() / 3600
                gaps.append(gap)
        
        if len(gaps) >= 2 and all(gaps[i] < gaps[i+1] for i in range(len(gaps)-1)):
            signal = BehavioralSignal(
                signal_type=SignalType.TIME_BETWEEN_SESSIONS_GROWTH,
                timestamp=datetime.now(),
                metadata={"gap_hours": gaps}
            )
            self.signals.append(signal)
            return signal
        
        return None
    
    def get_recent_signals(self, minutes: int = 30) -> List[BehavioralSignal]:
        """Get signals from the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [s for s in self.signals if s.timestamp >= cutoff]
    
    def get_all_signals(self) -> List[BehavioralSignal]:
        """Get all signals in the rolling window."""
        return list(self.signals)
    
    def get_recent_sessions(self, count: int = 5) -> List[UserSession]:
        """Get the most recent N sessions."""
        return list(self.sessions)[-count:]
