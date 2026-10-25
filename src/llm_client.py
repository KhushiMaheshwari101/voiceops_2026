import os
import time
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from src.config import GEMINI_API_KEY


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = None
        self._init_model()

    def _init_model(self):
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception:
            # Fallback to gemini-1.5-flash if 2.5 is unavailable
            self.model_name = "gemini-1.5-flash"
            self.model = genai.GenerativeModel(self.model_name)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> str:
        """Call Gemini LLM with retry mechanism."""
        if not self.api_key:
            return "API Key not configured."

        if system_instruction:
            active_model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )
        else:
            active_model = self.model

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=500,
        )

        for attempt in range(max_retries):
            try:
                response = active_model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                if response and response.text:
                    return response.text.strip()
                return ""
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    time.sleep(2 * (attempt + 1))
                elif attempt == max_retries - 1:
                    # Try fallback model if last attempt failed
                    if "2.5" in self.model_name:
                        self.model_name = "gemini-1.5-flash"
                        self._init_model()
                        try:
                            fallback_model = genai.GenerativeModel(
                                self.model_name,
                                system_instruction=system_instruction,
                            )
                            resp = fallback_model.generate_content(
                                prompt, generation_config=generation_config
                            )
                            return resp.text.strip() if resp and resp.text else ""
                        except Exception:
                            pass
                    return f"Error contacting model: {err_str}"
                else:
                    time.sleep(1)
        return ""
