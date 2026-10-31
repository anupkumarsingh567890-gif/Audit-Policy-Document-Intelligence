"""Gemini API integration using the Google Gen AI SDK (`google-genai`).

Speed features
- Streaming: `generate_stream()` yields the answer piece by piece, so the UI
  can show text as soon as Gemini starts writing.
- Thinking control: recent Flash models "think" before answering, which adds
  seconds. For answering from 5 short passages a low thinking level is enough;
  set GEMINI_THINKING in .env (off / low / default).
- Fallback: a rate-limited model is skipped immediately and put on a cooldown.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from src.utils import config


class GeminiError(RuntimeError):
    """Readable error shown to the user."""


# Actions decided from an API error
_NEXT_MODEL, _RETRY = "next", "retry"


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_models: list[str] | None = None,
        temperature: float = config.GEMINI_TEMPERATURE,
        max_output_tokens: int = config.GEMINI_MAX_OUTPUT_TOKENS,
        thinking: str = config.GEMINI_THINKING,
    ):
        from google import genai
        from google.genai import types

        api_key = (api_key or config.GEMINI_API_KEY).strip()
        if not api_key or api_key.startswith("your_"):
            raise GeminiError(
                "GEMINI_API_KEY is not set. Add it to the .env file in the project folder "
                "(get a free key at https://aistudio.google.com/apikey)."
            )
        # Fail after 60 s instead of hanging if Gemini doesn't respond
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=20_000))
        self.model = model or config.GEMINI_MODEL
        fallbacks = fallback_models if fallback_models is not None else config.GEMINI_FALLBACK_MODELS
        self.models_to_try = [self.model] + [m for m in fallbacks if m != self.model]
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.thinking = (thinking or "default").lower()
        self.last_model_used: str | None = None
        self.cooldown_seconds = 60
        self._cooldown_until: dict[str, float] = {}
        self._no_thinking_config: set[str] = set()   # models that rejected our thinking setting

    # ------------------------------------------------------------ helpers
    def _thinking_config(self, model: str):
        from google.genai import types

        if self.thinking == "default" or model in self._no_thinking_config:
            return None
        if "2.5" in model:   # Gemini 2.5 uses a token budget (0 = no thinking)
            return types.ThinkingConfig(thinking_budget=0 if self.thinking == "off" else 512)
        level = types.ThinkingLevel.MINIMAL if self.thinking == "off" else types.ThinkingLevel.LOW
        return types.ThinkingConfig(thinking_level=level)   # Gemini 3+ and -latest aliases

    def _config(self, model: str, system_prompt: str):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            thinking_config=self._thinking_config(model),
        )

    def _candidates(self) -> list[str]:
        now = time.monotonic()
        ready = [m for m in self.models_to_try if self._cooldown_until.get(m, 0) <= now]
        return ready or self.models_to_try   # if all are cooling down, try anyway

    def _handle_error(self, exc: Exception, model: str, attempt: int) -> str:
        """Decide what to do after an error: try the next model, retry this one, or raise."""
        from google.genai import errors

        msg = str(exc).lower()
        if isinstance(exc, errors.ClientError):
            code = getattr(exc, "code", None)
            if code == 429:                                   # rate limit -> next model now
                self._cooldown_until[model] = time.monotonic() + self.cooldown_seconds
                return _NEXT_MODEL
            if code == 400 and "thinking" in msg and model not in self._no_thinking_config:
                self._no_thinking_config.add(model)          # retry without the thinking setting
                return _RETRY
            if code == 404 or (code == 400 and "not found" in msg):
                self._cooldown_until[model] = time.monotonic() + 3600
                return _NEXT_MODEL
            if code in (401, 403) or "api key" in msg:
                raise GeminiError(f"Gemini rejected the API key: {exc}") from exc
            raise GeminiError(f"Gemini request failed: {exc}") from exc
        if isinstance(exc, errors.ServerError) and attempt == 0:   # 5xx -> one quick retry
            time.sleep(2)
            return _RETRY
        return _NEXT_MODEL                                     # timeouts, network, repeated 5xx

    # ------------------------------------------------------------ public API
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Return the complete answer (used by scripts and evaluation)."""
        return "".join(self.generate_stream(system_prompt, user_prompt)).strip()

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """Yield the answer as it is generated.

        Falling back to another model is only possible before the first piece
        of text arrives; `last_model_used` is set as soon as text starts.
        """
        candidates = self._candidates()
        last_error: Exception | None = None

        for model in candidates:
            attempt = 0
            while attempt < 3:
                started = False
                try:
                    stream = self._client.models.generate_content_stream(
                        model=model, contents=user_prompt, config=self._config(model, system_prompt)
                    )
                    for chunk in stream:
                        text = chunk.text or ""
                        if not text:
                            continue
                        if not started:
                            started = True
                            self.last_model_used = model
                        yield text
                    if not started:
                        raise GeminiError("Gemini returned an empty response (it may have been blocked by safety filters).")
                    return
                except GeminiError:
                    raise
                except Exception as exc:  
                    if started:   # text already shown -> can't switch models now
                        raise GeminiError(f"The answer was interrupted: {exc}") from exc
                    last_error = exc
                    if self._handle_error(exc, model, attempt) == _NEXT_MODEL:
                        break
                    attempt += 1

        raise GeminiError(
            "Gemini is unavailable right now — the free-tier limit has probably been reached "
            f"for {', '.join(candidates)}. Wait a minute and try again, or use Semantic Retrieval mode "
            f"(no Gemini needed). Details: {last_error}"
        )

    def list_models(self) -> list[str]:
        names = []
        for m in self._client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if not actions or "generateContent" in actions:
                names.append(m.name.replace("models/", ""))
        return sorted(names)
