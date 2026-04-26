# 📱 Databricks App: Data Extraction UI

A full-stack app for uploading PDFs, triggering the extraction pipeline, querying results, and chatting with the Supervisor Agent — built with FastAPI + React using the [APX framework](https://github.com/databricks-solutions/apx).

![Architecture](../docs/images/Architecture.png)

*The Databricks App corresponds to the **Web App** box in the bottom-left of the diagram — the customer-facing entry point on Databricks One that ties the Supervisor Agent, Genie Space, and extraction pipeline together.*

> **This bundle must be deployed from your local CLI.** The workspace bundle UI is not supported for app bundles.

---

## 🛠️ Tech Stack

- **Backend:** Python + [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend:** React + [shadcn/ui](https://ui.shadcn.com/)
- **API Client:** Auto-generated TypeScript client from OpenAPI schema
- **Framework:** [APX](https://github.com/databricks-solutions/apx)

---

## 🔧 Prerequisites

- Databricks CLI installed and configured (see [Install the Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html#install-the-databricks-cli))
- The ETL pipeline deployed and a job run completed (see [`../databricks_etl/README.md`](../databricks_etl/README.md))

> **Bundle root is `databricks_app/`**. Run all commands from this directory.

---

## ⚙️ Configure `app.yml`

Edit [`app.yml`](app.yml) before deploying. Set the following environment variables:

| Variable | Purpose |
|----------|---------|
| `WAREHOUSE_ID` | SQL warehouse ID for query execution |
| `JOB_ID` | Job ID of the extraction job triggered from the app |
| `VOLUME_PATH` | Volume path for PDF uploads, e.g. `/Volumes/<catalog>/<schema>/<volume>/` |
| `AI_EXTRACT_PROCESSED_TABLE` | Full table name (`catalog.schema.table`) for extraction results |
| `AGENT_ENDPOINT` | Serving endpoint name for the Supervisor Agent |

---

## ⚙️ Configure the App Name

In [`databricks.yml`](databricks.yml), set `variables.app_name_prefix`. The deployed app name will be `{app_name_prefix}-data-extraction-app`.

Override at deploy time without editing the file:

```bash
databricks bundle deploy -p <profile> --var app_name_prefix=my-team
```

---

## 🚀 Deploy

```bash
cd databricks_app
databricks bundle validate -p <profile>
databricks bundle deploy -p <profile>
```

After deploy, open **Compute → Apps** in your workspace, find the app, start it if stopped, and open its URL.

### Optional: deploy or refresh directly via CLI

```bash
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<your-user>/.bundle/data-extraction-app/dev/files/.build
```

---

## 👥 App User Permissions

Users of the app need access to the underlying resources it calls:

| Resource | Required privilege |
|----------|--------------------|
| Volume | Read / write |
| Processed table | `SELECT` |
| SQL warehouse | `CAN_USE` |
| Extraction job | `CAN_MANAGE_RUN` |
| Agent serving endpoint | `CAN_QUERY` |

---

## 💻 Local Development

Start all servers (backend, frontend, OpenAPI watcher) in development mode:

```bash
cd databricks_app && uv run apx dev start
```

### Useful dev commands

```bash
# View logs
uv run apx dev logs

# Stream logs in real-time
uv run apx dev logs -f

# Check server status
uv run apx dev status

# Stop all servers
uv run apx dev stop

# Type checking and linting (TypeScript + Python)
uv run apx dev check
```

### Build

Create a production-ready build:

```bash
uv run apx build
```

---

## 🔗 References

- [Deploy Databricks Apps with Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial)
- [APX framework](https://github.com/databricks-solutions/apx)
