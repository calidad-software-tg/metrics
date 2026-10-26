# Validaciones de hallazgos

Pruebas para comprobar si una relación robusta dice algo del proyecto o si la arma una explicación trivial. Cada script recalcula las variables sin lo que podría estar fabricando la relación y repite la misma correlación del cruce (`evaluar_par` de `cruce_dimensiones.py`): si la relación se mantiene, el hallazgo se sostiene; si desaparece, era construcción o composición.

Los scripts **no modifican nada**: leen la base con una conexión de solo lectura, el clon local (`.clones/next.js`, con `git log`) y los CSV del análisis, y escriben solo en `analisis/salidas/validaciones/<script>/` (fuera de git). Antes de comparar, cada uno verifica que el cálculo recalculado con todos los datos coincide con el del análisis.

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cdiv_sin_commits_doc.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/experiencia_sin_recien_llegados.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/anmcc_sin_commits_doc.py
```

Necesitan la base corregida cargada, el clon de Next.js y los CSV de persona agregada y del diccionario, igual que el resto del análisis. `experiencia_sin_recien_llegados.py` tarda unos minutos porque lee Development Experience, que tiene millones de filas.

## Qué prueba cada uno y qué dio

| Script | Relación | Explicación alternativa | Resultado |
|---|---|---|---|
| `cdiv_sin_commits_doc.py` | Contribution Diversity (mediana) ↔ commits que tocan documentación (Persona–Producto, −0,42) | Los commits que solo tocan documentación cambian pocos archivos: suben una métrica y bajan la otra | Sin esos commits: **−0,15**, +0,19 en 2016–19, canary −0,02. **Se descarta: construcción** |
| `experiencia_sin_recien_llegados.py` | LE (mediana) ↔ ANMCC (mediana), +0,48, y Development Experience (mediana) ↔ ANMCC (mediana), +0,38 (Persona–Producto y Producto) | Los recién llegados tienen poca experiencia y hacen commits chicos: en los releases con más gente nueva las medianas bajan juntas | Sin recién llegados: **+0,08** y **−0,01**. Sin commits solo de documentación: +0,28 y +0,23. **Se descarta: composición del equipo** |
| `anmcc_sin_commits_doc.py` | ANMCC (mediana) ↔ commits que tocan documentación (Producto, −0,45) | La misma que la primera, con ANMCC en lugar de Contribution Diversity | Sin commits solo de documentación: **−0,07**, canary +0,02. Sin recién llegados: −0,24. **Se descarta: construcción** |

Definiciones usadas:

- **Commit que solo toca documentación:** todos sus archivos cumplen `es_documentacion` (`16/dloc.py`), el mismo criterio de DLOC 2.0 y de commits que tocan documentación. Son 3.881 de 35.959 commits de la rama (10,8 %); cambian un archivo de mediana, contra cuatro en el resto.
- **Recién llegado:** quien commitea por primera vez en esa ventana, la misma definición de la variable "Nuevos (commits)" de `export_persona.py`. En la ventana mediana son el 37 % de quienes commitean.
