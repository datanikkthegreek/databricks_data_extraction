# Data Extraction App

A modern full-stack application for PDF document extraction built with [apx](https://github.com/databricks-solutions/apx), combined with Databricks Asset Bundles for jobs and pipelines.

See [README.md](README.md) for user setup steps (Databricks CLI and profile).

## Tech Stack

- **Backend**: Python + [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend**: React + [shadcn/ui](https://ui.shadcn.com/)
- **API Client**: Auto-generated TypeScript client from OpenAPI schema
- **Data Pipelines**: Databricks DLT (Delta Live Tables)

## Quick Start

App code and [pyproject.toml](databricks_app/pyproject.toml) live under [databricks_app/](databricks_app/). Run apx and uv commands from that directory (or prefix with `cd databricks_app &&`).

### Development Mode

Start all development servers (backend, frontend, and OpenAPI watcher) in detached mode:

```bash
cd databricks_app && uv run apx dev start
```

This will start an apx development server, which in turn runs backend, frontend and OpenAPI watcher. 
All servers run in the background, with logs kept in-memory of the apx dev server.

### Monitoring & Logs

```bash
cd databricks_app

# View all logs
uv run apx dev logs

# Stream logs in real-time
uv run apx dev logs -f

# Check server status
uv run apx dev status

# Stop all servers
uv run apx dev stop
```

## Code Quality

Run type checking and linting for both TypeScript and Python:

```bash
cd databricks_app && uv run apx dev check
```

## Build

Create a production-ready build:

```bash
cd databricks_app && uv run apx build
```

## Deployment

This repository has two [Databricks asset bundles](https://docs.databricks.com/dev-tools/bundles/index.html): one for the app and one for ETL jobs and pipelines. Deploy each from its folder:

```bash
# Databricks App (apx build runs during deploy from databricks_app/)
cd databricks_app && databricks bundle deploy -p <your-profile>
```

```bash
# Jobs and DLT pipelines
cd databricks_etl && databricks bundle deploy -p <your-profile>
```

---

# TestBundle Jobs & Pipelines

This project also includes the TestBundle asset bundle for jobs and pipelines.

## Getting Started with Jobs & Pipelines

### 1. Deployment

- Click the **deployment rocket** in the left sidebar to open the **Deployments** panel, then click **Deploy**.

### 2. Running Jobs & Pipelines

- To run a deployed job or pipeline, hover over the resource in the **Deployments** panel and click the **Run** button.

### 3. Managing Resources

- Use the **Add** dropdown to add resources to the asset bundle.
- Click **Schedule** on a notebook within the asset bundle to create a **job definition** that schedules the notebook.

## Documentation

- For information on using **Databricks Asset Bundles in the workspace**, see: [Databricks Asset Bundles in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-bundles)
- For details on the **Databricks Asset Bundles format** used in this asset bundle, see: [Databricks Asset Bundles Configuration reference](https://docs.databricks.com/aws/en/dev-tools/bundles/reference)

---

Built with [apx](https://github.com/databricks-solutions/apx)
