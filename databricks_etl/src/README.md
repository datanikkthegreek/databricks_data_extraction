# ETL bundle source layout

Under `databricks_etl/src/`:

- **`transformations/`** — DLT pipeline definitions (Python and SQL), e.g. `productmanuals/`, `invoices/`, `productmanuals_sql/`.
- **`genie_space/`** — Notebooks and scripts for Genie space setup.
- **`knowledge_assistant/`** — Create-or-update Knowledge Assistant notebooks run after extract jobs (`create_or_update_knowledge_assistant_*.ipynb`) and helpers (`manage_knowledge_assistant.py`).
- **`evaluation/`** — Evaluation scripts (e.g. MLflow genai scoring).
- **`exploration/`** — Ad-hoc exploration notebooks.
- **`data_extraction_etl/`** — Minimal Python package so pipeline environments can `pip install -e .` from the ETL bundle root.

## Getting started with DLT

Most pipeline code lives under **`transformations/`**. See [DLT Python reference](https://docs.databricks.com/dlt/python-ref.html).
