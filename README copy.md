# Data Extraction App – User setup

Complete these steps before developing or deploying the app.

## 1. Install Databricks CLI and create a profile

1. **Install the Databricks CLI** (if not already installed):
   - Follow [Install the Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html#install-the-databricks-cli).
   - Example with Homebrew (macOS): `brew install databricks/tap/databricks`

2. **Create a Databricks profile** for your workspace:
   - Run:  
     `databricks auth login https://<your-workspace-host> --profile=<profile-name>`
   - Example:  
     `databricks auth login https://e2-demo-field-eng.cloud.databricks.com --profile=FE-AWS`
   - Complete the browser sign-in (SSO). The profile is saved in `~/.databrickscfg`.

3. **Verify the profile**:
   - Run: `databricks auth profiles | grep <profile-name>`  
   - A valid profile shows `YES`.

Use this profile for bundle deploy and CLI commands, e.g.  
`databricks bundle deploy -p <profile-name>`.

---

## 2. Update all configs in config.py and databricks.yml

### config.py

Edit `src/data_extraction_app/backend/config.py` (or override via environment variables with prefix `DATA_EXTRACTION_` or a `.env` file):

| Setting | Description | Example / env |
|--------|--------------|----------------|
| `host` | Databricks workspace URL | `DATA_EXTRACTION_HOST` |
| `warehouse_http_path` | SQL Warehouse HTTP path | `DATA_EXTRACTION_WAREHOUSE_HTTP_PATH` |
| `volume_path` | Volume path for PDF storage | `DATA_EXTRACTION_VOLUME_PATH` |
| `processing_job_id` | Job ID for processing | `DATA_EXTRACTION_PROCESSING_JOB_ID` |
| `app_ai_query_table` | Full table name (catalog.schema.table) for extraction results | `DATA_EXTRACTION_APP_AI_QUERY_TABLE` |
| `agent_endpoint` | Databricks agent endpoint name for chat | — |
| `token` | Fallback PAT (or use `client_id` / `client_secret` for OAuth M2M) | `FEVM_TOKEN` or `DATA_EXTRACTION_TOKEN` |

Set these to match your workspace, warehouse, volume, job, and table.

### databricks.yml

Edit `databricks.yml` (and any target-specific config):

- **variables**: `catalog`, `schema`, `table`, `volume`, `knowledge_assistant_id` — set to your catalog, schema, volume path, and Knowledge Assistant id (for the update_knowledge_assistant job task).
- **targets.***.**workspace.host**: Workspace URL for the target (e.g. `dev`).

Ensure `knowledge_assistant_id` is set if you use the extract-invoices job (which runs the update_knowledge_assistant notebook after the pipeline).

---

## 3. Deploy the bundle and then the app using the build path of the app

1. **Build the app** (produces the `.build` directory used as the app’s source):

   ```bash
   uv run apx build
   ```

2. **Deploy the bundle** (syncs bundle assets and deploys jobs, pipelines, and the app from the bundle’s app resource):

   ```bash
   databricks bundle deploy -p <profile-name>
   ```

   The bundle’s app resource uses `source_code_path: ./.build`, so the built app in `.build` is what gets deployed when the bundle is deployed.

3. **Optional – deploy only the app** (if you already deployed the bundle and only need to update the app):

   ```bash
   databricks apps deploy data-extraction-app --source-code-path .build -p <profile-name>
   ```

   Use the same profile as in step 1. The app name must match the one in your bundle (`data-extraction-app` by default).

---

## 4. Create the multi-agent (Supervisor Agent)

1. In your Databricks workspace, go to **Agents**.
2. Choose **Supervisor Agent**.
3. **Name:** e.g. `supervisor-agent-extraction`
4. **Description:** e.g. *Answer questions about documents through extracted information and flexible Q&A.*
5. **Genie space:** Select the Genie space you created earlier (e.g. “Invoice extraction results”).
6. **Knowledge assistant endpoint:** Select the Knowledge Assistant endpoint you created earlier.
7. Click **Create**.
