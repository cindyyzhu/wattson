"""
Emotion Service for LeLamp

Provides emotion detection from text using Google Gemini API,
with automatic animation triggering based on detected emotions.
"""

from .emotion_service import EmotionService, get_emotion_service, init_emotion_service

__all__ = ['EmotionService', 'get_emotion_service', 'init_emotion_service']
