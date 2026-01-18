"""
Emotion Service for LeLamp

Analyzes text for emotions using Google Gemini API and triggers
matching animations based on detected emotions.
"""

import os
import logging
import time
import threading
from typing import Optional, Dict
from enum import Enum

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not available. Emotion service will be disabled.")

import lelamp.globals as g
from lelamp.user_data import get_recording_path

logger = logging.getLogger(__name__)


class Emotion(Enum):
    """Supported emotions for detection"""
    HAPPY = "happy"
    EXCITED = "excited"
    SAD = "sad"
    CURIOUS = "curious"
    THOUGHTFUL = "thoughtful"
    ANGRY = "angry"
    SURPRISED = "surprised"
    NEUTRAL = "neutral"


# Global instance
_emotion_service: Optional['EmotionService'] = None


def get_emotion_service() -> Optional['EmotionService']:
    """Get the global EmotionService instance"""
    return _emotion_service


def init_emotion_service(config: dict) -> Optional['EmotionService']:
    """Initialize the global EmotionService instance"""
    global _emotion_service
    
    emotion_config = config.get("emotion", {})
    if not emotion_config.get("enabled", False):
        logger.info("Emotion service disabled in config")
        return None
    
    try:
        _emotion_service = EmotionService(
            provider=emotion_config.get("provider", "gemini"),
            model=emotion_config.get("model", "gemini-1.5-flash"),
            auto_react=emotion_config.get("auto_react", True),
            min_confidence=emotion_config.get("min_confidence", 0.7),
            cooldown_seconds=emotion_config.get("cooldown_seconds", 2.0)
        )
        logger.info("Emotion service initialized")
        return _emotion_service
    except Exception as e:
        logger.error(f"Failed to initialize emotion service: {e}")
        _emotion_service = None
        return None


