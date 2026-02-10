"""
Duck TTS - Text-to-Speech Voice Module

Uses pyttsx3 for offline, low-latency text-to-speech.
The Duck speaks with context-aware tone and pacing.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum
import threading
import queue

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("pyttsx3 not installed. TTS will be disabled.")


class VoiceMood(Enum):
    """Duck's speaking mood/tone."""
    NEUTRAL = "neutral"
    ENCOURAGING = "encouraging"
    WARNING = "warning"
    PROTECTIVE = "protective"
    GENTLE = "gentle"
    CALM = "calm"
    URGENT = "urgent"


@dataclass
class VoiceSettings:
    """Settings for a specific voice mood."""
    rate: int           # Words per minute
    volume: float       # 0.0 to 1.0
    pitch: Optional[int] = None  # Some engines support pitch


MOOD_SETTINGS: Dict[VoiceMood, VoiceSettings] = {
    VoiceMood.NEUTRAL: VoiceSettings(rate=165, volume=0.9),
    VoiceMood.ENCOURAGING: VoiceSettings(rate=175, volume=0.95),
    VoiceMood.WARNING: VoiceSettings(rate=155, volume=0.95),
    VoiceMood.PROTECTIVE: VoiceSettings(rate=150, volume=0.9),
    VoiceMood.GENTLE: VoiceSettings(rate=160, volume=0.85),
    VoiceMood.CALM: VoiceSettings(rate=150, volume=0.85),
    VoiceMood.URGENT: VoiceSettings(rate=180, volume=1.0),
}


@dataclass
class SpeechRequest:
    """A request to speak."""
    text: str
    mood: VoiceMood
    timestamp: datetime
    priority: int = 0  # Higher = more important


