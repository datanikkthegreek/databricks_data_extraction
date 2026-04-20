# Databricks notebook source
# MAGIC %md
# MAGIC # Evaluate Product Manual Extraction Quality with MLflow
# MAGIC
# MAGIC This notebook evaluates the quality of AI-extracted product specifications
# MAGIC using MLflow 3 GenAI evaluation. It uses a combination of:
# MAGIC - **Custom code scorers** for structural validation (completeness, format)
# MAGIC - **LLM judge scorers** for semantic quality assessment (english compliance, extraction quality)

# COMMAND ----------

# MAGIC %pip install --upgrade "mlflow[databricks]>=3.1.0"
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
import mlflow.genai
from mlflow.genai.scorers import Guidelines, scorer
from mlflow.entities import Feedback

mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Users/merve.karali@databricks.com/product_manuals_extraction_eval")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Load Extracted Data
# MAGIC
# MAGIC Read from both the processed table (extracted fields) and the parsed table
# MAGIC (source document text) to build the evaluation dataset.

# COMMAND ----------

CATALOG = "data_extraction"
SCHEMA = "default"
try:
    TABLE_PREFIX = dbutils.widgets.get("table_prefix")
except Exception:
    TABLE_PREFIX = "app"

df_processed = spark.table(f"{CATALOG}.{SCHEMA}.{TABLE_PREFIX}_productmanuals_processed")
df_parsed = spark.table(f"{CATALOG}.{SCHEMA}.{TABLE_PREFIX}_productmanuals_parsed")

df_eval = df_processed.join(
    df_parsed.select("file_name", "document"),
    on="file_name",
    how="inner"
)

display(df_eval)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Build Evaluation Dataset
# MAGIC
# MAGIC Each row becomes one evaluation record. The `inputs` contain the source document,
# MAGIC and `outputs` contain the extracted fields. Since outputs are pre-computed by the
# MAGIC pipeline, no `predict_fn` is needed.

# COMMAND ----------

EXTRACTION_FIELDS = [
    "manufacturer", "model_number", "product_name", "product_type",
    "rated_voltage_v", "max_torque_nm", "no_load_speed_low_rpm",
    "no_load_speed_high_rpm", "chuck_capacity_mm",
    "max_drilling_diameter_wood_mm", "max_drilling_diameter_steel_mm",
    "weight_kg", "compatible_batteries", "compatible_chargers"
]

rows = df_eval.collect()

eval_data = []
for row in rows:
    outputs = {field: row[field] for field in EXTRACTION_FIELDS}
    outputs_str = "\n".join(f"  {k}: {v}" for k, v in outputs.items())

    eval_data.append({
        "inputs": {
            "file_name": row["file_name"],
            "source_text": row["document"][:5000] if row["document"] else "",
        },
        "outputs": {
            "response": outputs_str,
            "extracted_fields": outputs,
        },
    })

print(f"Built evaluation dataset with {len(eval_data)} records")
for record in eval_data:
    print(f"  - {record['inputs']['file_name']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Define Custom Scorers
# MAGIC
# MAGIC ### Completeness Scorer
# MAGIC Measures what fraction of the 14 extraction fields are non-null per document.

# COMMAND ----------

@scorer(aggregations=["mean", "min", "max"])
def completeness(outputs):
    fields = outputs.get("extracted_fields", {})
    total = len(EXTRACTION_FIELDS)
    filled = sum(1 for f in EXTRACTION_FIELDS if fields.get(f) is not None)
    ratio = filled / total if total > 0 else 0.0
    return Feedback(
        value=round(ratio, 2),
        rationale=f"{filled}/{total} fields extracted ({ratio*100:.0f}%)"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Format Validator
# MAGIC Checks whether numeric fields fall within physically reasonable ranges
# MAGIC and string fields match expected patterns.

# COMMAND ----------

@scorer
def format_validator(outputs):
    import re
    fields = outputs.get("extracted_fields", {})
    feedbacks = []

    checks = {
        "rated_voltage_v": (1, 60, "Voltage should be 1-60V"),
        "max_torque_nm": (1, 300, "Torque should be 1-300Nm"),
        "weight_kg": (0.3, 15, "Weight should be 0.3-15kg"),
        "no_load_speed_low_rpm": (50, 5000, "Low speed should be 50-5000 RPM"),
        "no_load_speed_high_rpm": (100, 10000, "High speed should be 100-10000 RPM"),
        "max_drilling_diameter_wood_mm": (5, 100, "Wood drilling should be 5-100mm"),
        "max_drilling_diameter_steel_mm": (3, 50, "Steel drilling should be 3-50mm"),
    }

    issues = []
    valid_count = 0

    for field, (lo, hi, desc) in checks.items():
        val = fields.get(field)
        if val is None:
            continue
        try:
            num = float(val)
            if lo <= num <= hi:
                valid_count += 1
            else:
                issues.append(f"{field}={num} out of range ({desc})")
        except (ValueError, TypeError):
            issues.append(f"{field}={val} is not numeric")

    chuck = fields.get("chuck_capacity_mm")
    if chuck is not None:
        if re.match(r"^\d+(\.\d+)?(-\d+(\.\d+)?)?(\s*mm)?$", str(chuck).strip()):
            valid_count += 1
        else:
            issues.append(f"chuck_capacity_mm='{chuck}' unexpected format")

    if issues:
        feedbacks.append(Feedback(
            name="format_issues",
            value=False,
            rationale=f"Issues found: {'; '.join(issues)}"
        ))
    else:
        feedbacks.append(Feedback(
            name="format_issues",
            value=True,
            rationale=f"All {valid_count} present numeric fields within expected ranges"
        ))

    return feedbacks

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Define LLM Judge Scorers
# MAGIC
# MAGIC ### English Language Compliance
# MAGIC Checks that all extracted values are in English (not German, French, etc.)

# COMMAND ----------

english_check = Guidelines(
    name="english_compliance",
    guidelines=[
        "All extracted values in the response must be in English.",
        "No German, French, Japanese, or other non-English language terms should appear in any field value.",
        "Product names, descriptions, and all text fields must use English words only.",
        "Brand names (e.g. Bosch, Makita) and model numbers (e.g. GSR 18V-65) are acceptable as-is."
    ]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Extraction Quality
# MAGIC Assesses whether extracted values look like legitimate product specifications.

# COMMAND ----------

extraction_quality = Guidelines(
    name="extraction_quality",
    guidelines=[
        "The manufacturer must be a real, well-known power tool brand name.",
        "The model_number must look like a real product identifier (alphanumeric pattern, not a sentence).",
        "The product_type must be a standard tool category such as drill, drill/driver, hammer drill, or impact driver.",
        "Numeric specifications like voltage, torque, and speed must be plausible for a cordless power tool.",
        "The response should not contain hallucinated or fabricated values that contradict common power tool specifications."
    ]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Run Evaluation

# COMMAND ----------

results = mlflow.genai.evaluate(
    data=eval_data,
    scorers=[completeness, format_validator, english_check, extraction_quality]
)

print(f"Evaluation run ID: {results.run_id}")
print(f"\nAggregate metrics:")
for metric, value in sorted(results.metrics.items()):
    print(f"  {metric}: {value}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. View Results
# MAGIC
# MAGIC Navigate to the MLflow experiment to see per-record scores, rationales,
# MAGIC and aggregate metrics. You can also view them inline below.

# COMMAND ----------

display(results.eval_table)
