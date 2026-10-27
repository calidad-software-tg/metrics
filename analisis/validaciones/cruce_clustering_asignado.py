"""Cruce con los grupos del clustering de métricas respetando la asignación de las métricas compartidas.

cruce_clustering.py arma los grupos de cada dimensión con todas sus métricas, sin aplicar el "asignar" de la
config. Cuando las dos dimensiones comparten métricas (Proceso–Producto: CFDR, NUB, NOI, README, etc.) quedan
grupos idénticos de los dos lados: los pares salen como mecánicos, pero la correlación canónica da 1,00.
Este script corre cruce_clustering.py sin modificarlo: antes de armar cada grupo le saca las métricas que la
config asigna al otro lado (las mismas que cruce_dimensiones.armar_lados deja de ese lado).

Uso (desde la raíz del repo, después de generar_pca.py, generar_clustering.py y cruce_dimensiones.py):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cruce_clustering_asignado.py \\
        Proceso Producto analisis/cruces/proceso_producto_asignado.json [propio|pca]

Escribe en analisis/salidas/cruces/<a>_<b>/clustering_<corte>_asignado/ (no pisa la salida de cruce_clustering.py).
"""
import inspect
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "analisis"))
import cruce_clustering as cc  # noqa: E402
import cruce_dimensiones as cd  # noqa: E402
import generar_pca as gp  # noqa: E402

dim_a, dim_b, config = sys.argv[1].capitalize(), sys.argv[2].capitalize(), sys.argv[3]
corte = sys.argv[4] if len(sys.argv) > 4 else "propio"
cfg = cd.mezclar(cd.DEFAULTS, json.loads(Path(config).read_text(encoding="utf-8")))
var_dict, _ = gp.cargar_datos()
lados, _ = cd.armar_lados(dim_a, dim_b, var_dict, cfg)

ns = vars(cc)
ns["PERMITIDAS"] = {d: set(v) for d, v in lados.items()}
# grupos_de: cada grupo conserva solo las métricas que quedan de su lado
src = inspect.getsource(cc.grupos_de)
viejo = "        miembros.setdefault(g, []).append(v)\n"
assert src.count(viejo) == 1, "cambió grupos_de en cruce_clustering.py"
src = src.replace(viejo, viejo + "    miembros = {g: [v for v in mv if v in PERMITIDAS[dim]] for g, mv in miembros.items()}\n"
                                 "    miembros = {g: mv for g, mv in miembros.items() if mv}\n")
exec(compile(src, "grupos_de_asignado", "exec"), ns)
# main: otra carpeta de salida
src = inspect.getsource(cc.main)
viejo = 'destino = base / f"clustering_{args.corte}"'
assert src.count(viejo) == 1, "cambió main en cruce_clustering.py"
exec(compile(src.replace(viejo, 'destino = base / f"clustering_{args.corte}_asignado"'), "main_asignado", "exec"), ns)

sys.argv = ["cruce_clustering.py", dim_a, dim_b, "--config", config, "--corte", corte]
cc.main()
