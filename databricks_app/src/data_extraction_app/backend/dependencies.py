from typing import Annotated

from databricks.sdk import WorkspaceClient
from fastapi import Depends, HTTPException, Request

from .config import AppConfig, get_access_token, get_access_token_diagnostic
from .runtime import Runtime


def get_config(request: Request) -> AppConfig:
    """
    Returns the AppConfig instance from app.state.
    The config is initialized during application lifespan startup.
    """
    if not hasattr(request.app.state, "config"):
        raise RuntimeError(
            "AppConfig not initialized. "
            "Ensure app.state.config is set during application lifespan startup."
        )
    return request.app.state.config


ConfigDep = Annotated[AppConfig, Depends(get_config)]


def get_runtime(request: Request) -> Runtime:
    """
    Returns the Runtime instance from app.state.
    The runtime is initialized during application lifespan startup.
    """
    if not hasattr(request.app.state, "runtime"):
        raise RuntimeError(
            "Runtime not initialized. "
            "Ensure app.state.runtime is set during application lifespan startup."
        )
    return request.app.state.runtime


RuntimeDep = Annotated[Runtime, Depends(get_runtime)]


def get_obo_ws(request: Request, config: ConfigDep) -> WorkspaceClient:
    """
    Returns a Databricks Workspace client using OBO: x-forwarded-access-token only (no env PAT).
    """
    token = get_access_token(request, config=None)
    if not token:
        diag = get_access_token_diagnostic(request, config)
        raise HTTPException(
            status_code=401,
            detail={
                "message": "x-forwarded-access-token header is required for this endpoint.",
                "hint": diag["hint"],
                "header_present": diag["header_present"],
                "fix_databricks": "Open the app from the Databricks Apps launcher so the platform sets x-forwarded-access-token.",
                "fix_local": "Send x-forwarded-access-token (this endpoint does not use FEVM_TOKEN). For local dev, proxy requests through the Apps shell or add the header manually.",
            },
        )
    return WorkspaceClient(
        host=config.host,
        token=token,
        auth_type="pat",
    )


def get_volume_obo_ws(config: ConfigDep, request: Request) -> WorkspaceClient:
    """
    Returns a WorkspaceClient for volume/job/chat operations.
    Uses x-forwarded-access-token when present, else config.token (FEVM_TOKEN / DATA_EXTRACTION_TOKEN).
    """
    use_token = get_access_token(request, config)
    if not use_token:
        diag = get_access_token_diagnostic(request, config)
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authentication required. No token from x-forwarded-access-token header or environment.",
                "hint": diag["hint"],
                "header_present": diag["header_present"],
                "fix_databricks": "Open the app from the Databricks Apps launcher (Apps menu or workspace URL) so the platform can set x-forwarded-access-token.",
                "fix_local": "Set FEVM_TOKEN or DATA_EXTRACTION_TOKEN in databricks_app/.env or the process environment.",
            },
        )
    return WorkspaceClient(
        host=config.host,
        token=use_token,
        auth_type="pat",
    )


def get_volume_token(config: ConfigDep, request: Request) -> str:
    """
    Returns the token string for SQL/MLflow (e.g. chat): header else config.token (env).
    """
    use_token = get_access_token(request, config)
    if not use_token:
        diag = get_access_token_diagnostic(request, config)
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authentication required. No token from x-forwarded-access-token header or environment.",
                "hint": diag["hint"],
                "header_present": diag["header_present"],
                "fix_databricks": "Open the app from the Databricks Apps launcher so the platform can set x-forwarded-access-token.",
                "fix_local": "Set FEVM_TOKEN or DATA_EXTRACTION_TOKEN.",
            },
        )
    return use_token
