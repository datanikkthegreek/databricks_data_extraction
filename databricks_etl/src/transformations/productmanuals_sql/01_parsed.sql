-- Streaming table: Parsed product manuals (Spark declarative pipeline)
CREATE OR REPLACE STREAMING TABLE ${table}_productmanuals_parsed
COMMENT 'Table containing parsed product manual data from PDF files, including file metadata'
AS
SELECT
    _metadata.file_path AS path,
    _metadata.file_name AS file_name,
    _metadata.file_size AS file_size,
    ai_parse_document(content, map(
        'version', '2.0',
        'descriptionElementTypes', '*'
      )) AS parsed,
    parsed:document::string AS document
FROM
    STREAM READ_FILES('${volume}/productmanuals', format => 'binaryFile');