class DuckVoice:
    """
    The Duck's voice system.
    
    Manages TTS with mood-based voice modulation.
    Non-blocking: speaks in background thread.
    """
    
    def __init__(
        self, 
        enabled: bool = True,
        cooldown_seconds: int = 10  # Minimum time between speeches
    ):
        self.enabled = enabled and TTS_AVAILABLE
        self.cooldown_seconds = cooldown_seconds
        self.last_speech_time: Optional[datetime] = None
        
        # Speech queue
        self.speech_queue: queue.Queue = queue.Queue()
        self.is_speaking = False
        
        # Initialize engine
        self.engine: Optional[pyttsx3.Engine] = None
        if self.enabled:
            try:
                self.engine = pyttsx3.init()
                # Set a pleasant default voice (prefer female voice if available)
                voices = self.engine.getProperty('voices')
                if len(voices) > 1:
                    # Try to find a female voice
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.engine.setProperty('voice', voice.id)
                            break
            except Exception as e:
                print(f"Failed to initialize TTS engine: {e}")
                self.enabled = False
        
        # Start speech worker thread
        if self.enabled:
            self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.worker_thread.start()
    
    def speak(
        self, 
        text: str, 
        mood: VoiceMood = VoiceMood.NEUTRAL,
        priority: int = 0,
        force: bool = False
    ) -> bool:
        """
        Queue text to be spoken.
        
        Args:
            text: Text to speak
            mood: Voice mood/tone
            priority: Higher priority speaks first
            force: Bypass cooldown
        
        Returns:
            True if queued, False if rejected (cooldown/disabled)
        """
        if not self.enabled:
            return False
        
        # Check cooldown
        if not force and self.last_speech_time:
            elapsed = (datetime.now() - self.last_speech_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
        
        # Queue the speech
        request = SpeechRequest(
            text=text,
            mood=mood,
            timestamp=datetime.now(),
            priority=priority
        )
        self.speech_queue.put(request)
        return True
    
    def speak_immediate(
        self, 
        text: str, 
        mood: VoiceMood = VoiceMood.URGENT
    ):
        """Speak immediately, interrupting current speech if needed."""
        if not self.enabled:
            return
        
        # Clear queue and speak
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        self.speak(text, mood, priority=999, force=True)
    
    def _speech_worker(self):
        """Background worker that processes speech queue."""
        while True:
            try:
                request = self.speech_queue.get(timeout=1.0)
                self._do_speak(request)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Speech error: {e}")
    
    def _do_speak(self, request: SpeechRequest):
        """Actually speak the text."""
        if not self.engine:
            return
        
        self.is_speaking = True
        
        try:
            # Apply mood settings
            settings = MOOD_SETTINGS[request.mood]
            self.engine.setProperty('rate', settings.rate)
            self.engine.setProperty('volume', settings.volume)
            
            # Speak
            self.engine.say(request.text)
            self.engine.runAndWait()
            
            self.last_speech_time = datetime.now()
            
        except Exception as e:
            print(f"Error speaking: {e}")
        finally:
            self.is_speaking = False
    
    def stop(self):
        """Stop current speech."""
        if self.engine and self.is_speaking:
            try:
                self.engine.stop()
            except:
                pass
    
    def set_enabled(self, enabled: bool):
        """Enable or disable TTS."""
        self.enabled = enabled and TTS_AVAILABLE
    
    def can_speak_now(self) -> bool:
        """Check if duck is ready to speak (not in cooldown)."""
        if not self.enabled or self.is_speaking:
            return False
        
        if not self.last_speech_time:
            return True
        
        elapsed = (datetime.now() - self.last_speech_time).total_seconds()
        return elapsed >= self.cooldown_seconds


class DuckPhrases:
    """
    Library of Duck's coaching phrases organized by context.
    
    These are carefully crafted to be:
    - Non-judgmental
    - Actionable
    - Brief
    - Socratic (questions > commands)
    """
    
    # Typing behavior
    TYPING_SLOW = [
        "Pause for a second. What's the constraint really asking?",
        "You seem stuck. Want to talk through the approach?",
        "Let's step back. What property stays true here?",
    ]
    
    TYPING_FAST = [
        "You're rushing. This problem rewards structure, not speed.",
        "Slow down. What's the invariant you're maintaining?",
        "Take a breath. Speed comes from clarity, not hurry.",
    ]
    
    # Code patterns
    EARLY_BRUTEFORCE = [
        "You're jumping to brute force. What structure could simplify this?",
        "Before nested loops, what makes this case different from that case?",
        "Pause. Is there a property you can exploit?",
    ]
    
    REWRITING_CODE = [
        "You're repeating the same idea. Let's step back.",
        "Third time on this block. What assumption needs to change?",
        "Stop. Write down what you know is true first.",
    ]
    
    CODE_EXPLOSION = [
        "This is growing fast. What's the simplest invariant?",
        "Simpler is better. What's the core idea in one sentence?",
        "You're overengineering. What's the minimal structure?",
    ]
    
    # Algorithm avoidance
    DP_AVOIDANCE = [
        "You've been avoiding DP today. Want a smaller state?",
        "This has overlapping subproblems. See it?",
        "What if you remembered what you already computed?",
    ]
    
    ALGO_AVOIDANCE = [
        "A standard algorithm could help here.",
        "This pattern has a well-known solution. Ring a bell?",
        "What tool from your toolkit fits this shape?",
    ]
    
    # Outdated patterns
    OUTDATED_TEMPLATE = [
        "This template is slowing you. Want to reset clean?",
        "That's old style. Modern tools make this easier.",
        "Let's update your approach. There's a cleaner way.",
    ]
    
    NO_DATA_STRUCTURES = [
        "A map or set could simplify this logic.",
        "You're doing this the hard way. What structure fits?",
        "Memory is cheap, clarity is cheaper.",
    ]
    
    # Burnout protection
    BURNOUT_WARNING = [
        "You've pushed hard today. Take a ten-minute break.",
        "Your ghost race score is dropping. Time to rest.",
        "Quality over quantity. Rest now, solve better later.",
    ]
    
    BURNOUT_PROTECTIVE = [
        "You're burning out. This is a good place to stop.",
        "Your brain needs recovery. Come back tomorrow.",
        "You've done enough today. Real improvement needs rest.",
    ]
    
    # Encouragement
    BREAKTHROUGH = [
        "Nice! That's the insight.",
        "There it is. Build on that.",
        "Good catch. Keep going.",
    ]
    
    PROGRESS = [
        "You're improving. This is the right direction.",
        "Better. Trust the process.",
        "Growth happening. Keep at it.",
    ]
    
    @classmethod
    def get_phrase(cls, category: str, context: Optional[Dict] = None) -> Optional[str]:
        """Get a phrase from a category."""
        import random
        
        category_map = {
            "typing_slow": cls.TYPING_SLOW,
            "typing_fast": cls.TYPING_FAST,
            "early_bruteforce": cls.EARLY_BRUTEFORCE,
            "rewriting_code": cls.REWRITING_CODE,
            "code_explosion": cls.CODE_EXPLOSION,
            "dp_avoidance": cls.DP_AVOIDANCE,
            "algo_avoidance": cls.ALGO_AVOIDANCE,
            "outdated_template": cls.OUTDATED_TEMPLATE,
            "no_data_structures": cls.NO_DATA_STRUCTURES,
            "burnout_warning": cls.BURNOUT_WARNING,
            "burnout_protective": cls.BURNOUT_PROTECTIVE,
            "breakthrough": cls.BREAKTHROUGH,
            "progress": cls.PROGRESS,
        }
        
        phrases = category_map.get(category, [])
        if not phrases:
            return None
        
        return random.choice(phrases)


# Global instance (singleton pattern)
_duck_voice_instance: Optional[DuckVoice] = None


def get_duck_voice(enabled: bool = True) -> DuckVoice:
    """Get or create the global Duck voice instance."""
    global _duck_voice_instance
    if _duck_voice_instance is None:
        _duck_voice_instance = DuckVoice(enabled=enabled)
    return _duck_voice_instance


def duck_speak(
    text: str, 
    mood: VoiceMood = VoiceMood.NEUTRAL,
    priority: int = 0
) -> bool:
    """Convenience function to make the duck speak."""
    duck = get_duck_voice()
    return duck.speak(text, mood, priority)
