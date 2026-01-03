"""LLM client helpers for extracting structured answers."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class OpenAIClient:
    """Lightweight OpenAI chat wrapper for JSON extraction."""

    def __init__(self, model: Optional[str] = None) -> None:
        from openai import OpenAI

        self._client = OpenAI()
        self._model = model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

    def extract_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


def get_openai_client() -> Optional[OpenAIClient]:
    """Return an OpenAI client if API key is configured."""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIClient()
    return None
