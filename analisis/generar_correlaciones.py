#!/usr/bin/env python3
"""Nombre anterior de correlaciones.py, que se mantiene por compatibilidad.
Ahora calcula solo los pares dentro de cada dimensión (los de dos dimensiones están en cruces.py;
con --entre-dimensiones se agregan como antes).

Importarlo devuelve el módulo correlaciones (los scripts de validaciones que reemplazan sus funciones o
constantes siguen funcionando); correrlo corre correlaciones.py con los mismos argumentos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones  # noqa: E402

if __name__ == "__main__":
    correlaciones.main()
else:
    sys.modules[__name__] = correlaciones
