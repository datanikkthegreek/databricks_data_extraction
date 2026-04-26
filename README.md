# 🧠 Intelligent Document Processing: PDF → Structured Product Catalog

Transform unstructured product manuals into structured, queryable data using **Databricks Agent Bricks AI Functions** — no custom model training, no rigid templates.

**Authors:** Merve Karali and Nikolaos Servos

> 📖 **Read the full blog post:** [Intelligent Document Processing for Data Extraction: Transforming Product Manuals into Actionable Insights](https://community.databricks.com/t5/technical-blog/intelligent-document-processing-for-data-extraction-transforming/ba-p/153847)

---

## 💡 Why This Solution?

- **No training data required.** Define what to extract through a declarative schema and start processing new document types immediately.
- **SQL-native, no infrastructure overhead.** The entire pipeline is expressed in streaming tables — no separate model endpoints or custom inference code.
- **Incremental by default.** Streaming tables process only new documents on each run, making the pipeline production-ready from day one.
- **End-to-end governance.** Unity Catalog governs PDFs, extracted tables, Genie Spaces, and Knowledge Assistants under one access control model.
- **Measurable quality.** MLflow evaluation provides quantitative metrics to track extraction quality over time and catch regressions early.

---

## 🗂️ Directory Structure

```
.
├── demo/                          # ✅ Start here — self-contained demo notebook
│   └── demo_notebook.ipynb
├── databricks_etl/                # Production Lakeflow pipeline + Jobs (Asset Bundle)
│   ├── databricks.yml
│   ├── resources/                 # Job and pipeline definitions
│   └── src/
│       ├── transformations/       # Parse → Extract → Process (productmanuals & invoices)
│       ├── evaluation/            # MLflow 3 GenAI evaluation
│       ├── genie_space/           # Genie Space creation
│       ├── knowledge_assistant/   # Knowledge Assistant creation
│       └── supervisor_agent/      # Supervisor Agent creation
├── databricks_app/                # FastAPI + React Databricks App (Asset Bundle)
│   ├── databricks.yml
│   └── app.yml
├── productmanuals/                # Sample PDF product manuals
└── docs/images/Architecture.png
```

---

## 🧭 Suggested Usage

| Path | Audience | Purpose |
|------|----------|---------|
| `demo/` | Anyone evaluating the solution | Run the full pipeline end-to-end in a single notebook |
| `databricks_etl/` | Data engineers, production deployments | Incremental Lakeflow pipeline with Jobs orchestration |
| `databricks_app/` | App developers | FastAPI + React UI for uploads, queries, and agent chat |

---

## 🏗️ Architecture

The pipeline parses raw PDFs, extracts structured fields, evaluates quality, and exposes results through complementary business-user interfaces — all on a single platform.

![Architecture](docs/images/Architecture.png)

---

## 🚀 Quick Start: Demo Notebook

The fastest way to experience the solution is the self-contained demo notebook. It requires no pipeline infrastructure — just a Databricks workspace with Unity Catalog.

**Prerequisites:** Unity Catalog enabled · DBR 14.3 ML or later · `CREATE CATALOG` privilege

**Steps:**

1. Clone this repository into a Databricks Git folder:
   ```text
   https://github.com/datanikkthegreek/databricks_data_extraction.git
   ```
2. Open [`demo/demo_notebook.ipynb`](demo/demo_notebook.ipynb).
3. Edit the configuration cell (catalog, schema, volume, table prefix), upload sample PDFs from [`productmanuals/`](productmanuals/) to your volume, and run top to bottom.

The notebook walks through:

| Step | What it does |
|------|-------------|
| 0 | Creates catalog, schema, and volume |
| 1 | Parses PDFs with `ai_parse_document` |
| 2 | Extracts 14 structured fields with `ai_extract` (v2) |
| 3 | Flattens results into a typed Delta table |
| 4 | Evaluates extraction quality with MLflow 3 GenAI evaluation |

---

## ⚙️ Full Pipeline Deployment

The production pipeline is a **Databricks Asset Bundle** under [`databricks_etl/`](databricks_etl/) — a Lakeflow Spark Declarative Pipeline (incremental, serverless) orchestrated by Lakeflow Jobs.

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- A catalog, schema, and Unity Catalog volume where PDF files will land
- A SQL warehouse (for Genie Space creation)
- Sample PDFs uploaded to `{volume}/productmanuals` (use files from [`productmanuals/`](productmanuals/))

### Bundle variables

Set these in [`databricks_etl/databricks.yml`](databricks_etl/databricks.yml) before deploying:

| Variable | Purpose |
|----------|---------|
| `catalog` | Unity Catalog catalog |
| `schema` | Schema (database) |
| `table_prefix` | Prefix for all Delta table and job display names |
| `volume` | UC volume path, e.g. `/Volumes/<catalog>/<schema>/<volume>/` |
| `warehouse_id` | SQL warehouse ID for Genie Space creation |

> **Note:** The bundle root is `databricks_etl/`, not the repo root. Open or `cd` into that directory before running any bundle commands.

---

### Option A: Deploy from the Workspace UI

1. In Databricks, add a Git folder and clone this repo.
2. Open the `databricks_etl/` directory as your bundle project.
3. Edit `databricks_etl/databricks.yml` and set the variables above.
4. Use the workspace **Deploy** flow, choose your target (`dev` or `prod`), and deploy.
   - Reference: [Deploy bundles and run workflows from the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy)
5. After a successful deploy, open **Workflows → Jobs** and run:
   - `{table_prefix}_extract_productmanuals_job`
   - `{table_prefix}_extract_invoices_job` *(optional)*

---

### Option B: Deploy from the CLI

**1. Install and configure the Databricks CLI**

```bash
brew install databricks/tap/databricks          # macOS
databricks auth login https://<workspace-host> --profile=<profile-name>
databricks auth profiles | grep <profile-name>  # should show YES
```

Reference: [Install the Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html#install-the-databricks-cli)

**2. Clone the repository**

```bash
git clone https://github.com/datanikkthegreek/databricks_data_extraction.git
cd databricks_data_extraction
```

**3. Sync Python dependencies**

```bash
cd databricks_etl && uv sync
```

**4. Deploy the bundle**

```bash
databricks bundle deploy -p <profile>
# If you need to force PAT auth:
DATABRICKS_AUTH_TYPE=pat databricks bundle deploy -p <profile>
```

**5. Run the jobs**

From the workspace UI (**Workflows → Jobs**), or from the CLI:

```bash
databricks bundle run extract_productmanuals_job -p <profile>
databricks bundle run extract_invoices_job -p <profile>
```

> Set the job parameter `create_agent` to `false` to skip Knowledge Assistant and Supervisor Agent creation. Default is `true`.
>
> ⏱️ **Note:** The Knowledge Assistant takes at least 15 minutes to build. The job does not wait for it to complete — check status under the **Agents** tab.

---

## 📱 Databricks App

The [`databricks_app/`](databricks_app/) bundle deploys a FastAPI + React app for uploading PDFs, triggering the extraction job, querying results, and chatting with the Supervisor Agent.

> **The app bundle must be deployed from your local CLI** — the workspace bundle UI is not supported for this bundle.

### Configure `app.yml`

Edit [`databricks_app/app.yml`](databricks_app/app.yml) before deploying:

| Environment variable | Purpose |
|----------------------|---------|
| `WAREHOUSE_ID` | SQL warehouse ID for query execution |
| `JOB_ID` | Job ID of the extraction job to trigger from the app |
| `VOLUME_PATH` | Volume path for PDF uploads, e.g. `/Volumes/<catalog>/<schema>/<volume>/` |
| `AI_EXTRACT_PROCESSED_TABLE` | Full table name (`catalog.schema.table`) for extraction results |
| `AGENT_ENDPOINT` | Serving endpoint name for the Supervisor Agent |

### Configure the app name

In [`databricks_app/databricks.yml`](databricks_app/databricks.yml), set `variables.app_name_prefix`. The deployed app name will be `{app_name_prefix}-data-extraction-app`. Override at deploy time without editing the file:

```bash
databricks bundle deploy -p <profile> --var app_name_prefix=my-team
```

### Deploy

```bash
cd databricks_app
databricks bundle validate -p <profile>
databricks bundle deploy -p <profile>
```

After deploy, open **Compute → Apps** in your workspace, find the app, start it if stopped, and open its URL.

### App user permissions

Users of the app need access to the underlying resources it calls:

| Resource | Required privilege |
|----------|--------------------|
| Volume | Read / write |
| Processed table | `SELECT` |
| SQL warehouse | `CAN_USE` |
| Extraction job | `CAN_MANAGE_RUN` |
| Agent serving endpoint | `CAN_QUERY` |

---

## 🔧 Additional Configuration

### Automatic file-arrival triggers

Both jobs support automatic triggering when new files land on the volume. Uncomment the `trigger` block in the job YAMLs and redeploy:

- [`databricks_etl/resources/extract_productmanuals.job.yml`](databricks_etl/resources/extract_productmanuals.job.yml) — lines 10–13
- [`databricks_etl/resources/extract_invoices.job.yml`](databricks_etl/resources/extract_invoices.job.yml) — lines 12–15

### Generating extraction schemas interactively

Use **Agents → Information Extraction** in the Databricks UI to design your extraction schema interactively before embedding it as code. Background: [Intelligent document processing](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing).

---

## 🌍 Applying This to Other Use Cases

The same parse → extract → evaluate pattern applies to any domain where structured data needs to be pulled from unstructured documents:

| Industry | Example use case |
|----------|-----------------|
| Manufacturing | Extract component specs from supplier data sheets for BOM automation |
| Healthcare | Pull structured fields from clinical trial reports or medical device docs |
| Financial Services | Parse loan agreements, insurance policies, or regulatory filings |
| Retail | Build product catalogs from vendor-provided PDFs for marketplace onboarding |

---

## 📚 Resources

- 📖 [Blog post: Intelligent Document Processing for Data Extraction](https://community.databricks.com/t5/technical-blog/intelligent-document-processing-for-data-extraction-transforming/ba-p/153847)
- 📄 [`ai_parse_document` documentation](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- 🔍 [`ai_extract` documentation](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- 📊 [MLflow 3 GenAI evaluation](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- 🤖 [Intelligent Document Processing overview](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing)
- 📦 [Databricks Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- 🗄️ [Lakeflow Spark Declarative Pipelines](https://docs.databricks.com/ldp/)
