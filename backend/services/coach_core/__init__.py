"""
Coach Engine - Burnout Detection & Sentiment Analysis + Cognitive Mirror

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

__version__ = "0.2.0"
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
]
