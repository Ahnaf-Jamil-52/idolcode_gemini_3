"""
Cross-Reference Fusion Module

The core intelligence that combines behavioral signals and text sentiment.
Neither layer alone is trustworthy - the cross-reference is what makes it agentic.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

from .signals import SignalCollector, BehavioralSignal, UserSession
from .scorer import BurnoutScorer, BurnoutScore, BurnoutLevel
from .trends import TrendDetector, TrendAnalysis, TrendDirection
from .states import CoachStateMachine, CoachState, StateTransition
from .sentiment import (
    HybridSentimentAnalyzer, SentimentResult, SentimentHistory,
    EmotionalState
)
from .gemini_analyzer import GeminiCoachAnalyzer


class BehaviorTextAlignment(Enum):
    """Matrix of truth - how behavior and text align."""
    GENUINE_GOOD = "genuine_good"      # Behavior: GOOD + Text: POSITIVE
    VENTING_OK = "venting_ok"          # Behavior: GOOD + Text: NEGATIVE
    MASKING = "masking"                # Behavior: BAD + Text: POSITIVE (DANGEROUS)
    CONFIRMED_BURNOUT = "confirmed"    # Behavior: BAD + Text: NEGATIVE
    SILENT_DISENGAGE = "silent"        # Behavior: BAD + Text: SILENT


class InterventionLevel(Enum):
    """Level of coach intervention needed."""
    NONE = "none"              # Continue normally
    MONITOR = "monitor"        # Watch closely
    GENTLE = "gentle"          # Subtle nudges
    ACTIVE = "active"          # Proactive intervention
    URGENT = "urgent"          # Immediate support needed


@dataclass
class FusionResult:
    """Complete assessment from fusing all signals."""
    alignment: BehaviorTextAlignment
    intervention_level: InterventionLevel
    
    # Component scores
    behavior_score: float          # 0.0 - 1.0
    text_sentiment_score: float    # -1.0 to 1.0 (negative to positive)
    trend_score: float             # Rate of change
    
    # Weighted composite
    composite_score: float         # 0.0 - 1.0 (overall burnout)
    
    # State info
    current_state: CoachState
    state_changed: bool
    
    # Flags
    is_masking: bool
    is_silent_disengagement: bool
    needs_immediate_attention: bool
    
    # Recommendations
    recommended_actions: List[str]
    ghost_speed_modifier: float    # 0.5 = 50% slower, 1.0 = normal
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "alignment": self.alignment.value,
            "intervention_level": self.intervention_level.value,
            "behavior_score": round(self.behavior_score, 3),
            "text_sentiment_score": round(self.text_sentiment_score, 3),
            "trend_score": round(self.trend_score, 4),
            "composite_score": round(self.composite_score, 3),
            "current_state": self.current_state.value,
            "state_changed": self.state_changed,
            "is_masking": self.is_masking,
            "is_silent_disengagement": self.is_silent_disengagement,
            "needs_immediate_attention": self.needs_immediate_attention,
            "recommended_actions": self.recommended_actions,
            "ghost_speed_modifier": self.ghost_speed_modifier,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TemporalComparison:
    """Comparison between current and historical performance."""
    current_vs_session_avg: float      # Ratio (>1 = worse than average)
    current_vs_last_week: float        # Ratio
    recovery_time_trend: str           # "increasing", "stable", "decreasing"
    message_tone_change: float         # % change in sentiment
    solve_time_variance: float         # High variance = frustration
    
    @property
    def is_concerning(self) -> bool:
        return (self.current_vs_session_avg > 1.3 or
                self.recovery_time_trend == "increasing" or
                self.message_tone_change < -30)


class FusionEngine:
    """
    The cross-referencing intelligence that combines all signals.
    
    Weights for composite score:
    - behavior_score: 65% (more reliable)
    - text_sentiment: 25% (direct expression)
    - trend_direction: 10% (momentum)
    """
    
    WEIGHTS = {
        "behavior": 0.65,
        "sentiment": 0.25,
        "trend": 0.10,
    }
    
    def __init__(
        self,
        use_local_nlp: bool = False,
        use_llm_api: bool = False,
        llm_api_key: Optional[str] = None,
        use_gemini: bool = False,
        gemini_api_key: Optional[str] = None
    ):
        # Core components
        self.signal_collector = SignalCollector()
        self.burnout_scorer = BurnoutScorer()
        self.trend_detector = TrendDetector()
        self.state_machine = CoachStateMachine()
        self.sentiment_analyzer = HybridSentimentAnalyzer(
            use_local_model=use_local_nlp,
            use_llm_api=use_llm_api,
            llm_api_key=llm_api_key
        )
        
        # Gemini integration
        self.use_gemini = use_gemini
        self.gemini_analyzer = GeminiCoachAnalyzer(gemini_api_key) if use_gemini else None
        
        # History tracking
        self.sentiment_history = SentimentHistory()
        self.fusion_history: List[FusionResult] = []
        self._session_burnout_peaks: List[float] = []
        
        # Temporal tracking
        self._last_message_time: Optional[datetime] = None
        self._message_count_session: int = 0
        self._failures_since_last_message: int = 0
        self._current_message: Optional[str] = None  # Store current message for Gemini
    
    def process_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[BehavioralSignal]:
        """
        Process a behavioral event.
        
        Returns list of signals detected.
        """
        signals = self.signal_collector.record_event(event_type, metadata)
        
        # Track failures for silent disengagement detection
        if event_type in ["wrong_answer", "problem_skipped", "ghost_race_result"]:
            if metadata and not metadata.get("won", False):
                self._failures_since_last_message += 1
        
        return signals
    
    def process_message(
        self,
        text: str,
        source: str = "chat"  # "chat", "search", "comment"
    ) -> SentimentResult:
        """
        Process a text message for sentiment.
        
        Returns sentiment analysis result.
        """
        # Store message for Gemini analysis
        self._current_message = text
        
        # Build behavioral context for masking detection
        burnout = self.burnout_scorer.calculate_burnout(
            list(self.signal_collector.signals),
            apply_smoothing=False
        )
        
        context = {
            "burnout_score": burnout.score,
            "consecutive_skips": sum(
                1 for s in list(self.signal_collector.signals)[-5:]
                if s.signal_type.value == "problem_skip_streak"
            ),
            "ghost_loss_streak": self.signal_collector._consecutive_ghost_losses,
            "session_minutes": (
                self.signal_collector.current_session.duration_minutes
                if self.signal_collector.current_session else 0
            ),
        }
        
        result = self.sentiment_analyzer.analyze(text, context)
        self.sentiment_history.add(result)
        
        # Reset failure counter on message
        self._last_message_time = datetime.now()
        self._message_count_session += 1
        self._failures_since_last_message = 0
        
        return result
    
    def analyze(self) -> FusionResult:
        """
        Perform complete fusion analysis of current state.
        
        This is the main intelligence function that cross-references
        all available signals.
        """
        now = datetime.now()
        
        # Get behavioral score
        signals = list(self.signal_collector.signals)
        burnout = self.burnout_scorer.calculate_burnout(signals)
        
        # Get trend
        session_scores = self.burnout_scorer.get_session_scores(5)
        if session_scores:
            trend = self.trend_detector.analyze(session_scores)
        else:
            trend = TrendAnalysis(
                direction=TrendDirection.STABLE,
                slope=0.0, intercept=0.0, r_squared=0.0,
                confidence=0.0, data_points=0,
                predicted_next=0.0, sessions_to_critical=None
            )
        
        # Get recent sentiment
        recent_sentiments = self.sentiment_history.get_recent(5)
        text_score = self._calculate_text_score(recent_sentiments)
        
        # Determine alignment (matrix of truth)
        alignment = self._determine_alignment(
            burnout.score, text_score, recent_sentiments
        )
        
        # Check for masking
        is_masking = alignment == BehaviorTextAlignment.MASKING
        
        # Check for silent disengagement
        is_silent = self._check_silent_disengagement(burnout.score)
        
        if is_silent and alignment != BehaviorTextAlignment.MASKING:
            alignment = BehaviorTextAlignment.SILENT_DISENGAGE
        
        # Use Gemini for complex psychological analysis (if enabled)
        gemini_insights = None
        if (self.use_gemini and self.gemini_analyzer and 
            self._needs_gemini_analysis(burnout.score, text_score, alignment)):
            
            try:
                # Get recent signals for context
                recent_signals = [s.signal_type.value for s in list(self.signal_collector.signals)[-10:]]
                session_context = {
                    "session_minutes": (
                        self.signal_collector.current_session.duration_minutes
                        if self.signal_collector.current_session else 0
                    ),
                    "recent_signals": recent_signals,
                    "ghost_loss_streak": self.signal_collector._consecutive_ghost_losses,
                    "failures_since_message": self._failures_since_last_message
                }
                
                gemini_insights = self.gemini_analyzer.analyze_burnout_context(
                    chat_message=self._current_message or "",
                    burnout_score=burnout.score,
                    recent_signals=recent_signals,
                    session_context=session_context
                )
                
                # Override alignment if Gemini detects masking
                if gemini_insights.get('emotional_state') == 'masked':
                    alignment = BehaviorTextAlignment.MASKING
                    is_masking = True
                
            except Exception as e:
                print(f"Gemini analysis failed: {e}")
                gemini_insights = None
        
        # Calculate composite score
        composite = self._calculate_composite(
            burnout.score, text_score, trend.slope, gemini_insights
        )
        
        # Update state machine
        transition = self.state_machine.update(
            burnout,
            trend,
            consecutive_failures=self._failures_since_last_message,
            ghost_loss_streak=self.signal_collector._consecutive_ghost_losses
        )
        
        # Determine intervention level
        intervention = self._determine_intervention(
            composite, alignment, self.state_machine.current_state
        )
        
        # Get recommendations
        actions = self._get_recommended_actions(
            alignment, intervention, self.state_machine.current_state
        )
        
        # Calculate ghost speed
        ghost_speed = self._calculate_ghost_speed(
            composite, self.state_machine.current_state
        )
        
        result = FusionResult(
            alignment=alignment,
            intervention_level=intervention,
            behavior_score=burnout.score,
            text_sentiment_score=text_score,
            trend_score=trend.slope,
            composite_score=composite,
            current_state=self.state_machine.current_state,
            state_changed=transition is not None,
            is_masking=is_masking,
            is_silent_disengagement=is_silent,
            needs_immediate_attention=(
                composite >= 0.7 or is_masking or 
                self.state_machine.current_state == CoachState.PROTECTIVE
            ),
            recommended_actions=actions,
            ghost_speed_modifier=ghost_speed,
            timestamp=now,
        )
        
        self.fusion_history.append(result)
        
        return result
    
    def _calculate_text_score(
        self, 
        sentiments: List[SentimentResult]
    ) -> float:
        """
        Calculate text sentiment score from recent messages.
        Returns -1.0 (very negative) to 1.0 (very positive)
        """
        if not sentiments:
            return 0.0  # Neutral if no messages
        
        score = 0.0
        for s in sentiments:
            if s.state == EmotionalState.CELEBRATING:
                score += 1.0 * s.intensity
            elif s.state == EmotionalState.MOTIVATED:
                score += 0.6 * s.intensity
            elif s.state == EmotionalState.NEUTRAL:
                score += 0.0
            elif s.state == EmotionalState.FRUSTRATED:
                score -= 0.7 * s.intensity
            elif s.state == EmotionalState.DISCOURAGED:
                score -= 0.9 * s.intensity
            elif s.state == EmotionalState.FATIGUED:
                score -= 0.6 * s.intensity
            elif s.state == EmotionalState.MASKED:
                score -= 0.8  # Masking is concerning
        
        return max(-1.0, min(1.0, score / len(sentiments)))
    
    def _determine_alignment(
        self,
        behavior_score: float,
        text_score: float,
        sentiments: List[SentimentResult]
    ) -> BehaviorTextAlignment:
        """
        Determine how behavior and text align.
        
        Matrix of Truth:
        - Behavior: GOOD + Text: POSITIVE → genuinely fine
        - Behavior: GOOD + Text: NEGATIVE → venting but okay
        - Behavior: BAD + Text: POSITIVE → MASKING (dangerous)
        - Behavior: BAD + Text: NEGATIVE → confirmed burnout
        - Behavior: BAD + Text: SILENT → silent disengagement
        """
        behavior_ok = behavior_score < 0.4
        text_positive = text_score > 0.2
        text_negative = text_score < -0.2
        
        # Check for any masking flags
        any_masked = any(s.is_masked for s in sentiments)
        
        if behavior_ok and text_positive:
            return BehaviorTextAlignment.GENUINE_GOOD
        
        if behavior_ok and text_negative:
            return BehaviorTextAlignment.VENTING_OK
        
        if not behavior_ok and (text_positive or any_masked):
            return BehaviorTextAlignment.MASKING
        
        if not behavior_ok and text_negative:
            return BehaviorTextAlignment.CONFIRMED_BURNOUT
        
        if not behavior_ok and not sentiments:
            return BehaviorTextAlignment.SILENT_DISENGAGE
        
        # Default to checking behavior
        if not behavior_ok:
            return BehaviorTextAlignment.CONFIRMED_BURNOUT
        
        return BehaviorTextAlignment.GENUINE_GOOD
    
    def _check_silent_disengagement(self, behavior_score: float) -> bool:
        """Check if user is silently disengaging."""
        # High burnout but no recent messages
        if behavior_score < 0.4:
            return False
        
        # No message in last 10 minutes but still active
        if self._last_message_time:
            silence_minutes = (datetime.now() - self._last_message_time).seconds / 60
            if silence_minutes > 10 and self._failures_since_last_message >= 3:
                return True
        else:
            # Never sent a message but has failures
            if self._failures_since_last_message >= 5:
                return True
        
        return False
    
    def _calculate_composite(
        self,
        behavior_score: float,
        text_score: float,
        trend_slope: float,
        gemini_insights: Optional[Dict] = None
    ) -> float:
        """
        Calculate weighted composite burnout score.
        
        Text score is inverted: positive text = lower burnout
        Trend slope is added: positive trend = worsening
        Includes Gemini insights adjustment for nuanced analysis.
        """
        # Convert text score to burnout contribution
        # text_score: -1 (negative) to 1 (positive)
        # We want: negative text = high burnout
        text_burnout = (1 - text_score) / 2  # Maps to 0-1
        
        # Trend contribution: positive slope = worsening
        trend_burnout = max(0, min(1, trend_slope * 2))  # 0.5 slope = 1.0 contribution
        
        composite = (
            self.WEIGHTS["behavior"] * behavior_score +
            self.WEIGHTS["sentiment"] * text_burnout +
            self.WEIGHTS["trend"] * trend_burnout
        )
        
        # Apply Gemini psychological adjustment if available
        if gemini_insights:
            intensity = gemini_insights.get('intensity', 0)
            state = gemini_insights.get('emotional_state', 'neutral')
            
            # Adjust based on detected hidden psychological states
            if state == 'masked' and intensity > 0.7:
                composite += 0.15  # Boost score for detected masking
            elif state == 'fatigued' and intensity > 0.6:
                composite += 0.10  # Mental exhaustion adjustment  
            elif state == 'frustrated' and intensity > 0.6:
                composite += 0.08  # Frustration scaling
            elif state in ['motivated', 'celebrating'] and intensity > 0.5:
                composite -= 0.10  # Positive state reduction
            elif state == 'discouraged' and intensity > 0.7:
                composite += 0.12  # Deep discouragement
        
        return max(0.0, min(1.0, composite))
    
    def _determine_intervention(
        self,
        composite_score: float,
        alignment: BehaviorTextAlignment,
        state: CoachState
    ) -> InterventionLevel:
        """Determine intervention level based on all factors."""
        
        # Masking is always concerning
        if alignment == BehaviorTextAlignment.MASKING:
            return InterventionLevel.ACTIVE
        
        # State-based defaults
        state_intervention = {
            CoachState.NORMAL: InterventionLevel.NONE,
            CoachState.WATCHING: InterventionLevel.MONITOR,
            CoachState.WARNING: InterventionLevel.GENTLE,
            CoachState.PROTECTIVE: InterventionLevel.ACTIVE,
            CoachState.RECOVERY: InterventionLevel.GENTLE,
        }
        
        base = state_intervention[state]
        
        # Escalate based on composite score
        if composite_score >= 0.7:
            return InterventionLevel.URGENT
        elif composite_score >= 0.5 and base.value < InterventionLevel.ACTIVE.value:
            return InterventionLevel.ACTIVE
        
        # Silent disengagement needs attention
        if alignment == BehaviorTextAlignment.SILENT_DISENGAGE:
            if base.value < InterventionLevel.GENTLE.value:
                return InterventionLevel.GENTLE
        
        return base
    
    def _get_recommended_actions(
        self,
        alignment: BehaviorTextAlignment,
        intervention: InterventionLevel,
        state: CoachState
    ) -> List[str]:
        """Get list of recommended actions for the coach."""
        actions = []
        
        # Alignment-specific actions
        if alignment == BehaviorTextAlignment.MASKING:
            actions.append("PROBE: Ask how user is actually feeling")
            actions.append("VALIDATE: Acknowledge that it's okay to struggle")
        
        elif alignment == BehaviorTextAlignment.SILENT_DISENGAGE:
            actions.append("INITIATE: Reach out to user")
            actions.append("OFFER: Suggest something fun instead of hard")
        
        elif alignment == BehaviorTextAlignment.CONFIRMED_BURNOUT:
            actions.append("VALIDATE: Acknowledge frustration")
            actions.append("HUMANIZE: Share idol's similar struggles")
        
        # State-specific actions
        if state == CoachState.PROTECTIVE:
            actions.append("SUGGEST: Offer rest break")
            actions.append("MODE: Enable cooperative ghost")
            actions.append("CELEBRATE: Small wins only")
        
        elif state == CoachState.WARNING:
            actions.append("SLOW: Reduce ghost speed")
            actions.append("REFRAME: This problem is tough for everyone")
        
        elif state == CoachState.RECOVERY:
            actions.append("ENCOURAGE: Gentle positive reinforcement")
            actions.append("EASY: Suggest easier problems")
        
        # Intervention-specific actions
        if intervention == InterventionLevel.URGENT:
            actions.insert(0, "IMMEDIATE: Stop and check in with user")
        
        return actions[:5]  # Max 5 actions
    
    def _calculate_ghost_speed(
        self,
        composite_score: float,
        state: CoachState
    ) -> float:
        """
        Calculate ghost speed modifier.
        
        Returns 0.0 - 1.0 where:
        - 1.0 = normal speed
        - 0.5 = 50% speed
        - 0.0 = stop/cooperative
        """
        # State-based modifiers
        state_modifiers = {
            CoachState.NORMAL: 1.0,
            CoachState.WATCHING: 0.95,
            CoachState.WARNING: 0.7,
            CoachState.PROTECTIVE: 0.3,
            CoachState.RECOVERY: 0.8,
        }
        
        base = state_modifiers[state]
        
        # Further reduce based on composite score
        if composite_score > 0.7:
            base *= 0.5
        elif composite_score > 0.5:
            base *= 0.7
        
        return max(0.0, min(1.0, base))
    
    def get_temporal_comparison(self) -> TemporalComparison:
        """Get comparison between current and historical performance."""
        
        recent_sessions = list(self.signal_collector.sessions)
        
        # Current vs session average
        if len(recent_sessions) >= 3:
            avg_score = sum(
                self._session_burnout_peaks[i] 
                for i in range(-3, 0) 
                if i < len(self._session_burnout_peaks)
            ) / 3
            current = self._session_burnout_peaks[-1] if self._session_burnout_peaks else 0
            ratio = current / avg_score if avg_score > 0 else 1.0
        else:
            ratio = 1.0
        
        # Sentiment change
        if len(self.sentiment_history.history) >= 10:
            first_5 = self.sentiment_history.history[:5]
            last_5 = self.sentiment_history.history[-5:]
            first_avg = sum(1 if s.state in [EmotionalState.MOTIVATED, EmotionalState.CELEBRATING] else -1 for s in first_5) / 5
            last_avg = sum(1 if s.state in [EmotionalState.MOTIVATED, EmotionalState.CELEBRATING] else -1 for s in last_5) / 5
            tone_change = (last_avg - first_avg) * 50
        else:
            tone_change = 0.0
        
        return TemporalComparison(
            current_vs_session_avg=ratio,
            current_vs_last_week=1.0,  # Would need longer history
            recovery_time_trend="stable",  # Would need tracking
            message_tone_change=tone_change,
            solve_time_variance=0.0,  # Would need solve time data
        )
    
    def start_session(self, user_id: str, session_id: str):
        """Start a new tracking session."""
        self.signal_collector.start_session(user_id, session_id)
        self._message_count_session = 0
        self._failures_since_last_message = 0
    
    def end_session(self):
        """End the current session."""
        session = self.signal_collector.end_session()
        if session:
            # Record peak burnout for this session
            burnout = self.burnout_scorer.calculate_burnout(
                list(self.signal_collector.signals)
            )
            self._session_burnout_peaks.append(burnout.score)
    
    def get_current_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state for API response."""
        analysis = self.analyze()
        
        return {
            "state": self.state_machine.current_state.value,
            "composite_score": round(analysis.composite_score, 2),
            "intervention_level": analysis.intervention_level.value,
            "ghost_speed": analysis.ghost_speed_modifier,
            "is_masking": analysis.is_masking,
            "needs_attention": analysis.needs_immediate_attention,
            "actions": analysis.recommended_actions[:3],
            "alignment": analysis.alignment.value,
        }
    
    def _needs_gemini_analysis(self, burnout_score: float, text_score: float, alignment: BehaviorTextAlignment) -> bool:
        """
        Determine if situation requires Gemini's advanced psychological analysis.
        
        Uses Gemini selectively to minimize API costs.
        """
        # Always analyze high burnout cases
        if burnout_score > 0.6:
            return True
        
        # Check for complex emotional scenarios
        if alignment == BehaviorTextAlignment.MASKING:
            return True
        
        # Analyze mixed signals (moderate burnout + neutral text)
        if 0.4 <= burnout_score <= 0.6 and -0.1 <= text_score <= 0.1:
            return True
        
        # Check if current message suggests complexity
        if self._current_message:
            message_lower = self._current_message.lower()
            complex_phrases = [
                "i'm fine", "it's okay", "whatever", "doesn't matter",
                "i guess", "maybe", "i don't know", "tired", "should i",
                "am i", "why can't", "everyone else", "give up"
            ]
            if any(phrase in message_lower for phrase in complex_phrases):
                return True
        
        return False
    
    def reset(self):
        """Reset all components."""
        self.signal_collector = SignalCollector()
        self.burnout_scorer.reset()
        self.state_machine.reset()
        self.sentiment_history = SentimentHistory()
        self.fusion_history.clear()
        self._session_burnout_peaks.clear()
        self._last_message_time = None
        self._message_count_session = 0
        self._failures_since_last_message = 0
        self._current_message = None
    
    # ==================== HYDRATION METHODS ====================
    # These methods enable MongoDB persistence by allowing the engine
    # to save and restore its state between API calls.
    
    def load_context(self, state_data: dict):
        """
        Hydrate the engine from MongoDB state.
        
        Called at the start of each request to restore the user's session state.
        """
        # Core metrics
        self.burnout_scorer.set_score(state_data.get("burnout_score", 0.0))
        
        # State machine
        state_name = state_data.get("current_state", "NORMAL")
        try:
            self.state_machine._current_state = CoachState[state_name]
        except KeyError:
            self.state_machine._current_state = CoachState.NORMAL
        
        # Internal counters
        self._failures_since_last_message = state_data.get("failures_since_last_message", 0)
        self._message_count_session = state_data.get("message_count_session", 0)
        self.signal_collector._consecutive_ghost_losses = state_data.get("consecutive_ghost_losses", 0)
        
        # Metrics
        metrics = state_data.get("metrics", {})
        # Apply any stored metrics to internal state
        
        # Restore recent signals (for trend analysis)
        recent_signals = state_data.get("recent_signals", [])
        for sig_data in recent_signals[-20:]:  # Only keep last 20
            try:
                from .signals import SignalType, BehavioralSignal
                signal = BehavioralSignal(
                    signal_type=SignalType[sig_data.get("signal_type", "CODE_PASTE")],
                    timestamp=datetime.fromisoformat(sig_data.get("timestamp", datetime.now().isoformat())),
                    weight=sig_data.get("weight", 0.1)
                )
                self.signal_collector.signals.append(signal)
            except (KeyError, ValueError):
                continue
        
        # Restore recent sentiments
        recent_sentiments = state_data.get("recent_sentiments", [])
        for sent_data in recent_sentiments[-10:]:
            try:
                result = SentimentResult(
                    state=EmotionalState[sent_data.get("state", "NEUTRAL")],
                    intensity=sent_data.get("intensity", 0.5),
                    confidence=sent_data.get("confidence", 0.5),
                    matched_patterns=[],
                    is_masked=sent_data.get("is_masked", False),
                    analysis_method=sent_data.get("analysis_method", "restored")
                )
                self.sentiment_history.add(result)
            except (KeyError, ValueError):
                continue
    
    def export_context(self) -> dict:
        """
        Export engine state for MongoDB persistence.
        
        Called after processing each signal to save the updated state.
        """
        # Get recent signals for storage
        recent_signals = []
        for sig in list(self.signal_collector.signals)[-20:]:
            recent_signals.append({
                "signal_type": sig.signal_type.name,
                "timestamp": sig.timestamp.isoformat(),
                "weight": sig.weight
            })
        
        # Get recent sentiments
        recent_sentiments = []
        for sent in self.sentiment_history.get_recent(10):
            recent_sentiments.append({
                "state": sent.state.name,
                "intensity": sent.intensity,
                "confidence": sent.confidence,
                "is_masked": sent.is_masked,
                "analysis_method": sent.analysis_method
            })
        
        # Get emotional trend
        emotional_trend = [s.state.name for s in self.sentiment_history.get_recent(5)]
        
        return {
            "burnout_score": self.burnout_scorer.get_current_score(),
            "current_state": self.state_machine.current_state.name,
            "emotional_trend": emotional_trend,
            "metrics": {
                "frustration_index": self._calculate_frustration_index(),
                "fatigue_index": self._calculate_fatigue_index(),
                "focus_score": self._calculate_focus_score(),
                "ghost_speed_modifier": self._calculate_ghost_speed(
                    self.burnout_scorer.get_current_score(),
                    self.state_machine.current_state
                ),
            },
            "failures_since_last_message": self._failures_since_last_message,
            "message_count_session": self._message_count_session,
            "consecutive_ghost_losses": self.signal_collector._consecutive_ghost_losses,
            "recent_signals": recent_signals,
            "recent_sentiments": recent_sentiments,
        }
    
    def _calculate_frustration_index(self) -> float:
        """Calculate frustration index from recent signals."""
        recent = list(self.signal_collector.signals)[-10:]
        if not recent:
            return 0.0
        frustration_signals = sum(1 for s in recent if s.signal_type.name in [
            "RAPID_WA_BURST", "RAGE_PASTE", "PROBLEM_SKIP_STREAK"
        ])
        return min(1.0, frustration_signals / 5)
    
    def _calculate_fatigue_index(self) -> float:
        """Calculate fatigue index from session duration and signals."""
        session = self.signal_collector.current_session
        if not session:
            return 0.0
        
        minutes = session.duration_minutes
        # Fatigue increases with time (exponential after 90 mins)
        base_fatigue = min(1.0, (minutes / 120) ** 1.5)
        
        # Increase if many idle periods
        idle_signals = sum(1 for s in list(self.signal_collector.signals) if s.signal_type.name == "LONG_IDLE")
        idle_fatigue = min(0.3, idle_signals * 0.1)
        
        return min(1.0, base_fatigue + idle_fatigue)
    
    def _calculate_focus_score(self) -> float:
        """Calculate focus score (100 = fully focused, 0 = distracted)."""
        recent = list(self.signal_collector.signals)[-10:]
        if not recent:
            return 100.0
        
        focus_drains = sum(1 for s in recent if s.signal_type.name in [
            "EXCESSIVE_TAB_SWITCHES", "LONG_IDLE", "PROBLEM_SKIP_STREAK"
        ])
        return max(0.0, 100.0 - (focus_drains * 15))
    
    def process_signal(
        self,
        signal_type: str,
        value: float = 0.0,
        metadata: dict = None,
        message: str = None
    ) -> dict:
        """
        Unified signal processing for API endpoint.
        
        Processes behavioral signals and optional chat messages,
        returning the coach's response.
        """
        metadata = metadata or {}
        
        # Process behavioral signal
        if signal_type == "chat" and message:
            # Process as sentiment
            sentiment_result = self.process_message(message)
        else:
            # Process as behavioral event
            # Map common signal types to event types
            event_mapping = {
                "run_failure": "wrong_answer",
                "test_failure": "wrong_answer",
                "problem_solved": "problem_solved",
                "problem_skipped": "problem_skipped",
                "ghost_race_lost": "ghost_race_result",
                "ghost_race_won": "ghost_race_result",
                "idle": "idle_detected",
                "hint_requested": "hint_requested",
            }
            
            event_type = event_mapping.get(signal_type, signal_type)
            
            # Add value and metadata
            if signal_type == "ghost_race_won":
                metadata["won"] = True
            elif signal_type == "ghost_race_lost":
                metadata["won"] = False
            elif signal_type == "idle":
                metadata["idle_minutes"] = value
            
            self.process_event(event_type, metadata)
            
            # Also process message if provided
            if message:
                self.process_message(message)
        
        # Run full analysis
        result = self.analyze()
        
        # Generate coach response if needed
        coach_response = None
        if result.needs_immediate_attention or result.intervention_level.value in ["active", "urgent"]:
            coach_response = self._generate_coach_response(result)
        
        return {
            "burnout_score": result.composite_score,
            "current_state": result.current_state.name,
            "intervention_level": result.intervention_level.value,
            "ghost_speed_modifier": result.ghost_speed_modifier,
            "is_masking": result.is_masking,
            "needs_attention": result.needs_immediate_attention,
            "coach_response": coach_response,
            "recommended_actions": result.recommended_actions,
        }
    
    def _generate_coach_response(self, result: FusionResult) -> str:
        """Generate appropriate coach response based on analysis."""
        if result.is_masking:
            return "Hey, I noticed you've been struggling. It's okay to take a break - even pros need them."
        
        if result.composite_score > 0.7:
            return "You're tilting. Let's pause and reset. A 5-minute break can clear your mind."
        
        if result.current_state == CoachState.PROTECTIVE:
            return "Let's slow down. How about we try an easier problem to rebuild momentum?"
        
        if result.current_state == CoachState.WARNING:
            return "I see you're hitting some walls. Remember, every top coder has been here. Take it one step at a time."
        
        if result.is_silent_disengagement:
            return "Haven't heard from you in a while. How's it going? Need a hint?"
        
        return None
