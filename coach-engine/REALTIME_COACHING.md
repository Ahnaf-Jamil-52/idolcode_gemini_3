# Real-Time Coaching System

## Overview

The Real-Time Coaching System provides live, intelligent feedback while coders work on problems. It detects behavioral signals in real-time and delivers context-aware coaching through text-to-speech.

## Features

### 1. **Real-Time Problem Detection** 
Monitors coding behavior and detects:
- **Typing Speed Changes**: Cognitive overload or panic mode
- **Long Idle Time**: Being stuck without asking for help
- **Code Rewrites**: Local confusion, rewriting same blocks repeatedly
- **Early Brute Force**: Jumping to nested loops before thinking
- **Data Structure Avoidance**: Using arrays when maps/sets would help
- **Code Explosion**: Line count growing too fast (overengineering)
- **Self-Doubt Markers**: Comments like "// idk", "// hack"
- **Outdated Patterns**: Old C-style templates, global arrays
- **Algorithm Delays**: Not using expected algorithms (DP, etc.)

### 2. **Duck TTS Voice**
- **Offline TTS** using pyttsx3 (no API calls needed)
- **Mood-Based Voice**: Gentle, warning, protective, encouraging
- **Non-Intrusive**: Cooldown periods prevent nagging
- **Context-Aware Phrases**: Different messages for different situations

### 3. **Enhanced State Machine**
Seven coaching states with smooth transitions:
- **SILENT**: Duck is completely quiet, observing only
- **NORMAL**: Normal operation, passive monitoring
- **WATCHING**: Attentive monitoring, no intervention yet
- **HINTING**: Gentle hints via questions (Socratic method)
- **WARNING**: Clear warnings, suggest stepping back
- **PROTECTIVE**: Active rest suggestions, burnout prevention
- **RECOVERY**: Encouraging feedback during recovery

### 4. **Live Cognitive Mirror**
Real-time inference of cognitive blocks:
- **Constraint Blindness**: Missing key problem constraints
- **Algorithm Gap**: Lacking needed algorithmic knowledge
- **Greedy Illusion**: Thinking greedy works when it doesn't
- **State Space Explosion**: Tracking too many variables
- **Confidence Crisis**: Doubting correct intuitions
- **Implementation Paralysis**: Know idea but can't code it

### 5. **Intelligent Intervention Selector**
Decides what to say and when:
- **One intervention per state** (no nagging)
- **Priority-based selection**: Burnout > Real-time signals > Archetypes
- **Cooldown management**: State-specific minimum intervals
- **Context consideration**: Consults all layers before speaking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   RealtimeCoach                         │
│                   (Orchestrator)                        │
└──────────┬──────────────────────────────────────┬───────┘
           │                                      │
    ┌──────▼──────┐                        ┌─────▼──────┐
    │  Realtime   │                        │   State    │
    │  Detector   │                        │  Machine   │
    └──────┬──────┘                        └─────┬──────┘
           │                                      │
    ┌──────▼──────────────┐              ┌───────▼────────┐
    │  Live Cognitive     │              │ Intervention   │
    │     Mirror          │              │   Selector     │
    └──────┬──────────────┘              └───────┬────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          │
                   ┌──────▼──────┐
                   │  Duck TTS   │
                   │   (Voice)   │
                   └─────────────┘
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required: pyttsx3 for TTS
pip install pyttsx3
```

## Quick Start

```python
from coach_engine.realtime_coach import RealtimeCoach

# Initialize coach
coach = RealtimeCoach(
    user_id="user123",
    enable_tts=True,
    enable_interventions=True
)

# Start a problem
coach.start_problem(
    problem_id=1001,
    tags=["dp", "dynamic programming"],
    difficulty=1500
)

# In your editor integration:

# On every keystroke
coach.on_typing(
    line_number=10,
    chars_added=5,
    chars_deleted=0
)

# On code change (every few seconds)
coach.on_code_change(
    code=current_code,
    line_count=len(lines)
)

# Periodic update (every 10-30 seconds)
update = coach.update()

# Check what happened
if update.intervention:
    print(f"Coach says: {update.intervention.text}")
    print(f"State: {update.coach_state.value}")
