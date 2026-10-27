"""Estabilidad de las relaciones dentro de cada dimensión con las épocas de todas las métricas en lugar del calendario.

La regla de estabilidad de generar_correlaciones.py pide el mismo signo en los cuatro períodos de calendario
(ETAPAS: 2016–2019, 2020–2022, 2023–2024, 2025–2026). Este script corre generar_correlaciones.py sin modificarlo
con las cuatro épocas que encuentra epocas_todas.py (todas las métricas, toda la historia, peso por dimensión),
cortadas en v9.1.7, v12.0.5 y v14.1.1, y compara los pares Persona–Persona, Proceso–Proceso y Producto–Producto
con los del calendario.

La época se asigna por número de release (periodo_num, que es el mismo en todas las series) y no por fecha: la
fecha de las series de producto es el inicio de la ventana y la de Persona es la del release, así que con un
corte por fecha el release del corte caería en épocas distintas según la variable.

Las columnas del CSV conservan los nombres de los períodos, pero en el modo epocas contienen las épocas:
rho_2016_2019 = E1 (hasta v9.1.6, ene 2020), rho_2020_2022 = E2 (hasta v12.0.4, dic 2021),
rho_2023_2024 = E3 (hasta v14.1.0, feb 2024), rho_2025_2026 = E4 (desde v14.1.1, mar 2024).

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/estabilidad_epocas.py calendario
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/estabilidad_epocas.py epocas
    python3 analisis/validaciones/estabilidad_epocas.py comparar

Los dos primeros escriben pares_correlacion.csv en analisis/salidas/validaciones/estabilidad_epocas/<modo>/
(no pisan la salida de generar_correlaciones.py); comparar escribe comparacion.csv y resumen.md en la carpeta base.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "analisis"))
BASE = ROOT / "analisis" / "salidas" / "validaciones" / "estabilidad_epocas"
CORTES = ["v9.1.7", "v12.0.5", "v14.1.1"]
INTRA = ["Persona–Persona", "Proceso–Proceso", "Producto–Producto"]
PERIODOS = ["2016_2019", "2020_2022", "2023_2024", "2025_2026"]
NOMBRES = {"calendario": ["2016–19", "2020–22", "2023–24", "2025–26"],
           "epocas": ["E1 ≤ ene 2020", "E2 ≤ dic 2021", "E3 ≤ feb 2024", "E4 ≥ mar 2024"]}


def correr(modo):
    import generar_correlaciones as gc
    salida = BASE / modo
    salida.mkdir(parents=True, exist_ok=True)
    for nombre in ("OUT_PARES", "OUT_VALS", "OUT_VALS_P", "OUT_VALS_R", "OUT_MD", "OUT_REV"):
        setattr(gc, nombre, salida / getattr(gc, nombre).name)
    if modo == "epocas":
        gc.ETAPAS = [(n, i + 1, i + 1) for i, (n, *_) in enumerate(gc.ETAPAS)]
        corte_pnum = {}
        _load = gc.excluir_backports

        def excluir_y_cortar(all_data):
            """Después de sacar los backports, busca el periodo_num de cada release de corte."""
            res = _load(all_data)
            for d in all_data.values():
                for pnum, t in d.get("versiones", {}).items():
                    if t[3] in CORTES:
                        assert corte_pnum.setdefault(t[3], pnum) == pnum, f"{t[3]} con dos periodo_num"
            assert set(corte_pnum) == set(CORTES), f"faltan cortes: {set(CORTES) - set(corte_pnum)}"
            print("  cortes:", ", ".join(f"{v} (release {p})" for v, p in corte_pnum.items()), flush=True)
            return res

        def con_epoca(serie):
            cs = sorted(corte_pnum.values())
            return {p: (t[0], t[1], 1 + sum(p >= c for c in cs), t[3], t[4]) for p, t in serie.items()}

        gc.excluir_backports = excluir_y_cortar
        _compute_pair = gc.compute_pair
        gc.compute_pair = lambda x_e, y_e, x_c, y_c, *a, **k: _compute_pair(con_epoca(x_e), con_epoca(y_e), x_c, y_c, *a, **k)
    gc.main()


def leer(modo):
    with open(BASE / modo / "pares_correlacion.csv", newline="", encoding="utf-8") as f:
        return {(r["cruce"], r["par_id"]): r for r in csv.DictReader(f) if r["cruce"] in INTRA}


def es(v):
    return v == "True"


def comparar():
    cal, epo = leer("calendario"), leer("epocas")
    filas, lineas = [], []
    lineas += ["# Estabilidad dentro de cada dimensión: calendario frente a épocas", "",
               "Épocas de `epocas_todas.py` (todas las métricas, toda la historia, peso por dimensión), cortes en "
               + ", ".join(CORTES) + ". Patrón = `hallazgo_candidato` de generar_correlaciones.py.", "",
               "| Cruce | Pares | Estables cal. | Estables ép. | Robustos cal. | Robustos ép. | Patrones cal. | Patrones ép. | En los dos | Solo cal. | Solo ép. |",
               "|---|---|---|---|---|---|---|---|---|---|---|"]
    for cruce in INTRA:
        ids = [p for p in cal if p[0] == cruce]
        c = Counter()
        for p in ids:
            a, b = cal[p], epo[p]
            pa, pb = es(a["hallazgo_candidato"]), es(b["hallazgo_candidato"])
            c["estable_c"] += es(a["estable"]); c["estable_e"] += es(b["estable"])
            c["rob_c"] += es(a["robusta"]); c["rob_e"] += es(b["robusta"])
            c["pat_c"] += pa; c["pat_e"] += pb; c["ambos"] += pa and pb
            c["solo_c"] += pa and not pb; c["solo_e"] += pb and not pa
            if pa or pb:
                filas.append(dict(cruce=cruce, par_id=p[1], x=a["x_nombre"], y=a["y_nombre"],
                                  patron=("los dos" if pa and pb else "solo calendario" if pa else "solo épocas"),
                                  rho_corregida=a["rho_corregida"], rho_canary=a["rho_canary"],
                                  rho_tamano=a["rho_corregida_tamano"],
                                  **{f"cal_{n}": a[f"rho_{q}"] for n, q in zip(NOMBRES["calendario"], PERIODOS)},
                                  **{f"ep_{n}": b[f"rho_{q}"] for n, q in zip(NOMBRES["epocas"], PERIODOS)},
                                  evaluables_cal=a["n_periodos_evaluables"], evaluables_ep=b["n_periodos_evaluables"],
                                  nivel_cal=a["nivel_evidencia"], nivel_ep=b["nivel_evidencia"],
                                  motivo_cal=a["motivo_descarte"], motivo_ep=b["motivo_descarte"]))
        lineas.append(f"| {cruce} | {len(ids)} | {c['estable_c']} | {c['estable_e']} | {c['rob_c']} | {c['rob_e']} | "
                      f"{c['pat_c']} | {c['pat_e']} | {c['ambos']} | {c['solo_c']} | {c['solo_e']} |")
    claves = list(filas[0]) if filas else []
    with open(BASE / "comparacion.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=claves)
        w.writeheader()
        w.writerows(sorted(filas, key=lambda r: (r["cruce"], r["patron"], r["par_id"])))
    for tipo in ("solo calendario", "solo épocas"):
        lineas += ["", f"## Patrones {tipo}", ""]
        for r in (r for r in filas if r["patron"] == tipo):
            cal_ = ", ".join(_f(r[f"cal_{n}"]) for n in NOMBRES["calendario"])
            ep_ = ", ".join(_f(r[f"ep_{n}"]) for n in NOMBRES["epocas"])
            lineas.append(f"- {r['cruce']}: **{r['x']} ↔ {r['y']}** (ρ {_f(r['rho_corregida'])}; canary {_f(r['rho_canary'])}). "
                          f"Calendario: {cal_}. Épocas: {ep_}. Motivo: {motivo(r, 'ep' if tipo == 'solo calendario' else 'cal')}")
    (BASE / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


def motivo(r, lado):
    """El motivo de generar_correlaciones dice "cambia de signo" también cuando hay menos de 3 períodos evaluables."""
    if int(r[f"evaluables_{lado}"] or 0) < 3:
        return f"solo {r[f'evaluables_{lado}']} períodos evaluables (hacen falta 3)"
    return r[f"motivo_{lado}"]


def _f(v):
    try:
        return f"{float(v):+.2f}"
    except (TypeError, ValueError):
        return "—"


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo in ("calendario", "epocas"):
        correr(modo)
    elif modo == "comparar":
        comparar()
    else:
        sys.exit(__doc__)
