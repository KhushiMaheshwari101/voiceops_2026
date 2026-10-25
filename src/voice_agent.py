import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from src.config import (
    GNANI_API_KEY,
    GNANI_TTS_MODEL,
    GNANI_TTS_VOICE,
    GNANI_LANGUAGE_CODE,
)
from src.agent import SupportAgent


def normalize_text_for_speech(text: str) -> str:
    """Normalize text so TTS reads order numbers and amounts clearly."""
    # Group long digits (like order IDs) into separated digits
    def space_digits(match):
        digits = match.group(0)
        return " ".join(list(digits))

    # Match 8 digit order IDs
    norm = re.sub(r"\b\d{8}\b", space_digits, text)
    # Match ₹ amounts: ₹500 -> 500 rupees
    norm = re.sub(r"₹\s*(\d+)", r"\1 rupees", norm)
    # Match Rs. amounts
    norm = re.sub(r"Rs\.?\s*(\d+)", r"\1 rupees", norm, flags=re.IGNORECASE)
    # Clean excessive markdown symbols
    norm = re.sub(r"[*_#`]", "", norm)
    return norm


class VoiceOpsAgent:
    def __init__(self, agent: Optional[SupportAgent] = None):
        self.agent = agent or SupportAgent(mode="step3")
        self.stt_client = None
        self.tts_client = None
        self._init_gnani()

    def _init_gnani(self):
        if not GNANI_API_KEY:
            return
        os.environ["GNANI_API_KEY"] = GNANI_API_KEY
        try:
            from gnani.stt import GnaniSTTClient
            from gnani.tts import GnaniTTSClient
            self.stt_client = GnaniSTTClient()
            self.tts_client = GnaniTTSClient()
        except Exception as e:
            print(f"Warning: Gnani SDK init warning: {e}")

    def transcribe_audio(self, audio_path: str, language_code: str = GNANI_LANGUAGE_CODE) -> str:
        """Transcribe customer audio using Gnani STT."""
        if not self.stt_client:
            return ""
        try:
            result = self.stt_client.transcribe(audio_path, language_code=language_code)
            if isinstance(result, dict):
                return result.get("transcript", "").strip()
            return str(result).strip()
        except Exception as e:
            print(f"Gnani STT error: {e}")
            return ""

    def synthesize_speech(
        self,
        text: str,
        output_file: str = "reply.wav",
        voice: str = GNANI_TTS_VOICE,
        model: str = GNANI_TTS_MODEL,
        language: str = GNANI_LANGUAGE_CODE,
    ) -> bool:
        """Synthesize agent reply using Gnani TTS."""
        if not self.tts_client:
            return False
        speech_text = normalize_text_for_speech(text)
        try:
            self.tts_client.synthesize(
                speech_text,
                voice=voice,
                model=model,
                language=language,
                output_file=output_file,
            )
            return os.path.exists(output_file)
        except Exception as e:
            print(f"Gnani TTS error: {e}")
            return False

    def voice_turn(
        self,
        audio_path: str,
        output_audio_path: str = "reply.wav",
    ) -> Dict[str, Any]:
        """
        Execute one complete turn of the VoiceOps pipeline:
        Audio -> Gnani STT -> Agent Brain -> Gnani TTS -> Reply Audio
        """
        heard = self.transcribe_audio(audio_path)
        if not heard:
            reply = "Sorry, I didn't catch that. Could you say it again?"
            retrieved_tokens = []
            tool_calls = None
        else:
            reply, retrieved_tokens, tool_calls = self.agent.respond(heard)

        # Synthesize audio
        success = self.synthesize_speech(reply, output_file=output_audio_path)

        return {
            "transcript_heard": heard,
            "agent_reply": reply,
            "audio_file": output_audio_path if success else None,
            "retrieved_tokens": retrieved_tokens,
            "tool_calls": tool_calls,
        }
