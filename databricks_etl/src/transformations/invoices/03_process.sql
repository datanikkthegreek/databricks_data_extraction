-- Streaming table: processed invoice fields from AI extraction (Spark Declarative Pipeline)
-- Reads from ${table_prefix}_invoices_extract and flattens ai_result with typed columns and comments.

CREATE OR REFRESH STREAMING TABLE ${table_prefix}_invoices_processed
(
  file_name STRING COMMENT 'Original PDF file name.',
  invoice_date DATE COMMENT 'Date of the invoice (YYYY-MM-DD).',
  invoice_sum DOUBLE COMMENT 'Total amount to be paid (numeric, no currency symbol).',
  seller STRING COMMENT 'Name of the company that issued the invoice.'
)
COMMENT 'Processed invoice data from PDFs: file name, invoice date, total amount, and seller. Use for financial analysis, tracking invoice payments, and monitoring expenses by seller.'
AS
SELECT
    file_name,
    ai_result:response.invoice_date::DATE AS invoice_date,
    ai_result:response.invoice_sum::DOUBLE AS invoice_sum,
    ai_result:response.seller::STRING AS seller
FROM STREAM(${table_prefix}_invoices_extract)