"""
Gemini AI Integration for Complex Burnout Analysis

Uses Google's Gemini API for nuanced psychological analysis and contextual understanding.
Includes intelligent caching to minimize API costs.
"""

import google.generativeai as genai
from typing import Dict, Optional, List, Any
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os
import pickle
from pathlib import Path


@dataclass
class CacheEntry:
    """Cached response with metadata"""
    response: Dict[str, Any]
    timestamp: datetime
    hit_count: int = 0
    ttl_hours: int = 24


class ResponseCache:
    """Intelligent caching system for Gemini responses"""
    
    def __init__(self, cache_dir: str = ".gemini_cache", max_size: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "responses.pkl"
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, CacheEntry]:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def _generate_key(self, prompt: str, context: Dict) -> str:
        """Generate cache key from prompt and context"""
        # Normalize context for consistent caching
        normalized = {
            'burnout_range': self._quantize_score(context.get('burnout_score', 0)),
            'signal_types': sorted(context.get('recent_signals', [])),
            'emotional_indicators': sorted(context.get('emotional_indicators', [])),
            'prompt_hash': hashlib.md5(prompt.encode()).hexdigest()[:16]
        }
        key_string = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def _quantize_score(self, score: float) -> str:
        """Quantize burnout score for better cache hits"""
        if score < 0.2: return "very_low"
        elif score < 0.4: return "low"  
        elif score < 0.6: return "moderate"
        elif score < 0.8: return "high"
        else: return "critical"
    
    def get(self, prompt: str, context: Dict) -> Optional[Dict]:
        """Get cached response if available and fresh"""
        key = self._generate_key(prompt, context)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() - entry.timestamp > timedelta(hours=entry.ttl_hours):
                del self.cache[key]
                return None
            
            # Update hit count and return
            entry.hit_count += 1
            return entry.response
        
        return None
    
    def set(self, prompt: str, context: Dict, response: Dict, ttl_hours: int = 24):
        """Cache response with TTL"""
        key = self._generate_key(prompt, context)
        
        # Cleanup old entries if cache too large
        if len(self.cache) >= self.max_size:
            self._cleanup_cache()
        
        self.cache[key] = CacheEntry(
            response=response,
            timestamp=datetime.now(),
            ttl_hours=ttl_hours
        )
        self._save_cache()
    
    def _cleanup_cache(self):
        """Remove old/unused entries"""
        # Sort by timestamp and hit count, remove oldest/least used
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: (x[1].hit_count, x[1].timestamp)
        )
        
        # Remove bottom 20%
        to_remove = int(len(sorted_entries) * 0.2)
        for key, _ in sorted_entries[:to_remove]:
            del self.cache[key]


