-- Seed de métricas: catálogo + mapeo ISL
-- Ejecutar luego de schema.sql y repos_seed.sql

-- ---------------------------------------------------------------------------
-- metric_catalog
-- ---------------------------------------------------------------------------
INSERT INTO metric_catalog (metric_key, metric_name, dim_producto, dim_proceso, dim_persona)
VALUES (
    'anmcc',
    'Average Number of Modified Components per Commit',
    TRUE,
    TRUE,
    FALSE
)
ON CONFLICT (metric_key) DO UPDATE SET
    metric_name  = EXCLUDED.metric_name,
    dim_producto = EXCLUDED.dim_producto,
    dim_proceso  = EXCLUDED.dim_proceso,
    dim_persona  = EXCLUDED.dim_persona;

INSERT INTO metric_catalog (metric_key, metric_name, dim_producto, dim_proceso, dim_persona)
VALUES (
    'mttr',
    'Mean Time to Repair',
    TRUE,
    TRUE,
    FALSE
)
ON CONFLICT (metric_key) DO UPDATE SET
    metric_name  = EXCLUDED.metric_name,
    dim_producto = EXCLUDED.dim_producto,
    dim_proceso  = EXCLUDED.dim_proceso,
    dim_persona  = EXCLUDED.dim_persona;

-- ---------------------------------------------------------------------------
-- metric_isl_map
-- ---------------------------------------------------------------------------
INSERT INTO metric_isl_map (metric_key, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'anmcc',
    '10',
    '52',
    'La utilización eficiente de recursos',
    'CPU Usage'
)
ON CONFLICT DO NOTHING;

INSERT INTO metric_isl_map (metric_key, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'mttr',
    '10',
    '52',
    'La utilización eficiente de recursos',
    'CPU Usage'
)
ON CONFLICT DO NOTHING;