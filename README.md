**Editors:** Merve Karali and Nikolaos Servos

The goal of this solution accelerator is to transform unstructured product manuals into structured, queryable data using Databricks Agent Bricks AI Functions, enabling organizations to build a complete document intelligence pipeline without custom model training or rigid templates. This solution addresses the challenge of extracting critical technical data—such as product specifications and component compatibility—from varying document formats and inconsistent vendor terminology, which is too slow and error-prone for manual processing.

### End-to-End Architecture Summary

The architecture is built as an incremental and production-ready **Lakeflow Spark Declarative Pipeline** on Databricks, orchestrated by **Lakeflow Jobs** and governed by **Unity Catalog**.

The solution involves three main pipeline steps:

1.  **Parse PDFs with `ai_parse_document`**: Raw PDF manuals are read as binary files from a Unity Catalog Volume. The `ai_parse_document` function processes these files and returns a structured JSON output containing text, tables, figures, and layout metadata.
2.  **Extract Structured Fields with `ai_extract` (v2)**: This function uses the parsed document and a declarative JSON schema (including types and descriptive field instructions) to extract key product specifications (e.g., manufacturer, model number, rated voltage). Prompt engineering is used here to steer the Large Language Model (LLM) toward specific values and terminology.
3.  **Flatten and Type-Cast**: The JSON result from `ai_extract` is converted into a clean table with strongly typed columns and descriptive column comments, creating the final structured product catalog.

**Quality Evaluation**
The extraction quality is continuously measured using **MLflow 3 GenAI evaluation**, which employs both code-based scorers (checking completeness) and LLM-as-judge scorers (verifying language and validity).

**Delivering Results to Business Users**
The processed data is made accessible through complementary interfaces on **Databricks One**:

  * **Genie Space**: Allows users to query the structured product catalog using natural language, which is translated into SQL.
  * **Knowledge Assistant**: Indexes the raw PDF manuals to provide cited, document-grounded answers for open-ended questions (e.g., safety instructions or troubleshooting steps).
  * **Supervisor Agent**: Ties the Genie Space and Knowledge Assistant together into a unified interface, which can be surfaced to the end user via a **Databricks App**.

All those elements are set-up and deployed with this solution by following the below steps.

Architecture

![Architecture](docs/images/architecture.png)

This guide covers deploying the **Databricks Asset Bundle** under [`databricks_etl/`](databricks_etl/) (Spark Declarative pipelines and jobs including a Supervisor Agent).

