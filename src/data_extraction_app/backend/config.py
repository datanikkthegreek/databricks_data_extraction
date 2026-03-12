"""All configurable values. Override via env vars: DATA_EXTRACTION_HOST, DATA_EXTRACTION_TOKEN, DATA_EXTRACTION_WAREHOUSE_HTTP_PATH, DATA_EXTRACTION_VOLUME_PATH, DATA_EXTRACTION_PROCESSING_JOB_ID, DATA_EXTRACTION_APP_AI_QUERY_TABLE."""

import os
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .._metadata import app_name, app_slug

if TYPE_CHECKING:
    from fastapi import Request

# Same as Flask: user_token = request.headers.get('x-forwarded-access-token')
# In FastAPI you inject Request and use request.headers.get(...) the same way.
FORWARDED_ACCESS_TOKEN_HEADER = "x-forwarded-access-token"


def get_access_token(request: "Request | None", config: "AppConfig | None" = None) -> str:
    """
    Resolve access token: x-forwarded-access-token header if present, else config.token (env fallback).
    When config is None, only the header is used (no env fallback).

    Flask equivalent:
        from flask import request
        user_token = request.headers.get('x-forwarded-access-token')

    FastAPI equivalent (in a route):
        @app.get("/")
        def route(request: Request):
            user_token = request.headers.get("x-forwarded-access-token")
    """
    header = (request.headers.get(FORWARDED_ACCESS_TOKEN_HEADER) or "").strip() if request else ""
    if header:
        return header
    if config is not None:
        return (config.token or "").strip()
    return ""


def get_access_token_diagnostic(request: "Request | None", config: "AppConfig | None" = None) -> dict:
    """
    Returns a small dict for debugging auth: header_present, token_resolved, hint.
    Use in 401 responses or a /api/auth/diagnostic endpoint. Does not expose token values.
    """
    header_val = (request.headers.get(FORWARDED_ACCESS_TOKEN_HEADER) or "").strip() if request else ""
    header_present = bool(header_val)
    fallback = (config.token or "").strip() if config is not None else ""
    token_resolved = bool(header_val or fallback)

    if token_resolved:
        hint = "Token resolved from header." if header_present else "Token resolved from env fallback (FEVM_TOKEN / DATA_EXTRACTION_TOKEN)."
    else:
        hint = (
            "Missing x-forwarded-access-token and no env fallback. "
            "On Databricks: open the app from the Databricks Apps launcher (not a direct URL) so the platform injects the header. "
            "Locally: set FEVM_TOKEN or DATA_EXTRACTION_TOKEN."
        )
    return {
        "header_present": header_present,
        "token_resolved": token_resolved,
        "hint": hint,
    }

# .env next to project root (parent of src)
_env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=_env_file,
        env_prefix="DATA_EXTRACTION_",
        extra="ignore",
    )

    # App
    app_name: str = Field(default=app_name, description="Application name")

    # Databricks
    host: str = Field(
        default="https://e2-demo-field-eng.cloud.databricks.com",
        description="Databricks workspace URL",
    )
    # OAuth M2M: when both set, used for all workspace/auth (no user token required)
    client_id: str = Field(
        default_factory=lambda: os.environ.get("DATABRICKS_CLIENT_ID", ""),
        description="OAuth client ID (app ID). When set with client_secret, auth uses OAuth M2M everywhere.",
    )
    client_secret: str = Field(
        default_factory=lambda: os.environ.get("DATABRICKS_CLIENT_SECRET", ""),
        description="OAuth client secret. When set with client_id, auth uses OAuth M2M everywhere.",
    )
    token: str = Field(
        default_factory=lambda: os.environ.get("FEVM_TOKEN", ""),
        description="Fallback PAT. Used when OAuth M2M (client_id/secret) is not set and X-Forwarded-Access-Token is not present.",
    )

    def use_oauth_m2m(self) -> bool:
        """True when client_id and client_secret are both set (use OAuth M2M for all auth)."""
        return bool((self.client_id or "").strip() and (self.client_secret or "").strip())

    # SQL Warehouse
    warehouse_http_path: str = Field(
        default="/sql/1.0/warehouses/4b9b953939869799",
        description="SQL Warehouse HTTP path",
    )

    # Volume & jobs
    volume_path: str = Field(
        default="/Volumes/data_extraction/default/documents",
        description="Volume path for PDF storage",
    )
    processing_job_id: str = Field(
        default="170364782025692",
        description="Job ID for Execute processing",
    )

    # Tables
    app_ai_query_table: str = Field(
        default="data_extraction.data_extraction.app_productmanuals_processed",
        description="Full table name (catalog.schema.table) for AI query results",
    )

    # Agent chat
    agent_endpoint: str = Field(
        default="mas-ce26527c-endpoint",
        description="Databricks agent endpoint name for chat",
    )
    # Supervisor Agent (multi-agent) endpoint created in Agents → Supervisor Agent
    supervisor_agent_endpoint: str = Field(
        default="",
        description="Supervisor Agent endpoint name (e.g. supervisor-agent-extraction). Override via DATA_EXTRACTION_SUPERVISOR_AGENT_ENDPOINT.",
    )

    # token fallback: FEVM_TOKEN or DATA_EXTRACTION_* from env (see get_access_token)

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")
