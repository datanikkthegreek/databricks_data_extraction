from pathlib import Path

app_name = "data-extraction-app"
app_entrypoint = "data_extraction_app.backend.app:app"
app_slug = "data_extraction_app"
api_prefix = "/api"
dist_dir = Path(__file__).parent / "__dist__"