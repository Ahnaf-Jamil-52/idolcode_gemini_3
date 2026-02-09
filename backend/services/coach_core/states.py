"""
State Machine Module

Implements the burnout state machine with managed transitions.
Prevents over-reaction by limiting state changes to one step at a time.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Callable, Any
from enum import Enum, auto

from .scorer import BurnoutScore, BurnoutLevel
from .trends import TrendAnalysis, TrendDirection


class CoachState(Enum):
    """
    States in the burnout detection state machine.
    
    State flow:
    NORMAL → WATCHING → WARNING → PROTECTIVE → RECOVERY → NORMAL
    """
    NORMAL = "normal"           # Default state, normal operation
    WATCHING = "watching"       # Coach paying attention, subtle monitoring
    WARNING = "warning"         # Ghost slows, coach speaks up
    PROTECTIVE = "protective"   # Cooperative mode, rest suggestions
    RECOVERY = "recovery"       # Gentle re-engagement after rest


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: CoachState
    to_state: CoachState
    timestamp: datetime
    trigger: str              # What caused the transition
    burnout_score: float
    trend_direction: Optional[TrendDirection] = None
    
    def to_dict(self) -> Dict:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "burnout_score": round(self.burnout_score, 3),
            "trend_direction": self.trend_direction.value if self.trend_direction else None,
        }


@dataclass 
class StateContext:
    """Context information for the current state."""
    state: CoachState
    entered_at: datetime
    burnout_score: float
    trend_direction: Optional[TrendDirection]
    consecutive_failures: int = 0
    ghost_loss_streak: int = 0
    successful_sessions_in_recovery: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_in_state(self) -> timedelta:
        return datetime.now() - self.entered_at
    
    @property
    def minutes_in_state(self) -> float:
        return self.duration_in_state.total_seconds() / 60
    
    def to_dict(self) -> Dict:
        return {
            "state": self.state.value,
            "entered_at": self.entered_at.isoformat(),
            "minutes_in_state": round(self.minutes_in_state, 1),
            "burnout_score": round(self.burnout_score, 3),
            "trend_direction": self.trend_direction.value if self.trend_direction else None,
            "consecutive_failures": self.consecutive_failures,
            "ghost_loss_streak": self.ghost_loss_streak,
            "successful_sessions_in_recovery": self.successful_sessions_in_recovery,
        }


class CoachStateMachine:
    """
    State machine for burnout detection and coach behavior.
    
    Key rules:
    1. Can only move ONE state at a time (no jumping)
    2. Transitions based on score thresholds AND trends
    3. Hysteresis: need sustained change to transition
    """
    
    # Define valid transitions (from_state -> [to_states])
    VALID_TRANSITIONS: Dict[CoachState, List[CoachState]] = {
        CoachState.NORMAL: [CoachState.WATCHING],
        CoachState.WATCHING: [CoachState.NORMAL, CoachState.WARNING],
        CoachState.WARNING: [CoachState.WATCHING, CoachState.PROTECTIVE],
        CoachState.PROTECTIVE: [CoachState.WARNING, CoachState.RECOVERY],
        CoachState.RECOVERY: [CoachState.PROTECTIVE, CoachState.NORMAL],
    }
    
    # State-specific thresholds
    THRESHOLDS = {
        "score_to_watching": 0.30,
        "score_to_warning": 0.50,
        "score_to_protective": 0.70,
        "trend_trigger": 0.1,  # Trend slope that triggers escalation
        "recovery_score": 0.30,  # Score to drop to for recovery
        "loss_streak_warning": 3,
        "loss_streak_protective": 5,
        "failures_warning": 3,
        "failures_protective": 5,
        "successful_sessions_to_normal": 2,
    }
    
    def __init__(self):
        self.current_context = StateContext(
            state=CoachState.NORMAL,
            entered_at=datetime.now(),
            burnout_score=0.0,
            trend_direction=None
        )
        self.transition_history: List[StateTransition] = []
        self._state_callbacks: Dict[CoachState, List[Callable]] = {
            state: [] for state in CoachState
        }
        self._min_state_duration = timedelta(minutes=2)  # Prevent rapid flipping
    
    @property
    def current_state(self) -> CoachState:
        return self.current_context.state
    
    def register_callback(
        self, 
        state: CoachState, 
        callback: Callable[[StateContext], None]
    ):
        """Register a callback to be called when entering a state."""
        self._state_callbacks[state].append(callback)
    
    def _can_transition(self, from_state: CoachState, to_state: CoachState) -> bool:
        """Check if transition is valid (one step rule)."""
        valid_targets = self.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    def _time_in_state_sufficient(self) -> bool:
        """Check if we've been in current state long enough to transition."""
        return self.current_context.duration_in_state >= self._min_state_duration
    
    def _determine_next_state(
        self,
        burnout_score: float,
        trend: Optional[TrendAnalysis] = None,
        consecutive_failures: int = 0,
        ghost_loss_streak: int = 0
    ) -> Optional[CoachState]:
        """
        Determine if we should transition to a new state.
        
        Returns None if no transition needed.
        """
        current = self.current_state
        trend_direction = trend.direction if trend else None
        trend_slope = trend.slope if trend else 0.0
        
        # Check minimum time in current state
        if not self._time_in_state_sufficient():
            return None
        
        # State-specific transition logic
        if current == CoachState.NORMAL:
            # Escalate to WATCHING
            if (burnout_score >= self.THRESHOLDS["score_to_watching"] or
                trend_slope > self.THRESHOLDS["trend_trigger"]):
                return CoachState.WATCHING
        
        elif current == CoachState.WATCHING:
            # Escalate to WARNING
            if (burnout_score >= self.THRESHOLDS["score_to_warning"] or
                ghost_loss_streak >= self.THRESHOLDS["loss_streak_warning"] or
                consecutive_failures >= self.THRESHOLDS["failures_warning"]):
                return CoachState.WARNING
            # De-escalate to NORMAL
            if (burnout_score < self.THRESHOLDS["score_to_watching"] - 0.05 and
                trend_direction != TrendDirection.DETERIORATING):
                return CoachState.NORMAL
        
        elif current == CoachState.WARNING:
            # Escalate to PROTECTIVE
            if (burnout_score >= self.THRESHOLDS["score_to_protective"] or
                ghost_loss_streak >= self.THRESHOLDS["loss_streak_protective"] or
                consecutive_failures >= self.THRESHOLDS["failures_protective"]):
                return CoachState.PROTECTIVE
            # De-escalate to WATCHING
            if (burnout_score < self.THRESHOLDS["score_to_warning"] - 0.05 and
                trend_direction == TrendDirection.RECOVERING):
                return CoachState.WATCHING
        
        elif current == CoachState.PROTECTIVE:
            # Move to RECOVERY when user rests or score drops significantly
            if burnout_score < self.THRESHOLDS["recovery_score"]:
                return CoachState.RECOVERY
            # Allow step back to WARNING if significant improvement
            if (burnout_score < self.THRESHOLDS["score_to_protective"] - 0.1 and
                trend_direction == TrendDirection.RECOVERING):
                return CoachState.WARNING
        
        elif current == CoachState.RECOVERY:
            # Back to NORMAL after successful sessions
            if self.current_context.successful_sessions_in_recovery >= \
               self.THRESHOLDS["successful_sessions_to_normal"]:
                return CoachState.NORMAL
            # Back to PROTECTIVE if relapse
            if burnout_score >= self.THRESHOLDS["score_to_warning"]:
                return CoachState.PROTECTIVE
        
        return None
    
    def update(
        self,
        burnout_score: BurnoutScore,
        trend: Optional[TrendAnalysis] = None,
        consecutive_failures: int = 0,
        ghost_loss_streak: int = 0,
        session_successful: Optional[bool] = None
    ) -> Optional[StateTransition]:
        """
        Update state machine with new data.
        
        Args:
            burnout_score: Current burnout score
            trend: Trend analysis result
            consecutive_failures: Number of consecutive problem failures
            ghost_loss_streak: Number of consecutive ghost race losses
            session_successful: If session just ended, was it successful?
            
        Returns:
            StateTransition if a transition occurred, None otherwise
        """
        # Update context
        self.current_context.burnout_score = burnout_score.score
        self.current_context.trend_direction = trend.direction if trend else None
        self.current_context.consecutive_failures = consecutive_failures
        self.current_context.ghost_loss_streak = ghost_loss_streak
        
        # Track successful sessions in recovery
        if self.current_state == CoachState.RECOVERY and session_successful is True:
            self.current_context.successful_sessions_in_recovery += 1
        
        # Determine if we should transition
        next_state = self._determine_next_state(
            burnout_score.score,
            trend,
            consecutive_failures,
            ghost_loss_streak
        )
        
        if next_state and self._can_transition(self.current_state, next_state):
            return self._transition_to(next_state, burnout_score.score, trend)
        
        return None
    
    def _transition_to(
        self,
        new_state: CoachState,
        burnout_score: float,
        trend: Optional[TrendAnalysis] = None
    ) -> StateTransition:
        """Execute a state transition."""
        old_state = self.current_state
        
        # Create transition record
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            timestamp=datetime.now(),
            trigger=self._get_trigger_reason(old_state, new_state, burnout_score, trend),
            burnout_score=burnout_score,
            trend_direction=trend.direction if trend else None
        )
        
        self.transition_history.append(transition)
        
        # Update context for new state
        self.current_context = StateContext(
            state=new_state,
            entered_at=datetime.now(),
            burnout_score=burnout_score,
            trend_direction=trend.direction if trend else None
        )
        
        # Call registered callbacks
        for callback in self._state_callbacks[new_state]:
            try:
                callback(self.current_context)
            except Exception as e:
                print(f"State callback error: {e}")
        
        return transition
    
    def _get_trigger_reason(
        self,
        from_state: CoachState,
        to_state: CoachState,
        score: float,
        trend: Optional[TrendAnalysis]
    ) -> str:
        """Generate human-readable trigger reason."""
        if to_state.value > from_state.value:  # Escalation
            if score >= 0.7:
                return f"Critical burnout score ({score:.2f})"
            elif score >= 0.5:
                return f"High burnout score ({score:.2f})"
            elif trend and trend.direction == TrendDirection.DETERIORATING:
                return f"Deteriorating trend (slope: {trend.slope:.3f})"
            else:
                return f"Score threshold crossed ({score:.2f})"
        else:  # De-escalation
            if trend and trend.direction == TrendDirection.RECOVERING:
                return f"Recovering trend (slope: {trend.slope:.3f})"
            else:
                return f"Score improved ({score:.2f})"
    
    def force_state(self, state: CoachState, reason: str = "manual override"):
        """Force transition to a specific state (for testing/admin)."""
        transition = StateTransition(
            from_state=self.current_state,
            to_state=state,
            timestamp=datetime.now(),
            trigger=reason,
            burnout_score=self.current_context.burnout_score,
            trend_direction=self.current_context.trend_direction
        )
        self.transition_history.append(transition)
        
        self.current_context = StateContext(
            state=state,
            entered_at=datetime.now(),
            burnout_score=self.current_context.burnout_score,
            trend_direction=self.current_context.trend_direction
        )
    
    def get_state_actions(self) -> Dict[str, Any]:
        """
        Get recommended actions for the current state.
        
        Returns dict of actions the coach/system should take.
        """
        state = self.current_state
        
        actions = {
            CoachState.NORMAL: {
                "ghost_speed": "normal",
                "coach_mode": "passive",
                "show_breaks": False,
                "intervention_level": "none",
            },
            CoachState.WATCHING: {
                "ghost_speed": "normal",
                "coach_mode": "attentive",
                "show_breaks": False,
                "intervention_level": "monitor",
            },
            CoachState.WARNING: {
                "ghost_speed": "slow",
                "coach_mode": "proactive",
                "show_breaks": True,
                "intervention_level": "gentle",
            },
            CoachState.PROTECTIVE: {
                "ghost_speed": "cooperative",
                "coach_mode": "supportive",
                "show_breaks": True,
                "intervention_level": "active",
            },
            CoachState.RECOVERY: {
                "ghost_speed": "encouraging",
                "coach_mode": "celebratory",
                "show_breaks": False,
                "intervention_level": "positive",
            },
        }
        
        return actions.get(state, actions[CoachState.NORMAL])
    
    def get_recent_transitions(self, count: int = 5) -> List[StateTransition]:
        """Get recent state transitions."""
        return self.transition_history[-count:]
    
    def reset(self):
        """Reset state machine to initial state."""
        self.current_context = StateContext(
            state=CoachState.NORMAL,
            entered_at=datetime.now(),
            burnout_score=0.0,
            trend_direction=None
        )
        self.transition_history.clear()
