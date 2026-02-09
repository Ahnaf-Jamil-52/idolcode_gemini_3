"""
Sentiment Analysis Module

Hybrid NLP approach:
1. Keyword + Pattern Matching (instant, free)
2. Optional: Local lightweight model (50ms, free)
3. Optional: LLM API call (300ms, paid, most accurate)

Analyzes chat messages, code comments, and search queries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re


class EmotionalState(Enum):
    """Detected emotional states."""
    FRUSTRATED = "frustrated"      # Struggling, angry
    DISCOURAGED = "discouraged"    # Losing confidence, comparing to others
    FATIGUED = "fatigued"          # Tired, disengaged, going through motions
    NEUTRAL = "neutral"            # Task-focused, no strong emotion
    MOTIVATED = "motivated"        # Engaged, curious, determined
    CELEBRATING = "celebrating"    # Just solved something, feeling good
    MASKED = "masked"              # Says positive but context suggests otherwise


class PatternCategory(Enum):
    """Categories of text patterns."""
    FRUSTRATION = "frustration"
    GIVING_UP = "giving_up"
    SELF_DOUBT = "self_doubt"
    FATIGUE = "fatigue"
    CONFIDENCE = "confidence"
    JOY = "joy"
    GROWTH = "growth"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    state: EmotionalState
    intensity: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    matched_patterns: List[Tuple[PatternCategory, str]]
    analysis_method: str  # "keyword", "local_model", "llm"
    is_masked: bool
    raw_text: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "state": self.state.value,
            "intensity": round(self.intensity, 3),
            "confidence": round(self.confidence, 3),
            "matched_patterns": [
                {"category": p[0].value, "pattern": p[1]} 
                for p in self.matched_patterns
            ],
            "analysis_method": self.analysis_method,
            "is_masked": self.is_masked,
            "timestamp": self.timestamp.isoformat(),
        }


# Pattern definitions for keyword matching
NEGATIVE_PATTERNS: Dict[PatternCategory, List[str]] = {
    PatternCategory.FRUSTRATION: [
        r"\bstuck\b", r"\bwtf\b", r"\bimpossible\b", r"\bhate\b", 
        r"\bstupid\b", r"\bbroken\b", r"\bconfusing\b", r"\bwhy\s+won'?t\b",
        r"\bdoesn'?t\s+work\b", r"\bwhat\s+the\b", r"\bso\s+hard\b",
        r"\bfrustrat", r"\bannoy", r"\bidk\b", r"\bugh\b",
    ],
    PatternCategory.GIVING_UP: [
        r"\bquit\b", r"\bdone\b", r"\blast\s+try\b", r"\bgive\s+up\b",
        r"\bcan'?t\s+do\s+this\b", r"\btoo\s+hard\b", r"\bforget\s+it\b",
        r"\bgive\s+up\b", r"\bno\s+point\b", r"\bnever\s+gonna\b",
        r"\bwaste\s+of\s+time\b", r"\bi'?m\s+out\b",
    ],
    PatternCategory.SELF_DOUBT: [
        r"\bi\s+suck\b", r"\bnot\s+smart\s+enough\b", r"\beveryone\s+else\b",
        r"\bnever\s+learn\b", r"\bdumb\b", r"\bstupid\s+me\b",
        r"\bi'?m\s+bad\b", r"\bcan'?t\s+understand\b", r"\btoo\s+dumb\b",
        r"\bnot\s+cut\s+out\b", r"\bwhat'?s\s+wrong\s+with\s+me\b",
    ],
    PatternCategory.FATIGUE: [
        r"\btired\b", r"\bexhausted\b", r"\bbored\b", r"\bwhatever\b",
        r"\bdon'?t\s+care\b", r"\bsleepy\b", r"\bzoned\s+out\b",
        r"\bbleh\b", r"\bmeh\b", r"\bover\s+it\b", r"\benough\b",
    ],
}

POSITIVE_PATTERNS: Dict[PatternCategory, List[str]] = {
    PatternCategory.CONFIDENCE: [
        r"\bgot\s+it\b", r"\bfigured\s+(it\s+)?out\b", r"\bmakes\s+sense\b",
        r"\bfinally\b", r"\bclicked\b", r"\bsee\s+it\s+now\b",
        r"\bi\s+understand\b", r"\beasy\b", r"\bsimple\b",
    ],
    PatternCategory.JOY: [
        r"\blove\s+this\b", r"\bawesome\b", r"\bcool\b", r"\bamazing\b",
        r"\bfun\b", r"\bnice\b", r"\byay\b", r"\byes\b", r"\blet'?s\s+go\b",
        r"\bwoohoo\b", r"\bhell\s+yeah\b",
    ],
    PatternCategory.GROWTH: [
        r"\blearned\b", r"\bunderstand\s+now\b", r"\bsee\s+the\s+pattern\b",
        r"\bimproved\b", r"\bgetting\s+better\b", r"\bprogress\b",
        r"\blevel\s+up\b", r"\bnew\s+concept\b",
    ],
}

# Masking detection patterns - positive words that may hide true feelings
MASKING_PHRASES: List[str] = [
    r"\bi'?m\s+fine\b", r"\bno\s+problem\b", r"\bit'?s\s+ok(ay)?\b",
    r"\ball\s+good\b", r"\byeah\s+sure\b", r"\bwhatever\s+works\b",
    r"\bdoesn'?t\s+matter\b", r"\bi\s+guess\b",
]


class KeywordSentimentAnalyzer:
    """
    Fast keyword-based sentiment analysis.
    Zero latency, zero cost, fully deterministic.
    """
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self._negative_compiled: Dict[PatternCategory, List[re.Pattern]] = {}
        self._positive_compiled: Dict[PatternCategory, List[re.Pattern]] = {}
        
        for category, patterns in NEGATIVE_PATTERNS.items():
            self._negative_compiled[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        for category, patterns in POSITIVE_PATTERNS.items():
            self._positive_compiled[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        self._masking_compiled = [
            re.compile(p, re.IGNORECASE) for p in MASKING_PHRASES
        ]
    
    def analyze(
        self,
        text: str,
        behavioral_context: Optional[Dict[str, Any]] = None
    ) -> SentimentResult:
        """
        Analyze text sentiment using pattern matching.
        
        Args:
            text: The text to analyze
            behavioral_context: Optional context from behavioral signals
                               (burnout_score, skips, losses, etc.)
        """
        text = text.strip()
        if not text:
            return SentimentResult(
                state=EmotionalState.NEUTRAL,
                intensity=0.0,
                confidence=0.0,
                matched_patterns=[],
                analysis_method="keyword",
                is_masked=False,
                raw_text=text,
            )
        
        negative_matches: List[Tuple[PatternCategory, str]] = []
        positive_matches: List[Tuple[PatternCategory, str]] = []
        masking_matches: List[str] = []
        
        # Check negative patterns
        for category, patterns in self._negative_compiled.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    negative_matches.append((category, match.group()))
        
        # Check positive patterns
        for category, patterns in self._positive_compiled.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    positive_matches.append((category, match.group()))
        
        # Check masking patterns
        for pattern in self._masking_compiled:
            match = pattern.search(text)
            if match:
                masking_matches.append(match.group())
        
        # Determine emotional state
        state, intensity = self._determine_state(
            negative_matches, positive_matches, masking_matches, behavioral_context
        )
        
        # Calculate confidence based on match strength
        all_matches = negative_matches + positive_matches
        confidence = min(1.0, len(all_matches) * 0.3 + 0.2)
        
        # Detect masking
        is_masked = self._detect_masking(
            masking_matches, state, behavioral_context
        )
        
        if is_masked:
            state = EmotionalState.MASKED
            confidence = max(confidence, 0.7)  # High confidence in masking
        
        return SentimentResult(
            state=state,
            intensity=intensity,
            confidence=confidence,
            matched_patterns=all_matches[:5],  # Top 5 matches
            analysis_method="keyword",
            is_masked=is_masked,
            raw_text=text[:100],  # Truncate for storage
        )
    
    def _determine_state(
        self,
        negative: List[Tuple[PatternCategory, str]],
        positive: List[Tuple[PatternCategory, str]],
        masking: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Tuple[EmotionalState, float]:
        """Determine emotional state from pattern matches."""
        
        neg_count = len(negative)
        pos_count = len(positive)
        
        # No matches - neutral
        if neg_count == 0 and pos_count == 0:
            return EmotionalState.NEUTRAL, 0.3
        
        # More positive than negative
        if pos_count > neg_count:
            # Determine which positive state
            categories = [m[0] for m in positive]
            if PatternCategory.JOY in categories:
                return EmotionalState.CELEBRATING, min(1.0, pos_count * 0.3)
            elif PatternCategory.GROWTH in categories:
                return EmotionalState.MOTIVATED, min(1.0, pos_count * 0.25)
            else:
                return EmotionalState.MOTIVATED, min(1.0, pos_count * 0.2)
        
        # More negative than positive
        elif neg_count > pos_count:
            categories = [m[0] for m in negative]
            
            if PatternCategory.GIVING_UP in categories:
                return EmotionalState.DISCOURAGED, min(1.0, neg_count * 0.35)
            elif PatternCategory.SELF_DOUBT in categories:
                return EmotionalState.DISCOURAGED, min(1.0, neg_count * 0.3)
            elif PatternCategory.FATIGUE in categories:
                return EmotionalState.FATIGUED, min(1.0, neg_count * 0.25)
            else:
                return EmotionalState.FRUSTRATED, min(1.0, neg_count * 0.3)
        
        # Equal - consider context
        else:
            if context and context.get("burnout_score", 0) > 0.5:
                return EmotionalState.FRUSTRATED, 0.4
            return EmotionalState.NEUTRAL, 0.3
    
    def _detect_masking(
        self,
        masking_matches: List[str],
        detected_state: EmotionalState,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Detect if user is masking true feelings.
        
        Masking occurs when:
        1. User says positive/neutral things
        2. But behavioral signals indicate distress
        """
        if not masking_matches:
            return False
        
        if not context:
            return False
        
        # Masking indicators from behavioral context
        burnout_score = context.get("burnout_score", 0)
        consecutive_skips = context.get("consecutive_skips", 0)
        ghost_loss_streak = context.get("ghost_loss_streak", 0)
        
        # User says "I'm fine" but...
        if burnout_score > 0.5:
            return True  # High burnout score
        if consecutive_skips >= 3:
            return True  # Multiple skips
        if ghost_loss_streak >= 3:
            return True  # Multiple losses
        
        return False


