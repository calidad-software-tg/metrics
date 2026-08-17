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
CREATE TABLE IF NOT EXISTS metric_catalog (
    metric_key    TEXT PRIMARY KEY,
    metric_name   TEXT NOT NULL,
    dim_producto  BOOLEAN DEFAULT FALSE,
    dim_proceso   BOOLEAN DEFAULT FALSE,
    dim_persona  BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metric_isl_map (
    map_id                SERIAL PRIMARY KEY,
    metric_key            TEXT REFERENCES metric_catalog(metric_key),
    id_registro            TEXT,
    id_consigna             TEXT,
    texto_consigna          TEXT,
    metrica_original_isl    TEXT
);
-- ---------------------------------------------------------------------------
-- Partición del historial de un repo en bloques temporales, para correr
-- las métricas bloque por bloque y analizar evolución en el tiempo.
CREATE TABLE IF NOT EXISTS bloques_temporales (
    bloque_id     SERIAL PRIMARY KEY,
    repo_id       INTEGER NOT NULL REFERENCES repos(repo_id),
    bloque_num    INTEGER NOT NULL,        -- orden dentro del repo: 1, 2, 3...
    fecha_inicio  TIMESTAMPTZ NOT NULL,
    fecha_fin     TIMESTAMPTZ NOT NULL,
    criterio      TEXT,                    -- 'trimestral' | 'semestral' | 'por release' | 'N commits' | ...
    etiqueta      TEXT,                    -- humano-legible, ej. '2023-Q1'
    UNIQUE(repo_id, bloque_num),
    UNIQUE(repo_id, fecha_inicio, fecha_fin)
);

-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS runs (
    run_id        SERIAL PRIMARY KEY,
    repo_id       INTEGER NOT NULL REFERENCES repos(repo_id),
    bloque_id     INTEGER REFERENCES bloques_temporales(bloque_id),  -- NULL si es una corrida "snapshot" sin partición
    fecha_inicio  TIMESTAMPTZ,   -- inicio de la ventana medida
    fecha_fin     TIMESTAMPTZ,   -- fin de la ventana medida
    ejecutado_en  TIMESTAMPTZ,   -- cuándo se corrió de verdad
    notas         TEXT
);


-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS results_producto (
    result_id    SERIAL PRIMARY KEY,
    run_id       INTEGER NOT NULL REFERENCES runs(run_id),
    metric_key   TEXT NOT NULL REFERENCES metric_catalog(metric_key),
    value        DOUBLE PRECISION,
    value_extra  JSONB,      -- opcional, para salidas compuestas (ej. desglose README Completeness)
    UNIQUE(run_id, metric_key)
);


-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS results_persona (
    result_id           SERIAL PRIMARY KEY,
    run_id              INTEGER NOT NULL REFERENCES runs(run_id),
    metric_key          TEXT NOT NULL REFERENCES metric_catalog(metric_key),
    contributor_login   TEXT NOT NULL,
    value               DOUBLE PRECISION,
    value_extra         JSONB,
    UNIQUE(run_id, metric_key, contributor_login)
);

CREATE INDEX IF NOT EXISTS idx_results_producto_run ON results_producto(run_id);
CREATE INDEX IF NOT EXISTS idx_results_persona_run ON results_persona(run_id);
CREATE INDEX IF NOT EXISTS idx_isl_map_metric ON metric_isl_map(metric_key);
CREATE INDEX IF NOT EXISTS idx_runs_bloque ON runs(bloque_id);
CREATE INDEX IF NOT EXISTS idx_bloques_repo ON bloques_temporales(repo_id);
