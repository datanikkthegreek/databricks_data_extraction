# 🔧 ETL Pipeline: Lakeflow Spark Declarative Pipeline + Jobs

This bundle deploys the production **Intelligent Document Processing** pipeline — a Lakeflow Spark Declarative Pipeline (incremental, serverless) orchestrated by Lakeflow Jobs.

**Pipeline steps:** Parse PDFs with `ai_parse_document` → Extract structured fields with `ai_extract` → Flatten into a typed Delta table → Evaluate quality with MLflow → Create Genie Space, Knowledge Assistant, and Supervisor Agent.

---

## 🔧 Prerequisites

- Databricks workspace with **Unity Catalog** enabled
- A catalog, schema, and Unity Catalog volume where PDF files will land
- A SQL warehouse (for Genie Space creation)
- Sample PDFs uploaded to `{volume}/productmanuals` — use files from [`../productmanuals/`](../productmanuals/)

> **Bundle root is `databricks_etl/`**, not the repo root. Open or `cd` into this directory before running any bundle commands.

---

## ⚙️ Bundle Variables

Set these in [`databricks.yml`](databricks.yml) before deploying:

| Variable | Purpose |
|----------|---------|
| `catalog` | Unity Catalog catalog |
| `schema` | Schema (database) |
| `table_prefix` | Prefix for all Delta table and job display names |
| `volume` | UC volume path, e.g. `/Volumes/<catalog>/<schema>/<volume>/` |
| `warehouse_id` | SQL warehouse ID for Genie Space creation |

---

## 🖥️ Option A: Deploy from the Workspace UI

1. In Databricks, add a Git folder and clone this repo.
2. Open the `databricks_etl/` directory as your bundle project.
3. Edit `databricks.yml` and set the variables above.
4. Use the workspace **Deploy** flow, choose your target (`dev` or `prod`), and deploy.
   - Reference: [Deploy bundles and run workflows from the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy)
5. After deploy, open **Workflows → Jobs** and run `{table_prefix}_extract_productmanuals_job`.

---

## 💻 Option B: Deploy from the CLI

**1. Install and configure the Databricks CLI**

```bash
brew install databricks/tap/databricks          # macOS
databricks auth login https://<workspace-host> --profile=<profile-name>
databricks auth profiles | grep <profile-name>  # should show YES
```

**2. Sync Python dependencies**

```bash
cd databricks_etl && uv sync
```

**3. Deploy**

```bash
databricks bundle deploy -p <profile>
# Force PAT auth if needed:
DATABRICKS_AUTH_TYPE=pat databricks bundle deploy -p <profile>
```

**4. Run the jobs**

From the workspace UI (**Workflows → Jobs**), or from the CLI:

```bash
databricks bundle run extract_productmanuals_job -p <profile>
databricks bundle run extract_invoices_job -p <profile>
```

---

## 📋 Job Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `create_agent` | `true` | Set to `false` to skip Knowledge Assistant and Supervisor Agent creation |
| `evaluation_experiment` | *(from yml)* | MLflow experiment path for evaluation results |

> ⏱️ **Note:** The Knowledge Assistant takes at least 15 minutes to build. The job does not wait for it — check status under the **Agents** tab.

---

## 🔧 Additional Configuration

### Automatic file-arrival triggers

Both jobs can trigger automatically when new files land on the volume. Uncomment the `trigger` block in the job YAMLs and redeploy:

- [`resources/extract_productmanuals.job.yml`](resources/extract_productmanuals.job.yml) — lines 10–13
- [`resources/extract_invoices.job.yml`](resources/extract_invoices.job.yml) — lines 12–15

### Generating extraction schemas interactively

Use **Agents → Information Extraction** in the Databricks UI to design your schema interactively before embedding it as code.
Reference: [Intelligent document processing](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing)
