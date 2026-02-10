"""
Test Suite for Cognitive Mirror System

Tests the core functionality:
- Failure archetype detection
- Problem intent engine
- Cognitive mirror reflections
"""

import pytest
from datetime import datetime, timedelta

from coach_engine.failure_archetypes import (
    FailureArchetypeDetector,
    ProblemAttempt,
    FailureArchetype,
    ARCHETYPE_SIGNATURES
)
from coach_engine.problem_intent import (
    ProblemIntentEngine,
    ProblemMetadata,
    UserSkillProfile,
    CognitiveTrigger,
    SkillCategory
)
from coach_engine.cognitive_mirror import (
    CognitiveMirror,
    ReflectionType
)


def create_test_problem(problem_id: int = 1000, difficulty: int = 1400) -> ProblemMetadata:
    """Create a test problem for testing."""
    return ProblemMetadata(
        problem_id=problem_id,
        title=f"Test Problem {problem_id}",
        difficulty=difficulty,
        tags=["dp", "greedy"],
        hidden_skills=["optimization"],
        cognitive_triggers=[CognitiveTrigger.FORCES_ABSTRACTION],
        common_wrong_paths=["brute force"],
        failure_archetypes_targeted=["brute_forcer"],
        historical_role="test_problem",
        typical_solve_time_minutes=30,
        required_skills=["basic_dp"],
        recommended_prerequisites=[],
        source="test"
    )


class TestFailureArchetypeDetector:
    """Test failure archetype detection."""
    
    def test_detector_initialization(self):
        """Test detector can be initialized."""
        detector = FailureArchetypeDetector()
        assert detector is not None
        assert len(detector.attempt_history) == 0
    
    def test_record_attempt(self):
        """Test recording problem attempts."""
        detector = FailureArchetypeDetector()
        
        attempt = ProblemAttempt(
            problem_id=1000,
            timestamp=datetime.now(),
            time_spent_seconds=1800,
            submission_count=3,
            final_verdict="TLE",
            tags=["dp"],
            difficulty=1400
        )
        
        detector.record_attempt(attempt)
        assert len(detector.attempt_history) == 1
    
    def test_brute_forcer_detection(self):
        """Test detection of Brute Forcer archetype."""
        detector = FailureArchetypeDetector()
        
        # Create 5 attempts showing brute forcer pattern
        for i in range(5):
            attempt = ProblemAttempt(
                problem_id=1000 + i,
                timestamp=datetime.now() - timedelta(hours=5-i),
                time_spent_seconds=3600,  # Too long
                submission_count=4,
                final_verdict="TLE",  # Time limit exceeded
                tags=["dp", "implementation"],
                difficulty=1400,
                long_idle=True
            )
            detector.record_attempt(attempt)
        
        evidence = detector.detect_archetype()
        
        assert evidence is not None
        assert evidence.archetype == FailureArchetype.BRUTE_FORCER
        assert evidence.confidence > 0.6
    
    def test_speed_demon_detection(self):
        """Test detection of Speed Demon archetype."""
        detector = FailureArchetypeDetector()
        
        # Create attempts showing speed demon pattern - rushes through problems
        verdicts = ["WA", "WA", "RTE", "WA", "RTE"]  # Mix of WA and RTE from rushing
        times = [250, 300, 200, 350, 280]  # Very fast (< 6 min for 15 min problems)
        submissions = [2, 3, 2, 3, 2]  # Fewer attempts (rushes to submit)
        
        for i in range(5):
            attempt = ProblemAttempt(
                problem_id=800 + i,
                timestamp=datetime.now() - timedelta(hours=5-i),
                time_spent_seconds=times[i],
                submission_count=submissions[i],
                final_verdict=verdicts[i],
                tags=["greedy", "implementation"],  # Prefers quick greedy solutions
                difficulty=1000,
                rapid_submissions=True
            )
            detector.record_attempt(attempt)
        
        evidence = detector.detect_archetype()
        
        assert evidence is not None
        assert evidence.archetype == FailureArchetype.SPEED_DEMON
    
    def test_insufficient_data(self):
        """Test that detector returns None with insufficient data."""
        detector = FailureArchetypeDetector()
        
        # Only 2 attempts (need at least 5)
        for i in range(2):
            attempt = ProblemAttempt(
                problem_id=1000 + i,
                timestamp=datetime.now(),
                time_spent_seconds=1800,
                submission_count=1,
                final_verdict="AC",
                tags=["dp"],
                difficulty=1400
            )
            detector.record_attempt(attempt)
        
        evidence = detector.detect_archetype()
        assert evidence is None