class HybridSentimentAnalyzer:
    """
    Multi-layer sentiment analysis.
    
    Flow:
    1. Always run keyword matching (instant)
    2. If concern detected, run local model
    3. If ambiguous/critical, call LLM API
    """
    
    def __init__(
        self,
        use_local_model: bool = False,
        use_llm_api: bool = False,
        llm_api_key: Optional[str] = None
    ):
        self.keyword_analyzer = KeywordSentimentAnalyzer()
        self.use_local_model = use_local_model
        self.use_llm_api = use_llm_api
        self.llm_api_key = llm_api_key
        
        # Lazy load local model if enabled
        self._local_model = None
        self._local_tokenizer = None
    
    def _load_local_model(self):
        """Lazy load local sentiment model."""
        if self._local_model is not None:
            return
        
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self._local_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._local_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            print(f"Loaded local sentiment model: {model_name}")
        except ImportError:
            print("transformers library not installed. Local model disabled.")
            self.use_local_model = False
        except Exception as e:
            print(f"Failed to load local model: {e}")
            self.use_local_model = False
    
    def _analyze_with_local_model(self, text: str) -> Tuple[EmotionalState, float]:
        """Analyze using local transformer model."""
        if not self.use_local_model:
            return EmotionalState.NEUTRAL, 0.0
        
        self._load_local_model()
        
        if self._local_model is None:
            return EmotionalState.NEUTRAL, 0.0
        
        try:
            import torch
            
            inputs = self._local_tokenizer(
                text, return_tensors="pt", truncation=True, max_length=128
            )
            
            with torch.no_grad():
                outputs = self._local_model(**inputs)
                scores = torch.softmax(outputs.logits, dim=1)
                
            # Model outputs: negative, neutral, positive
            neg_score = scores[0][0].item()
            neu_score = scores[0][1].item()
            pos_score = scores[0][2].item()
            
            if pos_score > neg_score and pos_score > neu_score:
                if pos_score > 0.7:
                    return EmotionalState.CELEBRATING, pos_score
                return EmotionalState.MOTIVATED, pos_score
            elif neg_score > pos_score and neg_score > neu_score:
                if neg_score > 0.8:
                    return EmotionalState.FRUSTRATED, neg_score
                return EmotionalState.DISCOURAGED, neg_score
            else:
                return EmotionalState.NEUTRAL, neu_score
                
        except Exception as e:
            print(f"Local model error: {e}")
            return EmotionalState.NEUTRAL, 0.0
    
    async def _analyze_with_llm(
        self,
        text: str,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[EmotionalState, float]:
        """Analyze using LLM API for nuanced understanding."""
        if not self.use_llm_api or not self.llm_api_key:
            return EmotionalState.NEUTRAL, 0.0
        
        try:
            import httpx
            
            # Build context prompt
            context_str = ""
            if context:
                context_str = f"""
Context:
- User has lost {context.get('ghost_loss_streak', 0)} ghost races in a row
- Current burnout score: {context.get('burnout_score', 0):.2f}
- Session length so far: {context.get('session_minutes', 0)} minutes
- Problems skipped: {context.get('consecutive_skips', 0)}
"""
            
            prompt = f"""You are analyzing a competitive programmer's chat message.
Classify the emotional state as exactly one of:
- frustrated (struggling, angry)
- discouraged (losing confidence, comparing to others)
- fatigued (tired, disengaged, going through motions)
- neutral (task-focused, no strong emotion)
- motivated (engaged, curious, determined)
- celebrating (just solved something, feeling good)
- masked (says positive things but context suggests otherwise)

Also rate intensity from 0.0 to 1.0.
{context_str}
Message: "{text}"

Respond in this exact format:
STATE: <state>
INTENSITY: <number>
"""
            
            # This is a placeholder - replace with actual API call
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(...)
            
            return EmotionalState.NEUTRAL, 0.5
            
        except Exception as e:
            print(f"LLM API error: {e}")
            return EmotionalState.NEUTRAL, 0.0
    
    def analyze(
        self,
        text: str,
        behavioral_context: Optional[Dict[str, Any]] = None
    ) -> SentimentResult:
        """
        Analyze text with hybrid approach.
        
        Flow:
        1. Always run keyword matching
        2. If concern detected → run local model
        3. If still ambiguous → could call LLM (async)
        """
        # Step 1: Keyword matching (instant)
        keyword_result = self.keyword_analyzer.analyze(text, behavioral_context)
        
        # If no concern, return keyword result
        if keyword_result.state in [EmotionalState.NEUTRAL, 
                                     EmotionalState.MOTIVATED,
                                     EmotionalState.CELEBRATING]:
            if keyword_result.confidence > 0.6:
                return keyword_result
        
        # Step 2: If concern detected and local model enabled
        if self.use_local_model and keyword_result.confidence < 0.7:
            local_state, local_confidence = self._analyze_with_local_model(text)
            
            if local_confidence > keyword_result.confidence:
                # Override with local model result
                keyword_result.state = local_state
                keyword_result.confidence = local_confidence
                keyword_result.analysis_method = "local_model"
        
        # Check for masking one more time with combined results
        if behavioral_context:
            burnout_score = behavioral_context.get("burnout_score", 0)
            if (keyword_result.state in [EmotionalState.NEUTRAL, 
                                          EmotionalState.MOTIVATED] and
                burnout_score > 0.5):
                keyword_result.is_masked = True
                keyword_result.state = EmotionalState.MASKED
        
        return keyword_result
    
    def quick_check(self, text: str) -> Tuple[EmotionalState, bool]:
        """
        Quick check for sentiment - keyword only.
        Returns (state, is_concerning)
        """
        result = self.keyword_analyzer.analyze(text)
        concerning = result.state in [
            EmotionalState.FRUSTRATED,
            EmotionalState.DISCOURAGED,
            EmotionalState.FATIGUED,
            EmotionalState.MASKED
        ]
        return result.state, concerning


class SentimentHistory:
    """Tracks sentiment over time for pattern detection."""
    
    def __init__(self, max_size: int = 50):
        self.history: List[SentimentResult] = []
        self.max_size = max_size
    
    def add(self, result: SentimentResult):
        """Add a sentiment result to history."""
        self.history.append(result)
        if len(self.history) > self.max_size:
            self.history.pop(0)
    
    def get_recent(self, count: int = 10) -> List[SentimentResult]:
        """Get recent sentiment results."""
        return self.history[-count:]
    
    def get_state_distribution(self) -> Dict[EmotionalState, int]:
        """Get distribution of emotional states."""
        dist: Dict[EmotionalState, int] = {}
        for result in self.history:
            dist[result.state] = dist.get(result.state, 0) + 1
        return dist
    
    def get_average_intensity(self, state: Optional[EmotionalState] = None) -> float:
        """Get average intensity, optionally for a specific state."""
        relevant = self.history
        if state:
            relevant = [r for r in self.history if r.state == state]
        
        if not relevant:
            return 0.0
        
        return sum(r.intensity for r in relevant) / len(relevant)
    
    def sentiment_declining(self, window: int = 10) -> bool:
        """Check if sentiment is getting worse over time."""
        recent = self.get_recent(window)
        if len(recent) < 4:
            return False
        
        # Count negative states in first vs second half
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]
        
        negative_states = {
            EmotionalState.FRUSTRATED,
            EmotionalState.DISCOURAGED,
            EmotionalState.FATIGUED,
            EmotionalState.MASKED
        }
        
        first_negative = sum(1 for r in first_half if r.state in negative_states)
        second_negative = sum(1 for r in second_half if r.state in negative_states)
        
        return second_negative > first_negative
