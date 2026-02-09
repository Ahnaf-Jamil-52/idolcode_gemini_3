"""
Coach Response Selector Module

Selects appropriate coach responses based on sentiment analysis
and burnout detection. Maps emotional states to supportive messages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import random

from .sentiment import EmotionalState
from .fusion import BehaviorTextAlignment, InterventionLevel, FusionResult
from .states import CoachState
from .gemini_analyzer import GeminiCoachAnalyzer


class ResponseStrategy(Enum):
    """High-level response strategies."""
    VALIDATE_REFRAME = "validate_reframe"    # Acknowledge + perspective shift
    HUMANIZE_SLOW = "humanize_slow"          # Show idol struggled too + reduce pace
    SUGGEST_REST = "suggest_rest"            # Encourage break
    GENTLE_PROBE = "gentle_probe"            # Ask how they're really feeling
    AMPLIFY_SUCCESS = "amplify_success"      # Celebrate wins
    INITIATE_CONTACT = "initiate_contact"    # Reach out to silent user
    ENCOURAGE_CONTINUE = "encourage_continue"  # Positive reinforcement
    STAY_QUIET = "stay_quiet"                # Don't interrupt


@dataclass
class CoachResponse:
    """A coach response to deliver to the user."""
    message: str
    strategy: ResponseStrategy
    emotion_display: str  # For avatar animation
    priority: int  # 1 = highest
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "strategy": self.strategy.value,
            "emotion_display": self.emotion_display,
            "priority": self.priority,
            "metadata": self.metadata,
        }


# Response templates organized by strategy
RESPONSE_TEMPLATES: Dict[ResponseStrategy, List[Dict[str, Any]]] = {
    ResponseStrategy.VALIDATE_REFRAME: [
        {
            "message": "This one's tough. Even {idol_name} got 5 WAs on this exact problem.",
            "emotion": "understanding",
            "requires": ["idol_name"],
        },
        {
            "message": "That's a tricky edge case. Most people miss it the first time.",
            "emotion": "supportive",
            "requires": [],
        },
        {
            "message": "I see what you're trying. The logic is right, just needs a small tweak.",
            "emotion": "encouraging",
            "requires": [],
        },
        {
            "message": "This problem has a 30% acceptance rate. You're doing fine.",
            "emotion": "calm",
            "requires": [],
        },
        {
            "message": "Frustration means you're pushing your limits. That's growth.",
            "emotion": "wise",
            "requires": [],
        },
    ],
    
    ResponseStrategy.HUMANIZE_SLOW: [
        {
            "message": "You're not behind. You're at the exact stage {idol_name} was at contest #{contest_num}. They felt this too.",
            "emotion": "empathetic",
            "requires": ["idol_name", "contest_num"],
        },
        {
            "message": "{idol_name} spent 2 hours on this problem type before it clicked. You're on track.",
            "emotion": "patient",
            "requires": ["idol_name"],
        },
        {
            "message": "Even pros have off days. {idol_name}'s rating dropped 100 points before their breakthrough.",
            "emotion": "understanding",
            "requires": ["idol_name"],
        },
        {
            "message": "Let's slow down a bit. No rush. The ghost will wait.",
            "emotion": "calm",
            "requires": [],
        },
        {
            "message": "Quality thinking matters more than speed right now.",
            "emotion": "wise",
            "requires": [],
        },
    ],
    
    ResponseStrategy.SUGGEST_REST: [
        {
            "message": "Legends also rested here. 🌙 Rest is part of the journey.",
            "emotion": "caring",
            "requires": [],
        },
        {
            "message": "Your brain is still processing in the background. A 10-minute break often unlocks solutions.",
            "emotion": "knowing",
            "requires": [],
        },
        {
            "message": "You've been going strong for {session_minutes} minutes. That's impressive! Maybe grab some water?",
            "emotion": "supportive",
            "requires": ["session_minutes"],
        },
        {
            "message": "Sleep on it? Solutions often appear after rest. {idol_name} was famous for this.",
            "emotion": "wise",
            "requires": ["idol_name"],
        },
        {
            "message": "No shame in pausing. You can pick up right where you left off.",
            "emotion": "calm",
            "requires": [],
        },
    ],
    
    ResponseStrategy.GENTLE_PROBE: [
        {
            "message": "How are you actually feeling about this problem? No wrong answer.",
            "emotion": "curious",
            "requires": [],
        },
        {
            "message": "I notice we've been moving through problems differently today. Want to try something new?",
            "emotion": "attentive",
            "requires": [],
        },
        {
            "message": "What's going through your mind right now?",
            "emotion": "open",
            "requires": [],
        },
        {
            "message": "Scale of 1-10, how energized are you feeling?",
            "emotion": "curious",
            "requires": [],
        },
        {
            "message": "Something feels different this session. Want to talk about it?",
            "emotion": "concerned",
            "requires": [],
        },
    ],
    
    ResponseStrategy.AMPLIFY_SUCCESS: [
        {
            "message": "That's real growth 🎉 You solved it faster than {idol_name} did at your rating!",
            "emotion": "excited",
            "requires": ["idol_name"],
        },
        {
            "message": "Clean solution! Your thinking is getting sharper.",
            "emotion": "proud",
            "requires": [],
        },
        {
            "message": "See that? Your instincts are improving. Trust them more.",
            "emotion": "encouraging",
            "requires": [],
        },
        {
            "message": "That approach was creative. Not the standard solution, but elegant.",
            "emotion": "impressed",
            "requires": [],
        },
        {
            "message": "Streak continues! You're in the zone.",
            "emotion": "hyped",
            "requires": [],
        },
    ],
    
    ResponseStrategy.INITIATE_CONTACT: [
        {
            "message": "Hey, haven't heard from you. Want me to find something fun instead of hard?",
            "emotion": "friendly",
            "requires": [],
        },
        {
            "message": "Still there? No pressure, just checking in.",
            "emotion": "caring",
            "requires": [],
        },
        {
            "message": "I have a puzzle that might be more enjoyable. Interested?",
            "emotion": "playful",
            "requires": [],
        },
        {
            "message": "Take your time. I'm here when you're ready.",
            "emotion": "patient",
            "requires": [],
        },
        {
            "message": "The ghost misses racing you. 👻 Ready when you are!",
            "emotion": "playful",
            "requires": [],
        },
    ],
    
    ResponseStrategy.ENCOURAGE_CONTINUE: [
        {
            "message": "You're making great progress. Keep it up!",
            "emotion": "supportive",
            "requires": [],
        },
        {
            "message": "Solid session so far. Your consistency is building real skill.",
            "emotion": "proud",
            "requires": [],
        },
        {
            "message": "The pattern recognition is coming together.",
            "emotion": "observant",
            "requires": [],
        },
        {
            "message": "Good recovery from earlier. That resilience is valuable.",
            "emotion": "admiring",
            "requires": [],
        },
        {
            "message": "One problem at a time. You've got this.",
            "emotion": "calm",
            "requires": [],
        },
    ],
    
    ResponseStrategy.STAY_QUIET: [],  # No messages - let user focus
}

# Map emotional states to response strategies
STATE_TO_STRATEGY: Dict[EmotionalState, ResponseStrategy] = {
    EmotionalState.FRUSTRATED: ResponseStrategy.VALIDATE_REFRAME,
    EmotionalState.DISCOURAGED: ResponseStrategy.HUMANIZE_SLOW,
    EmotionalState.FATIGUED: ResponseStrategy.SUGGEST_REST,
    EmotionalState.MASKED: ResponseStrategy.GENTLE_PROBE,
    EmotionalState.CELEBRATING: ResponseStrategy.AMPLIFY_SUCCESS,
    EmotionalState.MOTIVATED: ResponseStrategy.STAY_QUIET,
    EmotionalState.NEUTRAL: ResponseStrategy.STAY_QUIET,
}

# Map alignments to strategies (overrides emotional state)
ALIGNMENT_TO_STRATEGY: Dict[BehaviorTextAlignment, ResponseStrategy] = {
    BehaviorTextAlignment.MASKING: ResponseStrategy.GENTLE_PROBE,
    BehaviorTextAlignment.SILENT_DISENGAGE: ResponseStrategy.INITIATE_CONTACT,
    BehaviorTextAlignment.CONFIRMED_BURNOUT: ResponseStrategy.SUGGEST_REST,
    BehaviorTextAlignment.VENTING_OK: ResponseStrategy.VALIDATE_REFRAME,
    BehaviorTextAlignment.GENUINE_GOOD: ResponseStrategy.STAY_QUIET,
}


class ResponseSelector:
    """
    Selects appropriate coach responses based on fusion analysis.
    
    Uses a priority system:
    1. Critical states (masking, high burnout) always respond
    2. Emotional states trigger appropriate strategies
    3. Random selection from appropriate templates
    4. Cooldown prevents message spam
    """
    
    def __init__(
        self,
        cooldown_seconds: int = 60,
        idol_name: str = "tourist",
        use_gemini: bool = False,
        gemini_api_key: Optional[str] = None
    ):
        self.cooldown_seconds = cooldown_seconds
        self.idol_name = idol_name
        self.use_gemini = use_gemini
        self.gemini_analyzer = GeminiCoachAnalyzer(gemini_api_key) if use_gemini else None
        self._last_response_time: Optional[datetime] = None
        self._responses_this_session: List[CoachResponse] = []
        self._used_templates: set = set()  # Avoid repetition
    
    def select_strategy(
        self,
        fusion_result: FusionResult,
        emotional_state: Optional[EmotionalState] = None
    ) -> ResponseStrategy:
        """Select the best response strategy for current state."""
        
        # Alignment-based strategies take priority
        if fusion_result.alignment in ALIGNMENT_TO_STRATEGY:
            return ALIGNMENT_TO_STRATEGY[fusion_result.alignment]
        
        # State machine overrides
        if fusion_result.current_state == CoachState.PROTECTIVE:
            return ResponseStrategy.SUGGEST_REST
        
        if fusion_result.current_state == CoachState.RECOVERY:
            return ResponseStrategy.ENCOURAGE_CONTINUE
        
        # Emotional state strategies
        if emotional_state and emotional_state in STATE_TO_STRATEGY:
            return STATE_TO_STRATEGY[emotional_state]
        
        # Default: stay quiet unless there's a reason to speak
        return ResponseStrategy.STAY_QUIET
    
    def _can_respond(self) -> bool:
        """Check if enough time passed since last response."""
        if self._last_response_time is None:
            return True
        
        elapsed = (datetime.now() - self._last_response_time).total_seconds()
        return elapsed >= self.cooldown_seconds
    
    def _select_template(
        self,
        strategy: ResponseStrategy,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select an appropriate template from the strategy."""
        templates = RESPONSE_TEMPLATES.get(strategy, [])
        
        if not templates:
            return None
        
        # Filter templates by available context
        available = []
        for template in templates:
            required = template.get("requires", [])
            if all(key in context for key in required):
                # Check if we've used this recently
                template_key = f"{strategy.value}:{template['message'][:30]}"
                if template_key not in self._used_templates:
                    available.append(template)
        
        # If all templates used, reset and try again
        if not available:
            self._used_templates = set()
            available = [
                t for t in templates 
                if all(k in context for k in t.get("requires", []))
            ]
        
        if not available:
            return None
        
        return random.choice(available)
    
    def _format_message(
        self,
        template: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Format template with context values."""
        message = template["message"]
        
        try:
            return message.format(**context)
        except KeyError:
            # Fallback if missing context
            return message
    
    def generate_response(
        self,
        fusion_result: FusionResult,
        emotional_state: Optional[EmotionalState] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CoachResponse]:
        """
        Generate a coach response based on current state.
        
        Returns None if:
        - Strategy is STAY_QUIET
        - Cooldown active
        - No appropriate template
        """
        # Check cooldown (bypass for urgent situations)
        if not fusion_result.needs_immediate_attention and not self._can_respond():
            return None
        
        # Select strategy
        strategy = self.select_strategy(fusion_result, emotional_state)
        
        if strategy == ResponseStrategy.STAY_QUIET:
            return None
        
        # Build context for templates
        ctx = context or {}
        ctx.setdefault("idol_name", self.idol_name)
        ctx.setdefault("contest_num", random.randint(20, 100))
        ctx.setdefault("session_minutes", 30)
        
        # Select and format template
        template = self._select_template(strategy, ctx)
        
        if not template:
            return None
        
        # Use Gemini for personalized responses in complex cases
        if (self.use_gemini and self.gemini_analyzer and 
            self._should_use_gemini_response(strategy, fusion_result)):
            
            try:
                # Extract user state from fusion result
                user_state = {
                    'burnout_score': fusion_result.composite_score,
                    'emotional_state': emotional_state.value if emotional_state else 'neutral',
                    'recommended_response_tone': self._strategy_to_tone(strategy),
                    'suggested_action': self._strategy_to_action(strategy),
                    'alignment': fusion_result.alignment.value,
                    'intervention_needed': fusion_result.needs_immediate_attention
                }
                
                # Get context for Gemini
                problem_context = ctx.copy()
                
                # Generate personalized response with Gemini
                gemini_message = self.gemini_analyzer.generate_contextual_response(
                    user_state=user_state,
                    idol_name=self.idol_name,
                    problem_context=problem_context
                )
                
                if gemini_message and len(gemini_message.strip()) > 10:  # Valid response
                    message = gemini_message
                else:
                    message = self._format_message(template, ctx)  # Fallback
                    
            except Exception as e:
                print(f"Gemini response generation failed: {e}")
                message = self._format_message(template, ctx)  # Fallback
        else:
            message = self._format_message(template, ctx)
        
        # Create response
        response = CoachResponse(
            message=message,
            strategy=strategy,
            emotion_display=template.get("emotion", "neutral"),
            priority=self._get_priority(strategy, fusion_result),
            metadata={
                "alignment": fusion_result.alignment.value,
                "state": fusion_result.current_state.value,
                "composite_score": fusion_result.composite_score,
            }
        )
        
        # Track response
        self._last_response_time = datetime.now()
        self._responses_this_session.append(response)
        
        # Track used template
        template_key = f"{strategy.value}:{template['message'][:30]}"
        self._used_templates.add(template_key)
        
        return response
    
    def _get_priority(
        self,
        strategy: ResponseStrategy,
        fusion_result: FusionResult
    ) -> int:
        """Determine response priority (1 = highest)."""
        if fusion_result.needs_immediate_attention:
            return 1
        
        priority_map = {
            ResponseStrategy.GENTLE_PROBE: 2,  # Masking is concerning
            ResponseStrategy.SUGGEST_REST: 2,
            ResponseStrategy.INITIATE_CONTACT: 3,
            ResponseStrategy.VALIDATE_REFRAME: 3,
            ResponseStrategy.HUMANIZE_SLOW: 3,
            ResponseStrategy.AMPLIFY_SUCCESS: 4,
            ResponseStrategy.ENCOURAGE_CONTINUE: 5,
        }
        
        return priority_map.get(strategy, 5)
    
    def force_response(
        self,
        strategy: ResponseStrategy,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CoachResponse]:
        """Force a response of a specific strategy (for testing)."""
        ctx = context or {}
        ctx.setdefault("idol_name", self.idol_name)
        
        template = self._select_template(strategy, ctx)
        
        if not template:
            return None
        
        message = self._format_message(template, ctx)
        
        return CoachResponse(
            message=message,
            strategy=strategy,
            emotion_display=template.get("emotion", "neutral"),
            priority=3,
        )
    
    def get_session_responses(self) -> List[CoachResponse]:
        """Get all responses from this session."""
        return self._responses_this_session.copy()
    
    def _should_use_gemini_response(self, strategy: ResponseStrategy, fusion_result: FusionResult) -> bool:
        """Determine if Gemini should generate this response instead of template."""
        # Use Gemini for complex psychological situations
        complex_strategies = [
            ResponseStrategy.GENTLE_PROBE,
            ResponseStrategy.VALIDATE_REFRAME,
            ResponseStrategy.HUMANIZE_SLOW
        ]
        
        # Always use Gemini for masking detection
        if fusion_result.alignment == BehaviorTextAlignment.MASKING:
            return True
        
        # Use for high burnout situations
        if fusion_result.composite_score > 0.6:
            return True
        
        # Use for complex strategies
        if strategy in complex_strategies:
            return True
        
        return False
    
    def _strategy_to_tone(self, strategy: ResponseStrategy) -> str:
        """Convert strategy to tone for Gemini."""
        tone_map = {
            ResponseStrategy.VALIDATE_REFRAME: "supportive",
            ResponseStrategy.HUMANIZE_SLOW: "supportive", 
            ResponseStrategy.SUGGEST_REST: "protective",
            ResponseStrategy.GENTLE_PROBE: "encouraging",
            ResponseStrategy.AMPLIFY_SUCCESS: "encouraging",
            ResponseStrategy.INITIATE_CONTACT: "supportive",
            ResponseStrategy.ENCOURAGE_CONTINUE: "encouraging"
        }
        return tone_map.get(strategy, "supportive")
    
    def _strategy_to_action(self, strategy: ResponseStrategy) -> str:
        """Convert strategy to action for Gemini."""
        action_map = {
            ResponseStrategy.VALIDATE_REFRAME: "encourage",
            ResponseStrategy.HUMANIZE_SLOW: "slow_ghost",
            ResponseStrategy.SUGGEST_REST: "suggest_break", 
            ResponseStrategy.GENTLE_PROBE: "probe_deeper",
            ResponseStrategy.AMPLIFY_SUCCESS: "celebrate",
            ResponseStrategy.INITIATE_CONTACT: "probe_deeper",
            ResponseStrategy.ENCOURAGE_CONTINUE: "encourage"
        }
        return action_map.get(strategy, "encourage")
    
    def reset_session(self):
        """Reset for new session."""
        self._last_response_time = None
        self._responses_this_session.clear()
        self._used_templates.clear()


class EmotionToAvatarMapper:
    """Maps coach emotions to avatar animation states."""
    
    EMOTION_ANIMATIONS = {
        "understanding": {"pose": "nodding", "expression": "empathetic", "intensity": 0.7},
        "supportive": {"pose": "open", "expression": "warm", "intensity": 0.6},
        "encouraging": {"pose": "thumbs_up", "expression": "positive", "intensity": 0.8},
        "calm": {"pose": "relaxed", "expression": "serene", "intensity": 0.4},
        "wise": {"pose": "thinking", "expression": "knowing", "intensity": 0.5},
        "empathetic": {"pose": "leaning_forward", "expression": "concerned", "intensity": 0.7},
        "patient": {"pose": "waiting", "expression": "calm", "intensity": 0.3},
        "caring": {"pose": "hands_together", "expression": "gentle", "intensity": 0.6},
        "knowing": {"pose": "pointing_up", "expression": "enlightened", "intensity": 0.5},
        "curious": {"pose": "head_tilt", "expression": "interested", "intensity": 0.6},
        "attentive": {"pose": "leaning_in", "expression": "focused", "intensity": 0.7},
        "open": {"pose": "arms_open", "expression": "welcoming", "intensity": 0.5},
        "concerned": {"pose": "leaning_forward", "expression": "worried", "intensity": 0.7},
        "excited": {"pose": "celebrating", "expression": "joyful", "intensity": 0.9},
        "proud": {"pose": "standing_tall", "expression": "satisfied", "intensity": 0.8},
        "impressed": {"pose": "clapping", "expression": "amazed", "intensity": 0.8},
        "hyped": {"pose": "jumping", "expression": "ecstatic", "intensity": 1.0},
        "friendly": {"pose": "waving", "expression": "happy", "intensity": 0.6},
        "playful": {"pose": "bouncing", "expression": "mischievous", "intensity": 0.7},
        "observant": {"pose": "watching", "expression": "attentive", "intensity": 0.5},
        "admiring": {"pose": "nodding", "expression": "impressed", "intensity": 0.6},
        "neutral": {"pose": "standing", "expression": "neutral", "intensity": 0.3},
    }
    
    @classmethod
    def get_animation(cls, emotion: str) -> Dict[str, Any]:
        """Get avatar animation parameters for an emotion."""
        return cls.EMOTION_ANIMATIONS.get(
            emotion, 
            cls.EMOTION_ANIMATIONS["neutral"]
        )
