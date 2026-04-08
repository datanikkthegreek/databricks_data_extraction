from pyspark import pipelines as dp
from pyspark.sql import SparkSession


def _register() -> None:
    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("SparkSession required for pipeline dataset definitions")
    prefix = spark.conf.get("pipelines.table", "app")

    @dp.table(
        name=f"{prefix}_productmanuals_processed",
        comment="Processed product catalog from power tool manuals: structured specifications for cross-vendor comparison, procurement intelligence, and product recommendation.",
    )
    def productmanuals_processed():
        return spark.sql(
            f"""
SELECT
    file_name,
    ai_result:response.manufacturer::STRING AS manufacturer,
    ai_result:response.model_number::STRING AS model_number,
    ai_result:response.product_name::STRING AS product_name,
    ai_result:response.product_type::STRING AS product_type,
    ai_result:response.rated_voltage_v::DOUBLE AS rated_voltage_v,
    ai_result:response.max_torque_nm::DOUBLE AS max_torque_nm,
    ai_result:response.no_load_speed_low_rpm::INT AS no_load_speed_low_rpm,
    ai_result:response.no_load_speed_high_rpm::INT AS no_load_speed_high_rpm,
    ai_result:response.chuck_capacity_mm::STRING AS chuck_capacity_mm,
    ai_result:response.max_drilling_diameter_wood_mm::DOUBLE AS max_drilling_diameter_wood_mm,
    ai_result:response.max_drilling_diameter_steel_mm::DOUBLE AS max_drilling_diameter_steel_mm,
    ai_result:response.weight_kg::DOUBLE AS weight_kg,
    ai_result:response.compatible_batteries::STRING AS compatible_batteries,
    ai_result:response.compatible_chargers::STRING AS compatible_chargers
FROM STREAM({prefix}_productmanuals_extract)
"""
        )


_register()