```

## Editor Integration

### VS Code Extension Example

```javascript
// Track typing
editor.onDidChangeTextDocument((event) => {
    const change = event.contentChanges[0];
    coach.onTyping(
        change.range.start.line,
        change.text.length,
        change.rangeLength
    );
});

// Periodic snapshot
setInterval(() => {
    const code = editor.document.getText();
    const lineCount = editor.document.lineCount;
    coach.onCodeChange(code, lineCount);
}, 3000);

// Update coach state
setInterval(() => {
    const update = coach.update();
    
    if (update.intervention) {
        // Show notification or let duck speak
        showNotification(update.intervention.text);
    }
}, 15000);
```

## Examples

### Example 1: Detecting Burnout

```python
coach = RealtimeCoach(user_id="user1", enable_tts=True)
coach.start_problem(1001, ["implementation"])

# Simulate failures
for i in range(5):
    coach.on_problem_submit(success=False)
    coach.on_ghost_race_result(won=False)
    update = coach.update()
    
    if update.coach_state == CoachState.PROTECTIVE:
        # Duck says: "You're burning out. This is a good place to stop."
        break
```

### Example 2: Detecting Code Patterns

```python
# User writes old C-style code
old_code = """
#include <bits/stdc++.h>
int arr[100005];
int main() {
    scanf("%d", &n);
    // ...
}
"""

coach.on_code_change(old_code, 6)
update = coach.update()

if RealtimeSignal.OUTDATED_TEMPLATE_USAGE in update.active_signals:
    # Duck might say: "This template is slowing you. Want to reset clean?"
    pass
```

### Example 3: Detecting Stuck State

```python
# User is idle for 45 seconds
import time
time.sleep(45)

update = coach.update()

if RealtimeSignal.LONG_IDLE in update.active_signals:
    # Duck might say: "You seem stuck. Want to talk through the approach?"
    pass
```

## Configuration

### Adjusting Detection Sensitivity

```python
# In realtime_detector.py
detector = RealtimeDetector()

# Adjust thresholds
detector.idle_threshold_seconds = 20  # Default: 30
detector.long_idle_threshold_seconds = 40  # Default: 60
detector.rewrite_threshold = 4  # Default: 3
```

### Adjusting State Transitions

```python
# In states.py
state_machine = CoachStateMachine()

# Adjust thresholds
state_machine.THRESHOLDS["score_to_hinting"] = 0.35  # Default: 0.40
state_machine.THRESHOLDS["realtime_signal_threshold"] = 3  # Default: 2
```

### Customizing Duck Phrases

```python
from coach_engine.duck_tts import DuckPhrases

# Add your own phrases
DuckPhrases.TYPING_SLOW.append("Take your time. Quality over speed.")
DuckPhrases.EARLY_BRUTEFORCE.append("What if we think smarter, not harder?")
```

### Disabling TTS (Text-Only Mode)

```python
coach = RealtimeCoach(
    user_id="user1",
    enable_tts=False,  # No voice
    enable_interventions=True  # Still get text interventions
)
```

## Running the Demo

```bash
# Run the comprehensive demo
python examples/realtime_coach_demo.py

