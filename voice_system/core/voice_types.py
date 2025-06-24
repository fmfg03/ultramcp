# voice_types.py
from enum import Enum
from typing import Dict, Optional, Union
from dataclasses import dataclass

class VoiceTier(Enum):
    PREMIUM = "premium"      # OpenAI TTS-HD - Customer facing
    STANDARD = "standard"    # OpenAI TTS-1 - Internal use
    BASIC = "basic"         # eSpeak - Testing only

class AgentType(Enum):
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    INTERNAL = "internal"
    TESTING = "testing"
    RAG_ASSISTANT = "rag_assistant"

class Language(Enum):
    SPANISH_MX = "es_mx"
    ENGLISH = "en"

class TTSProvider(Enum):
    OPENAI = "openai"
    ESPEAK = "espeak"

@dataclass
class VoiceConfig:
    provider: TTSProvider = TTSProvider.OPENAI
    model: str = "tts-1"
    voice: str = "alloy"
    speed: float = 1.0
    response_format: str = "mp3"

@dataclass
class AudioResponse:
    audio_data: bytes
    text: str
    language: str
    tier: str
    provider: str
    cost: float
    duration_ms: int
    voice_used: str
