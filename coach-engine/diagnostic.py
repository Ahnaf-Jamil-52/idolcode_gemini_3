"""
Coach Engine Diagnostic Tool

Checks all modules can be imported and basic functionality works.
Run this to verify your installation is correct.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

import traceback
from datetime import datetime


class DiagnosticRunner:
    """Runs diagnostic checks on coach engine."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def check(self, name: str, func):
        """Run a diagnostic check."""
        try:
            func()
            self.results.append((name, True, None))
            self.passed += 1
            print(f"[OK] {name}")
            return True
        except Exception as e:
            self.results.append((name, False, str(e)))
            self.failed += 1
            print(f"[FAIL] {name}")
            print(f"  Error: {e}")
            if "--verbose" in sys.argv:
                traceback.print_exc()
            return False
    
    def print_summary(self):
        """Print diagnostic summary."""
        print("\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 60)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.failed > 0:
            print("\n❌ Some checks failed. See errors above.")
            print("   Run with --verbose for full traceback.")
        else:
            print("\n✅ All checks passed! Coach engine is working correctly.")
    
    def run_all(self):
        """Run all diagnostic checks."""
        print("=" * 60)
        print("COACH ENGINE DIAGNOSTIC")
        print("=" * 60)
        print()
        
        # Module imports
        print("Checking module imports...")
        self.check("Import signals", lambda: __import__("coach_engine.signals"))
        self.check("Import scorer", lambda: __import__("coach_engine.scorer"))
        self.check("Import trends", lambda: __import__("coach_engine.trends"))
        self.check("Import states", lambda: __import__("coach_engine.states"))
        self.check("Import sentiment", lambda: __import__("coach_engine.sentiment"))
        self.check("Import fusion", lambda: __import__("coach_engine.fusion"))
        self.check("Import responses", lambda: __import__("coach_engine.responses"))
        self.check("Import failure_archetypes", lambda: __import__("coach_engine.failure_archetypes"))
        self.check("Import problem_intent", lambda: __import__("coach_engine.problem_intent"))
        self.check("Import cognitive_mirror", lambda: __import__("coach_engine.cognitive_mirror"))
        self.check("Import realtime_detector", lambda: __import__("coach_engine.realtime_detector"))
        self.check("Import duck_tts", lambda: __import__("coach_engine.duck_tts"))
        self.check("Import interventions", lambda: __import__("coach_engine.interventions"))
        self.check("Import live_cognitive_mirror", lambda: __import__("coach_engine.live_cognitive_mirror"))
        self.check("Import realtime_coach", lambda: __import__("coach_engine.realtime_coach"))
        
        print("\nChecking core functionality...")
        
        # Test signal collector
        def test_signal_collector():
            from coach_engine.signals import SignalCollector, SignalType
            collector = SignalCollector()
            # Start a session first
            collector.start_session("test_user", "test_session")
            signals = collector.record_event("submission", metadata={"verdict": "WA"})
            assert collector.signals is not None
        
        self.check("Signal collector", test_signal_collector)
        
        # Test burnout scorer
        def test_burnout_scorer():
            from coach_engine.scorer import BurnoutScorer
            from coach_engine.signals import SignalCollector
            
            collector = SignalCollector()
            collector.start_session("test_user", "test_session")
            collector.record_event("submission", metadata={"verdict": "WA"})
            scorer = BurnoutScorer()
            score = scorer.calculate_burnout(list(collector.signals))
            assert score.score >= 0 and score.score <= 1
        
        self.check("Burnout scorer", test_burnout_scorer)
        
        # Test state machine
        def test_state_machine():
            from coach_engine.states import CoachStateMachine, CoachState
            from coach_engine.scorer import BurnoutScorer, BurnoutLevel
            from datetime import datetime
            
            machine = CoachStateMachine()
            assert machine.current_state == CoachState.NORMAL
            
            # Create a simple burnout score
            from coach_engine.scorer import BurnoutScore
            score = BurnoutScore(
                score=0.35,
                level=BurnoutLevel.MODERATE,
                timestamp=datetime.now(),
                contributing_signals=[],
                raw_weighted_sum=0.35,
                ema_smoothed=0.35
            )
            machine.update(score, trend=None)
        
        self.check("State machine", test_state_machine)
        
        # Test sentiment analyzer
        def test_sentiment():
            from coach_engine.sentiment import KeywordSentimentAnalyzer
            
            analyzer = KeywordSentimentAnalyzer()
            result = analyzer.analyze("I hate this problem, it's frustrating")
            assert result.state is not None
        
        self.check("Sentiment analyzer", test_sentiment)
        
        # Test failure archetypes
        def test_archetypes():
            from coach_engine.failure_archetypes import FailureArchetypeDetector, ProblemAttempt
            
            detector = FailureArchetypeDetector()
            attempt = ProblemAttempt(
                problem_id=1001,
                timestamp=datetime.now(),
                time_spent_seconds=300,
                final_verdict="WA",
                submission_count=3,
                tags=["dp"],
                difficulty=1500
            )
            detector.record_attempt(attempt)
        
        self.check("Failure archetypes", test_archetypes)
        
        # Test cognitive mirror (simple test without full problem database)
        def test_cognitive_mirror():
            # Just test import capability - full test requires complex setup
            from coach_engine.cognitive_mirror import CognitiveMirror
            assert CognitiveMirror is not None
        
        self.check("Cognitive mirror import", test_cognitive_mirror)
        
        # Test real-time detector
        def test_realtime_detector():
            from coach_engine.realtime_detector import RealtimeDetector
            
            detector = RealtimeDetector()
            detector.start_problem(["dp", "arrays"])
            detector.record_typing(1, chars_added=5)
            assert len(detector.typing_events) > 0
        
        self.check("Realtime detector", test_realtime_detector)
        
        # Test duck TTS
        def test_duck_tts():
            from coach_engine.duck_tts import get_duck_voice, VoiceMood
            
            duck = get_duck_voice(enabled=False)  # Disable actual audio
            duck.speak("Test", mood=VoiceMood.NEUTRAL)
        
        self.check("Duck TTS", test_duck_tts)
        
        # Test interventions
        def test_interventions():
            from coach_engine.interventions import InterventionSelector, InterventionContext
            from coach_engine.states import CoachState
            from coach_engine.scorer import BurnoutLevel
            
            selector = InterventionSelector()
            context = InterventionContext(
                coach_state=CoachState.NORMAL,
                burnout_level=BurnoutLevel.LOW,
                burnout_score=0.15,
                active_signals=set(),
                recent_detections=[],
                problem_tags=["dp"],
                time_on_problem_minutes=5.0
            )
            # May or may not return intervention, both are valid
            intervention = selector.select(context)
        
        self.check("Intervention selector", test_interventions)
        
        # Test live cognitive mirror
        def test_live_mirror():
            from coach_engine.live_cognitive_mirror import LiveCognitiveMirror
            from coach_engine.states import CoachState
            
            mirror = LiveCognitiveMirror()
            insight = mirror.infer_cognitive_state(
                active_signals=[],
                detected_archetype=None,
                problem_tags=["dp"],
                time_on_problem_minutes=5.0,
                burnout_state=CoachState.NORMAL
            )
        
        self.check("Live cognitive mirror", test_live_mirror)
        
        # Test realtime coach (full integration)
        def test_realtime_coach():
            from coach_engine.realtime_coach import RealtimeCoach
            
            coach = RealtimeCoach(user_id="diagnostic", enable_tts=False)
            coach.start_problem(1001, tags=["dp"], difficulty=1500)
            
            # Simulate some activity
            for i in range(5):
                coach.on_typing(line_number=i+1, chars_added=5)
            
            code = "def solve():\n    pass"
            coach.on_code_change(code, line_count=2)
            
            # Update
            update = coach.update()
            assert update is not None
            assert update.coach_state is not None
        
        self.check("Realtime coach (integration)", test_realtime_coach)
        
        # Check TTS library
        def test_pyttsx3():
            import pyttsx3
            engine = pyttsx3.init()
            engine.stop()  # Don't actually speak
        
        self.check("pyttsx3 library", test_pyttsx3)
        
        self.print_summary()
        
        return self.failed == 0


def main():
    """Run diagnostics."""
    runner = DiagnosticRunner()
    success = runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
