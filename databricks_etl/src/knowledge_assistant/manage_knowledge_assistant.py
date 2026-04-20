"""Knowledge Assistant REST API helpers (create, list, get, knowledge sources, sync)."""


def list_knowledge_assistants(
    workspace_client,
    *,
    page_size: int | None = None,
    page_token: str | None = None,
):
    """List Knowledge Assistants (GET ``/api/2.1/knowledge-assistants``).

    ``page_size`` is optional in ``[1, 100]``; if omitted, the API returns up to 100 items.
    ``page_token`` is optional; pass the ``next_page_token`` from a previous response for the next page.

    Returns a dict with ``knowledge_assistants`` (list) and optional ``next_page_token``.
    """
    query: dict[str, int | str] = {}
    if page_size is not None:
        query["page_size"] = page_size
    if page_token is not None:
        query["page_token"] = page_token
    return workspace_client.api_client.do(
        "GET",
        "/api/2.1/knowledge-assistants",
        query=query,
    )


def get_knowledge_assistant_id_by_name(workspace_client, name: str) -> str | None:
    """Return the ``id`` of the first Knowledge Assistant whose ``name`` equals ``name`` (stripped), else ``None``.

    Lists pages of 100 via :func:`list_knowledge_assistants` until a match is found or pages are exhausted.
    """
    want = name.strip()
    page_token: str | None = None
    while True:
        resp = list_knowledge_assistants(
            workspace_client, page_size=100, page_token=page_token
        )
        for assistant in resp.get("knowledge_assistants") or []:
            if (assistant.get("name") or "").strip() == want:
                return assistant.get("id")
        page_token = resp.get("next_page_token")
        if not page_token:
            break
    return None


def get_knowledge_assistant_id_by_display_name(workspace_client, display_name: str) -> str | None:
    """Return the ``id`` of the first Knowledge Assistant whose ``display_name`` matches (stripped), else ``None``.

    Lists pages of 100 via :func:`list_knowledge_assistants` until a match is found or pages are exhausted.
    """
    want = display_name.strip()
    page_token: str | None = None
    while True:
        resp = list_knowledge_assistants(
            workspace_client, page_size=100, page_token=page_token
        )
        for assistant in resp.get("knowledge_assistants") or []:
            if (assistant.get("display_name") or "").strip() == want:
                return assistant.get("id")
        page_token = resp.get("next_page_token")
        if not page_token:
            break
    return None


def create_knowledge_assistant(
    workspace_client,
    display_name: str,
    description: str,
    instructions: str | None = None,
):
    """Create a Knowledge Assistant. Returns the create response (id, name, state, etc.)."""
    body = {"display_name": display_name, "description": description}
    if instructions:
        body["instructions"] = instructions
    return workspace_client.api_client.do(
        "POST",
        "/api/2.1/knowledge-assistants",
        body=body,
    )


def get_knowledge_assistant(workspace_client, id: str):
    """Get a Knowledge Assistant by id. Returns the full response (state, description, etc.) or raises."""
    return workspace_client.api_client.do(
        "GET",
        f"/api/2.1/knowledge-assistants/{id}",
    )


def create_knowledge_source_files(
    workspace_client,
    assistant_id: str,
    display_name: str,
    description: str,
    volume_path: str,
):
    """Create a 'files' Knowledge Source pointing at a UC volume path. Returns the create response."""
    return workspace_client.api_client.do(
        "POST",
        f"/api/2.1/knowledge-assistants/{assistant_id}/knowledge-sources",
        body={
            "source_type": "files",
            "display_name": display_name,
            "description": description,
            "files": {"path": volume_path},
        },
    )


def get_knowledge_source(workspace_client, assistant_id: str, source_id: str):
    """Get a Knowledge Source by assistant id and source id. Returns the full response (state, description, etc.)."""
    return workspace_client.api_client.do(
        "GET",
        f"/api/2.1/knowledge-assistants/{assistant_id}/knowledge-sources/{source_id}",
    )


def sync_knowledge_sources(workspace_client, assistant_id: str):
    """Sync all non-index Knowledge Sources for a Knowledge Assistant. Returns the response (often empty {})."""
    return workspace_client.api_client.do(
        "POST",
        f"/api/2.1/knowledge-assistants/{assistant_id}/knowledge-sources:sync",
        body={},
    )
