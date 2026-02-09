"""
Coach State Persistence Models

Pydantic models for storing and retrieving coach state from MongoDB.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timezone


class CoachStateModel(BaseModel):
    """MongoDB document schema for coach session state."""
    user_handle: str
    burnout_score: float = 0.0
    current_state: str = "NORMAL"  # NORMAL, WATCHING, WARNING, PROTECTIVE, RECOVERY
    emotional_trend: List[str] = []  # Last 5 emotional states
    
    # Fusion Engine internal metrics
    metrics: Dict[str, float] = Field(default_factory=lambda: {
        "frustration_index": 0.0,
        "fatigue_index": 0.0,
        "focus_score": 100.0,
        "ghost_speed_modifier": 1.0,
    })
    
    # Signal tracking
    failures_since_last_message: int = 0
    message_count_session: int = 0
    consecutive_ghost_losses: int = 0
    
    # Recent signals for context restoration
    recent_signals: List[Dict] = []  # Last 20 signals
    recent_sentiments: List[Dict] = []  # Last 10 sentiment results
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SignalRequest(BaseModel):
    """API request body for coach signal processing."""
    user_handle: str
    signal_type: str  # "run_failure", "problem_solved", "idle", "chat", etc.
    value: float = 0.0  # e.g., 1 for failure count, 120 for WPM
    metadata: Dict = {}  # Extra context like problem_id, idle_minutes, etc.
    message: Optional[str] = None  # Chat message for sentiment analysis


class SignalResponse(BaseModel):
    """API response from coach signal processing."""
    status: str = "processed"
    new_burnout_score: float
    current_state: str
    intervention_level: str
    ghost_speed_modifier: float
    is_masking: bool = False
    needs_attention: bool = False
    coach_response: Optional[str] = None
    recommended_actions: List[str] = []


class ChatRequest(BaseModel):
    """API request body for chat messages."""
    user_handle: str
    text: str
    timestamp: Optional[str] = None
    current_problem_id: Optional[str] = None  # Phase 4: Problem context


class ChatResponse(BaseModel):
    """API response from coach chat."""
    reply: str
    detected_sentiment: str
    burnout_score: float
    intervention_level: str


class VoiceRequest(BaseModel):
    """API request body for voice queries (mic → Gemini multimodal)."""
    audio_data: str  # Base64-encoded audio
    code_context: str = ""  # Current editor code for context
    problem_id: Optional[str] = None  # Current problem context
    user_handle: str = "anonymous"
    audio_format: str = "wav"  # "wav" (from MCI) or "webm" (from browser)


class VoiceResponse(BaseModel):
    """API response from voice query."""
    reply: str
    detected_intent: str = "general"
    burnout_score: float = 0.0
