import base64
import io
import traceback
from datetime import datetime
from typing import Annotated

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError
from databricks.sdk.service.iam import User as UserOut
from fastapi import APIRouter, Depends, HTTPException, Request

from .._metadata import api_prefix
from .config import AppConfig, get_access_token_diagnostic
from .dependencies import ConfigDep, get_obo_ws, get_volume_obo_ws, get_volume_token
from .logger import logger
from .models import (
    AppAiQueryOut,
    ChatIn,
    ChatMessageOut,
    ChatOut,
    FileInfo,
    FileListOut,
    FilesUploadIn,
    JobRunOut,
    JobRunTriggerOut,
    VersionOut,
)

api = APIRouter(prefix=api_prefix)


def _as_int_ms_epoch(v) -> int | None:
    """Coerce SDK run timestamps to int ms for JSON / Pydantic (avoids response validation 500s)."""
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _http_status_for_databricks_error(e: DatabricksError) -> int | None:
    """Map common Jobs API failures to HTTP status codes."""
    code = (e.error_code or "").upper()
    msg = (str(e) or "").lower()
    if "PERMISSION" in code or "PERMISSION_DENIED" in code or "403" in msg or "forbidden" in msg:
        return 403
    if (
        "NOT_FOUND" in code
        or "DOES_NOT_EXIST" in code
        or "RESOURCE_DOES_NOT_EXIST" in code
        or ("INVALID_PARAMETER" in code and "job" in msg)
    ):
        return 404
    return None


class _BytesIOWithLen(io.BytesIO):
    """BytesIO that supports len() for SDKs that require it (e.g. Databricks files.upload)."""

    def __len__(self) -> int:
        return len(self.getvalue())


@api.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@api.get("/auth/diagnostic", operation_id="authDiagnostic")
def auth_diagnostic(request: Request, config: ConfigDep):
    """
    Check whether x-forwarded-access-token is present and if a token can be resolved.
    Use this when auth fails on Databricks to see if the header is being sent.
    Does not return any token value.
    """
    return get_access_token_diagnostic(request, config)


@api.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(obo_ws: Annotated[WorkspaceClient, Depends(get_obo_ws)]):
    return obo_ws.current_user.me()


@api.get("/files", response_model=FileListOut, operation_id="listFiles")
def list_files(
    config: ConfigDep,
    ws: Annotated[WorkspaceClient, Depends(get_volume_obo_ws)],
):
    """List PDF files in the configured volume (using OBO token from X-Forwarded-Access-Token)."""
    volume_path = f"{config.volume_path}/productmanuals"
    logger.info(f"[LIST] Listing files from volume: {volume_path}")
    logger.info(f"[LIST] Using host: {config.host}")

    files: list[FileInfo] = []
    try:
        logger.info(f"[LIST] Calling ws.files.list_directory_contents({volume_path})")
        for file_info in ws.files.list_directory_contents(volume_path):
            logger.info(f"[LIST] Found file: {file_info.name}")
            if file_info.name and file_info.name.lower().endswith(".pdf"):
                files.append(
                    FileInfo(
                        name=file_info.name,
                        path=file_info.path or "",
                        size=file_info.file_size or 0,
                        modified_at=datetime.fromtimestamp(file_info.last_modified / 1000)
                        if file_info.last_modified
                        else None,
                    )
                )
        logger.info(f"[LIST] Found {len(files)} PDF files")
    except Exception as e:
        logger.error(f"[LIST] Error listing files: {type(e).__name__}: {e}")
        err_msg = str(e)
        if "required scopes" in err_msg.lower() and "files" in err_msg.lower():
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "The token does not have the 'files' scope.",
                    "hint": "The token must have the Databricks 'files' scope to list/upload files.",
                    "fix": "Ensure the signed-in user's token (Apps) or PAT (local) includes the Databricks 'files' scope. For PATs: User Settings → Developer → Access tokens with Files enabled.",
                },
            ) from e
        raise HTTPException(status_code=502, detail=f"Failed to list files: {e!s}") from e

    return FileListOut(files=files)


