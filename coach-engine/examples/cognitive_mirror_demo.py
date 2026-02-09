#!/usr/bin/env python3
"""
Cognitive Mirror - Demo Script

Demonstrates the Cognitive Mirror system that provides:
1. Intelligent problem assignment with explanations
2. Failure archetype detection and feedback
3. Metacognitive insights 

This shows the "Why this problem?" and "What thinker are you?" features.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

from coach_engine.cognitive_mirror import CognitiveMirror, ReflectionType
from coach_engine.problem_intent import (
    ProblemMetadata, 
    UserSkillProfile,
    CognitiveTrigger
)
from coach_engine.failure_archetypes import (
    ProblemAttempt,
    FailureArchetype
)


def load_problem_database() -> list:
    """Load mock problems from JSON file."""
    problems_file = Path(__file__).parent.parent / "mock_data" / "problems.json"
    
    with open(problems_file, 'r') as f:
        problem_data = json.load(f)
    
    # Convert to ProblemMetadata objects
    problems = []
    for p in problem_data:
        # Convert cognitive triggers from strings to enums
        triggers = []
        for trigger_str in p.get('cognitive_triggers', []):
            try:
                trigger = CognitiveTrigger(trigger_str)
                triggers.append(trigger)
            except ValueError:
                pass
        
        problem = ProblemMetadata(
            problem_id=p['problem_id'],
            title=p['title'],
            difficulty=p['difficulty'],
            tags=p['tags'],
            hidden_skills=p['hidden_skills'],
            cognitive_triggers=triggers,
            common_wrong_paths=p['common_wrong_paths'],
            failure_archetypes_targeted=p['failure_archetypes_targeted'],
            historical_role=p['historical_role'],
            typical_solve_time_minutes=p['typical_solve_time_minutes'],
            required_skills=p.get('required_skills', []),
            recommended_prerequisites=p.get('recommended_prerequisites', []),
            source=p.get('source', 'codeforces'),
            url=p.get('url')
        )
        problems.append(problem)
    
    return problems


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print formatted section."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


def print_reflection(reflection):
    """Pretty print a cognitive reflection."""
    print(f"\n{'═' * 70}")
    print(f"  {reflection.title}")
    print(f"{'═' * 70}")
    print(f"\n{reflection.message}\n")
    
    if reflection.evidence:
        print("📊 Evidence:")
        for evidence in reflection.evidence:
            print(f"   • {evidence}")
    
    if reflection.recommended_actions:
        print("\n💡 Recommended Actions:")
        for action in reflection.recommended_actions:
            print(f"   → {action}")
    
    print(f"\nConfidence: {reflection.confidence:.0%}")
    print(f"Timestamp: {reflection.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def demo_scenario_1():
    """
    Scenario 1: New user starts practicing
    Shows intelligent problem assignment with explanation
    """
    print_header("Scenario 1: Intelligent Problem Assignment")
    
    # Load problem database
    problems = load_problem_database()
    print(f"\nLoaded {len(problems)} problems into database")
    
    # Initialize Cognitive Mirror
    mirror = CognitiveMirror(problem_database=problems)
    print("✓ Cognitive Mirror initialized")
    
    # Create a user profile
    user_profile = UserSkillProfile(
        user_id="alice_2026",
        current_rating=1200,
        weak_skills={"dp", "bitmask"},
        avoided_tags={"dp"},
        trajectory_phase="foundation"
    )
    
    print(f"\n👤 User Profile:")
    print(f"   Rating: {user_profile.current_rating}")
    print(f"   Weak Skills: {', '.join(user_profile.weak_skills)}")
    print(f"   Avoided Tags: {', '.join(user_profile.avoided_tags)}")
    print(f"   Phase: {user_profile.trajectory_phase}")
    
    # Start a session
    session = mirror.start_session(
        user_id=user_profile.user_id,
        session_id="practice_session_001",
        initial_rating=user_profile.current_rating
    )
    print(f"\n✓ Started session: {session.session_id}")
    
    # Assign a problem
    print_section("Assigning Problem")
    problem, reflection = mirror.assign_problem(
        user_profile=user_profile,
        strategic_goal="fill_gap"
    )
    
    print(f"\n🎯 Assigned: Problem {problem.problem_id} - {problem.title}")
    print(f"   Difficulty: {problem.difficulty}")
    print(f"   Tags: {', '.join(problem.tags)}")
    
    # Show the explanation
    print_reflection(reflection)


def demo_scenario_2():
    """
    Scenario 2: User fails multiple problems, archetype detected
    Shows failure pattern recognition and metacognitive feedback
    """
    print_header("Scenario 2: Failure Archetype Detection")
    
    # Load problems
    problems = load_problem_database()
    mirror = CognitiveMirror(problem_database=problems)
    
    # Create user profile
    user_profile = UserSkillProfile(
        user_id="bob_2026",
        current_rating=1400,
        weak_skills={"greedy", "constructive"},
        trajectory_phase="growth"
    )
    
    session = mirror.start_session(
        user_id=user_profile.user_id,
        session_id="practice_session_002",
        initial_rating=user_profile.current_rating
    )
    
    print(f"\n👤 User: {user_profile.user_id}")
    print(f"   Rating: {user_profile.current_rating}")
    
    # Simulate several problem attempts showing "Brute Forcer" pattern
    print_section("Simulating Problem Attempts")
    
    attempts = [
        ProblemAttempt(
            problem_id=1842,
            timestamp=datetime.now() - timedelta(hours=5),
            time_spent_seconds=3600,  # 1 hour (too long for 1400)
            submission_count=4,
            final_verdict="TLE",
            tags=["dp", "bitmask"],
            difficulty=1400,
            rapid_submissions=False,
            long_idle=True
        ),
        ProblemAttempt(
            problem_id=1500,
            timestamp=datetime.now() - timedelta(hours=4),
            time_spent_seconds=2700,  # 45 min (too long for 1200)
            submission_count=3,
            final_verdict="TLE",
            tags=["dp", "graphs"],
            difficulty=1200,
            rapid_submissions=False,
            long_idle=False
        ),
        ProblemAttempt(
            problem_id=1650,
            timestamp=datetime.now() - timedelta(hours=3),
            time_spent_seconds=4200,  # 70 min (way too long)
            submission_count=5,
            final_verdict="MLE",
            tags=["greedy", "constructive"],
            difficulty=1600,
            rapid_submissions=False,
            long_idle=True
        ),
        ProblemAttempt(
            problem_id=1100,
            timestamp=datetime.now() - timedelta(hours=2),
            time_spent_seconds=2400,  # 40 min (too long for easy)
            submission_count=4,
            final_verdict="TLE",
            tags=["binary_search", "math"],
            difficulty=1100,
            rapid_submissions=False,
            long_idle=False
        ),
        ProblemAttempt(
            problem_id=1750,
            timestamp=datetime.now() - timedelta(hours=1),
            time_spent_seconds=3900,  # 65 min (too long)
            submission_count=6,
            final_verdict="TLE",
            tags=["constructive", "math"],
            difficulty=1500,
            rapid_submissions=False,
            long_idle=True
        ),
    ]
    
    # Process each attempt
    for i, attempt in enumerate(attempts, 1):
        print(f"\n{i}. Problem {attempt.problem_id} ({attempt.difficulty})")
        print(f"   Time: {attempt.time_spent_seconds // 60} min | "
              f"Submissions: {attempt.submission_count} | "
              f"Result: {attempt.final_verdict}")
        
        reflection = mirror.analyze_attempt(
            user_id=user_profile.user_id,
            attempt=attempt,
            user_profile=user_profile
        )
        
        if reflection:
            print_reflection(reflection)
    
    # Show archetype summary
    print_section("Archetype Summary")
    summary = mirror.get_archetype_summary(user_profile.user_id)
    
    if summary:
        print(f"\n🎭 Detected Archetype: {summary['archetype_name']}")
        print(f"   {summary['description']}")
        print(f"\n   Detection Confidence: {summary['detection_count']}/{summary['total_detections']} attempts")
        print(f"\n   Intervention Strategy:")
        print(f"   {summary['intervention']}")
        print(f"\n   Recommended Practice:")
        for practice_type in summary['recommended_practice']:
            print(f"   • {practice_type}")


def demo_scenario_3():
    """
    Scenario 3: User overcomes pattern and achieves success
    Shows breakthrough moment recognition
    """
    print_header("Scenario 3: Pattern Breaking & Success")
    
    problems = load_problem_database()
    mirror = CognitiveMirror(problem_database=problems)
    
    user_profile = UserSkillProfile(
        user_id="charlie_2026",
        current_rating=1300,
        weak_skills={"dp"},
        trajectory_phase="growth"
    )
    
    session = mirror.start_session(
        user_id=user_profile.user_id,
        session_id="practice_session_003",
        initial_rating=user_profile.current_rating
    )
    
    print(f"\n👤 User: {user_profile.user_id}")
    
    # First, establish "Speed Demon" pattern with failures
    print_section("Phase 1: Establishing Pattern (Speed Demon)")
    
    failure_attempts = [
        ProblemAttempt(
            problem_id=800,
            timestamp=datetime.now() - timedelta(hours=3),
            time_spent_seconds=300,  # 5 min (too fast)
            submission_count=3,
            final_verdict="WA",
            tags=["implementation"],
            difficulty=800,
            rapid_submissions=True
        ),
        ProblemAttempt(
            problem_id=900,
            timestamp=datetime.now() - timedelta(hours=2, minutes=50),
            time_spent_seconds=420,  # 7 min (too fast)
            submission_count=4,
            final_verdict="WA",
            tags=["strings"],
            difficulty=900,
            rapid_submissions=True
        ),
        ProblemAttempt(
            problem_id=1100,
            timestamp=datetime.now() - timedelta(hours=2, minutes=30),
            time_spent_seconds=600,  # 10 min (too fast)
            submission_count=5,
            final_verdict="RTE",
            tags=["binary_search"],
            difficulty=1100,
            rapid_submissions=True
        ),
    ]
    
    for attempt in failure_attempts:
        print(f"\n   Problem {attempt.problem_id}: {attempt.time_spent_seconds // 60} min → {attempt.final_verdict}")
        reflection = mirror.analyze_attempt(
            user_id=user_profile.user_id,
            attempt=attempt,
            user_profile=user_profile
        )
    
    if reflection:
        print_reflection(reflection)
    
    # Then succeed with improved approach
    print_section("Phase 2: Breaking the Pattern (Success!)")
    
    success_attempt = ProblemAttempt(
        problem_id=1300,
        timestamp=datetime.now(),
        time_spent_seconds=360,  # 6 min (still fast but careful)
        submission_count=1,
        final_verdict="AC",  # SUCCESS!
        tags=["two_pointers"],
        difficulty=1300,
        rapid_submissions=False  # Not rushing anymore
    )
    
    print(f"\n   Problem {success_attempt.problem_id}: "
          f"{success_attempt.time_spent_seconds // 60} min → {success_attempt.final_verdict} ✓")
    
    reflection = mirror.analyze_attempt(
        user_id=user_profile.user_id,
        attempt=success_attempt,
        user_profile=user_profile
    )
    
    if reflection:
        print_reflection(reflection)
    
    # Show progress
    print_section("Session Summary")
    recent_reflections = mirror.get_reflections(user_profile.user_id, count=3)
    print(f"\n📈 Total Reflections: {len(recent_reflections)}")
    print(f"   Last archetype evolution: {session.archetype_evolution}")


def main():
    """Run all demo scenarios."""
    print_header("Cognitive Mirror System - Demo")
    print("\nThis demo shows:")
    print("  1. Intelligent problem assignment with explanations")
    print("  2. Failure archetype detection and analysis")
    print("  3. Pattern breaking and breakthrough moments")
    print("\nPress Enter to begin...")
    input()
    
    try:
        demo_scenario_1()
        print("\n\nPress Enter for next scenario...")
        input()
        
        demo_scenario_2()
        print("\n\nPress Enter for next scenario...")
        input()
        
        demo_scenario_3()
        
        print_header("Demo Complete")
        print("\nThe Cognitive Mirror system successfully demonstrated:")
        print("  ✓ Problem Intent Engine ('Why this problem?')")
        print("  ✓ Failure Archetype Detection ('What thinker are you?')")
        print("  ✓ Metacognitive Reflections (turning practice into learning)")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Could not find problem database.")
        print(f"   Make sure problems.json exists in mock_data/")
        print(f"   {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
