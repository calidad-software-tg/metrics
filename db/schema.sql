-- =============================================================================
-- Esquema: repos, metrica, periodo, resultado
-- =============================================================================

-- ---------------------------------------------------------------------------
-- repos: catálogo de repositorios del estudio (dato de referencia)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS repos (
    repo_id    SERIAL PRIMARY KEY,
    org        TEXT NOT NULL,
    repo       TEXT NOT NULL,
    full_name  TEXT NOT NULL UNIQUE,
    url        TEXT,
    plataforma TEXT DEFAULT 'GitHub'
);

-- ---------------------------------------------------------------------------
-- metrica: catálogo de métricas y su relación con las tres Ps
-- (una métrica puede pertenecer a más de una dimensión a la vez)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrica (
    metrica_id            TEXT PRIMARY KEY,   -- clave corta usada por el código: 'anmcc', 'mttr', 'readme_completeness', ...
    nombre                TEXT NOT NULL,
    dim_persona           BOOLEAN NOT NULL DEFAULT FALSE,
    dim_proceso           BOOLEAN NOT NULL DEFAULT FALSE,
    dim_producto          BOOLEAN NOT NULL DEFAULT FALSE,
    calculable            BOOLEAN,            -- NULL = todavía sin decidir si es calculable con los datos disponibles
    id_registro           TEXT,               -- id(s) del relevamiento ISL; puede traer varios separados por coma
    id_consigna           TEXT,
    texto_consigna        TEXT,
    metrica_original_isl  TEXT
    -- nota: no hay CHECK de "al menos una P" a propósito -- Metricas.xlsx trae
    -- varias filas todavía sin clasificar (dim_persona/proceso/producto en FALSE
    -- los tres), que se completan más adelante en vez de bloquear el insert.
);

-- ---------------------------------------------------------------------------
-- periodo: una ventana de tiempo concreta de UN repo, cortada con UN criterio
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS periodo (
    periodo_id         SERIAL PRIMARY KEY,
    repo_id            INTEGER NOT NULL REFERENCES repos(repo_id),
    tipo_analisis      TEXT NOT NULL CHECK (tipo_analisis IN (
                            'bloque_fijo',   -- calendario, ancho parejo
                            'adaptativo',    -- calendario, ancho fusionado hasta un piso mínimo de actividad
                            'versiones',     -- un período entre cada release/tag consecutivo
                            'volumen'        -- un período cada N eventos acumulados (commits o issues cerradas)
                        )),
    periodo_num        INTEGER NOT NULL,     -- orden dentro de (repo_id, tipo_analisis): 1, 2, 3...
    fecha_inicio       TIMESTAMPTZ NOT NULL,
    fecha_fin          TIMESTAMPTZ NOT NULL,
    etiqueta           TEXT,                 -- humano-legible, ej. '2023-Q1', 'v2.1'
    parametros         JSONB NOT NULL DEFAULT '{}',  -- cómo se generó, ej: {"meses":3} | {"piso_issues":15,"piso_colabs":3} | {} | {"n_por_bloque":50,"evento":"issues_cerradas"}
    n_issues_cerradas  INTEGER,              -- opcional: para auditar el piso mínimo después
    n_colaboradores    INTEGER,
    es_principal       BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE = el criterio que usás en el análisis central
    CHECK (fecha_inicio < fecha_fin),
    UNIQUE (repo_id, tipo_analisis, periodo_num),
    UNIQUE (repo_id, tipo_analisis, fecha_inicio, fecha_fin)
);

-- ---------------------------------------------------------------------------
-- resultado: el valor de UNA métrica en UN período (y, si es de Persona, de
-- UN colaborador dentro de ese período)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resultado (
    resultado_id         SERIAL PRIMARY KEY,
    periodo_id           INTEGER NOT NULL REFERENCES periodo(periodo_id),
    metrica_id           TEXT NOT NULL REFERENCES metrica(metrica_id),
    contribuyente_login  TEXT,          -- NULL para métricas de Proceso/Producto; login para métricas de Persona
    value                DOUBLE PRECISION,
    value_extra          JSONB,         -- opcional, para salidas compuestas (ej. desglose de README Completeness)
    calculado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unicidad correcta: en Postgres dos NULL nunca son "iguales" para un UNIQUE
-- normal, así que sin esto un resultado de Proceso/Producto (contribuyente_login
-- NULL) se podría duplicar al recalcularlo. Se separa en dos índices parciales:
CREATE UNIQUE INDEX IF NOT EXISTS resultado_uniq_sin_contribuyente
    ON resultado (periodo_id, metrica_id)
    WHERE contribuyente_login IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS resultado_uniq_con_contribuyente
    ON resultado (periodo_id, metrica_id, contribuyente_login)
    WHERE contribuyente_login IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_resultado_periodo ON resultado(periodo_id);
CREATE INDEX IF NOT EXISTS idx_resultado_metrica ON resultado(metrica_id);
CREATE INDEX IF NOT EXISTS idx_periodo_repo      ON periodo(repo_id);

-- ---------------------------------------------------------------------------
-- panel: vista lista para exportar a pandas/R, ya con el join armado
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW panel AS
SELECT
    r.full_name    AS repo,
    per.tipo_analisis,
    per.es_principal,
    per.periodo_id, per.periodo_num, per.fecha_inicio, per.fecha_fin, per.etiqueta,
    per.n_issues_cerradas, per.n_colaboradores,
    m.metrica_id, m.nombre AS metrica_nombre,
    m.dim_persona, m.dim_proceso, m.dim_producto,
    res.contribuyente_login,
    res.value
FROM resultado res
JOIN periodo per ON per.periodo_id = res.periodo_id
JOIN repos r     ON r.repo_id = per.repo_id
JOIN metrica m   ON m.metrica_id = res.metrica_id;