@api.post("/files", response_model=FileListOut, operation_id="uploadFiles")
def upload_files(
    config: ConfigDep,
    ws: Annotated[WorkspaceClient, Depends(get_volume_obo_ws)],
    payload: FilesUploadIn,
):
    """Upload PDF files to the configured volume (using OBO token from X-Forwarded-Access-Token)."""
    volume_path = f"{config.volume_path}/productmanuals"
    logger.info(f"[UPLOAD] Received upload request with {len(payload.files)} files")
    logger.info(f"[UPLOAD] Volume path: {volume_path}")
    logger.info(f"[UPLOAD] Host: {config.host}")

    uploaded: list[FileInfo] = []

    for file in payload.files:
        logger.info(f"[UPLOAD] Processing file: {file.name}")
        logger.info(f"[UPLOAD] Base64 content length: {len(file.content_base64)}")
        
        # Only accept PDF files
        if not file.name.lower().endswith(".pdf"):
            logger.warning(f"[UPLOAD] Skipping non-PDF file: {file.name}")
            continue

        try:
            # Decode base64 content
            logger.info(f"[UPLOAD] Decoding base64 content...")
            content = base64.b64decode(file.content_base64)
            logger.info(f"[UPLOAD] Decoded content size: {len(content)} bytes")
            
            file_path = f"{volume_path}/{file.name}"
            logger.info(f"[UPLOAD] Uploading to: {file_path}")

            # SDK expects a file-like object and may call len() on it; BytesIO has no __len__
            content_stream = _BytesIOWithLen(content)
            ws.files.upload(file_path, content_stream, overwrite=True)
            logger.info(f"[UPLOAD] Successfully uploaded: {file.name}")

            uploaded.append(
                FileInfo(
                    name=file.name,
                    path=file_path,
                    size=len(content),
                    modified_at=datetime.now(),
                )
            )
        except Exception as e:
            logger.error(f"[UPLOAD] Error uploading {file.name}: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            err_msg = str(e)
            if "required scopes" in err_msg.lower() and "files" in err_msg.lower():
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Upload failed for {file.name}: the token does not have the 'files' scope.",
                        "hint": "The token (from x-forwarded-access-token or environment) must have the Databricks 'files' scope to use the Files API.",
                        "fix": "Ensure the signed-in user's token (Apps) or PAT (local) includes the 'files' scope. For PATs: User Settings → Developer → Access tokens with Files enabled.",
                    },
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Upload failed for {file.name}: {e!s}",
            ) from e

    logger.info(f"[UPLOAD] Upload complete. Uploaded {len(uploaded)} files")
    return FileListOut(files=uploaded)


