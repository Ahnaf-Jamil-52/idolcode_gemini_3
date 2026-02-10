"""
Live Cognitive Mirror - Real-Time Metacognition

Extends the cognitive mirror to work in real-time during problem-solving.
Answers: "Why am I currently stuck?" instead of just "Why did I fail?"

Infers cognitive blocks from:
- Real-time typing behavior
- Detected failure archetype
- Burnout state
- Problem characteristics
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from .cognitive_mirror import CognitiveReflection, ReflectionType
from .failure_archetypes import FailureArchetype
from .realtime_detector import RealtimeSignal
from .states import CoachState


class CognitiveBlock(Enum):
    """Types of cognitive blocks during problem-solving."""
    PATTERN_MISMATCH = "pattern_mismatch"  # Problem doesn't fit known patterns
    CONSTRAINT_BLINDNESS = "constraint_blindness"  # Missing key constraint
    STATE_SPACE_EXPLOSION = "state_space_explosion"  # Too many cases to consider
    ALGORITHM_GAP = "algorithm_gap"  # Missing algorithmic knowledge
    IMPLEMENTATION_PARALYSIS = "implementation_paralysis"  # Know idea, can't code it
    OPTIMIZATION_TUNNEL = "optimization_tunnel"  # Stuck optimizing wrong approach
    GREEDY_ILLUSION = "greedy_illusion"  # Greedy won't work but seems like it should
    SUBPROBLEM_BLINDNESS = "subproblem_blindness"  # Not seeing recursive structure
    EDGE_CASE_OVERWHELM = "edge_case_overwhelm"  # Too many edge cases
    CONFIDENCE_CRISIS = "confidence_crisis"  # Doubting correct approach


@dataclass
class LiveCognitiveInsight:
    """A real-time insight about current cognitive state."""
    block_type: CognitiveBlock
    timestamp: datetime
    
    # The insight
    explanation: str  # Why they're stuck
    reframing: str    # How to see it differently
    
    # Supporting evidence
    evidence_signals: List[RealtimeSignal] = field(default_factory=list)
    evidence_archetype: Optional[FailureArchetype] = None
    
    # Confidence
    confidence: float = 0.7
    
    # Should we intervene?
    intervention_recommended: bool = True
    intervention_urgency: int = 5  # 1-10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_type": self.block_type.value,
            "timestamp": self.timestamp.isoformat(),
            "explanation": self.explanation,
            "reframing": self.reframing,
            "evidence_signals": [s.value for s in self.evidence_signals],
            "evidence_archetype": self.evidence_archetype.value if self.evidence_archetype else None,
            "confidence": round(self.confidence, 3),
            "intervention_recommended": self.intervention_recommended,
            "intervention_urgency": self.intervention_urgency
        }


class LiveCognitiveMirror:
    """
    Real-time cognitive mirror that infers why user is stuck.
    
    This is the "why" layer - explaining what's happening cognitively.
    """
    
    def __init__(self):
        self.insights: List[LiveCognitiveInsight] = []
        self.current_block: Optional[CognitiveBlock] = None
    
    def infer_cognitive_state(
        self,
        active_signals: List[RealtimeSignal],
        detected_archetype: Optional[FailureArchetype],
        problem_tags: List[str],
        time_on_problem_minutes: float,
        burnout_state: CoachState
    ) -> Optional[LiveCognitiveInsight]:
        """
        Infer what cognitive block the user is experiencing.
        
        This is heuristic-based inference, not mind reading.
        """
        # If burned out, that's the primary block
        if burnout_state in [CoachState.WARNING, CoachState.PROTECTIVE]:
            return self._infer_burnout_block(burnout_state, time_on_problem_minutes)
        
        # Check for specific signal combinations
        insight = None
        
        # Pattern: Typing slow + rewriting + early bruteforce = constraint blindness
        if (RealtimeSignal.TYPING_SPEED_DROP in active_signals and
            RealtimeSignal.REWRITE_SAME_BLOCK in active_signals and
            RealtimeSignal.EARLY_BRUTEFORCE_PATTERN in active_signals):
            insight = self._infer_constraint_blindness(active_signals, problem_tags)
        
        # Pattern: Algorithm delay + DS avoidance = algorithm gap
        elif (RealtimeSignal.ALGORITHM_DELAY in active_signals and
              RealtimeSignal.NO_DS_USAGE in active_signals):
            insight = self._infer_algorithm_gap(active_signals, problem_tags)
        
        # Pattern: Typing spike + early bruteforce = greedy illusion
        elif (RealtimeSignal.TYPING_SPEED_SPIKE in active_signals and
              RealtimeSignal.EARLY_BRUTEFORCE_PATTERN in active_signals):
            insight = self._infer_greedy_illusion(active_signals)
        
        # Pattern: Code explosion + rewriting = state space explosion
        elif (RealtimeSignal.CODE_LENGTH_EXPLOSION in active_signals and
              RealtimeSignal.REWRITE_SAME_BLOCK in active_signals):
            insight = self._infer_state_space_explosion(active_signals)
        
        # Pattern: Self doubt comments = confidence crisis
        elif RealtimeSignal.COMMENT_SELF_DOUBT in active_signals:
            insight = self._infer_confidence_crisis(active_signals)
        
        # Pattern: Long idle + low typing = implementation paralysis
        elif (RealtimeSignal.LONG_IDLE in active_signals and
              RealtimeSignal.TYPING_SPEED_DROP in active_signals and
              time_on_problem_minutes > 5):
            insight = self._infer_implementation_paralysis(active_signals)
        
        # Archetype-based inference
        elif detected_archetype:
            insight = self._infer_from_archetype(
                detected_archetype, 
                active_signals, 
                problem_tags
            )
        
        if insight:
            self.insights.append(insight)
            self.current_block = insight.block_type
        
        return insight
    
    def _infer_constraint_blindness(
        self,
        signals: List[RealtimeSignal],
        problem_tags: List[str]
    ) -> LiveCognitiveInsight:
        """User is missing a key constraint that makes problem simpler."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.CONSTRAINT_BLINDNESS,
            timestamp=datetime.now(),
            explanation="You're not using a critical constraint. The problem statement has a property that eliminates most cases.",
            reframing="Re-read the constraints. What property stays true throughout? What can't happen?",
            evidence_signals=signals,
            confidence=0.75,
            intervention_recommended=True,
            intervention_urgency=7
        )
    
    def _infer_algorithm_gap(
        self,
        signals: List[RealtimeSignal],
        problem_tags: List[str]
    ) -> LiveCognitiveInsight:
        """User lacks the algorithmic tool needed."""
        algo = "an algorithm" if not problem_tags else problem_tags[0]
        
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.ALGORITHM_GAP,
            timestamp=datetime.now(),
            explanation=f"This problem needs {algo}. You're trying to build from scratch what already exists.",
            reframing=f"What's the standard tool for this shape? {algo.upper()} problems have a pattern.",
            evidence_signals=signals,
            confidence=0.8,
            intervention_recommended=True,
            intervention_urgency=8
        )
    
    def _infer_greedy_illusion(
        self,
        signals: List[RealtimeSignal]
    ) -> LiveCognitiveInsight:
        """User thinks greedy works but it doesn't."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.GREEDY_ILLUSION,
            timestamp=datetime.now(),
            explanation="You're defaulting to greedy because it feels right, but this has a counterexample.",
            reframing="Can you construct a case where the greedy choice fails? Why?",
            evidence_signals=signals,
            confidence=0.7,
            intervention_recommended=True,
            intervention_urgency=7
        )
    
    def _infer_state_space_explosion(
        self,
        signals: List[RealtimeSignal]
    ) -> LiveCognitiveInsight:
        """User is trying to handle too many cases."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.STATE_SPACE_EXPLOSION,
            timestamp=datetime.now(),
            explanation="You're tracking too many variables. The state space is simpler than you think.",
            reframing="What's the minimal information needed at each step? Can you reduce dimensions?",
            evidence_signals=signals,
            confidence=0.75,
            intervention_recommended=True,
            intervention_urgency=6
        )
    
    def _infer_confidence_crisis(
        self,
        signals: List[RealtimeSignal]
    ) -> LiveCognitiveInsight:
        """User is doubting themselves."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.CONFIDENCE_CRISIS,
            timestamp=datetime.now(),
            explanation="You're doubting a correct intuition. Trust the pattern you're seeing.",
            reframing="What evidence do you have that it's wrong? Often your first instinct is right.",
            evidence_signals=signals,
            confidence=0.65,
            intervention_recommended=True,
            intervention_urgency=5
        )
    
    def _infer_implementation_paralysis(
        self,
        signals: List[RealtimeSignal]
    ) -> LiveCognitiveInsight:
        """User knows the idea but can't code it."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.IMPLEMENTATION_PARALYSIS,
            timestamp=datetime.now(),
            explanation="You have the right idea but are stuck translating to code. This is about tooling, not thinking.",
            reframing="Write pseudocode first. Don't worry about syntax - what are the steps?",
            evidence_signals=signals,
            confidence=0.7,
            intervention_recommended=True,
            intervention_urgency=6
        )
    
    def _infer_burnout_block(
        self,
        state: CoachState,
        time_minutes: float
    ) -> LiveCognitiveInsight:
        """Burnout is affecting cognition."""
        return LiveCognitiveInsight(
            block_type=CognitiveBlock.CONFIDENCE_CRISIS,
            timestamp=datetime.now(),
            explanation=f"You've been at this for {int(time_minutes)} minutes while burned out. Your cognition is impaired.",
            reframing="This isn't about the problem anymore. You need rest to think clearly.",
            confidence=0.9,
            intervention_recommended=True,
            intervention_urgency=10
        )
    
    def _infer_from_archetype(
        self,
        archetype: FailureArchetype,
        signals: List[RealtimeSignal],
        problem_tags: List[str]
    ) -> Optional[LiveCognitiveInsight]:
        """Infer block from failure archetype pattern."""
        archetype_to_block = {
            FailureArchetype.BRUTE_FORCER: CognitiveBlock.CONSTRAINT_BLINDNESS,
            FailureArchetype.PATTERN_CHASER: CognitiveBlock.PATTERN_MISMATCH,
            FailureArchetype.HESITATOR: CognitiveBlock.IMPLEMENTATION_PARALYSIS,
            FailureArchetype.SPEED_DEMON: CognitiveBlock.GREEDY_ILLUSION,
            FailureArchetype.AVOIDER: CognitiveBlock.ALGORITHM_GAP,
        }
        
        block = archetype_to_block.get(archetype)
        if not block:
            return None
        
        explanations = {
            CognitiveBlock.CONSTRAINT_BLINDNESS: 
                "You're brute-forcing because you're not exploiting a constraint.",
            CognitiveBlock.PATTERN_MISMATCH:
                "You're applying a memorized pattern that doesn't fit this problem's structure.",
            CognitiveBlock.IMPLEMENTATION_PARALYSIS:
                "You know the approach but are hesitating on implementation.",
            CognitiveBlock.GREEDY_ILLUSION:
                "You're rushing to the first idea without checking if it's optimal.",
            CognitiveBlock.ALGORITHM_GAP:
                f"You're avoiding {problem_tags[0] if problem_tags else 'this algorithm'} but this problem needs it.",
        }
        
        reframings = {
            CognitiveBlock.CONSTRAINT_BLINDNESS:
                "What constraint makes most cases impossible?",
            CognitiveBlock.PATTERN_MISMATCH:
                "Stop pattern matching. What's unique about this problem?",
            CognitiveBlock.IMPLEMENTATION_PARALYSIS:
                "Write the simplest version first. Optimize later.",
            CognitiveBlock.GREEDY_ILLUSION:
                "Can you prove greedy is optimal? Find a counterexample?",
            CognitiveBlock.ALGORITHM_GAP:
                "What's the standard approach for this problem type?",
        }
        
        return LiveCognitiveInsight(
            block_type=block,
            timestamp=datetime.now(),
            explanation=explanations.get(block, "You're in a known failure pattern."),
            reframing=reframings.get(block, "Step back and rethink the approach."),
            evidence_signals=signals,
            evidence_archetype=archetype,
            confidence=0.8,
            intervention_recommended=True,
            intervention_urgency=7
        )
    
    def get_current_insight(self) -> Optional[LiveCognitiveInsight]:
        """Get the most recent insight."""
        return self.insights[-1] if self.insights else None
    
    def clear_insights(self):
        """Clear insight history (call when problem changes)."""
        self.insights.clear()
        self.current_block = None
