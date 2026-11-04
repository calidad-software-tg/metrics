"""Tablas de los capítulos 4 y 5 como datos verificables, solo desde analisis/salidas/.

Uso:
    python3 analisis/tablas_informe.py

Escribe analisis/salidas/tablas/tablaNN_<slug>.csv y tablas.md, y compara cada tabla con los valores del texto
(la comparación queda en tablas.md, en la sección «Diferencias con el texto»).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figuras_informe as F  # noqa: E402
from figuras import estilo as E  # noqa: E402

TABLAS = E.SALIDAS / "tablas"
DIF = []


def comparar(tabla, etiqueta, dato, texto, tol=0.0):
    if isinstance(texto, (int, float)) and not (isinstance(dato, float) and np.isnan(dato)):
        ok = abs(dato - texto) <= tol
    else:
        ok = dato == texto
    if not ok:
        DIF.append((tabla, f"{etiqueta}: datos={dato} · texto={texto}"))


def a_markdown(df):
    def celda(v):
        if isinstance(v, float):
            return "—" if np.isnan(v) else E.rho(v) if abs(v) <= 1 else f"{v:.2f}".replace(".", ",")
        return str(v).replace("|", "/")
    filas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    filas += ["| " + " | ".join(celda(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(filas)


def rango_txt(v):
    v = sorted(v)
    if not v:
        return "—"
    if len(v) == 1:
        return E.rho(v[0])
    if len(v) == 2:
        return f"{E.rho(v[0])} y {E.rho(v[1])}"
    return f"{E.rho(v[0])} a {E.rho(v[-1])}"


def t07(p):
    t = F.tabla7(p)
    filas = []
    for D in F.DIMS:
        n = t[D]["n"]
        filas.append(dict(dimension=D, pares_evaluados=n[0], significativas=n[1], robustas=n[2], resisten_tamano=n[3],
                          mecanicas=n[4], descartadas_validacion=n[5], patrones=n[6]))
        for c, a, b in zip(list(filas[-1])[1:], n, F.TABLA7[D]):
            comparar("Tabla 7", f"{D} {c}", a, b)
    return pd.DataFrame(filas)


TEXTO_FAMILIAS = {"A": (5, "+0,25 a +0,47"), "B": (4, "+0,25 a +0,31"), "C": (2, "−0,33 y −0,30"), "D": (5, "+0,19 a +0,47"),
                  "E": (1, "+0,44"), "F": (2, "−0,29 y +0,24"), "G": (4, "−0,18 a +0,29"), "H": (6, "−0,27 a +0,32"),
                  "I": (1, "+0,83"), "J": (1, "−0,23"), "K": (2, "+0,20 y +0,29"), "L": (2, "+0,18 y +0,22"),
                  "M": (4, "−0,31 a −0,27"), "N": (2, "−0,16 y +0,47"), "O": (5, "+0,20 a +0,29"), "P": (2, "+0,23 y +0,23"),
                  "Q": (2, "+0,23 y +0,24"), "R": (4, "−0,29 a −0,20"), "S": (1, "+0,22"), "T": (1, "−0,20"), "U": (1, "+0,17")}


def t_familias(p, letras, tabla):
    f = F.familias(p)
    pi = p.set_index("clave")
    filas = []
    for L in letras:
        sub = f[f.familia == L]
        pats = [k for k in sub.clave if k in pi.index and pi.loc[k, "patron"]]
        rhos = [pi.loc[k, "rho"] for k in pats]
        no = [f"{E.par(r.var_a, r.var_b)} ({r.motivo})" for _, r in sub.iterrows() if not r.es_patron]
        filas.append(dict(familia=L, nombre=sub.nombre.iloc[0], patrones=len(pats), rho=rango_txt(rhos),
                          entre="; ".join(sorted({str(pi.loc[k, "entre"]) for k in pats if pd.notna(pi.loc[k, "entre"])})),
                          no_son_patron_en_los_datos="; ".join(no)))
        comparar(tabla, f"familia {L} patrones", len(pats), TEXTO_FAMILIAS[L][0])
        comparar(tabla, f"familia {L} ρ", rango_txt(rhos), TEXTO_FAMILIAS[L][1].replace("+0,23 y +0,23", "+0,23 y +0,23"))
    return pd.DataFrame(filas)


def t11(p):
    c, pat = F.conteo_pares(p)
    texto = {"Persona–Proceso": (27, 5, 22), "Persona–Producto": (20, 13, 7), "Proceso–Producto": (17, 8, 9)}
    filas = []
    for par in F.PARES:
        filas.append(dict(par=par, patrones=c[par][0], solo_entre=c[par][1], tambien_dentro=c[par][2]))
        for lab, a, b in zip(("patrones", "solo entre", "también dentro"), c[par], texto[par]):
            comparar("Tabla 11", f"{par} {lab}", a, b)
    return pd.DataFrame(filas)


def t13():
    u = pd.read_csv(E.SALIDAS / "multiverso_asignacion" / "universos.csv")
    azar = u[u.universo.str.startswith("azar")]
    texto = {"Persona–Proceso": (0.45, 0.005, 100), "Persona–Producto": (0.61, 0.005, 99), "Proceso–Producto": (0.33, 0.100, 81)}
    filas = []
    for par in F.PARES:
        pr = u[u.universo == "principal"].iloc[0]
        pct = (azar[f"cca {par} p"] < 0.05).mean() * 100
        filas.append(dict(par=par, cca_principal=round(pr[f"cca {par}"], 2), p=round(pr[f"cca {par} p"], 3),
                          pct_asignaciones_sobre_azar=round(pct, 1), n_azar=len(azar)))
        comparar("Tabla 13", f"{par} CCA", round(pr[f"cca {par}"], 2), texto[par][0])
        comparar("Tabla 13", f"{par} p", round(pr[f"cca {par} p"], 3), texto[par][1], 0.001)
        comparar("Tabla 13", f"{par} %", round(pct), texto[par][2])
    return pd.DataFrame(filas)


def t14():
    t = F.tabla14_datos()
    for _, r in t.iterrows():
        comparar("Tabla 14", f"{r.relacion} ρ original", round(r.rho_original, 2), r.texto_original)
        if not np.isnan(r.rho_validado):
            comparar("Tabla 14", f"{r.relacion} ρ validado", round(r.rho_validado, 2), r.texto_validado)
        else:
            DIF.append(("Tabla 14", f"{r.relacion}: sin validación en el repo (texto {E.rho(r.texto_validado)}; "
                                    f"en los datos: {r.estado_en_datos})"))
    return t


def t_triangulos():
    t = pd.read_csv(E.SALIDAS / "relaciones" / "triangulos.csv")
    filas = [dict(nivel="variables", elementos=r.variables, asignacion=r.asignaciones, tipo=r.tipo,
                  desaparece=r.desaparece_al_descontar) for _, r in t.iterrows()]
    b = pd.read_csv(E.SALIDAS / "bloques_etiquetas" / "triangulos.csv")
    filas += [dict(nivel=r.elementos, elementos=r.componentes, asignacion=r.asignaciones, tipo=r.tipo, desaparece=r.desaparece)
              for _, r in b.iterrows()]
    return pd.DataFrame(filas)


def anexo_i(p):
    pat = p[p.patron].copy()
    pat["relacion"] = [E.par(a, b) for a, b in zip(pat.x, pat.y)]
    return pat[["relacion", "x", "y", "rho", "rho_canary", "rho_tamano", "nivel", "tipo", "entre", "dentro", "mismo_tema"]]


def anexo_j(p):
    r = p[p.robusta & ~p.patron].copy()
    r["relacion"] = [E.par(a, b) for a, b in zip(r.x, r.y)]
    return r[["relacion", "x", "y", "rho", "rho_canary", "rho_tamano", "motivo"]]


def main():
    E.aplicar()
    TABLAS.mkdir(parents=True, exist_ok=True)
    p = F.patrones()
    tablas = [("tabla07_embudo_por_dimension", "Tabla 7. Pares que quedaron en cada etapa, por dimensión", t07(p)),
              ("tabla08_familias_persona", "Tabla 8. Familias de Persona", t_familias(p, "ABCDEF", "Tabla 8")),
              ("tabla09_familias_proceso", "Tabla 9. Familias de Proceso", t_familias(p, "GHIJKLMD", "Tabla 9")),
              ("tabla10_familias_producto", "Tabla 10. Familias de Producto", t_familias(p, "N", "Tabla 10")),
              ("tabla11_patrones_por_par", "Tabla 11. Patrones por par de dimensiones", t11(p)),
              ("tabla12_familias_entre_dimensiones", "Tabla 12. Familias entre dimensiones", t_familias(p, "OPQRSTU", "Tabla 12")),
              ("tabla13_correlacion_canonica", "Tabla 13. Correlación canónica entre pares de dimensiones", t13()),
              ("tabla14_validaciones", "Tabla 14. Relaciones validadas", t14()),
              ("tabla_triangulos", "Tabla (a numerar). Candidatos a triángulo de tres dimensiones", t_triangulos()),
              ("anexo_I_patrones", "Anexo I. Patrones", anexo_i(p)),
              ("anexo_J_robustas_no_patron", "Anexo J. Relaciones robustas que no son patrón", anexo_j(p))]
    md = ["# Tablas de los capítulos 4 y 5 (generadas desde analisis/salidas/)", ""]
    for archivo, titulo, df in tablas:
        df.to_csv(TABLAS / f"{archivo}.csv", index=False)
        md += [f"## {titulo}", "", f"`{archivo}.csv`", ""]
        md.append(a_markdown(df) if len(df) <= 80 else f"({len(df)} filas: ver el CSV)")
        md.append("")
    md += ["## Diferencias con el texto", ""]
    md += [f"- **{t}** · {m}" for t, m in DIF] or ["Sin diferencias."]
    (TABLAS / "tablas.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{len(tablas)} tablas en {TABLAS} · {len(DIF)} diferencias con el texto")


if __name__ == "__main__":
    main()