class EmotionService:
    """
    Service for detecting emotions in text and triggering animations.
    
    Uses Google Gemini API to analyze transcribed user text for emotions,
    then automatically triggers matching recordings based on detected emotions.
    """
    
    def __init__(
        self,
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        auto_react: bool = True,
        min_confidence: float = 0.7,
        cooldown_seconds: float = 2.0
    ):
        """
        Initialize emotion service.
        
        Args:
            provider: AI provider (currently only "gemini" supported)
            model: Gemini model name (e.g., "gemini-1.5-flash")
            auto_react: If True, automatically trigger animations on emotion detection
            min_confidence: Minimum confidence (0-1) to trigger reaction
            cooldown_seconds: Minimum seconds between reactions to prevent spam
        """
        self.provider = provider
        self.model_name = model
        self.auto_react = auto_react
        self.min_confidence = min_confidence
        self.cooldown_seconds = cooldown_seconds
        
        self.logger = logging.getLogger(__name__)
        self._last_reaction_time = 0.0
        self._cooldown_lock = threading.Lock()
        
        # Initialize Gemini client
        if not GEMINI_AVAILABLE:
            raise RuntimeError("google-generativeai package not installed")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        
        # Emotion to recording mapping
        self._emotion_to_recording = {
            Emotion.HAPPY: ["happy_wiggle", "excited"],
            Emotion.EXCITED: ["excited", "luxo_excited", "happy_wiggle"],
            Emotion.SAD: ["sad", "luxo_sad", "head_down"],
            Emotion.CURIOUS: ["curious", "luxo_curious"],
            Emotion.THOUGHTFUL: ["thinking", "thoughtful"],
            Emotion.ANGRY: ["luxo_sad", "head_down", "sad"],
            Emotion.SURPRISED: ["luxo_excited", "excited"],
            Emotion.NEUTRAL: ["idle"]
        }
        
        self.logger.info(f"EmotionService initialized with model {model}")
    
    def analyze_emotion(self, text: str) -> Optional[Dict[str, any]]:
        """
        Analyze text for emotion using Gemini API.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict with 'emotion' (str), 'confidence' (float), and 'raw_response' (str),
            or None if analysis fails
        """
        if not text or not text.strip():
            return None
        
        try:
            prompt = f"""Analyze the following text for emotion. Respond with ONLY a JSON object in this exact format:
{{
    "emotion": "happy|excited|sad|curious|thoughtful|angry|surprised|neutral",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Text to analyze: "{text}"

JSON response:"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=150
                )
            )
            
            # Parse response - try to extract JSON
            response_text = response.text.strip()
            
            # Find JSON in response (might have markdown code blocks)
            import json
            import re
            
            result = None
            
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            if not result:
                # Try to find JSON object directly
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            if not result:
                # Last resort: try parsing entire response
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse Gemini response as JSON: {response_text[:100]}")
                    return None
            
            if not result:
                return None
            
            # Validate result
            emotion_str = result.get("emotion", "").lower()
            confidence = float(result.get("confidence", 0.0))
            reasoning = result.get("reasoning", "")
            
            # Map to Emotion enum
            emotion_map = {
                "happy": Emotion.HAPPY,
                "excited": Emotion.EXCITED,
                "joy": Emotion.EXCITED,
                "sad": Emotion.SAD,
                "disappointed": Emotion.SAD,
                "upset": Emotion.SAD,
                "curious": Emotion.CURIOUS,
                "interested": Emotion.CURIOUS,
                "wondering": Emotion.CURIOUS,
                "thoughtful": Emotion.THOUGHTFUL,
                "thinking": Emotion.THOUGHTFUL,
                "contemplating": Emotion.THOUGHTFUL,
                "angry": Emotion.ANGRY,
                "frustrated": Emotion.ANGRY,
                "annoyed": Emotion.ANGRY,
                "surprised": Emotion.SURPRISED,
                "shocked": Emotion.SURPRISED,
                "neutral": Emotion.NEUTRAL,
                "calm": Emotion.NEUTRAL
            }
            
            emotion = emotion_map.get(emotion_str, Emotion.NEUTRAL)
            
            # Log detected emotion with details
            log_msg = (
                f"🎭 Emotion detected: '{emotion.value}' (raw: '{emotion_str}') "
                f"with confidence {confidence:.2f} "
                f"- Reasoning: {reasoning[:100] if reasoning else 'N/A'}"
            )
            self.logger.info(log_msg)
            print(log_msg)  # Also print to console for visibility
            
            return {
                "emotion": emotion,
                "emotion_str": emotion.value,
                "confidence": confidence,
                "reasoning": reasoning,
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing emotion: {e}")
            return None
    
    def map_emotion_to_recording(self, emotion: Emotion) -> Optional[str]:
        """
        Map detected emotion to a recording name.
        
        Args:
            emotion: Detected emotion
            
        Returns:
            Recording name, or None if no mapping found
        """
        recordings = self._emotion_to_recording.get(emotion, [])
        
        if not recordings:
            return None
        
        # Try each recording in order until we find one that exists
        for recording_name in recordings:
            if get_recording_path(recording_name) is not None:
                return recording_name
        
        # If none found, return first option anyway (will fail gracefully)
        return recordings[0] if recordings else None
    
    def trigger_reaction(self, text: str) -> bool:
        """
        Analyze text for emotion and trigger animation if emotion detected.
        
        Args:
            text: User transcription text
            
        Returns:
            True if reaction was triggered, False otherwise
        """
        if not self.auto_react:
            return False
        
        # Check cooldown
        with self._cooldown_lock:
            current_time = time.time()
            if current_time - self._last_reaction_time < self.cooldown_seconds:
                return False
        
        # Analyze emotion
        self.logger.debug(f"Analyzing emotion for text: '{text[:100]}...'")
        print(f"🔍 Analyzing emotion for: '{text[:80]}...'")
        result = self.analyze_emotion(text)
        if not result:
            self.logger.debug("Emotion analysis returned no result")
            print("⚠️  Emotion analysis returned no result")
            return False
        
        emotion = result["emotion"]
        confidence = result["confidence"]
        
        # Check minimum confidence
        if confidence < self.min_confidence:
            log_msg = (
                f"⚠️  Emotion '{emotion.value}' detected with confidence {confidence:.2f} "
                f"below threshold {self.min_confidence} - skipping reaction"
            )
            self.logger.info(log_msg)
            print(log_msg)
            return False
        
        # Skip neutral emotions
        if emotion == Emotion.NEUTRAL:
            self.logger.debug(f"Neutral emotion detected - skipping reaction")
            print(f"ℹ️  Neutral emotion detected - skipping reaction")
            return False
        
        # Map to recording
        recording_name = self.map_emotion_to_recording(emotion)
        if not recording_name:
            log_msg = f"⚠️  No recording mapping found for emotion: {emotion.value}"
            self.logger.warning(log_msg)
            print(log_msg)
            return False
        
        log_msg = f"📋 Mapped emotion '{emotion.value}' → recording: '{recording_name}'"
        self.logger.info(log_msg)
        print(log_msg)
        
        # Check if animation service is available
        if not g.animation_service:
            self.logger.warning("Animation service not available")
            return False
        
        # Check if recording exists
        if get_recording_path(recording_name) is None:
            self.logger.warning(f"Recording '{recording_name}' not found")
            return False
        
        # Trigger animation (non-blocking)
        try:
            g.animation_service.dispatch("play", recording_name)
            log_msg = (
                f"✅ Emotion reaction triggered: '{emotion.value}' → '{recording_name}' "
                f"(confidence: {confidence:.2f}, text: '{text[:50]}...')"
            )
            self.logger.info(log_msg)
            print(log_msg)  # Always print to console for visibility
            
            # Update cooldown
            with self._cooldown_lock:
                self._last_reaction_time = current_time
            
            return True
        except Exception as e:
            self.logger.error(f"Error triggering animation for emotion '{emotion.value}': {e}")
            return False