@api.post("/jobs/run", response_model=JobRunTriggerOut, operation_id="triggerJobRun")
def trigger_job_run(
    config: ConfigDep,
    ws: Annotated[WorkspaceClient, Depends(get_volume_obo_ws)],
):
    """Trigger the configured processing job (run now). Returns run_id for polling."""
    try:
        job_id = int(config.processing_job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid processing_job_id in config")
    try:
        waiter = ws.jobs.run_now(job_id=job_id)
        resp = waiter.response
        raw_run_id = getattr(resp, "run_id", None) if resp is not None else None
        if raw_run_id is None:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Job run was submitted but the workspace returned no run_id. "
                    "Check processing_job_id, Jobs API access, and that config.host matches the workspace."
                ),
            )
        run_id = int(raw_run_id)
        logger.info(f"[JOB] Triggered job_id={job_id}, run_id={run_id}")
        return JobRunTriggerOut(run_id=run_id, job_id=config.processing_job_id)
    except HTTPException:
        raise
    except DatabricksError as e:
        logger.error(f"[JOB] Error triggering job: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        mapped = _http_status_for_databricks_error(e)
        if mapped is not None:
            raise HTTPException(
                status_code=mapped,
                detail={
                    "message": str(e),
                    "error_code": e.error_code,
                    "hint": (
                        "Grant the signed-in user (OBO token) CAN_MANAGE_RUN or CAN_MANAGE on this job, "
                        "or ensure their token can run the job. "
                        "Ensure processing_job_id exists in the same workspace as config.host."
                    ),
                },
            ) from e
        raise HTTPException(status_code=502, detail=f"Failed to trigger job: {e!s}") from e
    except Exception as e:
        logger.error(f"[JOB] Error triggering job: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Failed to trigger job: {e!s}") from e


@api.get("/jobs/runs/{run_id}", response_model=JobRunOut, operation_id="getJobRun")
def get_job_run(
    run_id: int,
    ws: Annotated[WorkspaceClient, Depends(get_volume_obo_ws)],
):
    """Get current status and timing of a job run."""
    try:
        run = ws.jobs.get_run(run_id=run_id)
    except DatabricksError as e:
        logger.error(f"[JOB] Error getting run {run_id}: {type(e).__name__}: {e}")
        mapped = _http_status_for_databricks_error(e)
        status = mapped if mapped is not None else 502
        raise HTTPException(status_code=status, detail=str(e)) from e
    except Exception as e:
        logger.error(f"[JOB] Error getting run {run_id}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=404, detail=f"Run not found or error: {e!s}") from e
    state = getattr(run, "state", None) or getattr(run, "status", None)
    life_cycle_state = (
        getattr(state, "life_cycle_state", None)
        or getattr(run, "life_cycle_state", None)
        or "UNKNOWN"
    )
    result_state = getattr(state, "result_state", None) or getattr(run, "result_state", None)
    start_time = getattr(run, "start_time", None)
    end_time = getattr(run, "end_time", None)

    def _enum_value_name(v):
        if v is None:
            return None
        if hasattr(v, "name"):
            return getattr(v, "name")
        s = str(v)
        return s.split(".")[-1] if "." in s else s

    life_cycle_state_str = _enum_value_name(life_cycle_state) or "UNKNOWN"
    result_state_str = _enum_value_name(result_state)

    raw_rid = getattr(run, "run_id", None)
    effective_run_id = int(raw_rid) if raw_rid is not None else run_id

    st = _as_int_ms_epoch(start_time)
    et = _as_int_ms_epoch(end_time)
    execution_duration_ms = None
    if st is not None and et is not None and et > 0:
        execution_duration_ms = et - st
    return JobRunOut(
        run_id=effective_run_id,
        life_cycle_state=life_cycle_state_str,
        result_state=result_state_str,
        start_time=st,
        end_time=et if (et is not None and et > 0) else None,
        execution_duration_ms=execution_duration_ms,
    )


def _row_to_json_serializable(row: tuple, columns: list[str]) -> dict:
    """Convert a row tuple to a dict with JSON-serializable values."""
    out = {}
    for i, col in enumerate(columns):
        if i >= len(row):
            break
        v = row[i]
        if v is None:
            out[col] = None
        elif isinstance(v, (datetime,)):
            out[col] = v.isoformat()
        elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
            out[col] = str(v)
        else:
            out[col] = v
    return out


@api.get("/query/app_ai_query", response_model=AppAiQueryOut, operation_id="getAppAiQuery")
def get_app_ai_query(
    config: ConfigDep,
    token: Annotated[str, Depends(get_volume_token)],
):
    """Query the app_ai_query table via SQL Warehouse and return rows."""
    from databricks import sql as databricks_sql

    server_hostname = (config.host or "").replace("https://", "").replace("http://", "")
    if not server_hostname or not config.warehouse_http_path or not token:
        raise HTTPException(
            status_code=500,
            detail="SQL Warehouse configuration or token missing",
        )
    def _quote_table(name: str) -> str:
        return ".".join("`" + part.replace("`", "``") + "`" for part in name.split("."))

    try:
        with databricks_sql.connect(
            server_hostname=server_hostname,
            http_path=config.warehouse_http_path,
            access_token=token,
        ) as conn:
            with conn.cursor() as cursor:
                table = config.app_ai_query_table
                quoted_table = _quote_table(table)
                cursor.execute(f"SELECT * FROM {quoted_table} LIMIT 1000")
                columns = [d[0] for d in (cursor.description or [])]
                raw_rows = cursor.fetchall()
        rows = [_row_to_json_serializable(r, columns) for r in raw_rows]
        return AppAiQueryOut(rows=rows, columns=columns)
    except Exception as e:
        logger.error(f"[QUERY] Error querying app_ai_query: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Query failed: {e!s}") from e


def _format_agent_response_for_user(raw: list | dict | object) -> str:
    """Turn agent response (list of message/function_call items or dict) into a single user-friendly string."""
    import re
    if isinstance(raw, list):
        parts = []
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
                        text = block.get("text") or ""
                        text = (text or "").strip()
                        # Skip internal agent handoff lines like <name>agent-invoiceanalyser</name>
                        if re.match(r"^<name>\s*[\w-]+\s*</name>\s*$", text):
                            continue
                        if text:
                            parts.append(text)
            elif kind == "function_call":
                # Optionally show a short hint that the agent is using a tool (skip for cleaner output)
                pass
        if parts:
            return "\n\n".join(parts)
        return str(raw)
    if isinstance(raw, dict):
        content = raw.get("content") or raw.get("output")
        if content is not None:
            return content if isinstance(content, str) else str(content)
        if "choices" in raw and raw["choices"]:
            first = raw["choices"][0]
            msg = first.get("message", first) if isinstance(first, dict) else first
            if isinstance(msg, dict):
                return (msg.get("content") or "") if isinstance(msg.get("content"), str) else str(msg)
            c = getattr(msg, "content", None)
            return str(c) if c is not None else str(raw)
    return str(raw)


def _chat_via_mlflow(config: AppConfig, token: str, api_messages: list[dict]) -> ChatMessageOut:
    """Use MLflow deployments client (recommended for agent endpoints)."""
    import os
    from mlflow.deployments import get_deploy_client

    # MLflow Databricks client reads from env
    host = (config.host or "").replace("https://", "").replace("http://", "")
    prev_host = os.environ.get("DATABRICKS_HOST")
    prev_token = os.environ.get("DATABRICKS_TOKEN")
    try:
        os.environ["DATABRICKS_HOST"] = f"https://{host}" if host else ""
        os.environ["DATABRICKS_TOKEN"] = token or ""
        client = get_deploy_client("databricks")
        # Agent endpoints expect "input" (list of {role, content}), not "messages"
        inputs = {"input": api_messages}
        response = client.predict(endpoint=config.agent_endpoint, inputs=inputs)
    finally:
        if prev_host is not None:
            os.environ["DATABRICKS_HOST"] = prev_host
        elif "DATABRICKS_HOST" in os.environ:
            del os.environ["DATABRICKS_HOST"]
        if prev_token is not None:
            os.environ["DATABRICKS_TOKEN"] = prev_token
        elif "DATABRICKS_TOKEN" in os.environ:
            del os.environ["DATABRICKS_TOKEN"]

    # Agent can return a list of message/function_call items; normalize to user-friendly string
    if isinstance(response, list):
        content = _format_agent_response_for_user(response)
        return ChatMessageOut(role="assistant", content=content)
    if isinstance(response, dict):
        # Dict might wrap the list (e.g. {"output": [...]}) or be OpenAI-like
        for key in ("output", "content", "candidates", "messages"):
            val = response.get(key)
            if isinstance(val, list):
                content = _format_agent_response_for_user(val)
                return ChatMessageOut(role="assistant", content=content)
        content = response.get("content") or response.get("output")
        if content is None and "choices" in response:
            choices = response["choices"]
            if choices:
                first = choices[0]
                msg = first.get("message", first) if isinstance(first, dict) else first
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                else:
                    content = getattr(msg, "content", None) or ""
        if content is None:
            content = str(response)
        return ChatMessageOut(role="assistant", content=content if isinstance(content, str) else str(content))
    choices = getattr(response, "choices", None) or []
    if choices:
        first = choices[0]
        msg = getattr(first, "message", first)
        content = getattr(msg, "content", None) or ""
    else:
        content = str(response)
    return ChatMessageOut(role="assistant", content=content if isinstance(content, str) else str(content))


@api.post("/chat", response_model=ChatOut, operation_id="chat")
def chat(
    config: ConfigDep,
    ws: Annotated[WorkspaceClient, Depends(get_volume_obo_ws)],
    token: Annotated[str, Depends(get_volume_token)],
    payload: ChatIn,
):
    """Send messages to the configured Databricks agent endpoint and return the assistant reply.
    Uses MLflow deployments client (recommended for agents) with fallback to OpenAI-compatible client.
    See https://docs.databricks.com/en/generative-ai/agent-framework/query-agent and
    https://github.com/databricks/app-templates/blob/main/e2e-chatbot-app-next/README.md

    Authentication (how the chat endpoint is authenticated):
    - This route uses the same auth as the rest of the app via get_volume_obo_ws and get_volume_token.
    - Token source (in order):
      1) X-Forwarded-Access-Token request header: when the app runs inside Databricks (e.g. Databricks
         Apps), the platform forwards the user's OAuth token in this header. The backend uses it to call
         the agent endpoint on behalf of that user.
      2) Fallback (local dev): If the header is missing or empty, the backend uses the token from
         config.token, which is loaded from environment: FEVM_TOKEN or DATA_EXTRACTION_TOKEN (see
         config.py). So for local development you set one of those env vars (e.g. a PAT) and do not
         need to send X-Forwarded-Access-Token.
    - The token is then used in two ways:
      - MLflow path: DATABRICKS_HOST (from config.host) and DATABRICKS_TOKEN are set in the process
        env before calling get_deploy_client("databricks"); the MLflow client uses them to call the
        Databricks serving API.
      - OpenAI path: the WorkspaceClient (ws) was already built with host=config.host and
        token=use_token; ws.serving_endpoints.get_open_ai_client() uses that to call the endpoint.
    - The agent endpoint (config.agent_endpoint, e.g. mas-2e8563e1-endpoint) must allow the token's
      identity (user or service principal) to CAN_QUERY; otherwise the serving gateway returns an
      error that surfaces as 502.
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    api_messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    # 1) Try MLflow deployments client (recommended for agent/MAS endpoints; see template README)
    mlflow_error = None
    try:
        msg_out = _chat_via_mlflow(config, token, api_messages)
        return ChatOut(message=msg_out)
    except Exception as e:
        mlflow_error = e
        logger.error(
            "[CHAT] MLflow agent call failed: %s: %s",
            type(e).__name__,
            e,
            exc_info=True,
        )

    # 2) Fallback: Databricks OpenAI-compatible client
    try:
        client = ws.serving_endpoints.get_open_ai_client()
        response = client.chat.completions.create(
            model=config.agent_endpoint,
            messages=api_messages,
        )
    except Exception as e:
        logger.error(
            "[CHAT] OpenAI client call failed: %s: %s",
            type(e).__name__,
            e,
            exc_info=True,
        )
        # Build detail so user sees both errors if both paths failed
        detail_parts = [f"OpenAI client: {type(e).__name__}: {e!s}"]
        if mlflow_error is not None:
            detail_parts.insert(
                0,
                f"MLflow client: {type(mlflow_error).__name__}: {mlflow_error!s}",
            )
        raise HTTPException(
            status_code=502,
            detail="; ".join(detail_parts),
        ) from e
    try:
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise HTTPException(status_code=502, detail="Agent returned no reply")
        first = choices[0]
        msg = getattr(first, "message", first)
        content = getattr(msg, "content", None) or ""
        role = getattr(msg, "role", None) or "assistant"
        return ChatOut(message=ChatMessageOut(role=str(role), content=str(content)))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "[CHAT] Error parsing agent response: %s: %s",
            type(e).__name__,
            e,
            exc_info=True,
        )
        raise HTTPException(status_code=502, detail=f"Agent response invalid: {e!s}") from e
