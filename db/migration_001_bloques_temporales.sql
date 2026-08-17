CREATE TABLE IF NOT EXISTS bloques_temporales (
    bloque_id     SERIAL PRIMARY KEY,
    repo_id       INTEGER NOT NULL REFERENCES repos(repo_id),
    bloque_num    INTEGER NOT NULL,
    fecha_inicio  TIMESTAMPTZ NOT NULL,
    fecha_fin     TIMESTAMPTZ NOT NULL,
    criterio      TEXT,
    etiqueta      TEXT,
    UNIQUE(repo_id, bloque_num),
    UNIQUE(repo_id, fecha_inicio, fecha_fin)
);

ALTER TABLE runs ADD COLUMN IF NOT EXISTS bloque_id INTEGER REFERENCES bloques_temporales(bloque_id);

CREATE INDEX IF NOT EXISTS idx_runs_bloque ON runs(bloque_id);
CREATE INDEX IF NOT EXISTS idx_bloques_repo ON bloques_temporales(repo_id);
