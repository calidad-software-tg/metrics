#!/usr/bin/env python3
"""Nombre anterior de cruces.py, que se mantiene por compatibilidad. El cruce con los grupos del clustering
está en cruces.py --grupos.

Importarlo devuelve el módulo cruces (los scripts de validaciones que reemplazan sus funciones o
constantes siguen funcionando); correrlo corre cruces.py con los mismos argumentos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cruces  # noqa: E402

if __name__ == "__main__":
    # --corte propio|pca de antes es --grupos propio|pca de cruces.py
    argv = ["--grupos" if a == "--corte" else a for a in sys.argv[1:]]
    cruces.main(argv if "--grupos" in argv else argv + ["--grupos", "propio"])
else:
    sys.modules[__name__] = cruces
