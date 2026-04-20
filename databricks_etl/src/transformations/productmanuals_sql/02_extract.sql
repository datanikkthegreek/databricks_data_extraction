-- Streaming table: AI extraction from parsed product manual documents (Spark declarative pipeline)
-- Extracts structured product specifications from power tool manuals for building a unified product catalog.

SET prompt = 'Extract product specifications from this power tool manual. Focus only on the English language sections. All extracted values (including product_name) must be in English. Look for technical data in specification tables, feature lists, and product descriptions throughout the entire document. If a specification is mentioned anywhere in the document (not just in tables), extract it. If multiple models are listed, extract the primary model.';


CREATE OR REFRESH STREAMING TABLE ${table_prefix}_productmanuals_extract
COMMENT 'Extracted product specifications (manufacturer, model, voltage, torque, etc.) via AI from parsed product manual PDFs'
AS
SELECT
    path,
    file_name,
    file_size,
    ai_extract(
        parsed,
        schema => '{
      "manufacturer": {"type": "string", "description": "Brand or manufacturer name, e.g. Bosch, Makita, BLACK+DECKER"},
      "model_number": {"type": "string", "description": "Product model number or identifier, e.g. GSR 18V-65, BCD382, DF033D"},
      "product_name": {"type": "string", "description": "Full product name or description, e.g. Cordless Drill/Driver, 20V MAX Cordless Drill"},
      "product_type": {"type": "string", "description": "Type of tool: drill, drill/driver, hammer drill, impact driver, etc."},
      "rated_voltage_v": {"type": "number", "description": "Rated or nominal voltage in volts"},
      "max_torque_nm": {"type": "number", "description": "Maximum torque in Newton-meters (Nm). Use the hard screwdriving value if both hard and soft are given. May appear as max torque, tightening torque, or fastening torque."},
      "no_load_speed_low_rpm": {"type": "number", "description": "No-load speed for gear 1 or low speed setting in RPM. Use the max value if a range is given. May appear as speed setting 1 or low gear."},
      "no_load_speed_high_rpm": {"type": "number", "description": "No-load speed for gear 2 or high speed setting in RPM. Use the max value if a range is given. May appear as speed setting 2 or high gear."},
      "chuck_capacity_mm": {"type": "string", "description": "Chuck capacity range in mm, e.g. 1.5-13 or 10. Look for chuck size, collet capacity, or clamping range."},
      "max_drilling_diameter_wood_mm": {"type": "number", "description": "Maximum drilling diameter in wood in mm. May appear as drilling capacity in wood or max bore diameter wood."},
      "max_drilling_diameter_steel_mm": {"type": "number", "description": "Maximum drilling diameter in steel in mm. May appear as drilling capacity in steel or max bore diameter steel."},
      "weight_kg": {"type": "number", "description": "Weight of the tool in kg without battery. If given in lbs, convert to kg (1 lb = 0.4536 kg). Use minimum value if a range is given."},
      "compatible_batteries": {"type": "string", "description": "List of compatible battery packs or battery model numbers, comma-separated. Look in accessories, battery, or recommended sections."},
      "compatible_chargers": {"type": "string", "description": "List of compatible chargers or charger model numbers, comma-separated. Look in accessories, charger, or recommended sections."}
    }',
        options => map(
          'version', '2.0',
          'instructions', '${prompt}'
        )
    ) AS ai_result
FROM STREAM(${table_prefix}_productmanuals_parsed);
