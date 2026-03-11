"""
Rel GPT client utilities.
Supports OpenAI-compatible chat completion endpoints.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


class RelGPTClient:
    """Thin wrapper around an OpenAI-compatible API for Rel GPT usage."""

    def __init__(self) -> None:
        rel_api_key = os.getenv("REL_GPT_API_KEY", "").strip()
        rel_base_url = os.getenv("REL_GPT_BASE_URL", "").strip()
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

        self.model = os.getenv("REL_GPT_MODEL", "gpt-4.1-mini")
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4.1-mini")

        self.rel_enabled = bool(rel_api_key)
        self.openai_enabled = bool(openai_api_key)
        self.enabled = self.rel_enabled or self.openai_enabled

        self.rel_client = OpenAI(api_key=rel_api_key, base_url=rel_base_url or None) if self.rel_enabled else None
        self.openai_client = OpenAI(api_key=openai_api_key) if self.openai_enabled else None

        if not self.enabled:
            logger.warning(
                "No model API key found. Set REL_GPT_API_KEY and/or OPENAI_API_KEY for AI generation."
            )

    def _chat_completion(
        self,
        client: OpenAI,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Optional[str]:
        """Execute a chat completion and normalize text output."""
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            return None
        if isinstance(content, str):
            return content.strip()
        try:
            chunks = []
            for part in content:
                part_text = getattr(part, "text", None)
                if part_text:
                    chunks.append(part_text)
            return "\n".join(chunks).strip() if chunks else None
        except Exception:
            return str(content).strip()

    def generate_text(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """Generate plain text from Rel GPT."""
        if not self.enabled:
            return None

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        if self.rel_enabled and self.rel_client:
            try:
                text = self._chat_completion(
                    client=self.rel_client,
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if text:
                    return text
            except Exception as exc:
                logger.error("Rel GPT text generation failed: %s", exc)

        if self.openai_enabled and self.openai_client:
            try:
                text = self._chat_completion(
                    client=self.openai_client,
                    model=self.fallback_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if text:
                    logger.info("Used OpenAI fallback model for text generation")
                    return text
            except Exception as exc:
                logger.error("OpenAI fallback text generation failed: %s", exc)
        return None

    def generate_json(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> Optional[Any]:
        """Generate and parse JSON from Rel GPT output."""
        text = self.generate_text(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if not text:
            return None

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
            if not match:
                logger.warning("Rel GPT returned non-JSON text")
                return None
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("Rel GPT JSON extraction failed")
                return None


rel_gpt_client = RelGPTClient()