**App deployment:** the FastAPI / apx app bundle lives under [`databricks_app/`](databricks_app/). **The app bundle is deployed only from your local machine** using the Databricks CLI, not from the workspace bundle UI. Follow **step 8** under [Local Deployment via CLI](#local-deployment-via-cli).

# Deployment from the Databricks Workspace UI

If you want to deploy via CLI from locally check the next Chapter

## 1. Clone the repository in a Git folder

In Databricks, add a Git folder and clone:

```text
https://github.com/datanikkthegreek/databricks_data_extraction.git
```

**Bundle location in this repo:** the Declarative Automation Bundle (`databricks.yml`) lives under [`databricks_etl/`](databricks_etl/), not at the monorepo root. Databricks identifies a folder as a bundle when `databricks.yml` sits at the **root of that folder**—see [I have a bundle in a GitHub repository](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace.html). After the clone appears in the workspace, **open the `databricks_etl` directory** as your bundle project (the directory that contains [`databricks_etl/databricks.yml`](databricks_etl/databricks.yml)). If your UI only attaches bundle tooling at the Git repo root, use the web terminal from step 1 and run bundle commands after `cd databricks_etl`, same as the CLI guide.

## 2. Unity Catalog: catalog, schema, volume, and sample data

1. In Databricks, create or choose a **catalog**, **schema**, and a **Unity Catalog volume** (managed or external) where ingestion files will live. See [What is Unity Catalog?](https://docs.databricks.com/en/data-governance/unity-catalog/index.html) and [Create and work with volumes](https://docs.databricks.com/en/volumes/index.html).

2. Set the bundle `volume` variable (step 4) to the UC path prefix for that volume, in the form:  
   `/Volumes/<catalog>/<schema>/<volume-name>/`  
   (trailing slash is fine if it matches your `databricks.yml`.)

3. **Upload sample files** so pipeline paths exist:
   - **Product manuals pipeline**: upload the contents of the repo folder [`productmanuals/`](productmanuals/) into **`{volume}/productmanuals`** on the volume (the pipeline reads `${volume}/productmanuals`).
   - **Invoices pipeline** (if you run the invoices job): place files under **`{volume}/invoices`** (see `01_parsed.sql` in the invoices transformation).

## 3. Configure the bundle

Edit [`databricks_etl/databricks.yml`](databricks_etl/databricks.yml) in the workspace (editor, Repos, or the bundle experience) and set **`variables`** for your workspace:

| Variable | Purpose |
|----------|---------|
| `catalog` | Unity Catalog catalog for DLT |
| `schema` | Schema for DLT |
| `table_prefix` | Prefix for Delta table names and for **job/pipeline display names** in the workspace |
| `volume` | UC volume path used by pipelines (see step 3) |
| `warehouse_id` | SQL warehouse ID for Genie-related notebook tasks in the jobs |

For editing and committing YAML from the UI, see [Author bundles in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-author).

## 4. Deploy the bundle

Use the workspace **Deploy** flow for your bundle, choose the correct **target** (for example `dev` vs `prod`) as defined in [`databricks_etl/databricks.yml`](databricks_etl/databricks.yml), and deploy. Step-by-step help: [Tutorial: Create and deploy a bundle in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-tutorial) and [Deploy bundles and run workflows from the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy).

You **cannot** deploy the same bundle from the workspace bundle editor into **another** Databricks workspace; for that, use CI/CD (for example GitHub Actions) with the CLI, as recommended in [Collaborate on bundles in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace.html).

## 5. Run the Databricks jobs

After a successful deploy, open **Workflows** → **Jobs** (or run workflows from the bundle UI as described in [Deploy bundles and run workflows from the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-deploy)). Job display names include `table_prefix`, for example:

- `[dev <Your Name>]{table_prefix}_extract_invoices_job`
- `[dev <Your Name>]{table_prefix}_extract_productmanuals_job`

When starting a run from the UI, you can set the job parameter **`create_agent`** to `false` if the Knowledge Assistant and Supervisor notebook tasks should be skipped; the default is `true`.

Important: The Knowledge Assistant will take at least 15 min to build up. To reduce costs we do not let the job run until the syncing of the Agent has been completed. You can check the status on the Agents tab.

# Local Deployment via CLI

## 1. Install the Databricks CLI and configure a profile

1. **Install the Databricks CLI** (if not already installed):
   - Follow [Install the Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html#install-the-databricks-cli).
   - Example with Homebrew (macOS): `brew install databricks/tap/databricks`

2. **Create a profile** for your workspace (pick one approach):
   - **Browser (SSO)**: run  
     `databricks auth login https://<your-workspace-host> --profile=<profile-name>`  
     Complete sign-in in the browser. The profile is stored in `~/.databrickscfg`.
   - **Personal access token (PAT)**: configure the same file (or env vars) so the profile has **host** and **token**; see [Databricks authentication](https://docs.databricks.com/en/dev-tools/auth/index.html). PAT is typical for scripts and CI.

3. **Verify the profile**:  
   `databricks auth profiles | grep <profile-name>` — a valid profile shows `YES`.

The profile name in the deploy example below (`FEVM`) is only an example; substitute your own.

## 2. Clone the repository

```bash
git clone https://github.com/datanikkthegreek/databricks_data_extraction.git
cd databricks_data_extraction
```

## 3. Unity Catalog: catalog, schema, volume, and sample data

1. In Databricks, create or choose a **catalog**, **schema**, and a **Unity Catalog volume** (managed or external) where ingestion files will live. See [What is Unity Catalog?](https://docs.databricks.com/en/data-governance/unity-catalog/index.html) and [Create and work with volumes](https://docs.databricks.com/en/volumes/index.html).

2. Set the bundle `volume` variable (step 4) to the UC path prefix for that volume, in the form:  
   `/Volumes/<catalog>/<schema>/<volume-name>/`  
   (trailing slash is fine if it matches your `databricks.yml`.)

3. **Upload sample files** so pipeline paths exist:
   - **Product manuals pipeline**: upload the contents of the repo folder [`productmanuals/`](productmanuals/) into **`{volume}/productmanuals`** on the volume (the pipeline reads `${volume}/productmanuals`).
   - **Invoices pipeline** (if you run the invoices job): place files under **`{volume}/invoices`** (see `01_parsed.sql` in the invoices transformation).

## 4. Configure the bundle

Edit [`databricks_etl/databricks.yml`](databricks_etl/databricks.yml) and set **`variables`** for your workspace:

| Variable | Purpose |
|----------|---------|
| `catalog` | Unity Catalog catalog for DLT |
| `schema` | Schema for DLT |
| `table_prefix` | Prefix for Delta table names and for **job/pipeline display names** in the workspace |
| `volume` | UC volume path used by pipelines (see step 3) |
| `warehouse_id` | SQL warehouse ID for Genie-related notebook tasks in the jobs |

## 5. Sync Python dependencies

From the ETL bundle directory:

```bash
cd databricks_etl && uv sync
```

This aligns the local environment with [`databricks_etl/pyproject.toml`](databricks_etl/pyproject.toml) before deploy.

## 6. Deploy the bundle

From `databricks_etl`, deploy using your profile. Example with PAT auth type and a profile named `FEVM`:

```bash
cd databricks_etl
databricks bundle deploy -p FEVM
```

In some cases you might want to enforce PAT deployment

```bash
DATABRICKS_AUTH_TYPE=pat databricks bundle deploy -p FEVM
```

## 7. Run the Databricks jobs

After a successful deploy, open **Workflows** → **Jobs** in the workspace. Run the jobs you need; their display names include `table_prefix`, for example:

- `[dev <Your Name>]{table_prefix}_extract_invoices_job` 
- `[dev <Your Name>]{table_prefix}_extract_productmanuals_job` 

From the repo, after `cd databricks_etl`, you can also trigger a run from the CLI, for example:

```bash
databricks bundle run extract_invoices_job -p FEVM
databricks bundle run extract_productmanuals_job -p FEVM
```

(Replace `FEVM` with your profile name.)

You can also run the job with different settings and set the parameter create_agent to `false` if the knowledge assistant and supervisor should not be created. Default is `true`

Important: The Knowledge Assistant will take at least 15 min to build up. To reduce costs we do not let the job run until the syncing of the Agent has been completed. You can check the status on the Agents tab.

## 8. Databricks App (`databricks_app`)

This step deploys the **Databricks App** (FastAPI + [apx](https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial)) that orchestrates uploads, SQL warehouse queries, and chat against your agent serving endpoint. It is a **separate** bundle from [`databricks_etl/`](databricks_etl/): the bundle root is the directory that contains [`databricks_app/databricks.yml`](databricks_app/databricks.yml). **Deploy this app bundle from your local CLI only** (workspace bundle UI is not used here); complete the substeps below from your machine.

**Prerequisites:** Install the Databricks CLI and configure a profile as in [§ 1](#1-install-the-databricks-cli-and-configure-a-profile) (*Install the Databricks CLI and configure a profile*).

### 8.1 Configure app environment (`app.yml`)

Edit [`databricks_app/app.yml`](databricks_app/app.yml) in your **local clone** before you run `databricks bundle deploy` (this repo does not document deploying that bundle from the workspace UI).

Runtime environment variables for the app are defined there:

| `env` name | Purpose |
|------------|---------|
| `WAREHOUSE_ID` | SQL warehouse ID; the app builds the HTTP path `/sql/1.0/warehouses/{id}` for warehouse queries. |
| `JOB_ID` | Databricks Jobs job ID used when triggering the processing job from the app. |
| `VOLUME_PATH` | Unity Catalog volume path where PDFs are stored (same style as ETL: `/Volumes/<catalog>/<schema>/<volume>/`). |
| `AI_EXTRACT_PROCESSED_TABLE` | Full table name (`catalog.schema.table`) for the processed / queryable extraction results. |
| `AGENT_ENDPOINT` | Name of the **serving endpoint** for the supervisor / chat agent. |

For **local** runs (for example `apx dev`), the backend also expects a workspace **host** and token fallback via `DATABRICKS_HOST` or `DATA_EXTRACTION_HOST`, and `FEVM_TOKEN` or `DATA_EXTRACTION_TOKEN`, typically in [`databricks_app/.env`](databricks_app/.env). On Databricks Apps, the platform usually supplies the forwarded access token; align any extra env with your workspace policy.

### 8.2 Configure the deployed app name prefix

In [`databricks_app/databricks.yml`](databricks_app/databricks.yml), set **`variables.app_name_prefix`**. The Apps resource **`name`** is `"${var.app_name_prefix}-data-extraction-app"` (for example `extract-7-data-extraction-app` when the default prefix is `extract-7`). You can override at deploy time without editing the file:

```bash
databricks bundle deploy -p <profile> --var app_name_prefix=my-team
```

### 8.3 Build and deploy the app bundle

From the app bundle directory (must be the folder containing `databricks.yml`):

```bash
cd databricks_app
databricks bundle validate -p <profile>
databricks bundle deploy -p <profile>
```

`databricks bundle deploy` runs the bundle `artifacts.app` build (`uv run apx build`) and syncs `.build` to the workspace. Replace `<profile>` with your CLI profile (see § 1).

Official reference: [Deploy Databricks Apps with Databricks Asset Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/apps-tutorial).

### 8.4 Start the app manually

After a successful deploy, open the workspace **Apps** experience (for example **Compute → Apps**, depending on your workspace UI), select the app whose name matches `${app_name_prefix}-data-extraction-app`, and **start** it if it is stopped, then open the app URL. Policies vary by workspace; if the app does not auto-start, use this step before testing.

### 8.5 Optional: deploy or refresh from the Apps CLI

You can point the app at an already-synced bundle build under your user’s `.bundle` path (for example after `databricks bundle deploy`). Use your workspace account segment and bundle target in place of the placeholders:

```bash
databricks apps deploy <app-name> \
  --source-code-path /Workspace/Users/<workspace-user>/.bundle/data-extraction-app/dev/files/.build
```

Example (replace the user segment with yours):

```bash
databricks apps deploy extract-7-data-extraction-app \
  --source-code-path /Workspace/Users/nikolaos.servos@databricks.com/.bundle/data-extraction-app/dev/files/.build
```

- **`<app-name>`** must match the deployed app **`name`** in [`databricks_app/databricks.yml`](databricks_app/databricks.yml) (`${var.app_name_prefix}-data-extraction-app`).
- **`data-extraction-app`** in the path is **`bundle.name`** in that file; **`<target>`** is the bundle target (for example `dev`).

### 8.6 App users and underlying resources

Anyone who should **use** the Data Extraction App (not only deploy it) needs **Unity Catalog and workspace access** to the same underlying resources the app calls: the **volume** used for uploads, the **processed table** queried in SQL, the **SQL warehouse**, the **Jobs** job triggered for processing, and the **agent serving endpoint** used for chat. Grant the appropriate privileges (for example read/write on the volume, `SELECT` on the table, `CAN_USE` on the warehouse, `CAN_MANAGE_RUN` or run permission on the job, and `CAN_QUERY` on the endpoint) so each user’s identity is allowed for those objects in your workspace (typically the signed-in user when the app runs on Databricks Apps).

## Additional information



### Automatic job runs (file arrival)

The **invoices** and **product manuals** jobs can each run automatically when new files land on the UC volume. Uncomment the commented `trigger` block (`pause_status: UNPAUSED` and `file_arrival` with `url: ${var.volume}`) in the job definition, then redeploy the bundle:

- [`databricks_etl/resources/extract_invoices.job.yml`](databricks_etl/resources/extract_invoices.job.yml) — lines **12–15**
- [`databricks_etl/resources/extract_productmanuals.job.yml`](databricks_etl/resources/extract_productmanuals.job.yml) — lines **10–13**

The job watches the configured volume path for arrivals (see Databricks job trigger documentation for behavior and limits).

### Generating extraction code (Agents)

To scaffold or iterate on extraction logic, use the Databricks UI: **Agents → Information Extraction**, which builds on **Intelligent Document Processing** (document parsing, extraction, and classification on the lakehouse). Background: [Intelligent document processing](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing).

