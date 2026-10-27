"""Validación de los pares de grupos del clustering de métricas en los cruces con Persona.

Con los grupos de cruce_clustering.py aparecen patrones que con el PCA no salen entre componentes. Algunos grupos
incluyen una métrica que comparte eventos con el otro lado (SC cuenta issues propias cerradas, como NCI y Jarczyk;
la proporción que cierra issues sube cuando se cierran más issues nuevas; Contribution Diversity y los commits que
tocan documentación salen de los mismos commits). Este script arma la serie de cada grupo como cruce_clustering.py
(promedio de los rangos ajustados, orientado a la métrica central o a la indicada) con y sin esas métricas, y la
cruza con los grupos del otro lado con evaluar_par de cruce_dimensiones.py. Si la relación se mantiene sin la
métrica sospechosa, el hallazgo se sostiene.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/grupos_persona_sin_superposicion.py

Escribe analisis/salidas/validaciones/grupos_persona_sin_superposicion/resultados.csv. Solo lee la base.
"""
import csv
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "analisis"))
import cruce_clustering as cc  # noqa: E402
import cruce_dimensiones as cd  # noqa: E402
import generar_pca as gp  # noqa: E402

warnings.filterwarnings("ignore")
SALIDA = ROOT / "analisis" / "salidas" / "validaciones" / "grupos_persona_sin_superposicion"

PERSONA = {
    "concentración": ["exprev_share_top10pct", "nc_share_top10pct", "prop_commitean_ratio", "sc_mediana", "sc_p90"],
    "concentración sin SC mediana": ["exprev_share_top10pct", "nc_share_top10pct", "prop_commitean_ratio", "sc_p90"],
    "concentración sin SC": ["exprev_share_top10pct", "nc_share_top10pct", "prop_commitean_ratio"],
    "núcleo de revisión": ["exprev_p90", "nc_p90", "prop_cierran_ratio", "rexprev_mediana"],
    "núcleo sin proporción que cierra": ["exprev_p90", "nc_p90", "rexprev_mediana"],
    "veteranía": ["activos_commits_conteo", "cdiv_mediana", "dev_exp_mediana", "le_mediana", "nuevos_commits_conteo",
                  "rexp_mediana", "tasa_nuevos_commits_ratio"],
    "veteranía sin CDIV": ["activos_commits_conteo", "dev_exp_mediana", "le_mediana", "nuevos_commits_conteo",
                           "rexp_mediana", "tasa_nuevos_commits_ratio"],
    "solo experiencia (LE, Dev. Experience, REXP)": ["dev_exp_mediana", "le_mediana", "rexp_mediana"],
    "solo renovación (commiters nuevos, tasa de ingreso, activos)": ["activos_commits_conteo", "nuevos_commits_conteo",
                                                                    "tasa_nuevos_commits_ratio"],
}
# orientación: los grupos de veteranía se orientan a LE (más alto = equipo más veterano); renovación, a commiters nuevos
ORIENTAR = {"veteranía": "le_mediana", "veteranía sin CDIV": "le_mediana",
            "solo experiencia (LE, Dev. Experience, REXP)": "le_mediana",
            "solo renovación (commiters nuevos, tasa de ingreso, activos)": "nuevos_commits_conteo"}
OTRO_LADO = {
    "Proceso · resolución de lo nuevo": (["jarczyk_success_rate_producto", "process_performance_producto"], "jarczyk_success_rate_producto"),
    "Proceso · limpieza de lo viejo": (["mttr_producto", "nci_producto"], "mttr_producto"),
    "Proceso/Producto · bugs de usuarios": (["cfdr_producto", "nub_producto"], "cfdr_producto"),
    "Producto · flujo de documentación": (["commits_doc_producto", "dloc_flujo_producto"], "commits_doc_producto"),
}


def main():
    var_dict, datos = gp.cargar_datos()
    size_e = datos["activos_interaccion_conteo"]["versiones"]
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v, d in datos.items():
        if v.startswith("__"):
            continue
        for s in duraciones:
            for p, t in d.get(s, {}).items():
                if t[0] is not None:
                    duraciones[s].setdefault(p, t[0])

    def serie(variables, central=None):
        out = {}
        for nombre, db in (("estable", "versiones"), ("canary", "versiones_canary")):
            Z, pnums, filas = cc.matriz(variables, datos, nombre, "ajustado")
            R = np.corrcoef(Z, rowvar=False)
            c = variables.index(central) if central else int(np.argmax(np.abs(R).mean(axis=0)))
            signo = np.sign(R[c])
            signo[signo == 0] = 1.0
            out[nombre] = cc.a_serie((Z * signo).mean(axis=1), pnums, filas, duraciones, db)
        return out

    otros = {k: serie(vs, c) for k, (vs, c) in OTRO_LADO.items()}
    filas = []
    for g, vs in PERSONA.items():
        s = serie(vs, ORIENTAR.get(g))
        for k, o in otros.items():
            r = cd.evaluar_par(s["estable"], o["estable"], s["canary"], o["canary"], size_e, True)
            filas.append(dict(grupo_persona=g, grupo_otro=k, rho=round(r["rho_corregida"], 3), p=round(r["p_corregida"], 4),
                              rho_tamano=round(r["rho_corregida_tamano"], 3), rho_canary=round(r["rho_canary"], 3),
                              estable=r["estable"]))
            print(f"{g:60s} ↔ {k:36s} ρ {r['rho_corregida']:+.2f}  p {r['p_corregida']:.4f}  "
                  f"tamaño {r['rho_corregida_tamano']:+.2f}  canary {r['rho_canary']:+.2f}", flush=True)
    SALIDA.mkdir(parents=True, exist_ok=True)
    with open(SALIDA / "resultados.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print("salida:", SALIDA / "resultados.csv")


if __name__ == "__main__":
    main()
