# voice_manager_cpu_optimized.py - Con .env loading
import asyncio
import os
import tempfile
import time
import subprocess
from typing import Dict, Optional, Tuple
import whisper
from openai import OpenAI
import scipy.io.wavfile as wavfile
import numpy as np
from dotenv import load_dotenv
from voice_types import *

# Load environment variables
load_dotenv()

class CPUOptimizedVoiceManager:
    def __init__(self):
        # Verify OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment. Check your .env file.")
        
        # Load Whisper model
        print("📥 Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("✅ Whisper loaded")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=api_key)
        print(f"✅ OpenAI client initialized with key: {api_key[:20]}...")
        
        # CPU-Optimized voice configuration (NO BARK)
        self.agent_voice_config = {
            AgentType.CUSTOMER_SERVICE: {
                "tier": VoiceTier.PREMIUM,
                Language.SPANISH_MX: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1-hd",
                    voice="nova",  # Female, clear, empathetic
                    speed=1.0
                ),
                Language.ENGLISH: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1-hd", 
                    voice="shimmer",  # Female, warm
                    speed=1.0
                )
            },
            AgentType.SALES: {
                "tier": VoiceTier.PREMIUM,
                Language.SPANISH_MX: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1-hd",
                    voice="onyx",  # Male, deep, authoritative
                    speed=1.1
                ),
                Language.ENGLISH: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1-hd",
                    voice="echo",  # Male, clear, confident
                    speed=1.1
                )
            },
            AgentType.INTERNAL: {
                "tier": VoiceTier.STANDARD,
                Language.SPANISH_MX: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1",  # Faster, cheaper
                    voice="alloy",   # Neutral
                    speed=1.2
                ),
                Language.ENGLISH: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1",
                    voice="alloy",
                    speed=1.2
                )
            },
            AgentType.RAG_ASSISTANT: {
                "tier": VoiceTier.STANDARD,
                Language.SPANISH_MX: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1",
                    voice="fable",  # British, narrative
                    speed=1.1
                ),
                Language.ENGLISH: VoiceConfig(
                    provider=TTSProvider.OPENAI,
                    model="tts-1",
                    voice="fable",
                    speed=1.1
                )
            },
            AgentType.TESTING: {
                "tier": VoiceTier.BASIC,
                Language.SPANISH_MX: VoiceConfig(
                    provider=TTSProvider.ESPEAK,
                    voice="es-mx",
                    speed=150
                ),
                Language.ENGLISH: VoiceConfig(
                    provider=TTSProvider.ESPEAK,
                    voice="en",
                    speed=150
                )
            }
        }

    async def transcribe_audio(self, audio_data: bytes, language: Language) -> str:
        """Speech to Text using Whisper - CPU optimized"""
        try:
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe with language hint
            language_code = "es" if language == Language.SPANISH_MX else "en"
            result = self.whisper_model.transcribe(
                temp_path, 
                language=language_code,
                fp16=False  # CPU optimization
            )
            
            # Cleanup
            os.unlink(temp_path)
            
            transcript = result["text"].strip()
            print(f"🎤 Transcribed: {transcript}")
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""

    async def generate_speech(self, text: str, agent_type: AgentType, language: Language) -> AudioResponse:
        """Generate speech using CPU-optimized providers"""
        
        config = self.agent_voice_config[agent_type][language]
        tier = self.agent_voice_config[agent_type]["tier"]
        
        start_time = time.time()
        
        try:
            if config.provider == TTSProvider.OPENAI:
                audio_data, cost = await self._generate_openai_speech(text, config)
            elif config.provider == TTSProvider.ESPEAK:
                audio_data, cost = await self._generate_espeak_speech(text, config, language)
            else:
                raise ValueError(f"Unknown provider: {config.provider}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AudioResponse(
                audio_data=audio_data,
                text=text,
                language=language.value,
                tier=tier.value,
                provider=config.provider.value,
                cost=cost,
                duration_ms=duration_ms,
                voice_used=config.voice
            )
            
        except Exception as e:
            print(f"❌ Speech generation error: {e}")
            # Fallback to eSpeak
            audio_data, cost = await self._generate_espeak_speech(
                text, 
                VoiceConfig(provider=TTSProvider.ESPEAK, voice="es-mx" if language == Language.SPANISH_MX else "en"),
                language
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            return AudioResponse(
                audio_data=audio_data,
                text=text,
                language=language.value,
                tier="basic",
                provider="espeak",
                cost=0.0,
                duration_ms=duration_ms,
                voice_used="fallback"
            )

    async def _generate_openai_speech(self, text: str, config: VoiceConfig) -> Tuple[bytes, float]:
        """Generate speech using OpenAI TTS - FAST on CPU"""
        try:
            print(f"🔊 Generating OpenAI speech: {config.model}/{config.voice}")
            
            response = self.openai_client.audio.speech.create(
                model=config.model,
                voice=config.voice,
                input=text,
                speed=config.speed,
                response_format=config.response_format
            )
            
            # Calculate cost (approximate)
            cost_per_char = 0.000015 if config.model == "tts-1" else 0.00003
            cost = len(text) * cost_per_char
            
            audio_data = response.content
            print(f"✅ OpenAI TTS generated {len(audio_data)} bytes")
            
            return audio_data, cost
            
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
            raise

    async def _generate_espeak_speech(self, text: str, config: VoiceConfig, language: Language) -> Tuple[bytes, float]:
        """Generate speech using eSpeak-ng - Ultra fast fallback"""
        try:
            print(f"🔊 Generating eSpeak speech: {config.voice}")
            
            voice = config.voice or ("es-mx" if language == Language.SPANISH_MX else "en")
            speed = getattr(config, 'speed', 150)
            
            # Run eSpeak
            result = subprocess.run([
                "espeak-ng",
                "-s", str(int(speed)),  # Speed (words per minute)
                "-v", voice,            # Voice
                "-a", "100",            # Amplitude
                text,
                "--stdout"
            ], capture_output=True, check=True)
            
            audio_data = result.stdout
            print(f"✅ eSpeak generated {len(audio_data)} bytes")
            
            return audio_data, 0.0  # Free
            
        except subprocess.CalledProcessError as e:
            print(f"❌ eSpeak error: {e}")
            raise
        except Exception as e:
            print(f"❌ eSpeak unexpected error: {e}")
            raise

    def get_voice_costs(self) -> Dict:
        """Return current voice generation costs"""
        return {
            "openai_tts_1": 0.000015,      # per character
            "openai_tts_1_hd": 0.00003,    # per character
            "espeak": 0.0,                 # free
            "whisper": 0.006               # per minute (OpenAI API)
        }

    def get_available_voices(self) -> Dict:
        """Return available voices by provider"""
        return {
            "openai": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            "espeak": ["es", "es-mx", "en", "en-us", "en-gb"]
        }
