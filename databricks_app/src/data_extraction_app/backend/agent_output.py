"""Normalize agent / serving responses into plain text for the chat UI."""

from __future__ import annotations

import re
from typing import Any


def format_agent_response_for_user(raw: list[Any] | dict[str, Any] | object) -> str:
    """Turn agent response (list of message/function_call items or dict) into a single user-friendly string."""
    if isinstance(raw, list):
        parts: list[str] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "message":
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "output_text":
                        text = (block.get("text") or "").strip()
                        if re.match(r"^<name>\s*[\w-]+\s*</name>\s*$", text):
                            continue
                        if text:
                            parts.append(text)
        if parts:
            return "\n\n".join(parts)
        return str(raw)
    if isinstance(raw, dict):
        preds = raw.get("predictions")
        if isinstance(preds, list) and preds:
            return format_agent_response_for_user(preds)
        out = raw.get("output")
        if isinstance(out, list) and out:
            return format_agent_response_for_user(out)
        content = raw.get("content") or raw.get("output")
        if content is not None:
            return content if isinstance(content, str) else str(content)
        if raw.get("choices"):
            first = raw["choices"][0]
            msg = first.get("message", first) if isinstance(first, dict) else first
            if isinstance(msg, dict):
                c = msg.get("content")
                return c if isinstance(c, str) else str(msg)
            c = getattr(msg, "content", None)
            return str(c) if c is not None else str(raw)
    return str(raw)
