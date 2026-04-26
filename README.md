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

The diagram below shows the end-to-end flow — from raw PDFs through the extraction pipeline to the business-user interfaces on Databricks One.

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

## 📂 Component Guides

### 🗒️ Demo Notebook — [`demo/`](demo/demo_notebook.ipynb)

The demo notebook provides a self-contained introduction to the solution. It covers catalog and volume creation, PDF parsing with `ai_parse_document`, structured field extraction with `ai_extract`, result flattening into a typed Delta table, and extraction quality evaluation with MLflow — all executable in sequence without any pipeline infrastructure.

**Prerequisites:** Unity Catalog enabled · Serverless compute or Databricks Runtime 17.3 ML or above

### ⚙️ ETL Pipeline — [`databricks_etl/`](databricks_etl/README.md)

The ETL bundle contains the production-grade Lakeflow Spark Declarative Pipeline and Lakeflow Jobs. It deploys the full incremental processing pipeline along with a Genie Space for natural-language querying of the structured output, a Knowledge Assistant for open-ended Q&A directly against the source PDFs, and a Supervisor Agent that unifies both interfaces. For deployment instructions, see the [ETL README](databricks_etl/README.md).

### 📱 Databricks App — [`databricks_app/`](databricks_app/README.md)

The application bundle deploys a full-stack web application built with FastAPI and React. It provides a user interface for uploading PDF documents, triggering the extraction pipeline, browsing structured results, and conversing with the Supervisor Agent. For deployment and local development instructions, see the [App README](databricks_app/README.md).

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
