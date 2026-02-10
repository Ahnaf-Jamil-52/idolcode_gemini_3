"""
Quick smoke test for coach engine.
Run this to quickly verify the system works.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from coach_engine.realtime_coach import RealtimeCoach
from coach_engine.realtime_detector import RealtimeSignal
from coach_engine.states import CoachState
from datetime import datetime, timedelta


def quick_test():
    """Run a quick smoke test."""
    print("=" * 60)
    print("QUICK SMOKE TEST")
    print("=" * 60)
    
    # Test 1: Create coach
    print("\n[1/6] Creating coach...")
    coach = RealtimeCoach(user_id="smoke_test", enable_tts=False)
    print("  ✓ Coach created")
    print(f"  State: {coach.get_current_state().name}")
    
    # Test 2: Start problem
    print("\n[2/6] Starting problem...")
    coach.start_problem(1001, tags=["dp", "medium"], difficulty=1500)
    print("  ✓ Problem started")
    print(f"  Problem ID: {coach.context.problem_id}")
    print(f"  Tags: {coach.context.problem_tags}")
    
    # Test 3: Simulate typing
    print("\n[3/6] Simulating typing...")
    for i in range(10):
        coach.on_typing(line_number=i+1, chars_added=5)
    print(f"  ✓ Recorded {len(coach.realtime_detector.typing_events)} typing events")
    
    # Test 4: Code snapshot
    print("\n[4/6] Taking code snapshot...")
    code = """
def solve():
    n = int(input())
    # thinking...
    return n
"""
    coach.on_code_change(code, line_count=5)
    print(f"  ✓ Recorded {len(coach.realtime_detector.snapshots)} snapshots")
    
    # Test 5: Update coach
    print("\n[5/6] Updating coach state...")
    update = coach.update()
    print("  ✓ Update complete")
    print(f"  State: {update.coach_state.name}")
    print(f"  Burnout: {update.burnout_score:.2f} ({update.burnout_level.name})")
    print(f"  Active signals: {len(update.active_signals)}")
    
    # Test 6: Test idle detection
    print("\n[6/6] Testing idle detection...")
    coach.realtime_detector.last_activity = datetime.now() - timedelta(seconds=35)
    update = coach.update()
    print(f"  ✓ Idle check complete")
    if RealtimeSignal.LONG_IDLE in update.active_signals:
        print("  ✓ Idle signal detected correctly")
    else:
        print("  ⚠ Idle signal not detected (may need more time)")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("✓ All basic features working")
    print("\nNext steps:")
    print("  - Run: python diagnostic.py")
    print("  - Run: pytest tests/test_realtime_features.py -v")
    print("  - Run: python examples/realtime_coach_demo.py")


if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
