#!/usr/bin/env python3
"""Nombre anterior de pca.py, que se mantiene por compatibilidad.

Importarlo devuelve el módulo pca (los scripts de validaciones que reemplazan sus funciones o
constantes siguen funcionando); correrlo corre pca.py con los mismos argumentos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pca  # noqa: E402

if __name__ == "__main__":
    pca.main()
else:
    sys.modules[__name__] = pca
