#!/usr/bin/env python3
"""
Coach Engine - Main Runner

Local runner for testing and demonstrating the burnout detection
and sentiment analysis features + Cognitive Mirror system.

Usage:
    python main.py demo          # Run burnout detection demo
    python main.py cognitive     # Run Cognitive Mirror demo
    python main.py interactive   # Interactive testing mode
    python main.py test          # Run tests
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from coach_engine.signals import SignalCollector, BehavioralSignal, SignalType
from coach_engine.scorer import BurnoutScorer, BurnoutScore
from coach_engine.trends import TrendDetector, TrendDirection
from coach_engine.states import CoachStateMachine, CoachState
from coach_engine.sentiment import HybridSentimentAnalyzer, EmotionalState
from coach_engine.fusion import FusionEngine, FusionResult
from coach_engine.responses import ResponseSelector, CoachResponse


def load_mock_data() -> Dict[str, Any]:
    """Load mock data from JSON files."""
    mock_dir = Path(__file__).parent / "mock_data"
    
    data = {}
    for file in ["events_log.json", "chat_log.json", "sessions.json"]:
        file_path = mock_dir / file
        if file_path.exists():
            with open(file_path, "r") as f:
                data[file.replace(".json", "")] = json.load(f)
    
    return data


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text: str):
    """Print a formatted section header."""
    print(f"\n--- {text} ---")


def run_demo(use_gemini: bool = False, gemini_key: str = None):
    """Run a demonstration with mock data."""
    print_header("Coach Engine Demo - Burnout Detection System")
    
    # Initialize engine with Gemini support
    engine = FusionEngine(use_gemini=use_gemini, gemini_api_key=gemini_key)
    response_selector = ResponseSelector(cooldown_seconds=0, use_gemini=use_gemini, gemini_api_key=gemini_key)  # No cooldown for demo
    
    # Load mock data
    mock_data = load_mock_data()
    events = mock_data.get("events_log", [])
    messages = mock_data.get("chat_log", [])
    
    print(f"\nLoaded {len(events)} events and {len(messages)} messages from mock data")
    
    # Start a session
    print_section("Starting Session")
    engine.start_session("user_001", "demo_session")
    
    # Process events chronologically
    print_section("Processing Events")
    
    # Merge and sort by timestamp
    all_items = []
    for event in events:
        all_items.append({"type": "event", "data": event, "ts": event["timestamp"]})
    for msg in messages:
        all_items.append({"type": "message", "data": msg, "ts": msg["timestamp"]})
    
    all_items.sort(key=lambda x: x["ts"])
    
    # Process first 15 items for demo
    for i, item in enumerate(all_items[:15]):
        if item["type"] == "event":
            event = item["data"]
            event_type = event["event_type"]
            metadata = event.get("metadata", {})
            
            signals = engine.process_event(event_type, metadata)
            
            if signals:
                print(f"\n[Event] {event_type}")
                for sig in signals:
                    print(f"  → Signal detected: {sig.signal_type.value} (weight: {sig.weight})")
        
        elif item["type"] == "message":
            msg = item["data"]
            text = msg["text"]
            
            sentiment = engine.process_message(text)
            
            print(f"\n[Message] \"{text[:50]}...\"")
            print(f"  → State: {sentiment.state.value}, Intensity: {sentiment.intensity:.2f}")
            if sentiment.is_masked:
                print(f"  → ⚠️  MASKING DETECTED")
    
    # Analyze current state
    print_section("Current Analysis")
    result = engine.analyze()
    
    print(f"\nComposite Burnout Score: {result.composite_score:.2f}")
    print(f"Current State: {result.current_state.value}")
    print(f"Alignment: {result.alignment.value}")
    print(f"Intervention Level: {result.intervention_level.value}")
    print(f"Ghost Speed Modifier: {result.ghost_speed_modifier:.2f}")
    
    if result.is_masking:
        print("\n⚠️  MASKING DETECTED: User may be hiding true feelings")
    
    if result.is_silent_disengagement:
        print("\n⚠️  SILENT DISENGAGEMENT: User stopped communicating")
    
    print("\nRecommended Actions:")
    for action in result.recommended_actions:
        print(f"  • {action}")
    
    # Generate coach response
    print_section("Coach Response")
    
    # Get recent sentiment for response
    recent_sentiment = engine.sentiment_history.get_recent(1)
    emotional_state = recent_sentiment[0].state if recent_sentiment else None
    
    response = response_selector.generate_response(
        result,
        emotional_state,
        context={
            "idol_name": "tourist",
            "session_minutes": 45,
            "contest_num": 47
        }
    )
    
    if response:
        print(f"\nCoach says ({response.emotion_display}):")
        print(f'  "{response.message}"')
        print(f"\nStrategy: {response.strategy.value}")
    else:
        print("\n[Coach stays quiet - no intervention needed]")
    
    # End session
    engine.end_session()
    
    print_section("Demo Complete")


def run_interactive(use_gemini: bool = False, gemini_key: str = None):
    """Run interactive testing mode."""
    print_header("Coach Engine - Interactive Mode")
    print("\nCommands:")
    print("  event <type>     - Simulate an event")
    print("  msg <text>       - Analyze a message")
    print("  status           - Show current status")
    print("  analyze          - Run full analysis")
    print("  state            - Show state machine info")
    print("  reset            - Reset the engine")
    print("  help             - Show commands")
    print("  quit             - Exit")
    
    engine = FusionEngine(use_gemini=use_gemini, gemini_api_key=gemini_key)
    response_selector = ResponseSelector(cooldown_seconds=10, use_gemini=use_gemini, gemini_api_key=gemini_key)
    engine.start_session("interactive_user", "interactive_session")
    
    event_types = [
        "submission", "wrong_answer", "problem_opened", "problem_skipped",
        "problem_solved", "ghost_race_result", "hint_requested", "hint_declined",
        "code_paste", "tab_switch", "idle_detected"
    ]
    
    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if cmd == "quit" or cmd == "exit":
            break
        
        elif cmd == "help":
            print("Event types:", ", ".join(event_types))
            print("\nFor ghost_race_result, add 'win' or 'lose':")
            print("  event ghost_race_result lose")
        
        elif cmd == "event":
            event_type = arg.split()[0] if arg else "wrong_answer"
            
            if event_type not in event_types:
                print(f"Unknown event type. Available: {', '.join(event_types)}")
                continue
            
            metadata = {}
            if event_type == "ghost_race_result":
                won = "win" in arg.lower()
                metadata["won"] = won
                print(f"Ghost race: {'WON' if won else 'LOST'}")
            elif event_type == "idle_detected":
                metadata["idle_minutes"] = 25
            
            signals = engine.process_event(event_type, metadata)
            print(f"Processed: {event_type}")
            
            for sig in signals:
                print(f"  Signal: {sig.signal_type.value} (weight: {sig.weight:.2f})")
        
        elif cmd == "msg":
            if not arg:
                print("Usage: msg <your message>")
                continue
            
            result = engine.process_message(arg)
            print(f"State: {result.state.value}")
            print(f"Intensity: {result.intensity:.2f}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Method: {result.analysis_method}")
            
            if result.is_masked:
                print("⚠️  MASKING DETECTED")
            
            if result.matched_patterns:
                print("Patterns:", [p[1] for p in result.matched_patterns[:3]])
        
        elif cmd == "status":
            result = engine.analyze()
            print(f"Burnout Score: {result.composite_score:.2f}")
            print(f"State: {result.current_state.value}")
            print(f"Alignment: {result.alignment.value}")
            print(f"Ghost Speed: {result.ghost_speed_modifier:.0%}")
        
        elif cmd == "analyze":
            result = engine.analyze()
            print(json.dumps(result.to_dict(), indent=2))
            
            # Generate response
            recent = engine.sentiment_history.get_recent(1)
            emotion = recent[0].state if recent else None
            
            response = response_selector.generate_response(result, emotion)
            if response:
                print(f"\nCoach: \"{response.message}\"")
        
        elif cmd == "state":
            ctx = engine.state_machine.current_context
            print(f"State: {ctx.state.value}")
            print(f"Minutes in state: {ctx.minutes_in_state:.1f}")
            print(f"Burnout: {ctx.burnout_score:.2f}")
            
            transitions = engine.state_machine.get_recent_transitions(3)
            if transitions:
                print("\nRecent transitions:")
                for t in transitions:
                    print(f"  {t.from_state.value} → {t.to_state.value}: {t.trigger}")
        
        elif cmd == "reset":
            engine.reset()
            engine.start_session("interactive_user", "interactive_session")
            print("Engine reset.")
        
        else:
            print(f"Unknown command: {cmd}. Type 'help' for commands.")
    
    print("\nGoodbye!")


def run_quick_test(use_gemini: bool = False, gemini_key: str = None):
    """Run quick component tests."""
    print_header("Coach Engine - Quick Tests")
    
    # Test 1: Signal detection
    print_section("Test 1: Signal Detection")
    collector = SignalCollector()
    collector.start_session("test_user", "test_session")
    
    # Simulate 3 wrong answers in 2 minutes (should trigger rapid_wa_burst)
    signals = []
    signals.extend(collector.record_event("wrong_answer", {}))
    signals.extend(collector.record_event("wrong_answer", {}))
    signals.extend(collector.record_event("wrong_answer", {}))
    
    burst_detected = any(s.signal_type == SignalType.RAPID_WA_BURST for s in signals)
    print(f"  Rapid WA burst detection: {'✓ PASS' if burst_detected else '✗ FAIL'}")
    
    # Test 2: Burnout scoring
    print_section("Test 2: Burnout Scoring")
    scorer = BurnoutScorer()
    
    # Create test signals
    test_signals = [
        BehavioralSignal(SignalType.GHOST_LOSS_STREAK, datetime.now(), 0.20),
        BehavioralSignal(SignalType.PROBLEM_SKIP_STREAK, datetime.now(), 0.18),
        BehavioralSignal(SignalType.RAPID_WA_BURST, datetime.now(), 0.15),
    ]
    
    score = scorer.calculate_burnout(test_signals)
    print(f"  Score from 3 negative signals: {score.score:.2f}")
    print(f"  Level: {score.level.value}")
    print(f"  Score > 0.3: {'✓ PASS' if score.score > 0.3 else '✗ FAIL'}")
    
    # Test 3: Trend detection
    print_section("Test 3: Trend Detection")
    detector = TrendDetector()
    
    # Increasing scores = deteriorating
    scores = [0.2, 0.3, 0.4, 0.5, 0.6]
    trend = detector.analyze(scores)
    print(f"  Trend for increasing scores: {trend.direction.value}")
    print(f"  Slope: {trend.slope:.3f}")
    print(f"  Is deteriorating: {'✓ PASS' if trend.direction == TrendDirection.DETERIORATING else '✗ FAIL'}")
    
    # Test 4: Sentiment analysis
    print_section("Test 4: Sentiment Analysis")
    analyzer = HybridSentimentAnalyzer()
    
    test_cases = [
        ("I can't do this, it's too hard", EmotionalState.DISCOURAGED),
        ("wtf this is broken", EmotionalState.FRUSTRATED),
        ("I'm tired, whatever", EmotionalState.FATIGUED),
        ("Yes! Finally got it!", EmotionalState.CELEBRATING),
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = analyzer.analyze(text)
        match = result.state == expected
        passed += 1 if match else 0
        status = "✓" if match else "✗"
        print(f"  {status} \"{text[:30]}...\" → {result.state.value} (expected: {expected.value})")
    
    print(f"  Passed: {passed}/{len(test_cases)}")
    
    # Test 5: State machine
    print_section("Test 5: State Machine")
    state_machine = CoachStateMachine()
    
    print(f"  Initial state: {state_machine.current_state.value}")
    
    # Simulate high burnout
    high_burnout = BurnoutScore(
        score=0.55, level=BurnoutLevel.HIGH,
        timestamp=datetime.now(),
        contributing_signals=[], raw_weighted_sum=0.55, ema_smoothed=0.55
    )
    
    # Force time passage for transition
    state_machine._min_state_duration = timedelta(seconds=0)
    
    transition = state_machine.update(high_burnout)
    print(f"  After high burnout: {state_machine.current_state.value}")
    print(f"  Transitioned: {'✓ PASS' if transition else '✗ FAIL'}")
    
    # Test 6: Complete fusion
    print_section("Test 6: Fusion Engine")
    engine = FusionEngine(use_gemini=use_gemini, gemini_api_key=gemini_key)
    engine.start_session("test", "test")
    
    # Add some negative events
    engine.process_event("wrong_answer")
    engine.process_event("wrong_answer")
    engine.process_event("problem_skipped")
    engine.process_message("I'm stuck and frustrated")
    
    result = engine.analyze()
    print(f"  Composite score: {result.composite_score:.2f}")
    print(f"  State: {result.current_state.value}")
    print(f"  Alignment: {result.alignment.value}")
    print(f"  Fusion working: {'✓ PASS' if result.composite_score > 0 else '✗ FAIL'}")
    
    print_section("All Tests Complete")


# Import BurnoutLevel for tests
from coach_engine.scorer import BurnoutLevel


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Coach Engine - Burnout Detection & Sentiment Analysis"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="demo",
        choices=["demo", "cognitive", "interactive", "test"],
        help="Run mode: demo (burnout), cognitive (mirror), interactive, or test"
    )
    parser.add_argument(
        "--use-gemini",
        action="store_true",
        help="Enable Gemini AI for advanced psychological analysis"
    )
    parser.add_argument(
        "--gemini-key",
        type=str,
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        run_demo(use_gemini=args.use_gemini, gemini_key=args.gemini_key)
    elif args.mode == "cognitive":
        # Import and run cognitive mirror demo
        try:
            from examples.cognitive_mirror_demo import main as cognitive_demo_main
            cognitive_demo_main()
        except ImportError as e:
            print(f"Error: Could not import cognitive mirror demo: {e}")
            print("Make sure examples/cognitive_mirror_demo.py exists")
    elif args.mode == "interactive":
        run_interactive(use_gemini=args.use_gemini, gemini_key=args.gemini_key)
    elif args.mode == "test":
        run_quick_test(use_gemini=args.use_gemini, gemini_key=args.gemini_key)


if __name__ == "__main__":
    main()
