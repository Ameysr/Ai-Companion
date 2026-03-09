"""
provider.py — Unified LLM interface for Gemini + DeepSeek.
Tries Gemini first, falls back to DeepSeek, handles errors.
"""

import json
from google import genai
from google.genai import types
from openai import OpenAI
from config import (
    GEMINI_API_KEY, DEEPSEEK_API_KEY,
    GEMINI_MODEL, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, LLM_PROVIDER,
)


class LLMProvider:
    """Unified LLM interface with Gemini primary + DeepSeek fallback."""

    def __init__(self):
        self._gemini_ready = False
        self._gemini_client = None
        self._deepseek_client = None

        # Token usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_requests = 0

        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            self._gemini_ready = True

        if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your_deepseek_api_key_here":
            self._deepseek_client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
            )

    def get_usage(self) -> dict:
        """Return cumulative token usage stats."""
        return {
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "total_requests": self._total_requests,
        }

    def _track_usage(self, prompt_tokens: int, completion_tokens: int):
        """Accumulate token counts."""
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._total_requests += 1

    @property
    def is_available(self) -> bool:
        return self._gemini_ready or self._deepseek_client is not None

    @property
    def active_provider(self) -> str:
        if LLM_PROVIDER == "deepseek" and self._deepseek_client:
            return "DeepSeek"
        if self._gemini_ready:
            return "Gemini"
        elif self._deepseek_client:
            return "DeepSeek"
        return "None"

    def call(self, prompt: str, system_prompt: str = "",
             temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Call LLM with automatic fallback. Respects LLM_PROVIDER setting."""
        # DeepSeek as primary
        if LLM_PROVIDER == "deepseek" and self._deepseek_client:
            try:
                return self._call_deepseek(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                if self._gemini_ready:
                    return self._call_gemini(prompt, system_prompt, temperature, max_tokens)
                raise e

        # Gemini as primary (default)
        if self._gemini_ready:
            try:
                return self._call_gemini(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                if self._deepseek_client:
                    return self._call_deepseek(prompt, system_prompt, temperature, max_tokens)
                raise e

        if self._deepseek_client:
            return self._call_deepseek(prompt, system_prompt, temperature, max_tokens)

        return "[No LLM configured. Please add GEMINI_API_KEY or DEEPSEEK_API_KEY to your .env file.]"

    def call_json(self, prompt: str, system_prompt: str = "",
                  temperature: float = 0.3) -> dict:
        """Call LLM and parse response as JSON."""
        full_prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no code fences, no extra text."
        response = self.call(full_prompt, system_prompt, temperature)

        # Clean up response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse JSON", "raw": response}

    def _call_gemini(self, prompt: str, system_prompt: str,
                     temperature: float, max_tokens: int) -> str:
        contents = prompt
        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = self._gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        # Track token usage from Gemini response metadata
        try:
            usage = response.usage_metadata
            if usage:
                self._track_usage(
                    getattr(usage, 'prompt_token_count', 0) or 0,
                    getattr(usage, 'candidates_token_count', 0) or 0,
                )
        except Exception:
            pass
        return response.text

    def _call_deepseek(self, prompt: str, system_prompt: str,
                       temperature: float, max_tokens: int) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Track token usage from DeepSeek/OpenAI response
        try:
            usage = response.usage
            if usage:
                self._track_usage(
                    getattr(usage, 'prompt_tokens', 0) or 0,
                    getattr(usage, 'completion_tokens', 0) or 0,
                )
        except Exception:
            pass
        return response.choices[0].message.content
