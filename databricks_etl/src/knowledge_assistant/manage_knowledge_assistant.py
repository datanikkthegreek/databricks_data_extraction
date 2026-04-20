"""Knowledge Assistant REST API helpers (create, get, knowledge sources, sync)."""


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
