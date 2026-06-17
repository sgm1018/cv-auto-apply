"""LLM gateway with LiteLLM supporting multiple providers."""
import json
from typing import Any

import litellm

from cvapplier.core.exceptions import (
    LLMError,
    LLMInvalidKeyError,
    LLMNotConfigured,
    LLMTimeoutError,
)


class LLMGateway:
    """Unified adapter for DeepSeek, OpenAI, Anthropic, Ollama, or custom endpoints."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.model_string = model if provider == "custom" else f"{provider}/{model}"

    def _kwargs(self) -> dict[str, Any]:
        kw: dict[str, Any] = {}
        if self.api_key:
            kw["api_key"] = self.api_key
        if self.api_base:
            kw["api_base"] = self.api_base
        return kw

    async def ping(self) -> None:
        try:
            await litellm.acompletion(
                model=self.model_string,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                **self._kwargs(),
            )
        except litellm.AuthenticationError as e:
            raise LLMInvalidKeyError(str(e)) from e
        except litellm.Timeout as e:
            raise LLMTimeoutError(str(e)) from e
        except litellm.APIConnectionError as e:
            raise LLMNotConfigured(str(e)) from e
        except litellm.Exception as e:
            raise LLMError(str(e)) from e

    async def complete_json(
        self, *, system: str, user_msg: str, timeout: int = 30, max_tokens: int = 1500,
    ) -> dict:
        try:
            resp = await litellm.acompletion(
                model=self.model_string,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                timeout=timeout,
                max_tokens=max_tokens,
                **self._kwargs(),
            )
        except litellm.AuthenticationError as e:
            raise LLMInvalidKeyError(str(e)) from e
        except litellm.Timeout as e:
            raise LLMTimeoutError(str(e)) from e
        except litellm.APIConnectionError as e:
            raise LLMNotConfigured(str(e)) from e
        except litellm.Exception as e:
            raise LLMError(str(e)) from e
        content = resp["choices"][0]["message"]["content"]
        return self._parse_and_validate(content)

    async def complete_text(
        self, *, system: str, user_msg: str, timeout: int = 30, max_tokens: int = 2000,
    ) -> str:
        try:
            resp = await litellm.acompletion(
                model=self.model_string,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                timeout=timeout,
                max_tokens=max_tokens,
                **self._kwargs(),
            )
        except litellm.Exception as e:
            raise LLMError(str(e)) from e
        return resp["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_and_validate(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM returned non-JSON: {e}") from e
