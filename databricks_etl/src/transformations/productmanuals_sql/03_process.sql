-- Streaming table: processed product manual fields from AI extraction (Spark Declarative Pipeline)
-- Reads from ${table_prefix}_productmanuals_extract and flattens ai_result into typed columns.

CREATE OR REFRESH STREAMING TABLE ${table_prefix}_productmanuals_processed
(
  file_name STRING COMMENT 'Original PDF file name.',
  manufacturer STRING COMMENT 'Brand or manufacturer name.',
  model_number STRING COMMENT 'Product model number or identifier.',
  product_name STRING COMMENT 'Full product name or description.',
  product_type STRING COMMENT 'Type of tool (drill, drill/driver, hammer drill, etc.).',
  rated_voltage_v DOUBLE COMMENT 'Rated voltage in volts.',
  max_torque_nm DOUBLE COMMENT 'Maximum torque in Newton-meters.',
  no_load_speed_low_rpm INT COMMENT 'No-load speed for low gear in RPM.',
  no_load_speed_high_rpm INT COMMENT 'No-load speed for high gear in RPM.',
  chuck_capacity_mm STRING COMMENT 'Chuck capacity range in mm.',
  max_drilling_diameter_wood_mm DOUBLE COMMENT 'Maximum drilling diameter in wood in mm.',
  max_drilling_diameter_steel_mm DOUBLE COMMENT 'Maximum drilling diameter in steel in mm.',
  weight_kg DOUBLE COMMENT 'Weight of the tool in kg (without battery).',
  compatible_batteries STRING COMMENT 'Compatible battery packs.',
  compatible_chargers STRING COMMENT 'Compatible chargers.'
)
COMMENT 'Processed product catalog from power tool manuals: structured specifications for cross-vendor comparison, procurement intelligence, and product recommendation.'
AS
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
FROM STREAM(${table_prefix}_productmanuals_extract)
