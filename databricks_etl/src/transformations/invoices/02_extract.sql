-- Streaming table: AI extraction from parsed invoice documents (Spark declarative pipeline)

-- Could be used for simpler use-cases like in this case instead of complex_schema
-- '["invoice_date", "invoice_sum", "seller"]';

SET prompt = 'I want to analyze private invoices';


CREATE OR REFRESH STREAMING TABLE ${table_prefix}_invoices_extract
COMMENT 'Extracted invoice fields (invoice_date, invoice_sum, seller) via AI from parsed PDFs'
AS
SELECT
    path,
    file_name,
    file_size,
    ai_extract(
        parsed,
        schema => '{
      "invoice_date": {"type": "string", "description": "Date of invoice in form YYYY-MM-DD"},
      "invoice_sum": {"type": "number", "description": "The total value to pay"},
      "seller": {"type": "string", "description": "Who was selling sth and created the invoice"}
    }',
        options => map(
          'version', '2.0',
          'instructions', '${prompt}'
        )
    ) AS ai_result
FROM STREAM(${table_prefix}_invoices_parsed);


-- =============================================================================
-- ALTERNATIVE APPROACH: ai_query (LLM prompt-based extraction)
-- Use when you need full control over the prompt and response format.
-- Requires parsing the JSON response manually in the next step (03_ai_query_process.sql).
-- =============================================================================

-- SET prompt = 'Extract ONLY the following three fields from this invoice and return them as a JSON object with no additional text or explanation:
--
-- 1. invoice_date: The date of the invoice (format: YYYY-MM-DD)
-- 2. invoice_sum: The total amount to be paid (numeric value only, no currency symbol)
-- 3. seller: The name of the company issuing the invoice
--
-- Return ONLY valid JSON in this exact format:
-- {
--   "invoice_date": "YYYY-MM-DD",
--   "invoice_sum": 100,
--   "seller": "Company Name"
-- }
--
-- Do not include any markdown, explanations, tables, or additional information.';
--
-- CREATE OR REFRESH STREAMING TABLE ${table_prefix}_invoices_ai_query_extract
-- COMMENT 'Extracted invoice fields (invoice_date, invoice_sum, seller) via AI from parsed PDFs'
-- AS
-- SELECT
--     path,
--     file_name,
--     file_size,
--     ai_query(
--         endpoint => 'databricks-gpt-oss-120b',
--         request => CONCAT('${prompt}', '\n\n', document),
--         responseFormat => 'STRUCT<result: STRUCT<invoice_date: STRING, invoice_sum: DOUBLE, seller: STRING>>'
--     ) AS ai_result
-- FROM STREAM(${table_prefix}_invoices_parsed);
