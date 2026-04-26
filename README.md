# 🧠 Intelligent Document Processing: PDF → Structured Product Catalog

Transform unstructured product manuals into structured, queryable data using **Databricks Agent Bricks AI Functions** — no custom model training, no rigid templates.

**Authors:** Merve Karali and Nikolaos Servos

> 📖 **Read the full blog post:** [Intelligent Document Processing for Data Extraction](https://community.databricks.com/t5/technical-blog/intelligent-document-processing-for-data-extraction-transforming/ba-p/153847)

---

## 💡 Why This Solution?

- **No training data required.** Define what to extract through a declarative schema and start processing new document types immediately.
- **SQL-native, no infrastructure overhead.** The entire pipeline runs in streaming tables — no separate model endpoints or custom inference code.
- **Incremental by default.** Only new documents are processed on each run, making the pipeline production-ready from day one.
- **End-to-end governance.** Unity Catalog governs PDFs, extracted tables, Genie Spaces, and Knowledge Assistants under one access control model.
- **Measurable quality.** MLflow evaluation provides quantitative metrics to track extraction quality and catch regressions early.

---

## 🏗️ Architecture

![Architecture](docs/images/Architecture.png)

---

## 🗂️ Directory Structure

```
.
├── demo/                  # ✅ Start here — single notebook that runs the full pipeline
│                          #    end to end: catalog setup → parse → extract → evaluate
│
├── databricks_etl/        # Production-grade Lakeflow pipeline deployed as a Databricks
│                          #    Asset Bundle. Parses PDFs, extracts structured fields, and
│                          #    builds three business-user interfaces on top of the data:
│                          #    • Genie Space    — ask natural-language questions about the
│                          #                       extracted structured product catalog
│                          #    • Knowledge Assistant — ask open-ended questions answered
│                          #                       directly from the raw PDF documents
│                          #    • Supervisor Agent — single chat interface that routes
│                          #                       questions to Genie or Knowledge Assistant
│                          #                       depending on what is being asked
│
├── databricks_app/        # Full-stack web application (FastAPI + React) deployed as a
│                          #    Databricks App. Lets business users upload PDFs, trigger
│                          #    the extraction pipeline, browse the structured results,
│                          #    and chat with the Supervisor Agent — all in one UI.
│
└── productmanuals/        # Sample PDF product manuals (Bosch, Makita, DeWalt, Milwaukee)
                           #    used to demonstrate the pipeline
```

---

## 🧭 Where to Go Next

| I want to… | Go to |
|-----------|-------|
| Try the pipeline quickly without any infrastructure | [▶ Demo notebook](demo/demo_notebook.ipynb) |
| Deploy the production Lakeflow pipeline and Jobs | [▶ ETL deployment guide](databricks_etl/README.md) |
| Deploy the Databricks App (upload UI + chat) | [▶ App deployment guide](databricks_app/README.md) |

---

## 🚀 Quick Start: Demo Notebook

Open [`demo/demo_notebook.ipynb`](demo/demo_notebook.ipynb) and run top to bottom — it handles everything from catalog creation to MLflow evaluation in a single self-contained notebook.

**Prerequisites:** Unity Catalog enabled · DBR 14.3 ML or later · `CREATE CATALOG` privilege

---

## 🌍 Other Use Cases

| Industry | Example |
|----------|---------|
| Manufacturing | Component specs from supplier data sheets for BOM automation |
| Healthcare | Structured fields from clinical trial reports or device documentation |
| Financial Services | Loan agreements, insurance policies, or regulatory filings |
| Retail | Product catalogs from vendor-provided PDFs for marketplace onboarding |

---

## 📚 Resources

- 📖 [Blog post](https://community.databricks.com/t5/technical-blog/intelligent-document-processing-for-data-extraction-transforming/ba-p/153847)
- 📄 [`ai_parse_document` docs](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- 🔍 [`ai_extract` docs](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- 📊 [MLflow 3 GenAI evaluation](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- 🤖 [Intelligent Document Processing overview](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/intelligent-document-processing)