class GeminiCoachAnalyzer:
    """Advanced burnout analysis using Gemini AI with intelligent caching"""
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        # Try to import config, fall back to env var
        try:
            from config import GEMINI_API_KEY
            self.api_key = api_key or GEMINI_API_KEY
        except ImportError:
            self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        
        self.use_cache = use_cache
        self.cache = ResponseCache() if use_cache else None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-1.5-flash for speed + capability balance
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                print("✅ Gemini AI enabled with gemini-1.5-flash model")
            except Exception as e:
                self.model = None
                self.enabled = False
                print(f"❌ Gemini API Error: {e}")
        else:
            self.model = None
            self.enabled = False
            print("⚠️  Gemini API key not found. Using fallback mode.")

    
    def analyze_burnout_context(self, 
                               chat_message: str,
                               burnout_score: float,
                               recent_signals: List[str],
                               session_context: Dict) -> Dict:
        """Deep contextual analysis of user's mental state"""
        
        if not self.enabled:
            return self._fallback_analysis(chat_message, burnout_score)
        
        context = {
            'burnout_score': burnout_score,
            'recent_signals': recent_signals,
            'emotional_indicators': self._extract_emotional_indicators(chat_message)
        }
        
        # Check cache first
        if self.use_cache:
            cached = self.cache.get(self._get_analysis_prompt_template(), context)
            if cached:
                return cached
        
        prompt = self._build_analysis_prompt(chat_message, burnout_score, recent_signals, session_context)
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Cache successful response
            if self.use_cache:
                self.cache.set(self._get_analysis_prompt_template(), context, result, ttl_hours=6)
            
            return result
            
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return self._fallback_analysis(chat_message, burnout_score)
    
    def generate_contextual_response(self, 
                                   user_state: Dict,
                                   idol_name: str,
                                   problem_context: Dict) -> str:
        """Generate personalized coach response using idol-specific context"""
        
        if not self.enabled:
            return self._fallback_response(user_state, idol_name)
        
        context = {
            'burnout_score': user_state.get('burnout_score', 0),
            'emotional_state': user_state.get('emotional_state', 'neutral'),
            'idol': idol_name
        }
        
        # Check cache
        if self.use_cache:
            cached = self.cache.get(self._get_response_prompt_template(), context)
            if cached and 'response' in cached:
                return cached['response']
        
        prompt = self._build_response_prompt(user_state, idol_name, problem_context)
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Cache response
            if self.use_cache:
                cache_data = {'response': result}
                self.cache.set(self._get_response_prompt_template(), context, cache_data, ttl_hours=12)
            
            return result
            
        except Exception as e:
            print(f"❌ Gemini response error: {e}")
            return self._fallback_response(user_state, idol_name)
    
    async def generate_chat_response(self, 
                                     user_message: str,
                                     coach_state: str,
                                     sentiment: str,
                                     burnout_score: float = 0.0,
                                     problem_context: Optional[Dict] = None) -> str:
        """
        Generate a chat response with full problem context (Phase 4: Live AI)
        
        This is the main method for the "Live" coach that understands
        exactly what problem the user is solving.
        """
        
        if not self.enabled:
            return self._fallback_chat_response(user_message, coach_state, sentiment)
        
        # Build context block
        context_str = ""
        if problem_context:
            context_str = f"""
CURRENT PROBLEM CONTEXT:
- Problem: {problem_context.get('contestId', '')}{problem_context.get('index', '')} - {problem_context.get('name', 'Unknown')}
- Rating: {problem_context.get('rating', 'N/A')}
- Tags: {problem_context.get('tags', [])}
- Statement: {str(problem_context.get('problemStatement', 'N/A'))[:500]}...
"""
        
        # Build the persona prompt based on state
        system_instruction = f"""You are a world-class Competitive Programming Coach (like a helpful rubber duck 🦆).
Current Coach State: {coach_state}
User Sentiment: {sentiment}
Burnout Level: {burnout_score:.1%}

{context_str}

COACHING RULES:
- If state is NORMAL: Be helpful but brief. Use Socratic method - ask guiding questions.
- If state is WATCHING: Be more alert. Ask specific questions about their logic/approach.
- If state is PROTECTIVE: Be firm but caring. Tell them to step back and breathe.
- NEVER give full code solutions. Only logic hints and conceptual guidance.
- Keep responses under 2-3 sentences unless the user explicitly asks for a deep explanation.
- If you see the problem context, give hints specific to THAT problem.
- Be encouraging but realistic. Don't be overly cheerful if they're struggling.
"""
        
        try:
            # Generate response
            response = self.model.generate_content(
                f"{system_instruction}\n\nUser says: {user_message}"
            )
            result = response.text.strip()
            print(f"🧠 Gemini generated response ({len(result)} chars)")
            return result
            
        except Exception as e:
            print(f"❌ Gemini chat error: {e}")
            return self._fallback_chat_response(user_message, coach_state, sentiment)
    
    def _fallback_chat_response(self, message: str, state: str, sentiment: str) -> str:
        """Fallback when Gemini unavailable"""
        message_lower = message.lower()
        
        if state == "PROTECTIVE":
            return "🦆 Hey, I notice you might be pushing too hard. Take a breather - the problem will still be here."
        
        if "stuck" in message_lower or "help" in message_lower:
            return "🦆 What's the core constraint here? Sometimes re-reading the problem helps spot what we missed."
        
        if "why" in message_lower or "wrong" in message_lower:
            return "🦆 Let's debug together. What does your code output for the first example? Does it match?"
        
        if sentiment in ["negative", "frustrated"]:
            return "🦆 I can see this one's tricky. What approach have you tried so far?"
        
        return "🦆 Tell me more about what you're thinking. Sometimes talking through it helps!"

    async def generate_voice_response(self,
                                      audio_base64: str,
                                      code_context: str = "",
                                      problem_context: Optional[Dict] = None,
                                      audio_format: str = "wav") -> str:
        """
        Process voice audio via Gemini 1.5 Pro multimodal.
        
        Receives Base64-encoded audio, writes to temp file, uploads
        to Gemini, and generates a coaching response.
        Supports wav (from Windows MCI) and webm (from browser MediaRecorder).
        """
        import tempfile
        import base64

        if not self.enabled:
            return "🦆 Voice mode isn't available right now — Gemini API key not configured."

        # Decode Base64 audio to a temp file
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            print(f"❌ Voice: bad base64 data: {e}")
            return "🦆 I couldn't understand that recording. Try again?"

        tmp = None
        try:
            suffix = f".{audio_format}"
            mime_type = f"audio/{audio_format}"
            tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            tmp.write(audio_bytes)
            tmp.flush()
            tmp.close()

            # Upload audio file to Gemini
            audio_file = genai.upload_file(tmp.name, mime_type=mime_type)

            # Build coaching prompt
            context_block = ""
            if problem_context:
                context_block = f"""
CURRENT PROBLEM:
- {problem_context.get('contestId', '')}{problem_context.get('index', '')} — {problem_context.get('name', 'Unknown')}
- Rating: {problem_context.get('rating', 'N/A')}
- Tags: {problem_context.get('tags', [])}
"""
            code_block = ""
            if code_context and code_context.strip():
                code_block = f"\nUSER'S CURRENT CODE:\n```\n{code_context[:3000]}\n```"

            prompt = f"""You are a Competitive Programming Coach (like a helpful rubber-duck 🦆).
Listen to the user's voice message and reply with short, actionable coaching guidance.

{context_block}{code_block}

RULES:
- NEVER give full solutions — only hints and guiding questions.
- Keep responses to 2-3 sentences.
- If you can't understand the audio, say so politely.
- Sound warm but concise — you're talking to a competitive coder.
"""

            # Use gemini-1.5-pro for multimodal audio support
            pro_model = genai.GenerativeModel('gemini-1.5-pro')
            response = await pro_model.generate_content_async([audio_file, prompt])
            result = response.text.strip()
            print(f"🎙️ Voice response ({len(result)} chars)")
            return result

        except Exception as e:
            print(f"❌ Voice processing error: {e}")
            return "🦆 I had trouble processing your voice. Could you try again?"
        finally:
            # Clean up temp file
            if tmp:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

    def detect_advanced_patterns(self, event_sequence: List[Dict]) -> Dict:
        """Detect subtle burnout patterns using Gemini's pattern recognition"""
        
        if not self.enabled or len(event_sequence) < 3:
            return {"detected_patterns": [], "overall_concern_level": 0.0}
        
        # Simplify events for caching
        pattern_signature = self._create_pattern_signature(event_sequence)
        context = {'pattern_signature': pattern_signature}
        
        if self.use_cache:
            cached = self.cache.get(self._get_pattern_prompt_template(), context)
            if cached:
                return cached
        
        prompt = self._build_pattern_prompt(event_sequence)
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Cache pattern analysis
            if self.use_cache:
                self.cache.set(self._get_pattern_prompt_template(), context, result, ttl_hours=2)
            
            return result
            
        except Exception as e:
            print(f"Gemini pattern error: {e}")
            return {"detected_patterns": [], "overall_concern_level": 0.0}
    
    def _extract_emotional_indicators(self, message: str) -> List[str]:
        """Extract emotional indicators for cache key generation"""
        indicators = []
        message_lower = message.lower()
        
        frustration_words = ['stuck', 'frustrated', 'annoyed', 'hate', 'stupid', 'impossible']
        sadness_words = ['tired', 'sad', 'depressed', 'hopeless', 'give up']
        confidence_words = ['easy', 'confident', 'got it', 'understand', 'clear']
        
        if any(word in message_lower for word in frustration_words):
            indicators.append('frustration')
        if any(word in message_lower for word in sadness_words):
            indicators.append('sadness')
        if any(word in message_lower for word in confidence_words):
            indicators.append('confidence')
        
        return indicators
    
    def _create_pattern_signature(self, events: List[Dict]) -> str:
        """Create pattern signature for caching"""
        types = [event.get('type', 'unknown') for event in events[-10:]]  # Last 10 events
        return '_'.join(types)
    
    def _build_analysis_prompt(self, message: str, score: float, signals: List[str], context: Dict) -> str:
        """Build analysis prompt"""
        return f"""You are an expert competitive programming coach analyzing a student's emotional state.

CONTEXT:
- Current burnout score: {score:.2f}/1.0 
- Recent behavioral signals: {signals}
- Session info: {context}
- User message: "{message}"

Analyze and return JSON:
{{
    "emotional_state": "frustrated|discouraged|fatigued|masked|motivated|celebrating",
    "intensity": 0.0-1.0,
    "hidden_feelings": "what they're not saying directly",
    "intervention_needed": true/false,
    "recommended_response_tone": "supportive|technical|encouraging|protective",
    "suggested_action": "slow_ghost|suggest_break|offer_easier|celebrate|probe_deeper"
}}

Focus on detecting:
1. MASKING: Says positive but context suggests struggle
2. SILENT DISENGAGEMENT: Withdrawn, going through motions
3. EGO DAMAGE: Comparing self negatively to idol
4. FATIGUE MASKING: "I'm fine" but showing exhaustion signs"""
    
    def _build_response_prompt(self, user_state: Dict, idol_name: str, problem_context: Dict) -> str:
        """Build response generation prompt"""
        return f"""You are {idol_name}'s AI coach speaking to a competitive programmer who idolizes them.

SITUATION:
- User emotional state: {user_state.get('emotional_state', 'neutral')}
- Burnout level: {user_state.get('burnout_score', 0):.2f}/1.0
- Recommended tone: {user_state.get('recommended_response_tone', 'supportive')}
- Suggested action: {user_state.get('suggested_action', 'encourage')}

Generate a response that:
1. Speaks as {idol_name}'s mentor/coach
2. References {idol_name}'s competitive journey appropriately  
3. Matches the needed tone and takes suggested action
4. Is 1-2 sentences, encouraging but realistic

Keep it natural and avoid over-referencing the idol."""
    
    def _build_pattern_prompt(self, events: List[Dict]) -> str:
        """Build pattern detection prompt"""
        return f"""Analyze this sequence of competitive programming events for burnout patterns:

EVENTS: {json.dumps(events[-20:], indent=2)}

Detect patterns indicating:
1. SPIRAL PATTERNS: Performance degrading over time
2. AVOIDANCE PATTERNS: Systematically avoiding challenge
3. PERFECTIONIST PARALYSIS: Fear of making mistakes
4. COMPARISON BURNOUT: Obsessing over idol performance gaps

Return JSON:
{{
    "detected_patterns": [
        {{
            "pattern_name": "spiral_pattern|avoidance|paralysis|comparison_burnout",
            "confidence": 0.0-1.0,
            "evidence": ["brief description of supporting events"],
            "severity": "low|moderate|high|critical"
        }}
    ],
    "overall_concern_level": 0.0-1.0,
    "intervention_urgency": "immediate|soon|monitor|none"
}}"""
    
    def _get_analysis_prompt_template(self) -> str:
        return "burnout_analysis_v1"
    
    def _get_response_prompt_template(self) -> str:
        return "response_generation_v1"
    
    def _get_pattern_prompt_template(self) -> str:
        return "pattern_detection_v1"
    
    def _fallback_analysis(self, message: str, score: float) -> Dict:
        """Fallback analysis when Gemini unavailable"""
        message_lower = message.lower()
        
        if score > 0.7:
            state = "fatigued"
        elif any(word in message_lower for word in ['stuck', 'hard', 'difficult']):
            state = "frustrated"  
        elif any(word in message_lower for word in ['tired', 'break']):
            state = "fatigued"
        else:
            state = "neutral"
        
        return {
            "emotional_state": state,
            "intensity": min(score + 0.2, 1.0),
            "hidden_feelings": "Analysis unavailable - using fallback",
            "intervention_needed": score > 0.6,
            "recommended_response_tone": "supportive" if score > 0.5 else "encouraging",
            "suggested_action": "suggest_break" if score > 0.7 else "encourage"
        }
    
    def _fallback_response(self, user_state: Dict, idol_name: str) -> str:
        """Fallback response generation"""
        score = user_state.get('burnout_score', 0)
        
        if score > 0.7:
            return f"Even {idol_name} took breaks when needed. Rest is part of growth."
        elif score > 0.5:
            return f"This reminds me of challenges {idol_name} faced early on. Keep going!"
        else:
            return f"You're making progress just like {idol_name} did. Stay focused!"