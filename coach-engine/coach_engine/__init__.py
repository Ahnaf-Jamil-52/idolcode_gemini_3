"""
Coach Engine - Burnout Detection & Sentiment Analysis + Cognitive Mirror + Real-Time Coaching

A behavioral signal processing system for detecting user burnout,
analyzing sentiment, and providing adaptive coaching responses.

Layers:
1. Behavioral Signals (implicit, no NLP) - signals.py, scorer.py
2. Textual Sentiment (explicit, NLP) - sentiment.py
3. Cross-Reference Fusion (intelligence) - fusion.py
4. State Machine (progression) - states.py
5. Coach Responses (output) - responses.py

Cognitive Mirror System:
6. Failure Archetypes (pattern matcher) - failure_archetypes.py
7. Problem Intent Engine (why this problem) - problem_intent.py
8. Cognitive Mirror (metacognition) - cognitive_mirror.py

Real-Time Coaching System:
9. Real-Time Detector (live signals) - realtime_detector.py
10. Duck TTS (voice output) - duck_tts.py
11. Interventions (coaching decisions) - interventions.py
12. Live Cognitive Mirror (live metacognition) - live_cognitive_mirror.py
13. Real-Time Coach (orchestrator) - realtime_coach.py
"""

from .signals import (
    SignalCollector,
    BehavioralSignal,
    SignalType,
    UserSession,
    SIGNAL_WEIGHTS,
)

from .scorer import (
    BurnoutScorer,
    BurnoutScore,
    BurnoutLevel,
    SessionBurnoutTracker,
)

from .trends import (
    TrendDetector,
    TrendAnalysis,
    TrendDirection,
    MultiMetricTrendAnalyzer,
)

from .states import (
    CoachStateMachine,
    CoachState,
    StateTransition,
    StateContext,
)

from .sentiment import (
    HybridSentimentAnalyzer,
    KeywordSentimentAnalyzer,
    SentimentResult,
    SentimentHistory,
    EmotionalState,
    PatternCategory,
)

from .fusion import (
    FusionEngine,
    FusionResult,
    BehaviorTextAlignment,
    InterventionLevel,
    TemporalComparison,
)

from .responses import (
    ResponseSelector,
    CoachResponse,
    ResponseStrategy,
    EmotionToAvatarMapper,
)

from .gemini_analyzer import (
    GeminiCoachAnalyzer,
    ResponseCache,
    CacheEntry,
)

from .failure_archetypes import (
    FailureArchetypeDetector,
    FailureArchetype,
    ArchetypeEvidence,
    ProblemAttempt,
    ArchetypeSignature,
    ARCHETYPE_SIGNATURES,
)

from .problem_intent import (
    ProblemIntentEngine,
    ProblemMetadata,
    UserSkillProfile,
    ReasonVector,
    SkillCategory,
    CognitiveTrigger,
)

from .cognitive_mirror import (
    CognitiveMirror,
    CognitiveReflection,
    MirrorSession,
    ReflectionType,
)

from .realtime_detector import (
    RealtimeDetector,
    RealtimeSignal,
    RealtimeDetection,
    TypingEvent,
    CodeSnapshot,
)

from .duck_tts import (
    DuckVoice,
    VoiceMood,
    DuckPhrases,
    get_duck_voice,
    duck_speak,
)

from .interventions import (
    InterventionSelector,
    InterventionType,
    InterventionContext,
    Intervention,
    select_and_deliver,
)

from .live_cognitive_mirror import (
    LiveCognitiveMirror,
    LiveCognitiveInsight,
    CognitiveBlock,
)

from .realtime_coach import (
    RealtimeCoach,
    RealtimeCoachContext,
    CoachingUpdate,
    get_realtime_coach,
)

__version__ = "0.3.0"
__all__ = [
    # Signals
    "SignalCollector",
    "BehavioralSignal",
    "SignalType",
    "UserSession",
    "SIGNAL_WEIGHTS",
    # Scorer
    "BurnoutScorer",
    "BurnoutScore",
    "BurnoutLevel",
    "SessionBurnoutTracker",
    # Trends
    "TrendDetector",
    "TrendAnalysis",
    "TrendDirection",
    "MultiMetricTrendAnalyzer",
    # States
    "CoachStateMachine",
    "CoachState",
    "StateTransition",
    "StateContext",
    # Sentiment
    "HybridSentimentAnalyzer",
    "KeywordSentimentAnalyzer",
    "SentimentResult",
    "SentimentHistory",
    "EmotionalState",
    "PatternCategory",
    # Fusion
    "FusionEngine",
    "FusionResult",
    "BehaviorTextAlignment",
    "InterventionLevel",
    "TemporalComparison",
    # Responses
    "ResponseSelector",
    "CoachResponse",
    "ResponseStrategy",
    "EmotionToAvatarMapper",
    # Gemini AI
    "GeminiCoachAnalyzer",
    "ResponseCache",
    "CacheEntry",
    # Cognitive Mirror - Failure Archetypes
    "FailureArchetypeDetector",
    "FailureArchetype",
    "ArchetypeEvidence",
    "ProblemAttempt",
    "ArchetypeSignature",
    "ARCHETYPE_SIGNATURES",
    # Cognitive Mirror - Problem Intent
    "ProblemIntentEngine",
    "ProblemMetadata",
    "UserSkillProfile",
    "ReasonVector",
    "SkillCategory",
    "CognitiveTrigger",
    # Cognitive Mirror - Main System
    "CognitiveMirror",
    "CognitiveReflection",
    "MirrorSession",
    "ReflectionType",
    # Real-Time Coaching - Detector
    "RealtimeDetector",
    "RealtimeSignal",
    "RealtimeDetection",
    "TypingEvent",
    "CodeSnapshot",
    # Real-Time Coaching - TTS
    "DuckVoice",
    "VoiceMood",
    "DuckPhrases",
    "get_duck_voice",
    "duck_speak",
    # Real-Time Coaching - Interventions
    "InterventionSelector",
    "InterventionType",
    "InterventionContext",
    "Intervention",
    "select_and_deliver",
    # Real-Time Coaching - Live Cognitive Mirror
    "LiveCognitiveMirror",
    "LiveCognitiveInsight",
    "CognitiveBlock",
    # Real-Time Coaching - Coordinator
    "RealtimeCoach",
    "RealtimeCoachContext",
    "CoachingUpdate",
    "get_realtime_coach",
]
