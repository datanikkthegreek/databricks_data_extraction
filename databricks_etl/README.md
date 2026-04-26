# 🔧 ETL Pipeline: Lakeflow Spark Declarative Pipeline + Jobs

This bundle deploys the production-grade **Intelligent Document Processing** pipeline — a Lakeflow Spark Declarative Pipeline (incremental, serverless) orchestrated by Lakeflow Jobs.

**Pipeline steps:** Parse PDFs with `ai_parse_document` → Extract structured fields with `ai_extract` → Flatten into a typed Delta table → Evaluate quality with MLflow → Create Genie Space, Knowledge Assistant, and Supervisor Agent.

![Architecture](../docs/images/Architecture.png)

*Deploying this bundle provisions everything shown above — from the PDF ingestion streaming tables through to the Genie Space, Knowledge Assistant, and Supervisor Agent on Databricks One.*

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
| `volume` | UC volume path, e.g. `/Volumes/<CATALOG>/<SCHEMA>/<VOLUME_NAME>/` |
| `warehouse_id` | SQL warehouse ID for Genie Space creation |
| `evaluation_experiment` | MLflow experiment path for extraction quality evaluation (defaults to `/Shared/<table_prefix>_product_manuals_extraction_eval`) |

---

## 🚀 Deployment

1. In Databricks, add a Git folder and clone this repo.
2. Open the `databricks_etl/` directory as your bundle project.
3. Edit [`databricks.yml`](databricks.yml) and set the variables above.
4. Use the workspace **Deploy** flow, choose your target (`dev` or `prod`), and deploy.
   - Reference: [Deploy bundles and run workflows from the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy)
5. After deploy, open **Workflows → Jobs** and run `{table_prefix}_extract_productmanuals_job`.

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

Both jobs can trigger automatically when new files land on the volume. Uncomment the `trigger` block in the job YAML and redeploy:

- [`resources/extract_productmanuals.job.yml`](resources/extract_productmanuals.job.yml) — lines 10–13

### Generating extraction schemas interactively

Use **Agents → Information Extraction** in the Databricks UI to design your schema interactively before embedding it as code.
Reference: [Intelligent document processing](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing)
