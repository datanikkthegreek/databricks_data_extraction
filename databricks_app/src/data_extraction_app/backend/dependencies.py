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
    Returns a Databricks Workspace client.
    When DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET are set, uses OAuth M2M (no user token).
    Otherwise uses x-forwarded-access-token header (required).
    """
    if config.use_oauth_m2m():
        return WorkspaceClient(
            host=config.host,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
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
                "fix_local": "Set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET for OAuth M2M, or send the header.",
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
    When DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET are set, uses OAuth M2M (no user token).
    Otherwise uses x-forwarded-access-token when present, else config.token (FEVM_TOKEN / DATA_EXTRACTION_TOKEN).
    """
    if config.use_oauth_m2m():
        return WorkspaceClient(
            host=config.host,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
    use_token = get_access_token(request, config)
    if not use_token:
        diag = get_access_token_diagnostic(request, config)
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authentication required. No token from x-forwarded-access-token header or environment.",
                "hint": diag["hint"],
                "header_present": diag["header_present"],
                "fix_databricks": "Open the app from the Databricks Apps launcher (Apps menu or workspace URL) so the platform can set x-forwarded-access-token. Or set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET for OAuth M2M.",
                "fix_local": "Set FEVM_TOKEN or DATA_EXTRACTION_TOKEN, or DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET.",
            },
        )
    return WorkspaceClient(
        host=config.host,
        token=use_token,
        auth_type="pat",
    )


def get_volume_token(config: ConfigDep, request: Request) -> str:
    """
    Returns the token string for SQL/MLflow (e.g. chat). When OAuth M2M is used, obtains a token from the workspace client.
    Otherwise uses get_access_token(request, config): header else config.token (env).
    """
    if config.use_oauth_m2m():
        ws = WorkspaceClient(
            host=config.host,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )
        try:
            ws.config.authenticate()
            token_obj = ws.config.oauth_token()
            if token_obj and getattr(token_obj, "access_token", None):
                return token_obj.access_token
            headers = ws.config.authenticate()
            if isinstance(headers, dict):
                auth = headers.get("Authorization") or headers.get("authorization")
                if auth and isinstance(auth, str) and auth.startswith("Bearer "):
                    return auth[7:].strip()
        except (ValueError, AttributeError, Exception):
            pass
        raise HTTPException(
            status_code=500,
            detail="OAuth M2M: could not obtain access token for SQL/MLflow. Set FEVM_TOKEN or DATA_EXTRACTION_TOKEN as fallback for chat/SQL, or use token-based auth.",
        )
    use_token = get_access_token(request, config)
    if not use_token:
        diag = get_access_token_diagnostic(request, config)
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authentication required. No token from x-forwarded-access-token header or environment.",
                "hint": diag["hint"],
                "header_present": diag["header_present"],
                "fix_databricks": "Open the app from the Databricks Apps launcher so the platform can set x-forwarded-access-token. Or set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET.",
                "fix_local": "Set FEVM_TOKEN or DATA_EXTRACTION_TOKEN, or DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET.",
            },
        )
    return use_token