class TestProblemIntentEngine:
    """Test problem intent engine."""
    
    def test_engine_initialization(self):
        """Test engine can be initialized with problems."""
        problems = [create_test_problem(i, 1000 + i*100) for i in range(5)]
        engine = ProblemIntentEngine(problems)
        
        assert engine is not None
        assert len(engine.problems) == 5
    
    def test_select_problem(self):
        """Test problem selection."""
        problems = [create_test_problem(i, 1000 + i*100) for i in range(5)]
        engine = ProblemIntentEngine(problems)
        
        user_profile = UserSkillProfile(
            user_id="test_user",
            current_rating=1200,
            weak_skills={"dp"},
            trajectory_phase="foundation"
        )
        
        problem, reason = engine.select_problem(user_profile, strategic_goal="optimal_growth")
        
        assert problem is not None
        assert reason is not None
        assert isinstance(problem, ProblemMetadata)
    
    def test_generate_explanation(self):
        """Test explanation generation."""
        problems = [create_test_problem()]
        engine = ProblemIntentEngine(problems)
        
        user_profile = UserSkillProfile(
            user_id="test_user",
            current_rating=1200,
            weak_skills={"dp"}
        )
        
        problem, reason = engine.select_problem(user_profile)
        explanation = engine.generate_explanation(problem, reason)
        
        assert explanation is not None
        assert len(explanation) > 0
        assert "Problem" in explanation


class TestCognitiveMirror:
    """Test the complete cognitive mirror system."""
    
    def test_mirror_initialization(self):
        """Test mirror can be initialized."""
        problems = [create_test_problem()]
        mirror = CognitiveMirror(problems)
        
        assert mirror is not None
    
    def test_start_session(self):
        """Test starting a user session."""
        problems = [create_test_problem()]
        mirror = CognitiveMirror(problems)
        
        session = mirror.start_session("user1", "session1", initial_rating=1200)
        
        assert session is not None
        assert session.user_id == "user1"
        assert session.session_id == "session1"
        assert session.initial_rating == 1200
    
    def test_assign_problem(self):
        """Test problem assignment with reflection."""
        problems = [create_test_problem(i, 1200 + i*100) for i in range(5)]
        mirror = CognitiveMirror(problems)
        
        user_profile = UserSkillProfile(
            user_id="user1",
            current_rating=1200,
            weak_skills={"dp"}
        )
        
        mirror.start_session("user1", "session1", 1200)
        
        problem, reflection = mirror.assign_problem(user_profile)
        
        assert problem is not None
        assert reflection is not None
        assert reflection.reflection_type == ReflectionType.PROBLEM_ASSIGNMENT
        assert reflection.problem_id == problem.problem_id
    
    def test_analyze_attempt(self):
        """Test analyzing a problem attempt."""
        problems = [create_test_problem()]
        mirror = CognitiveMirror(problems)
        
        user_profile = UserSkillProfile(
            user_id="user1",
            current_rating=1200
        )
        
        mirror.start_session("user1", "session1", 1200)
        
        # Create multiple attempts to trigger detection
        for i in range(6):
            attempt = ProblemAttempt(
                problem_id=1000 + i,
                timestamp=datetime.now() - timedelta(hours=6-i),
                time_spent_seconds=3600,
                submission_count=4,
                final_verdict="TLE",
                tags=["dp"],
                difficulty=1400,
                long_idle=True
            )
            
            reflection = mirror.analyze_attempt("user1", attempt, user_profile)
        
        # Last reflection should be a failure analysis
        assert reflection is not None
        assert reflection.reflection_type == ReflectionType.FAILURE_ANALYSIS
        assert reflection.detected_archetype is not None
    
    def test_archetype_summary(self):
        """Test getting archetype summary."""
        problems = [create_test_problem()]
        mirror = CognitiveMirror(problems)
        
        mirror.start_session("user1", "session1")
        
        # Add attempts
        for i in range(6):
            attempt = ProblemAttempt(
                problem_id=1000 + i,
                timestamp=datetime.now(),
                time_spent_seconds=3600,
                submission_count=4,
                final_verdict="TLE",
                tags=["dp"],
                difficulty=1400,
                long_idle=True
            )
            mirror.analyze_attempt("user1", attempt)
        
        summary = mirror.get_archetype_summary("user1")
        
        assert summary is not None
        assert "dominant_archetype" in summary
        assert "archetype_name" in summary
        assert "intervention" in summary


class TestArchetypeSignatures:
    """Test archetype signature definitions."""
    
    def test_all_archetypes_have_signatures(self):
        """Test that all archetypes have defined signatures."""
        # Exclude UNKNOWN as it's a special case
        archetypes_to_check = [a for a in FailureArchetype if a != FailureArchetype.UNKNOWN]
        
        for archetype in archetypes_to_check:
            assert archetype in ARCHETYPE_SIGNATURES
            signature = ARCHETYPE_SIGNATURES[archetype]
            assert signature.name
            assert signature.description
            assert signature.targeted_intervention
    
    def test_signature_completeness(self):
        """Test that signatures have all required fields."""
        for archetype, signature in ARCHETYPE_SIGNATURES.items():
            if archetype == FailureArchetype.UNKNOWN:
                continue
            
            assert signature.archetype == archetype
            assert len(signature.name) > 0
            assert len(signature.description) > 0
            assert len(signature.targeted_intervention) > 0
            assert signature.confidence_threshold > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
