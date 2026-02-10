"""
Intervention Selector - Decides What The Duck Says

This is the decision engine that determines:
1. Whether to intervene
2. What type of intervention
3. What to say
4. How to say it (mood)

Critical rule: The coach may only speak once per state unless state changes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Any
from enum import Enum

from .states import CoachState, StateContext
from .realtime_detector import RealtimeSignal, RealtimeDetection
from .failure_archetypes import FailureArchetype
from .duck_tts import VoiceMood, DuckPhrases, duck_speak
from .scorer import BurnoutLevel


class InterventionType(Enum):
    """Types of interventions the coach can make."""
    NONE = "none"
    HINT = "hint"
    QUESTION = "question"
    REFRAME = "reframe"
    WARNING = "warning"
    REST_SUGGESTION = "rest_suggestion"
    ENCOURAGEMENT = "encouragement"
    MODERNIZATION = "modernization"
    ALGORITHM_NUDGE = "algorithm_nudge"
    SLOW_DOWN = "slow_down"
    STEP_BACK = "step_back"


@dataclass
class InterventionContext:
    """Context for making intervention decisions."""
    # State
    coach_state: CoachState
    burnout_level: BurnoutLevel
    burnout_score: float
    
    # Realtime signals
    active_signals: Set[RealtimeSignal]
    recent_detections: List[RealtimeDetection]
    
    # Failure archetype
    detected_archetype: Optional[FailureArchetype] = None
    archetype_confidence: float = 0.0
    
    # Problem context
    problem_tags: List[str] = field(default_factory=list)
    time_on_problem_minutes: float = 0.0
    
    # History
    interventions_in_current_state: int = 0
    last_intervention_time: Optional[datetime] = None
    user_adapted_to_last_intervention: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "coach_state": self.coach_state.value,
            "burnout_level": self.burnout_level.value,
            "burnout_score": round(self.burnout_score, 3),
            "active_signals": [s.value for s in self.active_signals],
            "detected_archetype": self.detected_archetype.value if self.detected_archetype else None,
            "problem_tags": self.problem_tags,
            "time_on_problem": round(self.time_on_problem_minutes, 1),
            "interventions_in_state": self.interventions_in_current_state,
        }


@dataclass
class Intervention:
    """A coaching intervention to be delivered."""
    intervention_type: InterventionType
    text: str
    mood: VoiceMood
    priority: int = 0
    should_speak: bool = True
    
    # Metadata
    triggered_by: str = ""
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.intervention_type.value,
            "text": self.text,
            "mood": self.mood.value,
            "priority": self.priority,
            "should_speak": self.should_speak,
            "triggered_by": self.triggered_by,
            "confidence": round(self.confidence, 3),
        }


class InterventionSelector:
    """
    Decides what coaching intervention to deliver.
    
    Key rules:
    1. Only one intervention per state (unless critical)
    2. Don't nag - wait for state changes
    3. Consult all layers: burnout + archetype + realtime + cognitive mirror
    4. Prefer questions over commands
    5. Escalate gradually
    """
    
    def __init__(self):
        self.intervention_history: List[Intervention] = []
        self.interventions_per_state: Dict[CoachState, int] = {}
        self.last_intervention_per_state: Dict[CoachState, datetime] = {}
        
        # Cooldowns (minimum time between interventions)
        self.cooldown_per_state = {
            CoachState.SILENT: timedelta(hours=1),
            CoachState.NORMAL: timedelta(minutes=30),
            CoachState.WATCHING: timedelta(minutes=15),
            CoachState.HINTING: timedelta(minutes=5),
            CoachState.WARNING: timedelta(minutes=3),
            CoachState.PROTECTIVE: timedelta(minutes=1),
            CoachState.RECOVERY: timedelta(minutes=5),
        }
    
    def select(self, context: InterventionContext) -> Optional[Intervention]:
        """
        Select the appropriate intervention based on context.
        
        Returns None if no intervention needed.
        """
        # Rule 1: Check if we can intervene at all
        if not self._should_intervene(context):
            return None
        
        # Rule 2: Check state-specific intervention limits
        if not self._within_intervention_limits(context):
            return None
        
        # Rule 3: Check cooldown
        if not self._cooldown_elapsed(context):
            return None
        
        # Select intervention based on priority order
        intervention = None
        
        # Priority 1: Burnout protection (highest priority)
        if context.burnout_level in [BurnoutLevel.HIGH, BurnoutLevel.CRITICAL]:
            intervention = self._select_burnout_intervention(context)
        
        # Priority 2: Real-time signals (immediate feedback)
        if not intervention and context.active_signals:
            intervention = self._select_realtime_intervention(context)
        
        # Priority 3: Failure archetype (pattern-based)
        if not intervention and context.detected_archetype:
            intervention = self._select_archetype_intervention(context)
        
        # Priority 4: State-based general coaching
        if not intervention:
            intervention = self._select_state_intervention(context)
        
        # Record intervention if selected
        if intervention:
            self._record_intervention(context.coach_state, intervention)
        
        return intervention
    
    def _should_intervene(self, context: InterventionContext) -> bool:
        """Check if we should intervene at all."""
        # Never intervene in SILENT state
        if context.coach_state == CoachState.SILENT:
            return False
        
        # Don't intervene in NORMAL unless there's a strong signal
        if context.coach_state == CoachState.NORMAL:
            return len(context.active_signals) >= 2 or context.burnout_level == BurnoutLevel.CRITICAL
        
        return True
    
    def _within_intervention_limits(self, context: InterventionContext) -> bool:
        """Check if we're within intervention limits for current state."""
        state = context.coach_state
        limit = self._get_intervention_limit(state)
        count = self.interventions_per_state.get(state, 0)
        
        # Allow more interventions in protective state
        if state == CoachState.PROTECTIVE:
            return count < limit
        
        # One intervention per state for others (unless critical)
        if context.burnout_level == BurnoutLevel.CRITICAL:
            return True  # Override for critical situations
        
        return count < limit
    
    def _get_intervention_limit(self, state: CoachState) -> int:
        """Get max interventions allowed per state."""
        limits = {
            CoachState.SILENT: 0,
            CoachState.NORMAL: 1,
            CoachState.WATCHING: 1,
            CoachState.HINTING: 2,
            CoachState.WARNING: 2,
            CoachState.PROTECTIVE: 5,
            CoachState.RECOVERY: 2,
        }
        return limits.get(state, 1)
    
    def _cooldown_elapsed(self, context: InterventionContext) -> bool:
        """Check if cooldown has elapsed since last intervention."""
        state = context.coach_state
        last_time = self.last_intervention_per_state.get(state)
        
        if not last_time:
            return True
        
        cooldown = self.cooldown_per_state.get(state, timedelta(minutes=5))
        return datetime.now() - last_time >= cooldown
    
    def _select_burnout_intervention(
        self, 
        context: InterventionContext
    ) -> Optional[Intervention]:
        """Select intervention for burnout protection."""
        if context.burnout_level == BurnoutLevel.CRITICAL:
            phrase = DuckPhrases.get_phrase("burnout_protective")
            return Intervention(
                intervention_type=InterventionType.REST_SUGGESTION,
                text=phrase or "You're burning out. This is a good place to stop.",
                mood=VoiceMood.PROTECTIVE,
                priority=10,
                triggered_by="critical_burnout",
                confidence=1.0
            )
        
        elif context.burnout_level == BurnoutLevel.HIGH:
            phrase = DuckPhrases.get_phrase("burnout_warning")
            return Intervention(
                intervention_type=InterventionType.WARNING,
                text=phrase or "You've pushed hard today. Take a ten-minute break.",
                mood=VoiceMood.WARNING,
                priority=8,
                triggered_by="high_burnout",
                confidence=0.9
            )
        
        return None
    
    def _select_realtime_intervention(
        self, 
        context: InterventionContext
    ) -> Optional[Intervention]:
        """Select intervention based on real-time signals."""
        signals = context.active_signals
        
        # Priority order for signals
        if RealtimeSignal.TYPING_SPEED_DROP in signals:
            phrase = DuckPhrases.get_phrase("typing_slow")
            return Intervention(
                intervention_type=InterventionType.QUESTION,
                text=phrase or "You seem stuck. Want to talk through the approach?",
                mood=VoiceMood.GENTLE,
                priority=6,
                triggered_by="typing_speed_drop"
            )
        
        if RealtimeSignal.TYPING_SPEED_SPIKE in signals:
            phrase = DuckPhrases.get_phrase("typing_fast")
            return Intervention(
                intervention_type=InterventionType.SLOW_DOWN,
                text=phrase or "You're rushing. This problem rewards structure, not speed.",
                mood=VoiceMood.CALM,
                priority=7,
                triggered_by="typing_speed_spike"
            )
        
        if RealtimeSignal.EARLY_BRUTEFORCE_PATTERN in signals:
            phrase = DuckPhrases.get_phrase("early_bruteforce")
            return Intervention(
                intervention_type=InterventionType.STEP_BACK,
                text=phrase or "Before nested loops, what makes this case different from that case?",
                mood=VoiceMood.GENTLE,
                priority=7,
                triggered_by="early_bruteforce"
            )
        
        if RealtimeSignal.REWRITE_SAME_BLOCK in signals:
            phrase = DuckPhrases.get_phrase("rewriting_code")
            return Intervention(
                intervention_type=InterventionType.STEP_BACK,
                text=phrase or "Third time on this block. What assumption needs to change?",
                mood=VoiceMood.CALM,
                priority=6,
                triggered_by="code_rewrite"
            )
        
        if RealtimeSignal.CODE_LENGTH_EXPLOSION in signals:
            phrase = DuckPhrases.get_phrase("code_explosion")
            return Intervention(
                intervention_type=InterventionType.REFRAME,
                text=phrase or "This is growing fast. What's the simplest invariant?",
                mood=VoiceMood.CALM,
                priority=6,
                triggered_by="code_length_explosion"
            )
        
        if RealtimeSignal.OUTDATED_TEMPLATE_USAGE in signals:
            phrase = DuckPhrases.get_phrase("outdated_template")
            return Intervention(
                intervention_type=InterventionType.MODERNIZATION,
                text=phrase or "This template is slowing you. Want to reset clean?",
                mood=VoiceMood.NEUTRAL,
                priority=5,
                triggered_by="outdated_pattern"
            )
        
        if RealtimeSignal.NO_DS_USAGE in signals:
            phrase = DuckPhrases.get_phrase("no_data_structures")
            return Intervention(
                intervention_type=InterventionType.HINT,
                text=phrase or "A map or set could simplify this logic.",
                mood=VoiceMood.NEUTRAL,
                priority=5,
                triggered_by="ds_avoidance"
            )
        
        if RealtimeSignal.ALGORITHM_DELAY in signals:
            # Check if it's DP problem
            if "dp" in context.problem_tags or "dynamic programming" in context.problem_tags:
                phrase = DuckPhrases.get_phrase("dp_avoidance")
                return Intervention(
                    intervention_type=InterventionType.ALGORITHM_NUDGE,
                    text=phrase or "This has overlapping subproblems. See it?",
                    mood=VoiceMood.GENTLE,
                    priority=6,
                    triggered_by="dp_avoidance"
                )
            else:
                phrase = DuckPhrases.get_phrase("algo_avoidance")
                return Intervention(
                    intervention_type=InterventionType.ALGORITHM_NUDGE,
                    text=phrase or "A standard algorithm could help here.",
                    mood=VoiceMood.NEUTRAL,
                    priority=5,
                    triggered_by="algo_avoidance"
                )
        
        return None
    
    def _select_archetype_intervention(
        self, 
        context: InterventionContext
    ) -> Optional[Intervention]:
        """Select intervention based on failure archetype."""
        archetype = context.detected_archetype
        
        if not archetype or context.archetype_confidence < 0.6:
            return None
        
        # Archetype-specific interventions
        if archetype == FailureArchetype.BRUTE_FORCER:
            return Intervention(
                intervention_type=InterventionType.STEP_BACK,
                text="You're over-enumerating. What constraint can you exploit?",
                mood=VoiceMood.GENTLE,
                priority=5,
                triggered_by=f"archetype_{archetype.value}"
            )
        
        elif archetype == FailureArchetype.PATTERN_CHASER:
            return Intervention(
                intervention_type=InterventionType.REFRAME,
                text="This isn't a template problem. What's unique about it?",
                mood=VoiceMood.CALM,
                priority=5,
                triggered_by=f"archetype_{archetype.value}"
            )
        
        elif archetype == FailureArchetype.HESITATOR:
            return Intervention(
                intervention_type=InterventionType.ENCOURAGEMENT,
                text="You have the right idea. Trust it and implement.",
                mood=VoiceMood.ENCOURAGING,
                priority=4,
                triggered_by=f"archetype_{archetype.value}"
            )
        
        elif archetype == FailureArchetype.SPEED_DEMON:
            return Intervention(
                intervention_type=InterventionType.SLOW_DOWN,
                text="Slow down. Speed comes from clarity, not rushing.",
                mood=VoiceMood.CALM,
                priority=6,
                triggered_by=f"archetype_{archetype.value}"
            )
        
        return None
    
    def _select_state_intervention(
        self, 
        context: InterventionContext
    ) -> Optional[Intervention]:
        """Select generic intervention based on coach state."""
        state = context.coach_state
        
        if state == CoachState.HINTING:
            return Intervention(
                intervention_type=InterventionType.QUESTION,
                text="What property stays true when you extend the solution?",
                mood=VoiceMood.GENTLE,
                priority=3,
                triggered_by="state_hinting"
            )
        
        elif state == CoachState.WARNING:
            return Intervention(
                intervention_type=InterventionType.WARNING,
                text="You're struggling. Let's decompose this step by step.",
                mood=VoiceMood.CALM,
                priority=5,
                triggered_by="state_warning"
            )
        
        elif state == CoachState.RECOVERY:
            phrase = DuckPhrases.get_phrase("progress")
            return Intervention(
                intervention_type=InterventionType.ENCOURAGEMENT,
                text=phrase or "Better. Trust the process.",
                mood=VoiceMood.ENCOURAGING,
                priority=3,
                triggered_by="state_recovery"
            )
        
        return None
    
    def _record_intervention(self, state: CoachState, intervention: Intervention):
        """Record that an intervention was delivered."""
        self.intervention_history.append(intervention)
        self.interventions_per_state[state] = \
            self.interventions_per_state.get(state, 0) + 1
        self.last_intervention_per_state[state] = datetime.now()
    
    def on_state_change(self, new_state: CoachState):
        """Reset intervention counter when state changes."""
        # Keep history but reset per-state counter
        self.interventions_per_state[new_state] = 0
    
    def deliver_intervention(self, intervention: Intervention) -> bool:
        """
        Deliver the intervention via TTS.
        
        Returns True if delivered, False if failed.
        """
        if not intervention or not intervention.should_speak:
            return False
        
        return duck_speak(
            intervention.text,
            mood=intervention.mood,
            priority=intervention.priority
        )
    
    def get_recent_interventions(self, count: int = 5) -> List[Intervention]:
        """Get recent interventions."""
        return self.intervention_history[-count:]


# Convenience function
def select_and_deliver(context: InterventionContext) -> Optional[Intervention]:
    """Select and immediately deliver an intervention."""
    selector = InterventionSelector()
    intervention = selector.select(context)
    
    if intervention:
        selector.deliver_intervention(intervention)
    
    return intervention
