#!/usr/bin/env python3
"""Nombre anterior de cruces.py, que se mantiene por compatibilidad.

Importarlo devuelve el módulo cruces (los scripts de validaciones que reemplazan sus funciones o
constantes siguen funcionando); correrlo corre cruces.py con los mismos argumentos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cruces  # noqa: E402

if __name__ == "__main__":
    cruces.main()
else:
    sys.modules[__name__] = cruces
