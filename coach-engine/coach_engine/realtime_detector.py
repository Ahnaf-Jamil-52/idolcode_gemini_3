"""
Real-Time Problem Detection Module

Tracks live coding behavior to detect:
- Typing speed changes
- Idle time while editor is open
- Code rewrites and thrashing
- Early brute-force patterns
- Data structure avoidance
- Code length explosion
- Self-doubt markers

No full parsing needed - uses heuristics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Deque, Set
from collections import deque
from enum import Enum
import re


class RealtimeSignal(Enum):
    """Live signals detected during coding."""
    TYPING_SPEED_DROP = "typing_speed_drop"
    TYPING_SPEED_SPIKE = "typing_speed_spike"
    LONG_IDLE = "long_idle"
    REWRITE_SAME_BLOCK = "rewrite_same_block"
    EARLY_BRUTEFORCE_PATTERN = "early_bruteforce_pattern"
    NO_DS_USAGE = "no_ds_usage"
    CODE_LENGTH_EXPLOSION = "code_length_explosion"
    COMMENT_SELF_DOUBT = "comment_self_doubt"
    OUTDATED_TEMPLATE_USAGE = "outdated_template_usage"
    ALGORITHM_DELAY = "algorithm_delay"
    RAPID_BACKSPACE = "rapid_backspace"
    NESTED_LOOP_EARLY = "nested_loop_early"
    NO_FUNCTION_DECOMPOSITION = "no_function_decomposition"
    GLOBAL_ARRAY_ABUSE = "global_array_abuse"
    MANUAL_ALGO_REIMPLEMENTATION = "manual_algo_reimplementation"


@dataclass
class TypingEvent:
    """A keystroke or edit event."""
    timestamp: datetime
    line_number: int
    chars_added: int = 0
    chars_deleted: int = 0
    is_paste: bool = False


@dataclass
class CodeSnapshot:
    """Snapshot of code at a point in time."""
    timestamp: datetime
    line_count: int
    char_count: int
    content_hash: str  # Simple hash to detect rewrites
    detected_patterns: List[str] = field(default_factory=list)


@dataclass
class RealtimeDetection:
    """A detected real-time signal."""
    signal: RealtimeSignal
    timestamp: datetime
    severity: float  # 0.0 to 1.0
    context: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "signal": self.signal.value,
            "timestamp": self.timestamp.isoformat(),
            "severity": round(self.severity, 3),
            "context": self.context
        }


class RealtimeDetector:
    """
    Monitors live coding activity and detects behavioral signals.
    
    This is heuristic-based, not a full parser.
    """
    
    def __init__(self):
        # Typing tracking
        self.typing_events: Deque[TypingEvent] = deque(maxlen=100)
        self.typing_window_seconds = 60  # Track typing rate over 1 minute
        self.baseline_typing_speed: Optional[float] = None
        
        # Idle detection
        self.last_activity: Optional[datetime] = None
        self.idle_threshold_seconds = 30
        self.long_idle_threshold_seconds = 60
        
        # Code evolution tracking
        self.snapshots: Deque[CodeSnapshot] = deque(maxlen=20)
        self.rewrite_threshold = 3  # Same block edited 3+ times
        
        # Pattern detection state
        self.line_hashes: Dict[int, List[str]] = {}  # line_num -> [hashes]
        self.detected_signals: List[RealtimeDetection] = []
        
        # Problem context
        self.problem_start_time: Optional[datetime] = None
        self.problem_tags: List[str] = []
        
    def start_problem(self, tags: List[str]):
        """Called when user starts working on a problem."""
        self.problem_start_time = datetime.now()
        self.problem_tags = tags
        self.detected_signals.clear()
        self.typing_events.clear()
        self.snapshots.clear()
        self.line_hashes.clear()
        
    def record_typing(
        self, 
        line_number: int,
        chars_added: int = 0,
        chars_deleted: int = 0,
        is_paste: bool = False
    ):
        """Record a typing/edit event."""
        event = TypingEvent(
            timestamp=datetime.now(),
            line_number=line_number,
            chars_added=chars_added,
            chars_deleted=chars_deleted,
            is_paste=is_paste
        )
        self.typing_events.append(event)
        self.last_activity = datetime.now()
        
        # Check for typing speed changes
        self._check_typing_speed()
        
        # Check for rapid backspace (frustration indicator)
        if chars_deleted > chars_added and chars_deleted > 5:
            self._detect_rapid_backspace()
    
    def record_snapshot(self, code: str, line_count: int):
        """Record a snapshot of the current code."""
        snapshot = CodeSnapshot(
            timestamp=datetime.now(),
            line_count=line_count,
            char_count=len(code),
            content_hash=self._simple_hash(code),
            detected_patterns=[]  # Patterns are detected separately in _check_pattern_signals
        )
        self.snapshots.append(snapshot)
        
        # Run various detections
        self._check_code_rewrites()
        self._check_code_length_explosion()
        self._check_pattern_signals(code)
        
    def check_idle(self) -> Optional[RealtimeDetection]:
        """Check if user is idle (call this periodically)."""
        if not self.last_activity:
            return None
            
        idle_seconds = (datetime.now() - self.last_activity).total_seconds()
        
        if idle_seconds > self.long_idle_threshold_seconds:
            detection = RealtimeDetection(
                signal=RealtimeSignal.LONG_IDLE,
                timestamp=datetime.now(),
                severity=min(idle_seconds / 120.0, 1.0),  # Max at 2 minutes
                context={
                    "idle_seconds": int(idle_seconds),
                    "problem_time_elapsed": self._time_on_problem()
                }
            )
            self.detected_signals.append(detection)
            return detection
            
        return None
    
    def _check_typing_speed(self):
        """Detect typing speed changes."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.typing_window_seconds)
        
        # Get recent events
        recent = [e for e in self.typing_events if e.timestamp > cutoff]
        if len(recent) < 5:
            return
        
        # Calculate characters per minute
        total_chars = sum(e.chars_added for e in recent)
        time_span = (recent[-1].timestamp - recent[0].timestamp).total_seconds()
        if time_span == 0:
            return
            
        current_cpm = (total_chars / time_span) * 60
        
        # Establish baseline
        if self.baseline_typing_speed is None:
            self.baseline_typing_speed = current_cpm
            return
        
        # Check for significant drop (50% or more)
        if current_cpm < self.baseline_typing_speed * 0.5:
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.TYPING_SPEED_DROP,
                timestamp=now,
                severity=1.0 - (current_cpm / self.baseline_typing_speed),
                context={
                    "current_cpm": round(current_cpm),
                    "baseline_cpm": round(self.baseline_typing_speed),
                    "drop_percentage": round((1 - current_cpm / self.baseline_typing_speed) * 100)
                }
            ))
        
        # Check for spike (2x or more - panic mode)
        elif current_cpm > self.baseline_typing_speed * 2.0:
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.TYPING_SPEED_SPIKE,
                timestamp=now,
                severity=min((current_cpm / self.baseline_typing_speed) - 1.0, 1.0),
                context={
                    "current_cpm": round(current_cpm),
                    "baseline_cpm": round(self.baseline_typing_speed)
                }
            ))
    
    def _detect_rapid_backspace(self):
        """Detect rapid deletion (frustration)."""
        recent = list(self.typing_events)[-5:]
        deletions = sum(e.chars_deleted for e in recent)
        
        if deletions > 20:  # Deleted 20+ chars in last 5 events
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.RAPID_BACKSPACE,
                timestamp=datetime.now(),
                severity=min(deletions / 50.0, 1.0),
                context={"chars_deleted": deletions}
            ))
    
    def _check_code_rewrites(self):
        """Detect if same code block is being rewritten multiple times."""
        if len(self.snapshots) < 3:
            return
        
        recent = list(self.snapshots)[-5:]
        hashes = [s.content_hash for s in recent]
        
        # Check for oscillation (same hash appearing multiple times)
        from collections import Counter
        hash_counts = Counter(hashes)
        max_count = max(hash_counts.values())
        
        if max_count >= self.rewrite_threshold:
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.REWRITE_SAME_BLOCK,
                timestamp=datetime.now(),
                severity=min(max_count / 5.0, 1.0),
                context={"rewrite_count": max_count}
            ))
    
    def _check_code_length_explosion(self):
        """Detect if code is growing too fast (overengineering)."""
        if len(self.snapshots) < 3:
            return
        
        recent = list(self.snapshots)[-3:]
        line_growth = recent[-1].line_count - recent[0].line_count
        time_span = (recent[-1].timestamp - recent[0].timestamp).total_seconds() / 60
        
        if time_span > 0 and line_growth > 20:
            growth_rate = line_growth / time_span  # Lines per minute
            
            if growth_rate > 10:  # More than 10 lines/minute
                self.detected_signals.append(RealtimeDetection(
                    signal=RealtimeSignal.CODE_LENGTH_EXPLOSION,
                    timestamp=datetime.now(),
                    severity=min(growth_rate / 20.0, 1.0),
                    context={
                        "lines_added": line_growth,
                        "growth_rate_lpm": round(growth_rate, 1)
                    }
                ))
    
    def _check_pattern_signals(self, code: str):
        """Detect various coding patterns."""
        lines = code.split('\n')
        now = datetime.now()
        
        # Check for self-doubt comments
        doubt_patterns = [
            r'//\s*(idk|don\'t know|not sure|hack|temp|fix|wrong)',
            r'#\s*(idk|don\'t know|not sure|hack|temp|fix|wrong)',
        ]
        for pattern in doubt_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                self.detected_signals.append(RealtimeDetection(
                    signal=RealtimeSignal.COMMENT_SELF_DOUBT,
                    timestamp=now,
                    severity=0.6,
                    context={"pattern": pattern}
                ))
                break
        
        # Check for outdated patterns
        if self._has_outdated_patterns(code):
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.OUTDATED_TEMPLATE_USAGE,
                timestamp=now,
                severity=0.7,
                context={}
            ))
        
        # Check for early nested loops (brute force indicator)
        minutes_elapsed = self._time_on_problem()
        if minutes_elapsed < 2:
            nested_loops = self._count_nested_loops(code)
            if nested_loops >= 2:
                self.detected_signals.append(RealtimeDetection(
                    signal=RealtimeSignal.EARLY_BRUTEFORCE_PATTERN,
                    timestamp=now,
                    severity=0.8,
                    context={"nested_depth": nested_loops}
                ))
        
        # Check for data structure avoidance
        if len(lines) > 15 and not self._uses_modern_ds(code):
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.NO_DS_USAGE,
                timestamp=now,
                severity=0.6,
                context={"line_count": len(lines)}
            ))
        
        # Check for algorithm avoidance on tagged problems
        if minutes_elapsed > 5:
            if "dp" in self.problem_tags and not self._has_dp_structure(code):
                self.detected_signals.append(RealtimeDetection(
                    signal=RealtimeSignal.ALGORITHM_DELAY,
                    timestamp=now,
                    severity=0.7,
                    context={"expected_algo": "dynamic programming"}
                ))
        
        # Check for global array abuse
        if self._has_global_array_abuse(code):
            self.detected_signals.append(RealtimeDetection(
                signal=RealtimeSignal.GLOBAL_ARRAY_ABUSE,
                timestamp=now,
                severity=0.5,
                context={}
            ))
    
    def _has_outdated_patterns(self, code: str) -> bool:
        """Detect C-style patterns in C++/modern code."""
        patterns = [
            r'\bscanf\s*\(',
            r'\bprintf\s*\(',
            r'^\s*int\s+[a-z_]+\s*\[\s*\d{5,}\s*\]',  # Large global arrays
            r'#define\s+(ll|LL)\s+long\s+long',
        ]
        return any(re.search(p, code, re.MULTILINE) for p in patterns)
    
    def _count_nested_loops(self, code: str) -> int:
        """Count maximum loop nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            stripped = line.strip()
            if re.match(r'for\s*\(|while\s*\(', stripped):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif stripped == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _uses_modern_ds(self, code: str) -> bool:
        """Check if code uses modern data structures."""
        modern_ds = [
            r'\bmap\b', r'\bset\b', r'\bvector\b',
            r'\bunordered_map\b', r'\bunordered_set\b',
            r'\bdeque\b', r'\bpriority_queue\b',
            r'\bdict\b', r'\blist\b',  # Python
        ]
        return any(re.search(ds, code) for ds in modern_ds)
    
    def _has_dp_structure(self, code: str) -> bool:
        """Check if code has DP-like structure."""
        indicators = [
            r'\bdp\[',
            r'\bmemo\[',
            r'@lru_cache',
            r'\bmemoization\b',
        ]
        return any(re.search(ind, code, re.IGNORECASE) for ind in indicators)
    
    def _has_global_array_abuse(self, code: str) -> bool:
        """Check for massive global arrays (C++ bad practice)."""
        pattern = r'^\s*int\s+[a-z_]+\s*\[\s*\d{5,}\s*\]'
        return bool(re.search(pattern, code, re.MULTILINE))
    
    def _simple_hash(self, code: str) -> str:
        """Simple hash for code comparison."""
        # Normalize whitespace and hash
        normalized = re.sub(r'\s+', ' ', code.strip())
        return str(hash(normalized))
    
    def _time_on_problem(self) -> float:
        """Minutes spent on current problem."""
        if not self.problem_start_time:
            return 0.0
        return (datetime.now() - self.problem_start_time).total_seconds() / 60
    
    def get_recent_signals(
        self, 
        minutes: int = 5,
        min_severity: float = 0.5
    ) -> List[RealtimeDetection]:
        """Get recent high-severity signals."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            d for d in self.detected_signals
            if d.timestamp > cutoff and d.severity >= min_severity
        ]
    
    def get_active_signals(self) -> Set[RealtimeSignal]:
        """Get currently active signal types (last 2 minutes)."""
        recent = self.get_recent_signals(minutes=2)
        return {d.signal for d in recent}
