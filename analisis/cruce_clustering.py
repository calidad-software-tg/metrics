#!/usr/bin/env python3
"""
analisis/cruce_clustering.py

Cruce entre dos dimensiones usando los grupos del clustering de métricas en lugar de los
componentes del PCA. Repite, con el mismo procedimiento de cruce_dimensiones.py, los análisis que
usan componentes:

  2. Cruce de grupos: la correlación parcial entre la serie por release de cada grupo de una
     dimensión y la de cada grupo de la otra.
  3. Conjunto reducido: de cada lado, la serie de cada grupo de dos o más métricas más las variables
     que quedan solas o fuera del clustering.
  4. Correlación canónica entre los grupos de las dos dimensiones.
  5. Triangulación: un patrón del cruce de variables se confirma si los grupos de sus dos variables
     también forman un patrón.

Cada grupo se convierte en una serie por release de tres formas, y el cruce se hace con cada una:

  promedio        promedio de los rangos ajustados de sus métricas, con el signo orientado (las que
                  correlacionan en negativo con la métrica central del grupo se invierten);
  componente      el primer componente principal de las métricas del grupo (pesos del autovector,
                  orientado como la métrica central);
  representativa  la métrica más parecida al resto del grupo (mayor |correlación| promedio), con la
                  misma transformación que el PCA, como las variables marcadoras de cruce_dimensiones.py.

Los grupos, las variables y los releases salen de clustering_<dim>.json (generar_clustering.py), que
a su vez usa las mismas variables y la misma transformación que el PCA de la dimensión. La serie
canary de cada grupo se arma con las mismas métricas y los mismos signos o pesos que la estable.

Uso (después de generar_pca.py, generar_clustering.py de las dos dimensiones y cruce_dimensiones.py):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_clustering.py Persona Producto \\
        --config analisis/cruces/persona_producto.json [--corte propio|pca]

--corte propio (por defecto) usa la cantidad de grupos que elige el clustering; --corte pca, la misma
cantidad que componentes del PCA.

Salidas en analisis/salidas/cruces/<dima>_<dimb>/clustering_<corte>/:
    <metodo>/pares_grupos.csv, <metodo>/pares_reducido.csv, <metodo>/triangulacion.csv,
    resumen.json y comparacion.md (los tres métodos entre sí y frente al cruce con el PCA).
"""
import argparse
import csv
import json
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cruce_dimensiones as cd  # noqa: E402
import generar_correlaciones as gc  # noqa: E402
import generar_pca as gp  # noqa: E402

METODOS = ("promedio", "componente", "representativa")
SERIE_DB = dict(gp.SERIES)


def cargar_clustering(dim):
    archivo = cd.PCA_DIR / f"clustering_{dim.lower()}.json"
    if not archivo.exists():
        sys.exit(f"Falta {archivo}: corré antes generar_clustering.py {dim}.")
    return json.loads(archivo.read_text(encoding="utf-8"))


def matriz(variables, datos, serie, enfoque):
    """Misma matriz que el PCA y el clustering: rangos sin tendencia ni duración, estandarizados."""
    filas, _ = gp.tabla(variables, datos, SERIE_DB[serie])
    if len(filas) < 30:
        return None, [], {}
    Z, pnums = gp.transformar(filas, enfoque)
    return Z, pnums, filas


def a_serie(valores, pnums, filas, duraciones, serie_db):
    """dict pnum -> (duración, valor, año, versión, fecha), el formato de evaluar_par."""
    return {p: (duraciones[serie_db].get(p, filas[p]["dur"]), float(v), filas[p]["anio"], filas[p]["version"], filas[p]["fecha"])
            for p, v in zip(pnums, valores)}


