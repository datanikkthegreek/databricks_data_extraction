This 

# ETL bundle deployment

This guide covers deploying the **Databricks Asset Bundle** under [`databricks_etl/`](databricks_etl/) (Spark Declarative pipelines and jobs including a Supervisor Agent).

**App deployment:** end-to-end deployment of the FastAPI / apx **app** bundle from Git is **coming soon**.

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

## Additional information

### ***Databricks App orchestrating the workflow is coming soon***

### Automatic job runs (file arrival)

The **invoices** and **product manuals** jobs can each run automatically when new files land on the UC volume. Uncomment the commented `trigger` block (`pause_status: UNPAUSED` and `file_arrival` with `url: ${var.volume}`) in the job definition, then redeploy the bundle:

- [`databricks_etl/resources/extract_invoices.job.yml`](databricks_etl/resources/extract_invoices.job.yml) — lines **12–15**
- [`databricks_etl/resources/extract_productmanuals.job.yml`](databricks_etl/resources/extract_productmanuals.job.yml) — lines **10–13**

The job watches the configured volume path for arrivals (see Databricks job trigger documentation for behavior and limits).

### Generating extraction code (Agents)

To scaffold or iterate on extraction logic, use the Databricks UI: **Agents → Information Extraction**, which builds on **Intelligent Document Processing** (document parsing, extraction, and classification on the lakehouse). Background: [Intelligent document processing](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing).