# This will simulate:
# - Normal typing
# - Getting stuck (idle)
# - Rewriting code multiple times
# - Early brute force patterns
# - Panic typing
# - Self-doubt comments
# - State transitions
```

## API Reference

### RealtimeCoach

Main orchestrator class.

**Methods:**
- `start_problem(problem_id, tags, difficulty)` - Start tracking a new problem
- `on_typing(line_number, chars_added, chars_deleted, is_paste)` - Record typing event
- `on_code_change(code, line_count)` - Record code snapshot
- `update()` - Main update loop, returns CoachingUpdate
- `on_problem_submit(success)` - Record problem submission
- `on_ghost_race_result(won)` - Record ghost race result
- `get_current_state()` - Get current coach state
- `enable_voice(enabled)` - Enable/disable TTS
- `enable_coaching(enabled)` - Enable/disable interventions

### RealtimeDetector

Detects live coding signals.

**Signals Detected:**
- TYPING_SPEED_DROP
- TYPING_SPEED_SPIKE
- LONG_IDLE
- REWRITE_SAME_BLOCK
- EARLY_BRUTEFORCE_PATTERN
- NO_DS_USAGE
- CODE_LENGTH_EXPLOSION
- COMMENT_SELF_DOUBT
- OUTDATED_TEMPLATE_USAGE
- ALGORITHM_DELAY
- (and more...)

### InterventionSelector

Decides when and what to say.

**Intervention Types:**
- HINT - Gentle suggestions
- QUESTION - Socratic questions
- REFRAME - Different perspective
- WARNING - Clear warnings
- REST_SUGGESTION - Break recommendations
- ENCOURAGEMENT - Positive feedback
- MODERNIZATION - Update old patterns
- ALGORITHM_NUDGE - Algo suggestions
- SLOW_DOWN - Pace reduction
- STEP_BACK - Reset thinking

### DuckVoice

Text-to-speech system.

**Voice Moods:**
- NEUTRAL - Balanced tone
- GENTLE - Soft, supportive
- CALM - Slowing pace
- WARNING - Clear concern
- PROTECTIVE - Strong care
- ENCOURAGING - Uplifting
- URGENT - Important message

## Integration with Existing Systems

The real-time coaching system integrates seamlessly with existing coach engine layers:

1. **Burnout Scorer**: Real-time signals feed into burnout calculation
2. **Failure Archetypes**: Live detection triggers archetype-based interventions
3. **Cognitive Mirror**: Extends to real-time cognitive block inference
4. **State Machine**: Enhanced with SILENT and HINTING states
5. **Responses**: TTS delivers response messages with appropriate mood

## Performance Considerations

- **Typing tracking**: Negligible overhead (~0.1ms per event)
- **Code snapshots**: Light regex patterns, no full parsing
- **Update frequency**: Recommended every 10-30 seconds
- **TTS latency**: ~200ms for voice synthesis (background thread)
- **Memory**: Code snapshots kept in deque (max 20)

## Best Practices

1. **Call `update()` regularly** but not too frequently (10-30 seconds is ideal)
2. **Track typing accurately** - more data = better detection
3. **Start problems correctly** - tags enable better algorithm detection
4. **Respect cooldowns** - avoid overwhelming users with interventions
5. **Test without TTS first** - use text-only mode for debugging
6. **Adjust thresholds** - tune for your user population

## Troubleshooting

### TTS Not Working

```python
# Check if pyttsx3 is installed
try:
    import pyttsx3
    print("pyttsx3 installed")
except ImportError:
    print("Install with: pip install pyttsx3")

# Test TTS directly
from coach_engine.duck_tts import duck_speak
duck_speak("Testing", VoiceMood.NEUTRAL)
```

### Interventions Not Triggering

```python
# Check state and signals
update = coach.update()
print(f"State: {update.coach_state}")
print(f"Signals: {update.active_signals}")
print(f"Interventions in state: {coach.intervention_selector.interventions_per_state}")

# Check if cooldown
from datetime import datetime, timedelta
last_time = coach.intervention_selector.last_intervention_per_state.get(update.coach_state)
if last_time:
    elapsed = datetime.now() - last_time
    print(f"Time since last intervention: {elapsed.total_seconds()}s")
```

### Signals Not Detected

```python
# Check detector state
detector = coach.realtime_detector
print(f"Typing events: {len(detector.typing_events)}")
print(f"Snapshots: {len(detector.snapshots)}")
print(f"Last activity: {detector.last_activity}")

# Check detected signals
recent = detector.get_recent_signals(minutes=10)
for sig in recent:
    print(f"{sig.signal.value}: severity={sig.severity}, context={sig.context}")
```

## Future Enhancements

- Code AST analysis for deeper pattern detection
- Machine learning for personalized thresholds
- Multi-language support for non-English coders
- Integration with problem submission feedback
- Historical pattern learning per user
- Team coaching for collaborative coding

## Contributing

Contributions welcome! Key areas:
- More detection heuristics
- Better phrase library
- Additional voice moods
- Editor integrations
- Performance optimizations

## License

Same as parent coach-engine project.

---

**Made with 🦆 by the Coach Engine Team**
