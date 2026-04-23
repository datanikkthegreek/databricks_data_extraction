"""
Databricks Apps / MLflow GenAI agent server handler.

Uses ``user_client = get_user_workspace_client(...)`` then ``user_client.serving_endpoints.query(...)``
with the end-user OBO token — not the app’s generic ``WorkspaceClient`` from route dependencies.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, Request
from mlflow.genai.agent_server import invoke
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

from ..agent_output import format_agent_response_for_user
from ..config import AppConfig
from ..models import ChatMessageOut
from ..logger import logger
from ..workspace_auth import (
    MissingServingUserTokenError,
    get_supervisor_endpoint_name,
    get_user_workspace_client,
)


def _minimal_assistant_message(text: str) -> dict[str, Any]:
    return {
        "type": "message",
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": text, "annotations": []}],
    }


def _serving_response_to_output_items(resp: Any) -> list[dict[str, Any]]:
    """Map ``serving_endpoints.query`` response to MLflow Responses ``output`` list."""
    d = resp.as_dict() if hasattr(resp, "as_dict") else {}
    if not isinstance(d, dict):
        return [_minimal_assistant_message(str(resp))]

    out = d.get("output")
    if isinstance(out, list) and out and isinstance(out[0], dict):
        return out

    preds = d.get("predictions")
    if isinstance(preds, list) and preds:
        p0 = preds[0]
        if isinstance(p0, dict):
            inner = p0.get("output")
            if isinstance(inner, list) and inner:
                return inner
            if isinstance(inner, str) and inner.strip():
                return [_minimal_assistant_message(inner)]
            if p0.get("type") == "message":
                return [p0]
            text = format_agent_response_for_user([p0] if p0 else preds)
            return [_minimal_assistant_message(text)]
        if isinstance(p0, str):
            return [_minimal_assistant_message(p0)]

    choices = d.get("choices")
    if isinstance(choices, list) and choices:
        c0 = choices[0]
        if isinstance(c0, dict):
            msg = c0.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, str) and content.strip():
                return [_minimal_assistant_message(content)]

    text = format_agent_response_for_user(d.get("predictions") or d)
    return [_minimal_assistant_message(text)]


def chat_supervisor_query(
    request: Request,
    config: AppConfig,
    api_messages: list[dict[str, str]],
) -> ChatMessageOut:
    """
    Same serving call as :func:`invoke_handler`, for the FastAPI ``/api/chat`` route.

    Uses ``x-forwarded-access-token`` on the request (never the volume/env PAT fallback used
    elsewhere), so ``serving_endpoints.query`` runs as the signed-in user on Apps.
    """
    endpoint = (config.agent_endpoint or get_supervisor_endpoint_name() or "").strip()
    if not endpoint:
        raise HTTPException(
            status_code=503,
            detail="DATA_EXTRACTION_AGENT_ENDPOINT / config.agent_endpoint is not set.",
        )
    try:
        user_client = get_user_workspace_client(request, override_host=config.host)
    except MissingServingUserTokenError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "message": str(e),
                "fix_databricks": "Open the app from the workspace Apps launcher so x-forwarded-access-token is injected.",
            },
        ) from e
    payload = [dict(m) for m in api_messages]
    try:
        resp = user_client.serving_endpoints.query(name=endpoint, input=payload)
    except Exception as first:
        logger.warning(
            "[CHAT] user_client.serving_endpoints.query(input=...) failed (%s: %s); retrying with inputs={'input': ...}",
            type(first).__name__,
            first,
        )
        resp = user_client.serving_endpoints.query(name=endpoint, inputs={"input": payload})

    d = resp.as_dict() if hasattr(resp, "as_dict") else {}
    text = format_agent_response_for_user(d)
    return ChatMessageOut(role="assistant", content=text)


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    endpoint = get_supervisor_endpoint_name()
    if not endpoint:
        raise ValueError("DATA_EXTRACTION_AGENT_ENDPOINT is not set in the environment.")

    user_client = get_user_workspace_client()
    payload = [m.model_dump(mode="json", exclude_none=True) for m in request.input]
    try:
        resp = user_client.serving_endpoints.query(name=endpoint, input=payload)
    except Exception as first:
        logger.warning(
            "[AGENT] user_client.serving_endpoints.query(input=...) failed (%s: %s); retrying with inputs={'input': ...}",
            type(first).__name__,
            first,
        )
        resp = user_client.serving_endpoints.query(name=endpoint, inputs={"input": payload})
    output = _serving_response_to_output_items(resp)
    return ResponsesAgentResponse(output=output)
