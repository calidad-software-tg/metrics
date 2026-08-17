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
    metric_key       TEXT PRIMARY KEY,
    metric_name      TEXT NOT NULL,
    dimension        TEXT,
    unidad_analisis  TEXT,
    calculable       TEXT,
    fuente           TEXT,
    notas            TEXT
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
CREATE TABLE IF NOT EXISTS runs (
    run_id        SERIAL PRIMARY KEY,
    repo_id       INTEGER NOT NULL REFERENCES repos(repo_id),
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
