"""
Cognitive Mirror - The Metacognition Engine

Cognitive Mirror = Explanation Engine + Pattern Matcher

Answers two questions every time a problem is assigned or failed:
1. Why this problem, for you, now?
2. What kind of thinker you behaved like when you failed?

This transforms practice into metacognition, not grinding.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

from .failure_archetypes import (
    FailureArchetypeDetector,
    FailureArchetype,
    ArchetypeEvidence,
    ProblemAttempt,
    ARCHETYPE_SIGNATURES
)
from .problem_intent import (
    ProblemIntentEngine,
    ProblemMetadata,
    UserSkillProfile,
    ReasonVector
)


class ReflectionType(Enum):
    """Types of metacognitive insights."""
    PROBLEM_ASSIGNMENT = "problem_assignment"  # Why this problem was chosen
    FAILURE_ANALYSIS = "failure_analysis"      # What went wrong and why
    PATTERN_RECOGNITION = "pattern_recognition"  # Recurring behavioral pattern
    BREAKTHROUGH_MOMENT = "breakthrough"       # Successful pattern breaking
    TRAJECTORY_UPDATE = "trajectory_update"    # Progress milestone


@dataclass
class CognitiveReflection:
    """
    A metacognitive insight delivered to the user.
    This is the "mirror" - showing them their own thinking patterns.
    """
    reflection_type: ReflectionType
    timestamp: datetime
    
    # The insight itself
    title: str
    message: str
    
    # Context
    problem_id: Optional[int] = None
    detected_archetype: Optional[FailureArchetype] = None
    user_rating: Optional[int] = None
    
    # Supporting data
    evidence: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 1.0  # 0-1, how certain we are
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflection_type": self.reflection_type.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "problem_id": self.problem_id,
            "detected_archetype": self.detected_archetype.value if self.detected_archetype else None,
            "user_rating": self.user_rating,
            "evidence": self.evidence,
            "recommended_actions": self.recommended_actions,
            "confidence": round(self.confidence, 3)
        }


@dataclass
class MirrorSession:
    """
    A session tracking metacognitive insights over time.
    """
    user_id: str
    session_id: str
    started_at: datetime
    
    # Reflections generated
    reflections: List[CognitiveReflection] = field(default_factory=list)
    
    # User progression
    initial_rating: Optional[int] = None
    current_rating: Optional[int] = None
    archetype_evolution: List[FailureArchetype] = field(default_factory=list)
    
    def add_reflection(self, reflection: CognitiveReflection):
        """Add a new reflection to the session."""
        self.reflections.append(reflection)
    
    def get_recent_reflections(self, count: int = 5) -> List[CognitiveReflection]:
        """Get most recent reflections."""
        return self.reflections[-count:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "reflections": [r.to_dict() for r in self.reflections],
            "initial_rating": self.initial_rating,
            "current_rating": self.current_rating,
            "archetype_evolution": [a.value for a in self.archetype_evolution]
        }


class CognitiveMirror:
    """
    The complete metacognition system.
    
    Combines:
    - Failure Archetype Detection (Pattern Matcher)
    - Problem Intent Engine (Explanation Engine)
    - Reflection Generation (Mirror)
    
    Usage:
        mirror = CognitiveMirror(problem_database)
        
        # When assigning a problem
        problem, reflection = mirror.assign_problem(user_profile)
        
        # When user fails/completes a problem
        reflection = mirror.analyze_attempt(attempt)
    """
    
    def __init__(self,
                 problem_database: List[ProblemMetadata],
                 use_gemini: bool = False,
                 gemini_api_key: Optional[str] = None):
        """
        Args:
            problem_database: List of problems with metadata
            use_gemini: Use Gemini for enhanced explanations
            gemini_api_key: Gemini API key
        """
        # Core engines
        self.intent_engine = ProblemIntentEngine(
            problem_database=problem_database,
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key
        )
        
        # Per-user archetype detectors
        self.archetype_detectors: Dict[str, FailureArchetypeDetector] = {}
        
        # Per-user sessions
        self.sessions: Dict[str, MirrorSession] = {}
        
        # Configuration
        self.use_gemini = use_gemini
        self.gemini_api_key = gemini_api_key
        
    def start_session(self, user_id: str, session_id: str, 
                     initial_rating: Optional[int] = None) -> MirrorSession:
        """Start a new metacognitive session for a user."""
        session = MirrorSession(
            user_id=user_id,
            session_id=session_id,
            started_at=datetime.now(),
            initial_rating=initial_rating,
            current_rating=initial_rating
        )
        self.sessions[user_id] = session
        
        # Initialize archetype detector
        if user_id not in self.archetype_detectors:
            self.archetype_detectors[user_id] = FailureArchetypeDetector()
        
        return session
    
    def assign_problem(self, 
                      user_profile: UserSkillProfile,
                      strategic_goal: str = "optimal_growth") -> Tuple[ProblemMetadata, CognitiveReflection]:
        """
        Assign a problem with full metacognitive explanation.
        
        This is the "Why this problem, for you, now?" moment.
        
        Args:
            user_profile: User's skill profile
            strategic_goal: What we're trying to achieve
            
        Returns:
            (problem, reflection explaining the choice)
        """
        # Get current archetype if available
        detector = self.archetype_detectors.get(user_profile.user_id)
        current_archetype = None
        archetype_name = None
        
        if detector:
            archetype_evidence = detector.detect_archetype()
            if archetype_evidence:
                current_archetype = archetype_evidence.archetype.value
                archetype_name = archetype_evidence.archetype
        
        # Select problem with intent
        problem, reason = self.intent_engine.select_problem(
            user_profile=user_profile,
            current_archetype=current_archetype,
            strategic_goal=strategic_goal
        )
        
        # Generate explanation
        explanation = self.intent_engine.generate_explanation(
            problem=problem,
            reason=reason,
            use_gemini=self.use_gemini
        )
        
        # Build reflection
        reflection = CognitiveReflection(
            reflection_type=ReflectionType.PROBLEM_ASSIGNMENT,
            timestamp=datetime.now(),
            title=f"Problem {problem.problem_id}: {problem.title}",
            message=explanation,
            problem_id=problem.problem_id,
            detected_archetype=archetype_name,
            user_rating=user_profile.current_rating,
            evidence=[
                f"Target skill: {reason.targeted_skill or 'General practice'}",
                f"Difficulty: {problem.difficulty} ({reason.difficulty_justification})",
                f"Strategic goal: {reason.strategic_goal}"
            ],
            confidence=0.9
        )
        
        # Record reflection
        if user_profile.user_id in self.sessions:
            self.sessions[user_profile.user_id].add_reflection(reflection)
        
        return problem, reflection
    
    def analyze_attempt(self,
                       user_id: str,
                       attempt: ProblemAttempt,
                       user_profile: Optional[UserSkillProfile] = None) -> Optional[CognitiveReflection]:
        """
        Analyze a problem attempt and generate metacognitive insight.
        
        This is the "What kind of thinker you behaved like" moment.
        
        Args:
            user_id: User identifier
            attempt: The problem attempt to analyze
            user_profile: Optional user profile for context
            
        Returns:
            Reflection on the attempt, or None if not enough data
        """
        # Get or create detector
        if user_id not in self.archetype_detectors:
            self.archetype_detectors[user_id] = FailureArchetypeDetector()
        
        detector = self.archetype_detectors[user_id]
        
        # Record the attempt
        detector.record_attempt(attempt)
        
        # Detect archetype
        archetype_evidence = detector.detect_archetype()
        
        if not archetype_evidence:
            return None  # Not enough data yet
        
        # Get archetype signature
        archetype = archetype_evidence.archetype
        signature = ARCHETYPE_SIGNATURES.get(archetype)
        
        if not signature:
            return None
        
        # Build reflection based on success/failure
        if attempt.final_verdict == "AC":
            reflection = self._generate_success_reflection(
                attempt=attempt,
                archetype=archetype,
                signature=signature,
                evidence=archetype_evidence,
                user_profile=user_profile
            )
        else:
            reflection = self._generate_failure_reflection(
                attempt=attempt,
                archetype=archetype,
                signature=signature,
                evidence=archetype_evidence,
                user_profile=user_profile
            )
        
        # Record in session
        if user_id in self.sessions:
            self.sessions[user_id].add_reflection(reflection)
            # Track archetype evolution
            if archetype not in self.sessions[user_id].archetype_evolution[-3:]:
                self.sessions[user_id].archetype_evolution.append(archetype)
        
        return reflection
    
    def _generate_failure_reflection(self,
                                    attempt: ProblemAttempt,
                                    archetype: FailureArchetype,
                                    signature: Any,
                                    evidence: ArchetypeEvidence,
                                    user_profile: Optional[UserSkillProfile]) -> CognitiveReflection:
        """Generate reflection for a failed attempt."""
        
        # Build the mirror message
        title = f"🔍 Pattern Detected: {signature.name}"
        
        message_parts = []
        message_parts.append(f"**What I observed:**")
        message_parts.append(f"You just behaved like **{signature.name}**.")
        message_parts.append(f"\n_{signature.description}_\n")
        
        # Show evidence
        if evidence.supporting_behaviors:
            message_parts.append(f"**Evidence:**")
            for behavior in evidence.supporting_behaviors[:3]:
                message_parts.append(f"  • {behavior}")
        
        # Explain what this means
        message_parts.append(f"\n**Why this matters:**")
        message_parts.append(
            f"This pattern explains why you got {attempt.final_verdict} on this problem. "
        )
        
        # Provide intervention
        message_parts.append(f"\n**What to do differently:**")
        message_parts.append(f"{signature.targeted_intervention}")
        
        message = "\n".join(message_parts)
        
        # Recommended actions
        actions = [
            f"Try problems tagged: {', '.join(signature.recommended_problem_types[:3])}",
            "Practice the intervention strategy on next attempt",
            "Track if this pattern repeats"
        ]
        
        reflection = CognitiveReflection(
            reflection_type=ReflectionType.FAILURE_ANALYSIS,
            timestamp=datetime.now(),
            title=title,
            message=message,
            problem_id=attempt.problem_id,
            detected_archetype=archetype,
            user_rating=user_profile.current_rating if user_profile else None,
            evidence=evidence.supporting_behaviors,
            recommended_actions=actions,
            confidence=evidence.confidence
        )
        
        return reflection
    
    def _generate_success_reflection(self,
                                    attempt: ProblemAttempt,
                                    archetype: FailureArchetype,
                                    signature: Any,
                                    evidence: ArchetypeEvidence,
                                    user_profile: Optional[UserSkillProfile]) -> CognitiveReflection:
        """Generate reflection for a successful attempt."""
        
        title = f"✨ Growth Moment"
        
        message_parts = []
        message_parts.append(f"**Breakthrough detected!**")
        message_parts.append(
            f"You solved this problem, but I noticed you're still showing signs of "
            f"**{signature.name}** behavior."
        )
        
        message_parts.append(f"\n**Your pattern:**")
        message_parts.append(f"_{signature.description}_")
        
        message_parts.append(f"\n**Next level:**")
        message_parts.append(
            f"You're getting results, but breaking this pattern will unlock the next tier. "
            f"{signature.targeted_intervention}"
        )
        
        message = "\n".join(message_parts)
        
        actions = [
            "Continue with similar problems to reinforce",
            f"Gradually try {', '.join(signature.recommended_problem_types[:2])}",
            "Notice if you apply the same pattern on harder problems"
        ]
        
        reflection = CognitiveReflection(
            reflection_type=ReflectionType.BREAKTHROUGH_MOMENT,
            timestamp=datetime.now(),
            title=title,
            message=message,
            problem_id=attempt.problem_id,
            detected_archetype=archetype,
            user_rating=user_profile.current_rating if user_profile else None,
            evidence=evidence.supporting_behaviors,
            recommended_actions=actions,
            confidence=evidence.confidence * 0.8  # Slightly less confident for success
        )
        
        return reflection
    
    def get_archetype_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of user's archetype patterns."""
        if user_id not in self.archetype_detectors:
            return None
        
        detector = self.archetype_detectors[user_id]
        current_archetype = detector.get_dominant_archetype()
        history = detector.get_archetype_history()
        
        if not current_archetype:
            return None
        
        signature = ARCHETYPE_SIGNATURES.get(current_archetype)
        
        return {
            "dominant_archetype": current_archetype.value,
            "archetype_name": signature.name if signature else "Unknown",
            "description": signature.description if signature else "",
            "detection_count": len([h for h in history if h.archetype == current_archetype]),
            "total_detections": len(history),
            "intervention": signature.targeted_intervention if signature else "",
            "recommended_practice": signature.recommended_problem_types if signature else []
        }
    
    def get_session(self, user_id: str) -> Optional[MirrorSession]:
        """Get user's current session."""
        return self.sessions.get(user_id)
    
    def get_reflections(self, user_id: str, count: int = 10) -> List[CognitiveReflection]:
        """Get recent reflections for a user."""
        session = self.sessions.get(user_id)
        if not session:
            return []
        return session.get_recent_reflections(count)
    
    def update_user_rating(self, user_id: str, new_rating: int):
        """Update user's rating and check for trajectory milestones."""
        session = self.sessions.get(user_id)
        if not session:
            return
        
        old_rating = session.current_rating or session.initial_rating
        session.current_rating = new_rating
        
        # Check for significant progress (200+ rating gain)
        if old_rating and new_rating - old_rating >= 200:
            reflection = CognitiveReflection(
                reflection_type=ReflectionType.TRAJECTORY_UPDATE,
                timestamp=datetime.now(),
                title="🚀 Major Progress Milestone",
                message=(
                    f"You've gained +{new_rating - old_rating} rating points!\n\n"
                    f"This represents real growth in your problem-solving abilities. "
                    f"Your archetype patterns are evolving."
                ),
                user_rating=new_rating,
                confidence=1.0
            )
            session.add_reflection(reflection)
