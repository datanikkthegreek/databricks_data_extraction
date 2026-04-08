from pyspark import pipelines as dp
from pyspark.sql import SparkSession


def _register() -> None:
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("SparkSession required for pipeline dataset definitions")
    table_prefix = spark.conf.get("pipelines.table", "app")

    @dp.table(
        name=f"{table_prefix}_productmanuals_parsed",
        comment="Table containing parsed product manual data from PDF files, including file metadata",
    )
    def productmanuals_parsed():
        vol = spark.conf.get("pipelines.volume")
        return spark.sql(
            f"""
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
    STREAM READ_FILES('{vol}/productmanuals', format => 'binaryFile')
"""
        )


_register()
