-- ============================================================================
-- migration_002: columna `variante` en periodo
--
-- Problema que resuelve: los UNIQUE actuales son
--     (repo_id, tipo_analisis, periodo_num)
--     (repo_id, tipo_analisis, fecha_inicio, fecha_fin)
-- Con eso, para un mismo repo solo entra UNA partición por tipo_analisis. Pero
-- el diseño del trabajo necesita varias del mismo tipo conviviendo:
--   - volumen con N=300, N=500 y N=1000 (chequeos de robustez)
--   - bloque_fijo mensual, trimestral y semestral
-- Sin esta columna, cargar la segunda pisa o rechaza la primera.
--
-- Aplicar con:
--   docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas \
--     < migration_002_variante.sql
-- ============================================================================

BEGIN;

ALTER TABLE periodo
    ADD COLUMN IF NOT EXISTS variante TEXT NOT NULL DEFAULT '';

COMMENT ON COLUMN periodo.variante IS
    'Distingue particiones del mismo tipo_analisis: n500_desde2016, trimestral, piso15x3...';

ALTER TABLE periodo DROP CONSTRAINT IF EXISTS periodo_repo_id_tipo_analisis_periodo_num_key;
ALTER TABLE periodo DROP CONSTRAINT IF EXISTS periodo_repo_id_tipo_analisis_fecha_inicio_fecha_fin_key;
ALTER TABLE periodo DROP CONSTRAINT IF EXISTS periodo_uniq_num;
ALTER TABLE periodo DROP CONSTRAINT IF EXISTS periodo_uniq_fechas;

ALTER TABLE periodo ADD CONSTRAINT periodo_uniq_num
    UNIQUE (repo_id, tipo_analisis, variante, periodo_num);

ALTER TABLE periodo ADD CONSTRAINT periodo_uniq_fechas
    UNIQUE (repo_id, tipo_analisis, variante, fecha_inicio, fecha_fin);

-- Duración: se usa en casi todo el análisis del criterio por volumen, donde el
-- tiempo que tardó el proyecto en producir N eventos es el inverso del throughput.
-- Se expone como columna generada para no recalcularla en cada consulta.
ALTER TABLE periodo
    ADD COLUMN IF NOT EXISTS duracion_dias DOUBLE PRECISION
    GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (fecha_fin - fecha_inicio)) / 86400) STORED;

CREATE INDEX IF NOT EXISTS idx_periodo_variante
    ON periodo (repo_id, tipo_analisis, variante);

-- La vista tiene que reflejar las columnas nuevas.
DROP VIEW IF EXISTS panel;
CREATE VIEW panel AS
SELECT
    r.full_name    AS repo,
    per.tipo_analisis,
    per.variante,
    per.es_principal,
    per.periodo_id, per.periodo_num, per.fecha_inicio, per.fecha_fin,
    per.duracion_dias, per.etiqueta,
    per.n_issues_cerradas, per.n_colaboradores,
    per.parametros,
    m.metrica_id, m.nombre AS metrica_nombre,
    m.dim_persona, m.dim_proceso, m.dim_producto,
    res.contribuyente_login,
    res.value
FROM resultado res
JOIN periodo per ON per.periodo_id = res.periodo_id
JOIN repos r     ON r.repo_id = per.repo_id
JOIN metrica m   ON m.metrica_id = res.metrica_id;

COMMIT;