def grupos_de(dim, cfg, datos, duraciones, corte, var_dict):
    C = cargar_clustering(dim)
    _, conj = cd.cargar_pca(dim, cfg)
    enf = cfg["componentes"]["enfoque"]
    ke, kc = f"{conj}|estable|{enf}", f"{conj}|canary|{enf}"
    if ke not in C["resultados"] or corte not in C["resultados"][ke]["soluciones"]:
        sys.exit(f"{dim}: no hay corte '{corte}' para {ke} en clustering_{dim.lower()}.json.")
    Ce = C["resultados"][ke]
    sol = Ce["soluciones"][corte]
    vs = Ce["variables"]
    Ze, pe, fe = matriz(vs, datos, "estable", enf)
    Cc = C["resultados"].get(kc)
    vc = Cc["variables"] if Cc else []
    Zc, pc, fc = matriz(vc, datos, "canary", enf) if Cc else (None, [], {})
    miembros = {}
    for v, g in zip(vs, sol["etiquetas"]):
        miembros.setdefault(g, []).append(v)
    grupos, sueltas = [], []
    for g, mv in sorted(miembros.items(), key=lambda x: -len(x[1])):
        if len(mv) < 2:
            sueltas += mv
            continue
        idx = [vs.index(v) for v in mv]
        R = np.corrcoef(Ze[:, idx], rowvar=False)
        central = int(np.argmax(np.abs(R).mean(axis=0)))          # la más parecida al resto
        signo = np.sign(R[central])
        signo[signo == 0] = 1.0
        val, vec = np.linalg.eigh(R)
        w = vec[:, -1] * (1.0 if vec[central, -1] >= 0 else -1.0)
        series = {}
        for metodo in METODOS:
            for serie, Z, pn, fil, vlist in (("estable", Ze, pe, fe, vs), ("canary", Zc, pc, fc, vc)):
                if Z is None or any(v not in vlist for v in mv):
                    series[(metodo, serie)] = {}
                    continue
                cols = [vlist.index(v) for v in mv]
                if metodo == "promedio":
                    x = (Z[:, cols] * signo).mean(axis=1)
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
                elif metodo == "componente":
                    x = Z[:, cols] @ w / np.sqrt(max(val[-1], 1e-12))
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
                else:
                    # la columna ya transformada de la métrica central: con los valores originales, la
                    # correlación canónica (que no descuenta la tendencia) mezclaría el crecimiento del proyecto
                    x = Z[:, cols[central]] * signo[central]
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
        grupos.append(dict(
            id=f"{dim.lower()}_g{len(grupos) + 1}", dim=dim, n=len(grupos) + 1, variables=mv,
            central=mv[central], signos=[int(s) for s in signo], pesos=[round(float(x), 3) for x in w],
            varianza_grupo=round(float(val[-1] / len(mv)), 3),
            # para las reglas de escala y de métricas compartidas, todas las métricas del grupo cuentan como "fuertes"
            cargas=[(v, float(s)) for v, s in zip(mv, signo)],
            series=series))
    return dict(conjunto=conj, enfoque=enf, corte=corte, k=sol["k"], estabilidad=sol["estabilidad"]["mediana"],
                ari_canary=sol.get("ari_canary"), ari_pca=sol["ari_pca"], grupos=grupos, sueltas=sueltas,
                cubiertas=set(vs))


def nombre_g(g, var_dict, metodo):
    vs = [var_dict[v]["nombre_legible"].split(" (")[0].replace(" [producto]", "") for v in g["variables"]]
    extra = f" · representa {var_dict[g['central']]['nombre_legible'].split(' (')[0]}" if metodo == "representativa" else ""
    return f"G{g['n']} {g['dim']}: " + ", ".join(vs[:5]) + ("…" if len(vs) > 5 else "") + extra


def tipo_par(pr):
    pr["control"] = pr.get("control", False)
    pr["mecanico"] = pr.get("misma_familia", False) or pr.get("solapamiento", False)
    pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                        and pr["resiste_tamano"] is not False)
    pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                  else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")


