"""
Failure Archetype Detection Module

Identifies recurring behavioral patterns in how users fail problems.
Maps user behavior to cognitive failure modes for targeted intervention.

The 7 Core Failure Archetypes:
1. The Brute Forcer - Over-enumerates, ignores constraints
2. The Pattern Chaser - Applies known template blindly
3. The Hesitator - Knows idea but doesn't commit
4. The Overfitter - Solves sample, fails edge cases
5. The Avoider - Skips certain tags subconsciously
6. The Speed Demon - Rushes, causes WA
7. The Perfectionist - Times out thinking
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from collections import Counter, deque


class FailureArchetype(Enum):
    """Core failure patterns that reveal thinking style."""
    BRUTE_FORCER = "brute_forcer"           # Over-enumerates, ignores constraints
    PATTERN_CHASER = "pattern_chaser"       # Applies known template blindly
    HESITATOR = "hesitator"                 # Knows idea but doesn't commit
    OVERFITTER = "overfitter"               # Solves sample, fails edge cases
    AVOIDER = "avoider"                     # Skips certain tags subconsciously
    SPEED_DEMON = "speed_demon"             # Rushes, causes WA
    PERFECTIONIST = "perfectionist"         # Times out thinking
    UNKNOWN = "unknown"                     # Not enough data


@dataclass
class ArchetypeSignature:
    """
    Behavioral fingerprint for an archetype.
    Defines the patterns that indicate this failure mode.
    """
    archetype: FailureArchetype
    name: str
    description: str
    
    # Behavioral indicators (what to look for)
    time_pattern: str                    # "too_fast", "too_slow", "inconsistent"
    submission_pattern: str              # "many_attempts", "single_fail", "no_submit"
    error_pattern: List[str]             # ["WA", "TLE", "RTE", etc.]
    tag_avoidance: List[str]             # Tags they avoid
    tag_overuse: List[str]               # Tags they overfit on
    
    # Coaching strategy
    targeted_intervention: str
    recommended_problem_types: List[str]
    
    # Thresholds for detection (with defaults)
    min_problems_for_detection: int = 5
    confidence_threshold: float = 0.6


# Define the 7 core archetypes with their signatures
ARCHETYPE_SIGNATURES: Dict[FailureArchetype, ArchetypeSignature] = {
    FailureArchetype.BRUTE_FORCER: ArchetypeSignature(
        archetype=FailureArchetype.BRUTE_FORCER,
        name="The Brute Forcer",
        description="Over-enumerates possibilities, ignores problem constraints. Likely to TLE.",
        time_pattern="too_slow",
        submission_pattern="many_attempts",
        error_pattern=["TLE", "MLE"],
        tag_avoidance=["optimization", "math"],
        tag_overuse=["implementation", "brute force"],
        targeted_intervention="Force constraint analysis before coding. Teach complexity bounds.",
        recommended_problem_types=["optimization", "greedy", "math_insight"]
    ),
    
    FailureArchetype.PATTERN_CHASER: ArchetypeSignature(
        archetype=FailureArchetype.PATTERN_CHASER,
        name="The Pattern Chaser",
        description="Applies memorized templates blindly without understanding problem structure.",
        time_pattern="too_fast",
        submission_pattern="single_fail",
        error_pattern=["WA"],
        tag_avoidance=["ad-hoc", "constructive"],
        tag_overuse=["dp", "graph", "binary search"],
        targeted_intervention="Force problem decomposition. Break template reliance.",
        recommended_problem_types=["ad-hoc", "observation", "constructive"]
    ),
    
    FailureArchetype.HESITATOR: ArchetypeSignature(
        archetype=FailureArchetype.HESITATOR,
        name="The Hesitator",
        description="Has the right intuition but lacks confidence to commit. Overthinks.",
        time_pattern="too_slow",
        submission_pattern="no_submit",
        error_pattern=[],  # Doesn't submit enough to fail
        tag_avoidance=[],
        tag_overuse=[],
        targeted_intervention="Build confidence through guided implementation. Time-box thinking.",
        recommended_problem_types=["implementation_heavy", "simulation", "straightforward_dp"]
    ),
    
    FailureArchetype.OVERFITTER: ArchetypeSignature(
        archetype=FailureArchetype.OVERFITTER,
        name="The Overfitter",
        description="Solves sample cases perfectly but fails edge cases. Lacks systematic testing.",
        time_pattern="inconsistent",
        submission_pattern="many_attempts",
        error_pattern=["WA"],
        tag_avoidance=[],
        tag_overuse=["implementation"],
        targeted_intervention="Teach edge case generation. Systematic input analysis.",
        recommended_problem_types=["edge_case_heavy", "corner_cases", "boundary_conditions"]
    ),
    
    FailureArchetype.AVOIDER: ArchetypeSignature(
        archetype=FailureArchetype.AVOIDER,
        name="The Avoider",
        description="Subconsciously skips certain problem types or tags. Comfort zone trapped.",
        time_pattern="inconsistent",
        submission_pattern="no_submit",
        error_pattern=[],
        tag_avoidance=["varies"],  # Detected dynamically
        tag_overuse=["varies"],
        targeted_intervention="Direct confrontation with avoided topics. Build missing foundations.",
        recommended_problem_types=["avoided_tags"]  # Personalized
    ),
    
    FailureArchetype.SPEED_DEMON: ArchetypeSignature(
        archetype=FailureArchetype.SPEED_DEMON,
        name="The Speed Demon",
        description="Rushes to submit, makes careless mistakes. Values speed over accuracy.",
        time_pattern="too_fast",
        submission_pattern="many_attempts",
        error_pattern=["WA", "RTE"],
        tag_avoidance=[],
        tag_overuse=["greedy", "implementation"],
        targeted_intervention="Force slow down protocol. Require mental verification before submit.",
        recommended_problem_types=["detail_oriented", "careful_implementation"]
    ),
    
    FailureArchetype.PERFECTIONIST: ArchetypeSignature(
        archetype=FailureArchetype.PERFECTIONIST,
        name="The Perfectionist",
        description="Overthinks every detail, times out before submitting. Analysis paralysis.",
        time_pattern="too_slow",
        submission_pattern="no_submit",
        error_pattern=["TLE"],
        tag_avoidance=[],
        tag_overuse=["dp", "graphs"],
        targeted_intervention="Implement 'good enough' mindset. Time-boxed problem solving.",
        recommended_problem_types=["time_pressure", "quick_decisions", "approximation"]
    ),
}


@dataclass
class ArchetypeEvidence:
    """Evidence for a specific archetype from user behavior."""
    archetype: FailureArchetype
    confidence: float  # 0.0 - 1.0
    supporting_behaviors: List[str]
    problem_ids: List[int]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProblemAttempt:
    """Record of a single problem attempt."""
    problem_id: int
    timestamp: datetime
    time_spent_seconds: int
    submission_count: int
    final_verdict: str  # "AC", "WA", "TLE", etc.
    tags: List[str]
    difficulty: int
    
    # Behavioral markers
    opened_but_not_submitted: bool = False
    rapid_submissions: bool = False  # < 5 min between submissions
    long_idle: bool = False  # > 30 min thinking


class FailureArchetypeDetector:
    """
    Analyzes problem-solving behavior to identify failure archetypes.
    
    The detector looks at patterns across multiple problems:
    - Time spent vs problem difficulty
    - Submission patterns
    - Error types
    - Tag avoidance/preference
    - Consistency of behavior
    """
    
    def __init__(self, lookback_problems: int = 20):
        """
        Args:
            lookback_problems: How many recent problems to analyze
        """
        self.lookback_problems = lookback_problems
        self.attempt_history: deque = deque(maxlen=lookback_problems)
        self.detected_archetypes: List[ArchetypeEvidence] = []
        
        # Statistics for detection
        self.tag_stats = Counter()  # Track tag frequencies
        self.error_stats = Counter()  # Track error types
        self.time_patterns: List[float] = []
        
    def record_attempt(self, attempt: ProblemAttempt):
        """Record a problem attempt for analysis."""
        self.attempt_history.append(attempt)
        
        # Update statistics
        for tag in attempt.tags:
            self.tag_stats[tag] += 1
        
        if attempt.final_verdict != "AC":
            self.error_stats[attempt.final_verdict] += 1
        
        # Normalize time by difficulty
        expected_time = self._expected_time_for_difficulty(attempt.difficulty)
        time_ratio = attempt.time_spent_seconds / expected_time if expected_time > 0 else 1.0
        self.time_patterns.append(time_ratio)
        
    def detect_archetype(self) -> Optional[ArchetypeEvidence]:
        """
        Analyze recent attempts and identify the dominant failure archetype.
        
        Returns:
            ArchetypeEvidence with highest confidence, or None if insufficient data
        """
        if len(self.attempt_history) < 5:
            return None
        
        # Score each archetype
        archetype_scores: Dict[FailureArchetype, float] = {}
        archetype_evidence: Dict[FailureArchetype, List[str]] = {}
        
        for archetype, signature in ARCHETYPE_SIGNATURES.items():
            if archetype == FailureArchetype.UNKNOWN:
                continue
                
            score, evidence = self._score_archetype(signature)
            archetype_scores[archetype] = score
            archetype_evidence[archetype] = evidence
        
        # Find best match
        if not archetype_scores:
            return None
            
        best_archetype = max(archetype_scores.items(), key=lambda x: x[1])
        archetype, confidence = best_archetype
        
        # Only report if confidence exceeds threshold
        signature = ARCHETYPE_SIGNATURES[archetype]
        if confidence < signature.confidence_threshold:
            return None
        
        # Get problem IDs for this archetype
        problem_ids = [attempt.problem_id for attempt in self.attempt_history]
        
        evidence = ArchetypeEvidence(
            archetype=archetype,
            confidence=confidence,
            supporting_behaviors=archetype_evidence[archetype],
            problem_ids=problem_ids[-10:]  # Last 10 problems
        )
        
        self.detected_archetypes.append(evidence)
        return evidence
    
    def _score_archetype(self, signature: ArchetypeSignature) -> tuple[float, List[str]]:
        """
        Score how well recent behavior matches an archetype signature.
        
        Returns:
            (confidence_score, list_of_evidence_strings)
        """
        score = 0.0
        evidence = []
        max_score = 0.0
        
        # 1. Time pattern matching (weight: 0.25)
        max_score += 0.25
        time_match, time_evidence = self._match_time_pattern(signature.time_pattern)
        score += time_match * 0.25
        if time_evidence:
            evidence.append(time_evidence)
        
        # 2. Submission pattern matching (weight: 0.25)
        max_score += 0.25
        submission_match, sub_evidence = self._match_submission_pattern(signature.submission_pattern)
        score += submission_match * 0.25
        if sub_evidence:
            evidence.append(sub_evidence)
        
        # 3. Error pattern matching (weight: 0.25)
        max_score += 0.25
        error_match, error_evidence = self._match_error_pattern(signature.error_pattern)
        score += error_match * 0.25
        if error_evidence:
            evidence.append(error_evidence)
        
        # 4. Tag pattern matching (weight: 0.25)
        max_score += 0.25
        tag_match, tag_evidence = self._match_tag_patterns(
            signature.tag_avoidance,
            signature.tag_overuse
        )
        score += tag_match * 0.25
        if tag_evidence:
            evidence.extend(tag_evidence)
        
        # Normalize to 0-1 range
        confidence = score / max_score if max_score > 0 else 0.0
        
        return confidence, evidence
    
    def _match_time_pattern(self, expected_pattern: str) -> tuple[float, Optional[str]]:
        """Check if user's time pattern matches expected."""
        if not self.time_patterns:
            return 0.0, None
        
        avg_ratio = sum(self.time_patterns) / len(self.time_patterns)
        
        if expected_pattern == "too_fast" and avg_ratio < 0.5:
            return 1.0, f"Solves {avg_ratio:.1%} faster than expected"
        elif expected_pattern == "too_slow" and avg_ratio > 1.5:
            return 1.0, f"Takes {avg_ratio:.1%} longer than expected"
        elif expected_pattern == "inconsistent":
            variance = sum((r - avg_ratio) ** 2 for r in self.time_patterns) / len(self.time_patterns)
            if variance > 0.5:
                return 1.0, "Highly inconsistent timing patterns"
        
        return 0.0, None
    
    def _match_submission_pattern(self, expected_pattern: str) -> tuple[float, Optional[str]]:
        """Check if submission behavior matches expected."""
        if not self.attempt_history:
            return 0.0, None
        
        many_attempts = sum(1 for a in self.attempt_history if a.submission_count > 3)
        no_submit = sum(1 for a in self.attempt_history if a.opened_but_not_submitted)
        single_fail = sum(1 for a in self.attempt_history 
                         if a.submission_count == 1 and a.final_verdict != "AC")
        
        total = len(self.attempt_history)
        
        if expected_pattern == "many_attempts" and many_attempts / total > 0.5:
            return 1.0, f"{many_attempts}/{total} problems had 3+ submissions"
        elif expected_pattern == "no_submit" and no_submit / total > 0.4:
            return 1.0, f"{no_submit}/{total} problems opened but not submitted"
        elif expected_pattern == "single_fail" and single_fail / total > 0.4:
            return 1.0, f"{single_fail}/{total} problems failed on first try"
        
        return 0.0, None
    
    def _match_error_pattern(self, expected_errors: List[str]) -> tuple[float, Optional[str]]:
        """Check if error types match expected."""
        if not expected_errors or not self.error_stats:
            return 0.0, None
        
        total_errors = sum(self.error_stats.values())
        matching_errors = sum(self.error_stats[err] for err in expected_errors 
                             if err in self.error_stats)
        
        if total_errors == 0:
            return 0.0, None
        
        match_ratio = matching_errors / total_errors
        
        if match_ratio > 0.6:
            top_errors = ", ".join(expected_errors[:2])
            return match_ratio, f"Primarily fails with {top_errors}"
        
        return 0.0, None
    
    def _match_tag_patterns(self, avoid_tags: List[str], 
                           overuse_tags: List[str]) -> tuple[float, List[str]]:
        """Check if tag usage matches expected patterns."""
        if not self.tag_stats:
            return 0.0, []
        
        evidence = []
        score = 0.0
        total_checks = 0
        
        # Check avoidance (low frequency tags)
        if avoid_tags and avoid_tags != ["varies"]:
            total_checks += 1
            avg_frequency = sum(self.tag_stats.values()) / len(self.tag_stats) if self.tag_stats else 1
            avoided_count = sum(1 for tag in avoid_tags 
                               if self.tag_stats.get(tag, 0) < avg_frequency * 0.3)
            
            if avoided_count > len(avoid_tags) * 0.5:
                score += 1.0
                evidence.append(f"Avoids {', '.join(avoid_tags[:2])}")
        
        # Check overuse (high frequency tags)
        if overuse_tags and overuse_tags != ["varies"]:
            total_checks += 1
            total_problems = sum(self.tag_stats.values())
            overused_count = sum(1 for tag in overuse_tags 
                                if self.tag_stats.get(tag, 0) / total_problems > 0.4)
            
            if overused_count > len(overuse_tags) * 0.5:
                score += 1.0
                evidence.append(f"Overuses {', '.join(overuse_tags[:2])}")
        
        # Dynamic detection for "varies" patterns
        if "varies" in avoid_tags or "varies" in overuse_tags:
            total_checks += 1
            # Detect if user has strong bias toward/against any tags
            if self.tag_stats:
                total = sum(self.tag_stats.values())
                outliers = [tag for tag, count in self.tag_stats.items() 
                           if count / total > 0.5 or count / total < 0.1]
                if outliers:
                    score += 0.5
                    evidence.append(f"Strong preferences detected")
        
        final_score = score / total_checks if total_checks > 0 else 0.0
        return final_score, evidence
    
    def _expected_time_for_difficulty(self, difficulty: int) -> float:
        """
        Estimate expected solve time based on difficulty.
        
        Rough heuristic:
        - 800-1000: ~15 min
        - 1200-1400: ~30 min
        - 1600-1800: ~45 min
        - 2000+: ~60 min
        """
        if difficulty < 1000:
            return 900  # 15 min
        elif difficulty < 1400:
            return 1800  # 30 min
        elif difficulty < 1800:
            return 2700  # 45 min
        else:
            return 3600  # 60 min
    
    def get_archetype_history(self) -> List[ArchetypeEvidence]:
        """Get history of detected archetypes."""
        return self.detected_archetypes
    
    def get_dominant_archetype(self) -> Optional[FailureArchetype]:
        """Get the most frequently detected archetype."""
        if not self.detected_archetypes:
            return None
        
        archetype_counts = Counter(evidence.archetype for evidence in self.detected_archetypes)
        if archetype_counts:
            return archetype_counts.most_common(1)[0][0]
        
        return None
