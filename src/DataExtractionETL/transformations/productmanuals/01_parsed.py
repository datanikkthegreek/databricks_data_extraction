from pyspark import pipelines as dp
import pyspark.sql.functions as F

table_prefix = spark.conf.get("table")
volume = spark.conf.get("volume")

@dp.table(
    name=f"{table_prefix}_productmanuals_parsed",
    comment="Table containing parsed product manual data from PDF files, including file metadata",
)
def productmanuals_parsed():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .load(f"{volume}/productmanuals")
        .withColumn(
            "parsed",
            F.ai_parse_document(
                F.col("content"),
                {"version": "2.0", "descriptionElementTypes": "*"},
            ),
        )
        .select(
            F.col("_metadata.file_path").alias("path"),
            F.col("_metadata.file_name").alias("file_name"),
            F.col("_metadata.file_size").alias("file_size"),
            F.col("parsed"),
            F.expr("parsed:document::string").alias("document"),
        )
    )