def correr(metodo, G, dim_a, dim_b, lados, datos, var_dict, cfg, size_e, pares_var, rng):
    cm = cfg["carga_minima"]
    serie = lambda g, s: g["series"][(metodo, s)]
    # ── cruce de grupos ──
    pares_g = {}
    for ga in G[dim_a]["grupos"]:
        for gb in G[dim_b]["grupos"]:
            pr = cd.evaluar_par(serie(ga, "estable"), serie(gb, "estable"), serie(ga, "canary"), serie(gb, "canary"), size_e, True)
            comunes = cd.metricas_cp(ga, cm, var_dict) & cd.metricas_cp(gb, cm, var_dict)
            pr.update(par_id=f"{ga['id']}__{gb['id']}", x_id=ga["id"], y_id=gb["id"],
                      x_nombre=nombre_g(ga, var_dict, metodo), y_nombre=nombre_g(gb, var_dict, metodo),
                      comparten=", ".join(sorted(comunes)),
                      escala=cd.es_escala_cp(ga, cm, var_dict, cfg) or cd.es_escala_cp(gb, cm, var_dict, cfg),
                      solapamiento=bool(comunes) or cd.solapan(ga["variables"], gb["variables"], var_dict))
            pares_g[pr["par_id"]] = pr
    cd.clasificar(pares_g, set())
    for pr in pares_g.values():
        tipo_par(pr)

    # ── conjunto reducido: grupos de dos o más métricas + variables solas o fuera del clustering ──
    def elementos(dim):
        els = []
        for g in G[dim]["grupos"]:
            els.append(dict(id=g["id"], tipo="grupo", nombre=nombre_g(g, var_dict, metodo), e=serie(g, "estable"), c=serie(g, "canary"),
                            escala=cd.es_escala_cp(g, cm, var_dict, cfg), familia="", metricas=cd.metricas_cp(g, cm, var_dict),
                            vars=g["variables"]))
        en_grupo = {v for g in G[dim]["grupos"] for v in g["variables"]}
        for v in lados[dim]:
            if v not in en_grupo:
                els.append(dict(id=v, tipo="variable", nombre=var_dict[v]["nombre_legible"], e=datos[v]["versiones"], c=datos[v]["versiones_canary"],
                                escala=cd.es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                metricas={gc.metrica_base(var_dict[v]["metrica_id"])}, vars=[v]))
        return els
    red_a, red_b = elementos(dim_a), elementos(dim_b)
    pares_r, control_r = {}, set()
    for ea in red_a:
        for eb in red_b:
            k = f"{ea['id']}__{eb['id']}"
            dos_vars = ea["tipo"] == "variable" and eb["tipo"] == "variable"
            if dos_vars and k in pares_var:
                base = pares_var[k]
                constr, misma_fam, solap = base["control"], base["misma_familia"], base["solapamiento"]
            else:
                constr = False
                solap = bool(ea["metricas"] & eb["metricas"]) or cd.solapan(ea["vars"], eb["vars"], var_dict)
                misma_fam = dos_vars and ea["familia"] not in ("", "otra") and ea["familia"] == eb["familia"]
            tam = not constr and not (dos_vars and "tamano" in (ea["familia"], eb["familia"]))
            pr = cd.evaluar_par(ea["e"], eb["e"], ea["c"], eb["c"], size_e, tam)
            pr.update(par_id=k, x_id=ea["id"], y_id=eb["id"], x_nombre=ea["nombre"], y_nombre=eb["nombre"],
                      x_tipo=ea["tipo"], y_tipo=eb["tipo"], escala=ea["escala"] or eb["escala"],
                      misma_familia=misma_fam, solapamiento=solap)
            pares_r[k] = pr
            if constr:
                control_r.add(k)
    cd.clasificar(pares_r, control_r)
    for k, pr in pares_r.items():
        pr["control"] = k in control_r
        tipo_par(pr)

    # ── correlación canónica ──
    cps = {d: [dict(estable=serie(g, "estable")) for g in G[d]["grupos"]] for d in (dim_a, dim_b)}
    res_cca = cd.cca(cps[dim_a], cps[dim_b], cfg["permutaciones"], rng)

    # ── triangulación ──
    def grupo_de(v, dim):
        return next((g for g in G[dim]["grupos"] if v in g["variables"]), None)
    triang = []
    for pr in pares_var.values():
        if not pr["patron"]:
            continue
        ga, gb = grupo_de(pr["x_id"], dim_a), grupo_de(pr["y_id"], dim_b)
        apoyo = pares_g.get(f"{ga['id']}__{gb['id']}") if ga and gb else None
        triang.append(dict(par_id=pr["par_id"], x_nombre=pr["x_nombre"], y_nombre=pr["y_nombre"], rho_corregida=pr["rho_corregida"],
                           grupo_x=f"G{ga['n']}" if ga else "solo", grupo_y=f"G{gb['n']}" if gb else "solo",
                           par_grupos=apoyo["par_id"] if apoyo else "", rho_grupos=apoyo["rho_corregida"] if apoyo else "",
                           tipo_par_grupos=(apoyo["tipo"] or "no robusto") if apoyo else "",
                           triangulado=bool(apoyo and apoyo["tipo"] == "patrón")))
    return pares_g, pares_r, red_a, red_b, res_cca, triang


def leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dim_a")
    ap.add_argument("dim_b")
    ap.add_argument("--config")
    ap.add_argument("--corte", choices=("propio", "pca"), default="propio")
    args = ap.parse_args()
    dim_a, dim_b = (d.strip().capitalize() for d in (args.dim_a, args.dim_b))
    cfg = cd.mezclar(cd.DEFAULTS, json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {})
    warnings.filterwarnings("ignore")
    base = cd.SALIDA / f"{dim_a.lower()}_{dim_b.lower()}"
    if not (base / "pares_variables.csv").exists():
        sys.exit(f"Falta {base / 'pares_variables.csv'}: corré antes cruce_dimensiones.py {dim_a} {dim_b}.")
    destino = base / f"clustering_{args.corte}"
    destino.mkdir(parents=True, exist_ok=True)

    print(f"=== cruce_clustering.py · {dim_a}–{dim_b} · corte {args.corte} ===", flush=True)
    var_dict, datos = gp.cargar_datos()
    lados, _ = cd.armar_lados(dim_a, dim_b, var_dict, cfg)
    size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if not v.startswith("__"):
            for s in duraciones:
                for p, t in datos[v].get(s, {}).items():
                    if t[0] is not None:
                        duraciones[s].setdefault(p, t[0])
    G = {d: grupos_de(d, cfg, datos, duraciones, args.corte, var_dict) for d in (dim_a, dim_b)}
    for d in (dim_a, dim_b):
        g = G[d]
        print(f"  {d}: {g['k']} grupos ({len(g['grupos'])} de dos o más métricas, {len(g['sueltas'])} métricas solas) · "
              f"estabilidad {g['estabilidad']:.2f} · canary {g['ari_canary'] if g['ari_canary'] is None else round(g['ari_canary'], 2)}")

    # patrones del cruce de variables (cruce_dimensiones.py), para el conjunto reducido y la triangulación
    pares_var = {}
    for r in leer_csv(base / "pares_variables.csv"):
        b = lambda c: r.get(c) == "True"
        pares_var[r["par_id"]] = dict(par_id=r["par_id"], x_id=r["x_id"], y_id=r["y_id"], x_nombre=r["x_nombre"], y_nombre=r["y_nombre"],
                                      rho_corregida=float(r["rho_corregida"]) if r["rho_corregida"] else np.nan,
                                      patron=b("patron"), control=b("control"), misma_familia=b("misma_familia"), solapamiento=b("solapamiento"))
    pca_cp = leer_csv(base / "pares_componentes.csv")
    pca_red = leer_csv(base / "pares_reducido.csv")

    cols = ["par_id", "x_nombre", "y_nombre", "tipo", "categoria", "n", "rho_corregida", "ic_inf", "ic_sup", "p_fdr",
            "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026", "estable", "rho_canary",
            "rho_corregida_tamano", "resiste_tamano", "robusta", "escala", "comparten"]
    res = {}
    for metodo in METODOS:
        rng = np.random.default_rng(gp.SEMILLA)
        pares_g, pares_r, red_a, red_b, res_cca, triang = correr(metodo, G, dim_a, dim_b, lados, datos, var_dict, cfg, size_e, pares_var, rng)
        (destino / metodo).mkdir(exist_ok=True)
        orden = lambda d: sorted(d.values(), key=lambda p: -abs(p["rho_corregida"]) if cd.num(p["rho_corregida"]) else 0)
        cd.escribir_csv(destino / metodo / "pares_grupos.csv", orden(pares_g), cols)
        cd.escribir_csv(destino / metodo / "pares_reducido.csv", orden(pares_r), ["x_tipo", "y_tipo"] + cols)
        cd.escribir_csv(destino / metodo / "triangulacion.csv", triang, list(triang[0]) if triang else ["par_id"])
        cuenta = lambda d: {t: sum(1 for p in d.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")}
        res[metodo] = dict(
            grupos={"pares": len(pares_g), "tipos": cuenta(pares_g),
                    "robustos": [dict(par=p["par_id"], x=p["x_nombre"], y=p["y_nombre"], rho=cd.r4(p["rho_corregida"]),
                                      tamano=cd.r4(p["rho_corregida_tamano"]), canary=cd.r4(p["rho_canary"]), tipo=p["tipo"])
                                 for p in orden(pares_g) if p["robusta"]]},
            reducido={"elementos": {dim_a: len(red_a), dim_b: len(red_b)}, "pares": len(pares_r), "tipos": cuenta(pares_r),
                      "patrones": [dict(par=p["par_id"], x=p["x_nombre"], y=p["y_nombre"], rho=cd.r4(p["rho_corregida"]),
                                        tamano=cd.r4(p["rho_corregida_tamano"]), canary=cd.r4(p["rho_canary"]))
                                   for p in orden(pares_r) if p["patron"]]},
            cca=res_cca,
            triangulacion=dict(patrones=len(triang), triangulados=sum(t["triangulado"] for t in triang),
                               detalle=[{k: (cd.r4(v) if isinstance(v, float) else v) for k, v in t.items()} for t in triang]))
        r_ = res[metodo]
        print(f"  {metodo:15s} grupos: {r_['grupos']['tipos']} · reducido: {r_['reducido']['tipos']} · "
              f"CCA {res_cca['correlaciones'][0] if res_cca else '—'} (p {res_cca['p_primera'] if res_cca else '—'}) · "
              f"triangulados {r_['triangulacion']['triangulados']} de {r_['triangulacion']['patrones']}", flush=True)

    resumen = dict(dimensiones=[dim_a, dim_b], corte=args.corte,
                   grupos={d: dict(k=G[d]["k"], conjunto=G[d]["conjunto"], estabilidad=G[d]["estabilidad"], ari_canary=G[d]["ari_canary"],
                                   ari_pca=G[d]["ari_pca"], sueltas=G[d]["sueltas"],
                                   grupos=[dict(id=g["id"], variables=g["variables"], central=g["central"], signos=g["signos"],
                                                pesos=g["pesos"], varianza_grupo=g["varianza_grupo"]) for g in G[d]["grupos"]])
                           for d in (dim_a, dim_b)},
                   metodos=res)
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ── comparación entre métodos y con el cruce que usa el PCA ──
    f = lambda v: f"{float(v):+.2f}".replace(".", ",") if v not in ("", None) and cd.num(float(v)) else "—"
    md = [f"# Cruce {dim_a}–{dim_b} con los grupos del clustering (corte {args.corte})", ""]
    for d in (dim_a, dim_b):
        g = G[d]
        md += [f"## Grupos de {d}", "",
               f"{g['k']} grupos en total, {len(g['grupos'])} de dos o más métricas · estabilidad {g['estabilidad']:.2f} · "
               f"canary {'—' if g['ari_canary'] is None else round(g['ari_canary'], 2)} · coincidencia con el PCA {g['ari_pca']:.2f}", ""]
        md += [f"- G{x['n']}: {', '.join(x['variables'])} (central: {x['central']}; varianza del primer componente {x['varianza_grupo']:.0%})"
               for x in g["grupos"]]
        md += [f"- Solas: {', '.join(g['sueltas'])}" if g["sueltas"] else "", ""]
    md += ["## Resumen por método", "",
           "| | Promedio | Primer componente | Más representativa |", "|---|---|---|---|"]
    fila = lambda t, fn: f"| {t} | " + " | ".join(fn(res[m]) for m in METODOS) + " |"
    md += [fila("Pares de grupos robustos", lambda r: str(len(r["grupos"]["robustos"]))),
           fila("Patrones entre grupos", lambda r: str(r["grupos"]["tipos"]["patrón"])),
           fila("Patrones en el conjunto reducido", lambda r: str(r["reducido"]["tipos"]["patrón"])),
           fila("Primera correlación canónica", lambda r: (f"{r['cca']['correlaciones'][0]:.2f} (p {r['cca']['p_primera']:.3f})".replace(".", ",") if r["cca"] else "—")),
           fila("Patrones triangulados", lambda r: f"{r['triangulacion']['triangulados']} de {r['triangulacion']['patrones']}"), ""]
    md += ["## Pares de grupos robustos", "", "| Método | Par | ρ corregida | con tamaño | canary | tipo |", "|---|---|---|---|---|---|"]
    for m in METODOS:
        md += [f"| {m} | {p['x']} ↔ {p['y']} | {f(p['rho'])} | {f(p['tamano'])} | {f(p['canary'])} | {p['tipo']} |" for p in res[m]["grupos"]["robustos"]]
    md += ["", "## Patrones del conjunto reducido", "", "| Método | Par | ρ corregida | con tamaño | canary |", "|---|---|---|---|---|"]
    for m in METODOS:
        md += [f"| {m} | {p['x']} ↔ {p['y']} | {f(p['rho'])} | {f(p['tamano'])} | {f(p['canary'])} |" for p in res[m]["reducido"]["patrones"]]
    md += ["", "## Triangulación de los patrones de variables", "", "| Patrón de variables | Promedio | Primer componente | Más representativa |", "|---|---|---|---|"]
    det = {m: {t["par_id"]: t for t in res[m]["triangulacion"]["detalle"]} for m in METODOS}
    for pid, t in det[METODOS[0]].items():
        celda = lambda m: (lambda x: f"{x['grupo_x']}–{x['grupo_y']}: {x['tipo_par_grupos'] or 'métrica sola'} ({f(x['rho_grupos'])})")(det[m][pid])
        md += [f"| {t['x_nombre']} ↔ {t['y_nombre']} | " + " | ".join(celda(m) for m in METODOS) + " |"]
    md += ["", "## Frente al cruce con el PCA (cruce_dimensiones.py)", ""]
    rob = [r for r in pca_cp if r.get("robusta") == "True"]
    md += [f"- Pares de componentes del PCA: {len(pca_cp)}, robustos {len(rob)}: " +
           ("; ".join(f"{r['x_nombre']} ↔ {r['y_nombre']} ({f(r['rho_corregida'])}, {r['tipo'] or 'no robusto'})" for r in rob) or "ninguno"),
           f"- Patrones del conjunto reducido con el PCA: {sum(1 for r in pca_red if r.get('patron') == 'True')}"]
    (destino / "comparacion.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  salida: {destino}")


if __name__ == "__main__":
    main()
