"""
Real-Time Coach Coordinator

The master orchestrator that ties all real-time coaching layers together:
1. Real-time signal detector
2. TTS duck voice
3. Enhanced state machine
4. Intervention selector
5. Live cognitive mirror
6. Failure archetype detector

This is the single integration point for real-time coaching.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Set

from .realtime_detector import RealtimeDetector, RealtimeSignal, RealtimeDetection
from .duck_tts import get_duck_voice, VoiceMood
from .states import CoachStateMachine, CoachState, StateTransition
from .interventions import (
    InterventionSelector,
    InterventionContext,
    Intervention,
    InterventionType
)
from .live_cognitive_mirror import LiveCognitiveMirror, LiveCognitiveInsight, CognitiveBlock
from .failure_archetypes import FailureArchetype, FailureArchetypeDetector
from .scorer import BurnoutScorer, BurnoutScore, BurnoutLevel
from .trends import TrendDetector


@dataclass
class RealtimeCoachContext:
    """Full context for real-time coaching decisions."""
    # Current problem
    problem_id: Optional[int] = None
    problem_tags: List[str] = field(default_factory=list)
    problem_difficulty: Optional[int] = None
    
    # User state
    user_id: str = ""
    session_id: str = ""
    
    # Time tracking
    problem_start_time: Optional[datetime] = None
    session_start_time: Optional[datetime] = None
    
    # Performance tracking
    consecutive_failures: int = 0
    ghost_loss_streak: int = 0
    
    def time_on_problem_minutes(self) -> float:
        """Minutes spent on current problem."""
        if not self.problem_start_time:
            return 0.0
        return (datetime.now() - self.problem_start_time).total_seconds() / 60


@dataclass
class CoachingUpdate:
    """Result of a real-time coaching update."""
    timestamp: datetime
    
    # State
    coach_state: CoachState
    burnout_score: float
    burnout_level: BurnoutLevel
    
    # Detections
    active_signals: Set[RealtimeSignal]
    cognitive_insight: Optional[LiveCognitiveInsight]
    detected_archetype: Optional[FailureArchetype]
    
    # Intervention
    intervention: Optional[Intervention]
    intervention_delivered: bool = False
    
    # State changes
    state_transition: Optional[StateTransition] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "coach_state": self.coach_state.value,
            "burnout_score": round(self.burnout_score, 3),
            "burnout_level": self.burnout_level.value,
            "active_signals": [s.value for s in self.active_signals],
            "cognitive_block": self.cognitive_insight.block_type.value if self.cognitive_insight else None,
            "detected_archetype": self.detected_archetype.value if self.detected_archetype else None,
            "intervention": self.intervention.to_dict() if self.intervention else None,
            "intervention_delivered": self.intervention_delivered,
            "state_changed": self.state_transition is not None,
        }


class RealtimeCoach:
    """
    Real-time coaching coordinator.
    
    This is the main class that orchestrates all real-time coaching features.
    Call this from your editor integration.
    """
    
    def __init__(
        self,
        user_id: str,
        enable_tts: bool = True,
        enable_interventions: bool = True
    ):
        self.user_id = user_id
        self.enable_tts = enable_tts
        self.enable_interventions = enable_interventions
        
        # Initialize all subsystems
        self.realtime_detector = RealtimeDetector()
        self.state_machine = CoachStateMachine()
        self.intervention_selector = InterventionSelector()
        self.cognitive_mirror = LiveCognitiveMirror()
        self.archetype_detector = FailureArchetypeDetector()
        self.burnout_scorer = BurnoutScorer()
        self.trend_detector = TrendDetector()
        
        # Get TTS instance
        self.duck = get_duck_voice(enabled=enable_tts)
        
        # Context
        self.context = RealtimeCoachContext(user_id=user_id)
        
        # History
        self.updates: List[CoachingUpdate] = []
        
        # Register state change callback
        self.state_machine.register_callback(
            CoachState.HINTING,
            self._on_state_change_to_hinting
        )
        self.state_machine.register_callback(
            CoachState.WARNING,
            self._on_state_change_to_warning
        )
        self.state_machine.register_callback(
            CoachState.PROTECTIVE,
            self._on_state_change_to_protective
        )
    
    def start_problem(
        self, 
        problem_id: int,
        tags: List[str],
        difficulty: Optional[int] = None
    ):
        """Called when user starts a new problem."""
        self.context.problem_id = problem_id
        self.context.problem_tags = tags
        self.context.problem_difficulty = difficulty
        self.context.problem_start_time = datetime.now()
        
        # Reset detectors
        self.realtime_detector.start_problem(tags)
        self.cognitive_mirror.clear_insights()
    
    def on_typing(
        self,
        line_number: int,
        chars_added: int = 0,
        chars_deleted: int = 0,
        is_paste: bool = False
    ):
        """Called when user types/edits code."""
        self.realtime_detector.record_typing(
            line_number,
            chars_added,
            chars_deleted,
            is_paste
        )
    
    def on_code_change(self, code: str, line_count: int):
        """Called when code changes (snapshot)."""
        self.realtime_detector.record_snapshot(code, line_count)
    
    def update(self) -> CoachingUpdate:
        """
        Main update function - call this periodically (e.g., every 10-30 seconds).
        
        This is where the magic happens:
        1. Check for idle time
        2. Get active signals
        3. Infer cognitive state
        4. Update state machine
        5. Select intervention
        6. Deliver if appropriate
        """
        now = datetime.now()
        
        # 1. Check idle
        self.realtime_detector.check_idle()
        
        # 2. Get active signals
        active_signals = self.realtime_detector.get_active_signals()
        recent_detections = self.realtime_detector.get_recent_signals(minutes=5)
        
        # 3. Get burnout score (you'll need to integrate with event log)
        # For now, we'll use a simple estimate based on signals
        burnout_score = self._estimate_burnout_from_signals(active_signals)
        
        # 4. Detect archetype (needs historical data, simplified here)
        detected_archetype = self._detect_current_archetype(active_signals)
        
        # 5. Infer cognitive state
        cognitive_insight = self.cognitive_mirror.infer_cognitive_state(
            active_signals=list(active_signals),
            detected_archetype=detected_archetype,
            problem_tags=self.context.problem_tags,
            time_on_problem_minutes=self.context.time_on_problem_minutes(),
            burnout_state=self.state_machine.current_state
        )
        
        # 6. Update state machine
        state_transition = self.state_machine.update(
            burnout_score=burnout_score,
            trend=None,  # Would need historical data
            consecutive_failures=self.context.consecutive_failures,
            ghost_loss_streak=self.context.ghost_loss_streak,
            realtime_signal_count=len(active_signals)
        )
        
        # 7. Select intervention
        intervention = None
        if self.enable_interventions:
            intervention_context = InterventionContext(
                coach_state=self.state_machine.current_state,
                burnout_level=burnout_score.level,
                burnout_score=burnout_score.score,
                active_signals=active_signals,
                recent_detections=recent_detections,
                detected_archetype=detected_archetype,
                problem_tags=self.context.problem_tags,
                time_on_problem_minutes=self.context.time_on_problem_minutes(),
                interventions_in_current_state=self.intervention_selector.interventions_per_state.get(
                    self.state_machine.current_state, 0
                )
            )
            
            intervention = self.intervention_selector.select(intervention_context)
        
        # 8. Deliver intervention
        intervention_delivered = False
        if intervention and self.enable_tts:
            intervention_delivered = self.intervention_selector.deliver_intervention(intervention)
        
        # 9. Create update record
        update = CoachingUpdate(
            timestamp=now,
            coach_state=self.state_machine.current_state,
            burnout_score=burnout_score.score,
            burnout_level=burnout_score.level,
            active_signals=active_signals,
            cognitive_insight=cognitive_insight,
            detected_archetype=detected_archetype,
            intervention=intervention,
            intervention_delivered=intervention_delivered,
            state_transition=state_transition
        )
        
        self.updates.append(update)
        
        return update
    
    def _estimate_burnout_from_signals(self, signals: Set[RealtimeSignal]) -> BurnoutScore:
        """Estimate burnout score from current signals (simplified)."""
        # Map signals to burnout contribution
        signal_weights = {
            RealtimeSignal.TYPING_SPEED_DROP: 0.15,
            RealtimeSignal.LONG_IDLE: 0.20,
            RealtimeSignal.REWRITE_SAME_BLOCK: 0.15,
            RealtimeSignal.RAPID_BACKSPACE: 0.10,
            RealtimeSignal.COMMENT_SELF_DOUBT: 0.10,
        }
        
        score = sum(signal_weights.get(s, 0.05) for s in signals)
        score = min(score, 1.0)
        
        # Determine level
        if score >= 0.70:
            level = BurnoutLevel.CRITICAL
        elif score >= 0.50:
            level = BurnoutLevel.HIGH
        elif score >= 0.30:
            level = BurnoutLevel.MODERATE
        else:
            level = BurnoutLevel.LOW
        
        return BurnoutScore(
            score=score,
            level=level,
            timestamp=datetime.now(),
            contributing_signals=[],  # Simplified - no signal breakdown
            raw_weighted_sum=score,
            ema_smoothed=score
        )
    
    def _detect_current_archetype(
        self, 
        signals: Set[RealtimeSignal]
    ) -> Optional[FailureArchetype]:
        """Detect archetype from current signals (simplified)."""
        # Map signal combinations to archetypes
        if RealtimeSignal.EARLY_BRUTEFORCE_PATTERN in signals:
            return FailureArchetype.BRUTE_FORCER
        
        if RealtimeSignal.TYPING_SPEED_SPIKE in signals:
            return FailureArchetype.SPEED_DEMON
        
        if RealtimeSignal.LONG_IDLE in signals and RealtimeSignal.TYPING_SPEED_DROP in signals:
            return FailureArchetype.HESITATOR
        
        if RealtimeSignal.OUTDATED_TEMPLATE_USAGE in signals:
            return FailureArchetype.PATTERN_CHASER
        
        if RealtimeSignal.ALGORITHM_DELAY in signals:
            return FailureArchetype.AVOIDER
        
        return None
    
    def _on_state_change_to_hinting(self, context):
        """Called when entering HINTING state."""
        if self.enable_tts:
            self.duck.speak(
                "I'm here to help if you need it.",
                mood=VoiceMood.GENTLE,
                priority=3
            )
    
    def _on_state_change_to_warning(self, context):
        """Called when entering WARNING state."""
        if self.enable_tts:
            self.duck.speak(
                "Let's take a step back.",
                mood=VoiceMood.CALM,
                priority=5
            )
    
    def _on_state_change_to_protective(self, context):
        """Called when entering PROTECTIVE state."""
        if self.enable_tts:
            self.duck.speak(
                "It's time for a break. You've pushed hard.",
                mood=VoiceMood.PROTECTIVE,
                priority=8
            )
    
    def on_problem_submit(self, success: bool):
        """Called when user submits a solution."""
        if not success:
            self.context.consecutive_failures += 1
        else:
            self.context.consecutive_failures = 0
    
    def on_ghost_race_result(self, won: bool):
        """Called when ghost race completes."""
        if not won:
            self.context.ghost_loss_streak += 1
        else:
            self.context.ghost_loss_streak = 0
    
    def get_current_state(self) -> CoachState:
        """Get current coach state."""
        return self.state_machine.current_state
    
    def get_state_actions(self) -> Dict[str, Any]:
        """Get recommended actions for current state."""
        return self.state_machine.get_state_actions()
    
    def get_latest_update(self) -> Optional[CoachingUpdate]:
        """Get most recent coaching update."""
        return self.updates[-1] if self.updates else None
    
    def get_active_signals(self) -> Set[RealtimeSignal]:
        """Get currently active signals."""
        return self.realtime_detector.get_active_signals()
    
    def get_current_cognitive_insight(self) -> Optional[LiveCognitiveInsight]:
        """Get current cognitive insight."""
        return self.cognitive_mirror.get_current_insight()
    
    def enable_voice(self, enabled: bool = True):
        """Enable or disable TTS."""
        self.enable_tts = enabled
        self.duck.set_enabled(enabled)
    
    def enable_coaching(self, enabled: bool = True):
        """Enable or disable interventions."""
        self.enable_interventions = enabled


# Convenience function for single-instance usage
_global_coach: Optional[RealtimeCoach] = None


def get_realtime_coach(
    user_id: str = "default",
    enable_tts: bool = True,
    enable_interventions: bool = True
) -> RealtimeCoach:
    """Get or create the global realtime coach instance."""
    global _global_coach
    if _global_coach is None:
        _global_coach = RealtimeCoach(
            user_id=user_id,
            enable_tts=enable_tts,
            enable_interventions=enable_interventions
        )
    return _global_coach
