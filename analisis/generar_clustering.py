#!/usr/bin/env python3
"""Nombre anterior de clustering.py, que se mantiene por compatibilidad.

Importarlo devuelve el módulo clustering (los scripts de validaciones que reemplazan sus funciones o
constantes siguen funcionando); correrlo corre clustering.py con los mismos argumentos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import clustering  # noqa: E402

if __name__ == "__main__":
    clustering.main()
else:
    sys.modules[__name__] = clustering
