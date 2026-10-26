"""Validación del PCA de Producto con toda la historia, sin tocar la base ni las salidas del análisis.

El PCA de Producto usa solo los releases desde julio de 2019, porque CFDR y NUB recién tienen datos desde la v9.0.0
y el PCA necesita dato en todas las variables a la vez. Este script comprueba si los componentes cambian al usar
toda la historia. Compara tres PCA con el mismo método de generar_pca.py (rangos, ajuste por tiempo y duración,
Horn, varimax y bootstrap de bloques), sobre las métricas de Producto a nivel repositorio y sin las variantes:

  A. referencia: las 13 variables, desde julio de 2019 (es el PCA del análisis);
  B. toda la historia: sin las variables que no tienen datos en toda la historia (CFDR y NUB);
  C. las mismas variables que B, pero solo desde julio de 2019.

A contra C muestra qué cambia por sacar CFDR y NUB, con los mismos releases; C contra B, qué cambia por agregar
los releases de 2016 a 2019, con las mismas variables. Cada componente se empareja con el más parecido del otro
PCA por congruencia de Tucker sobre las variables comunes (≥ 0,85: el mismo componente; 0,70 a 0,85: parecido).

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/pca_producto_historia_completa.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/pca_producto_historia_completa/.
"""
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "analisis"))

import numpy as np

import generar_pca as gp

SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "pca_producto_historia_completa"
SALIDA.mkdir(parents=True, exist_ok=True)
COBERTURA_HISTORIA = 0.95   # una variable "tiene toda la historia" si tiene dato en el 95 % de las ventanas estables

var_dict, datos = gp.cargar_datos()
variables = sorted(v for v, r in var_dict.items() if "Producto" in r["dims_texto"].split("+")
                   and r["nivel"] == "producto" and r["metrica_id"] not in gp.VARIANTES)
total = len(set().union(*(set(datos[v]["versiones"]) for v in variables)))
cob = {v: sum(1 for t in datos[v]["versiones"].values() if t[1] is not None) / total for v in variables}
con_historia = [v for v in variables if cob[v] >= COBERTURA_HISTORIA]
sin_historia = [v for v in variables if v not in con_historia]
print(f"variables de Producto: {len(variables)} · sin datos en toda la historia: "
      + ", ".join(f"{v} ({cob[v]:.0%})" for v in sin_historia))

desde_2019 = set(gp.tabla(variables, datos, "versiones")[0])  # los releases del PCA de referencia


def pca(nombre, vs, serie_db="versiones", solo=None):
    rng = np.random.default_rng(gp.SEMILLA)
    filas, _ = gp.tabla(vs, datos, serie_db)
    if solo is not None:
        filas = {p: f for p, f in filas.items() if p in solo}
    const = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if const:
        vs = [v for v in vs if v not in const]
        filas, _ = gp.tabla(vs, datos, serie_db)
        if solo is not None:
            filas = {p: f for p, f in filas.items() if p in solo}
    res = gp.analizar(vs, filas, "ajustado", None, rng)
    fechas = sorted(f["fecha"][:8] for f in filas.values())
    res.update(nombre=nombre, variables=vs, constantes=const, desde=fechas[0], hasta=fechas[-1])
    return res


A = pca("A · referencia (13 variables, desde 2019)", variables, solo=desde_2019)
B = pca("B · toda la historia (sin CFDR ni NUB)", con_historia)
C = pca("C · sin CFDR ni NUB, desde 2019", con_historia, solo=desde_2019)
B_canary = pca("B en canary", con_historia, "versiones_canary")


def corto(v):
    return var_dict[v]["nombre_legible"].split(" (")[0].replace(" [producto]", "")


def describir(res):
    Lr = res["sol"]["Lr"]
    comps = []
    for j in range(res["k"]):
        orden = np.argsort(-np.abs(Lr[:, j]))
        cargas = [(corto(res["variables"][i]), round(float(Lr[i, j]), 2)) for i in orden if abs(Lr[i, j]) >= 0.4]
        comps.append(dict(cp=j + 1, varianza=round(float((Lr[:, j] ** 2).sum() / res["p"]), 3),
                          bootstrap=round(float(res["boot"]["congruencia_mediana"][j]), 2), cargas=cargas))
    return comps


def emparejar(x, y):
    """Para cada componente de x, el más parecido de y (Tucker sobre las variables comunes)."""
    comunes = [v for v in x["variables"] if v in y["variables"]]
    ix = [x["variables"].index(v) for v in comunes]
    iy = [y["variables"].index(v) for v in comunes]
    Lx, Ly = x["sol"]["Lr"][ix], y["sol"]["Lr"][iy]
    out = []
    for j in range(Lx.shape[1]):
        # el componente se apoya sobre todo en variables que el otro PCA no tiene (menos de la mitad de su peso)
        if (Lx[:, j] ** 2).sum() < 0.5 * (x["sol"]["Lr"][:, j] ** 2).sum():
            out.append(dict(cp=j + 1, par=None, congruencia=None))
            continue
        c = [abs(gp.tucker(Lx[:, j], Ly[:, m])) for m in range(Ly.shape[1])]
        m = int(np.argmax(c))
        out.append(dict(cp=j + 1, par=m + 1, congruencia=round(float(c[m]), 2)))
    return out


def veredicto(c):
    return "sin equivalente (sus variables no están)" if c is None else (
        "el mismo" if c >= 0.85 else "parecido" if c >= 0.70 else "distinto")


salida = {"sin_historia": sin_historia, "pca": {}, "comparaciones": {}}
for res in (A, B, C, B_canary):
    comps = describir(res)
    salida["pca"][res["nombre"]] = dict(n=res["n"], desde=res["desde"], hasta=res["hasta"], k=res["k"],
                                        varianza_total=round(float(res["acum"][res["k"] - 1]), 3),
                                        constantes=res["constantes"], criterios=res["criterios"], componentes=comps)
    print(f"\n{res['nombre']}: {res['n']} releases ({res['desde']} a {res['hasta']}), Horn retiene {res['k']}, "
          f"{res['acum'][res['k'] - 1]:.0%} de la variación" + (f" · constantes: {res['constantes']}" if res["constantes"] else ""))
    for c in comps:
        print(f"   CP{c['cp']} ({c['varianza']:.0%}, bootstrap {c['bootstrap']}): "
              + ", ".join(f"{n} {v:+.2f}" for n, v in c["cargas"]))

for nom, x, y in (("A → C (sacar CFDR y NUB, mismos releases)", A, C),
                  ("C → B (agregar 2016–2019, mismas variables)", C, B),
                  ("A → B (referencia contra toda la historia)", A, B),
                  ("B → B canary (réplica)", B, B_canary)):
    em = emparejar(x, y)
    salida["comparaciones"][nom] = em
    print(f"\n{nom}")
    for e in em:
        print(f"   CP{e['cp']} → " + (f"CP{e['par']} ({e['congruencia']}, {veredicto(e['congruencia'])})" if e["par"] else veredicto(None)))
# componentes de B que no tienen equivalente en A
nuevos = [e for e in emparejar(B, A) if e["congruencia"] is not None and e["congruencia"] < 0.70]
salida["nuevos_en_historia_completa"] = nuevos
print("\nComponentes de B sin equivalente en A (congruencia < 0,70): "
      + (", ".join(f"CP{e['cp']} ({e['congruencia']})" for e in nuevos) or "ninguno"))

json.dump(salida, open(SALIDA / "resumen.json", "w"), ensure_ascii=False, indent=2)
print(f"\nSalidas en {SALIDA}")
