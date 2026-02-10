"""
Real-Time Coach Demo

Demonstrates the complete real-time coaching system with:
- Real-time problem detection
- TTS duck voice
- Live cognitive mirror
- Intervention system
- State machine

This simulates a coding session with the coach monitoring in real-time.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import coach_engine
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime

from coach_engine.realtime_coach import RealtimeCoach, get_realtime_coach
from coach_engine.realtime_detector import RealtimeSignal
from coach_engine.states import CoachState


def simulate_coding_session():
    """
    Simulate a coding session with various behaviors.
    
    This demonstrates how the coach responds to different patterns.
    """
    print("=" * 60)
    print("REAL-TIME COACHING DEMO")
    print("=" * 60)
    print()
    
    # Initialize coach
    coach = RealtimeCoach(
        user_id="demo_user",
        enable_tts=True,  # Set to False if you don't have pyttsx3 or want text only
        enable_interventions=True
    )
    
    print("âœ“ Coach initialized")
    print(f"  State: {coach.get_current_state().value}")
    print()
    
    # Scenario 1: Start a DP problem
    print("--- Scenario 1: Starting a DP problem ---")
    coach.start_problem(
        problem_id=1001,
        tags=["dp", "dynamic programming", "medium"],
        difficulty=1500
    )
    print("âœ“ Problem started: DP problem (1500 rating)")
    print()
    
    # Simulate some normal typing
    print("Simulating normal typing...")
    for i in range(5):
        coach.on_typing(line_number=i+1, chars_added=10)
        time.sleep(0.1)
    
    # Take a snapshot
    code = """
    def solve():
        n = int(input())
        # thinking...
    """
    coach.on_code_change(code, line_count=3)
    
    # Run update
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 2: User gets stuck (long idle)
    print("\n--- Scenario 2: User gets stuck (idle for 40 seconds) ---")
    print("Simulating 40 seconds of idle time...")
    
    # Simulate idle by not recording typing
    time.sleep(2)  # In real scenario this would be 40+ seconds
    
    # Manually trigger idle detection for demo
    from datetime import timedelta
    coach.realtime_detector.last_activity = datetime.now() - timedelta(seconds=45)
    
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 3: User rewrites same code multiple times
    print("\n--- Scenario 3: User rewrites same code block 3 times ---")
    
    for iteration in range(3):
        print(f"  Rewrite #{iteration + 1}")
        code = f"""
        def solve():
            n = int(input())
            # attempt {iteration + 1}
            for i in range(n):
                # wrong approach
        """
        coach.on_typing(line_number=4, chars_added=20)
        coach.on_typing(line_number=5, chars_deleted=10)
        coach.on_code_change(code, line_count=6)
        time.sleep(0.3)
    
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 4: User writes nested loops early (brute force)
    print("\n--- Scenario 4: User jumps to brute force with nested loops ---")
    
    code = """
    def solve():
        n = int(input())
        arr = list(map(int, input().split()))
        
        # brute force
        for i in range(n):
            for j in range(i+1, n):
                for k in range(j+1, n):
                    # check all triplets
    """
    
    coach.on_typing(line_number=7, chars_added=50, is_paste=False)
    coach.on_code_change(code, line_count=11)
    
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 5: User types very fast (panic mode)
    print("\n--- Scenario 5: User types very fast (panic mode) ---")
    
    for i in range(10):
        coach.on_typing(line_number=i+10, chars_added=30)
        time.sleep(0.05)  # Very fast typing
    
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 6: User adds self-doubt comments
    print("\n--- Scenario 6: User adds self-doubt comments ---")
    
    code = """
    def solve():
        n = int(input())
        arr = list(map(int, input().split()))
        
        # idk if this works
        # this is probably wrong
        # hack for now
    """
    
    coach.on_typing(line_number=15, chars_added=15)
    coach.on_code_change(code, line_count=8)
    
    update = coach.update()
    print_update(update)
    
    time.sleep(1)
    
    # Scenario 7: Show state progression
    print("\n--- Scenario 7: State progression with failures ---")
    
    # Simulate consecutive failures
    for fail_num in range(3):
        print(f"  Failure #{fail_num + 1}")
        coach.on_problem_submit(success=False)
        coach.context.consecutive_failures = fail_num + 1
        
        update = coach.update()
        print(f"  State: {update.coach_state.value}, Burnout: {update.burnout_score:.2f}")
        time.sleep(0.5)
    
    print()
    
    # Final update
    print("\n--- Final Status ---")
    final_update = coach.update()
    print_update(final_update)
    
    # Show state machine history
    print("\n--- State Transition History ---")
    transitions = coach.state_machine.get_recent_transitions(count=10)
    if transitions:
        for t in transitions:
            print(f"  {t.from_state.value} â†’ {t.to_state.value}")
            print(f"    Trigger: {t.trigger}")
            print(f"    Score: {t.burnout_score:.2f}")
            print()
    else:
        print("  No state transitions yet")
    
    # Show cognitive insights
    print("\n--- Cognitive Insights ---")
    insight = coach.get_current_cognitive_insight()
    if insight:
        print(f"  Block Type: {insight.block_type.value}")
        print(f"  Explanation: {insight.explanation}")
        print(f"  Reframing: {insight.reframing}")
        print(f"  Confidence: {insight.confidence:.2f}")
        print(f"  Intervention Recommended: {insight.intervention_recommended}")
    else:
        print("  No cognitive insights detected")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


def print_update(update):
    """Print a coaching update in a readable format."""
    print(f"  Timestamp: {update.timestamp.strftime('%H:%M:%S')}")
    print(f"  Coach State: {update.coach_state.value}")
    print(f"  Burnout Score: {update.burnout_score:.2f} ({update.burnout_level.value})")
    
    if update.active_signals:
        print(f"  Active Signals: {', '.join(s.value for s in update.active_signals)}")
    
    if update.cognitive_insight:
        print(f"  Cognitive Block: {update.cognitive_insight.block_type.value}")
    
    if update.detected_archetype:
        print(f"  Detected Archetype: {update.detected_archetype.value}")
    
    if update.intervention:
        print(f"  Intervention: {update.intervention.intervention_type.value}")
        print(f"    Message: \"{update.intervention.text}\"")
        print(f"    Mood: {update.intervention.mood.value}")
        print(f"    Delivered: {update.intervention_delivered}")
    
    if update.state_transition:
        print(f"  State Changed: {update.state_transition.from_state.value} â†’ {update.state_transition.to_state.value}")
    
    print()


def test_specific_signals():
    """Test specific signal detections."""
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC SIGNALS")
    print("=" * 60)
    print()
    
    coach = RealtimeCoach(user_id="test_user", enable_tts=False)
    
    # Test outdated patterns
    print("--- Testing Outdated Pattern Detection ---")
    coach.start_problem(problem_id=2001, tags=["implementation"])
    
    old_style_code = """
    #include <bits/stdc++.h>
    using namespace std;
    
    int arr[1000005];
    int n;
    
    int main() {
        scanf("%d", &n);
        for(int i = 0; i < n; i++) {
            scanf("%d", &arr[i]);
        }
        printf("%d\\n", n);
        return 0;
    }
    """
    
    coach.on_code_change(old_style_code, line_count=14)
    update = coach.update()
    
    if RealtimeSignal.OUTDATED_TEMPLATE_USAGE in update.active_signals:
        print("[OK] Detected outdated C-style patterns")
    
    if RealtimeSignal.GLOBAL_ARRAY_ABUSE in update.active_signals:
        print("[OK] Detected global array abuse")
    
    print_update(update)
    
    # Test data structure avoidance
    print("--- Testing Data Structure Avoidance ---")
    coach.start_problem(problem_id=2002, tags=["hash table"])
    
    no_ds_code = """
    def solve():
        n = int(input())
        arr = []
        for i in range(n):
            x = int(input())
            arr.append(x)
        
        # manually checking duplicates
        for i in range(len(arr)):
            for j in range(i+1, len(arr)):
                if arr[i] == arr[j]:
                    print("duplicate")
    """
    
    coach.on_code_change(no_ds_code, line_count=12)
    update = coach.update()
    
    if RealtimeSignal.NO_DS_USAGE in update.active_signals:
        print("[OK] Detected data structure avoidance")
    
    print_update(update)


if __name__ == "__main__":
    # Run the main simulation
    simulate_coding_session()
    
    # Run specific signal tests
    test_specific_signals()
    
    print("\n[TIP] Integrate this with your code editor using the RealtimeCoach class")
    print("   - Call on_typing() on every keystroke")
    print("   - Call on_code_change() periodically (every few seconds)")
    print("   - Call update() every 10-30 seconds")
    print("   - Listen to duck voice feedback!")

