import os
from pathlib import Path

import pandas as pd
import psycopg2

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_USER = os.environ.get("POSTGRES_USER", "metricas")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "metricas")
DB_NAME = os.environ.get("POSTGRES_DB", "resultados_metricas")

REPOS_SEED_PATH = Path(__file__).parent / "repos_seed.xlsx"

REPOS_COLUMNS = ["org", "repo", "full_name", "url", "plataforma"]


def _conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME
    )


def _cargar_repos_desde_excel() -> list[tuple]:
    df = pd.read_excel(REPOS_SEED_PATH, sheet_name="repos")

    faltantes = [c for c in REPOS_COLUMNS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en {REPOS_SEED_PATH.name}: {faltantes}")

    df = df[REPOS_COLUMNS].where(pd.notnull(df[REPOS_COLUMNS]), None)
    return list(df.itertuples(index=False, name=None))


def main():
    filas = _cargar_repos_desde_excel()

    con = _conn()
    cur = con.cursor()

    set_clause = ", ".join(f"{c}=EXCLUDED.{c}" for c in REPOS_COLUMNS if c != "full_name")
    cols_sql = ", ".join(REPOS_COLUMNS)
    placeholders = ", ".join(["%s"] * len(REPOS_COLUMNS))
    query = (
        f"INSERT INTO repos ({cols_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT (full_name) DO UPDATE SET {set_clause}"
    )
    cur.executemany(query, filas)
    con.commit()

    def _count(tabla):
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        return cur.fetchone()[0]

    print(f"Conectado a postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"  repos:             {_count('repos')}  (sincronizados desde {REPOS_SEED_PATH.name})")
    print(f"  runs:              {_count('runs')}")
    print(f"  results_producto:  {_count('results_producto')}")
    print(f"  results_persona:   {_count('results_persona')}")

    cur.close()
    con.close()


if __name__ == "__main__":
    main()