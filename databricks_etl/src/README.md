# ETL bundle source layout

Under `databricks_etl/src/`:

- **`transformations/`** — DLT pipeline definitions (Python and SQL), e.g. `productmanuals/`, `invoices/`, `productmanuals_sql/`.
- **`genie_space/`** — Notebooks and scripts for Genie space setup.
- **`knowledge_assistant/`** — Create-or-update Knowledge Assistant notebooks run after extract jobs (`create_or_update_knowledge_assistant_*.ipynb`) and helpers (`manage_knowledge_assistant.py`).
- **`supervisor_agent/`** — Supervisor Agent notebooks (`create_supervisor_agent_*.ipynb`) and REST helpers (`manage_supervisor_agent.py`).
- **`evaluation/`** — Evaluation scripts (e.g. MLflow genai scoring).
- **`exploration/`** — Ad-hoc exploration notebooks.
- **`data_extraction_etl/`** — Minimal Python package so pipeline environments can `pip install -e .` from the ETL bundle root.

## Databricks App users and permissions

Anyone who should **use** the Data Extraction App (not only deploy it) needs **Unity Catalog and workspace access** to the same underlying resources the app calls: the **volume** used for uploads, the **processed table** queried in SQL, the **SQL warehouse**, the **Jobs** job triggered for processing, and the **agent serving endpoint** used for chat. Grant the appropriate privileges (for example read/write on the volume, `SELECT` on the table, `CAN_USE` on the warehouse, `CAN_MANAGE_RUN` or run permission on the job, and `CAN_QUERY` on the endpoint) so their identity matches what the app runs as in your workspace.

## Getting started with DLT

Most pipeline code lives under **`transformations/`**. See [DLT Python reference](https://docs.databricks.com/dlt/python-ref.html).
