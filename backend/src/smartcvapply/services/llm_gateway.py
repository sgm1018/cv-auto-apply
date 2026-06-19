"""LLM gateway with LiteLLM supporting multiple providers."""
import json
import re
from typing import Any

import litellm

from smartcvapply.core.exceptions import (
    LLMError,
    LLMInvalidKeyError,
    LLMNotConfigured,
    LLMTimeoutError,
)


class LLMGateway:
    """Unified adapter for DeepSeek, OpenAI, Anthropic, Ollama, or custom endpoints."""

    _DEFAULT_BASES: dict[str, str] = {
        "deepseek": "https://api.deepseek.com/v1",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
    }

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
        self.api_base = api_base or self._DEFAULT_BASES.get(provider)
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

    async def _acomplete(
        self, *, system: str, user_msg: str, timeout: int, max_tokens: int,
        response_format: dict | None = None,
    ) -> tuple[str, Any]:
        kw = self._kwargs()
        params = dict(
            model=self.model_string,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            timeout=timeout,
            max_tokens=max_tokens,
        )
        if response_format:
            params["response_format"] = response_format
        try:
            resp = await litellm.acompletion(**params, **kw)
        except litellm.AuthenticationError as e:
            raise LLMInvalidKeyError(str(e)) from e
        except litellm.Timeout as e:
            raise LLMTimeoutError(str(e)) from e
        except litellm.APIConnectionError as e:
            raise LLMNotConfigured(str(e)) from e
        except litellm.Exception as e:
            raise LLMError(str(e)) from e
        content = resp["choices"][0]["message"]["content"]
        return content, resp

    async def complete_json(
        self, *, system: str, user_msg: str, timeout: int = 30, max_tokens: int = 1500,
    ) -> dict:
        content, _resp = await self._acomplete(
            system=system, user_msg=user_msg, timeout=timeout, max_tokens=max_tokens,
        )
        obj = _extract_json(content)
        if obj is not None:
            return obj
        # Fallback 1: retry with json_object response_format
        content, _resp = await self._acomplete(
            system=system, user_msg=user_msg, timeout=timeout, max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        obj = _extract_json(content)
        if obj is not None:
            return obj
        # Fallback 2: try with legacy model name if current model returns empty
        if self.provider == "deepseek" and self.model != "deepseek-chat":
            saved_model = self.model_string
            self.model_string = "deepseek/deepseek-chat"
            try:
                content, _resp = await self._acomplete(
                    system=system, user_msg=user_msg, timeout=timeout, max_tokens=max_tokens,
                )
                obj = _extract_json(content)
                if obj is not None:
                    return obj
            finally:
                self.model_string = saved_model
        snippet = content[:200] if content else "(empty)"
        raise LLMError(f"LLM returned non-JSON. Snippet: {snippet}")

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

def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from arbitrary text via regex."""
    # Match {...} or [...] blocks, longest first
    for pattern in (r'\{.*\}', r'\[.*\]'):
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    return None
