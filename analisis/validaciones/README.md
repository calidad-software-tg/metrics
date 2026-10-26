# Validaciones de hallazgos

Pruebas para comprobar si una relación robusta dice algo del proyecto o si la arma una explicación trivial. Cada script recalcula las variables sin lo que podría estar fabricando la relación y repite la misma correlación del cruce (`evaluar_par` de `cruce_dimensiones.py`): si la relación se mantiene, el hallazgo se sostiene; si desaparece, era construcción o composición.

Los scripts **no modifican nada**: leen la base con una conexión de solo lectura, el clon local (`.clones/next.js`, con `git log`) y los CSV del análisis, y escriben solo en `analisis/salidas/validaciones/<script>/` (fuera de git). Antes de comparar, cada uno verifica que el cálculo recalculado con todos los datos coincide con el del análisis.

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cdiv_sin_commits_doc.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/experiencia_sin_recien_llegados.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/anmcc_sin_commits_doc.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/pca_producto_historia_completa.py
```

Necesitan la base corregida cargada, el clon de Next.js y los CSV de persona agregada y del diccionario, igual que el resto del análisis. `experiencia_sin_recien_llegados.py` tarda unos minutos porque lee Development Experience, que tiene millones de filas.

## Qué prueba cada uno y qué dio

| Script | Relación | Explicación alternativa | Resultado |
|---|---|---|---|
| `cdiv_sin_commits_doc.py` | Contribution Diversity (mediana) ↔ commits que tocan documentación (Persona–Producto, −0,42) | Los commits que solo tocan documentación cambian pocos archivos: suben una métrica y bajan la otra | Sin esos commits: **−0,15**, +0,19 en 2016–19, canary −0,02. **Se descarta: construcción** |
| `experiencia_sin_recien_llegados.py` | LE (mediana) ↔ ANMCC (mediana), +0,48, y Development Experience (mediana) ↔ ANMCC (mediana), +0,38 (Persona–Producto y Producto) | Los recién llegados tienen poca experiencia y hacen commits chicos: en los releases con más gente nueva las medianas bajan juntas | Sin recién llegados: **+0,08** y **−0,01**. Sin commits solo de documentación: +0,28 y +0,23. **Se descarta: composición del equipo** |
| `anmcc_sin_commits_doc.py` | ANMCC (mediana) ↔ commits que tocan documentación (Producto, −0,45) | La misma que la primera, con ANMCC en lugar de Contribution Diversity | Sin commits solo de documentación: **−0,07**, canary +0,02. Sin recién llegados: −0,24. **Se descarta: construcción** |

## PCA de Producto con toda la historia

`pca_producto_historia_completa.py` comprueba si el período del PCA de Producto condiciona sus componentes. Ese PCA usa solo los 185 releases desde julio de 2019 (v9.0.0), porque CFDR y NUB recién tienen datos desde ahí y el PCA necesita dato en todas las variables. El script compara, con el mismo método de `generar_pca.py`, tres versiones: la del análisis (A), toda la historia sin CFDR ni NUB (B, 266 releases desde 2016) y las mismas variables que B desde 2019 (C), y empareja los componentes por congruencia de Tucker.

| Componente del análisis (A) | Con toda la historia (B) | Bootstrap A → B | Canary de B |
|---|---|---|---|
| Bugs de usuarios (CFDR, NUB) | No puede calcularse: sus variables solo tienen datos desde 2019 | — | — |
| Wiki y documentación temprana (Wiki Presence, CD, NOB) | El mismo (0,94), ahora también con README | 0,71 → 0,96 | Parecido (0,80) |
| Issues abiertas y README (README, NOI, ANMCC) | El mismo (0,89) | 0,84 → 0,83 | No se replica (0,57) |
| Flujo de documentación (DLOC 2.0, commits que tocan documentación, LE) | El mismo (0,95) | 0,92 → 0,94 | Se replica (0,90) |

Con toda la historia no aparece ningún componente nuevo, y sacar CFDR y NUB no cambia los otros tres (congruencia 1,00 entre A y C). El de Wiki se vuelve estable porque con toda la historia Wiki Presence cambia en muchos releases y no en uno solo, pero sigue siendo un escalón (la etapa con wiki, 2016–2020) y no se interpreta como patrón.

Definiciones usadas:

- **Commit que solo toca documentación:** todos sus archivos cumplen `es_documentacion` (`16/dloc.py`), el mismo criterio de DLOC 2.0 y de commits que tocan documentación. Son 3.881 de 35.959 commits de la rama (10,8 %); cambian un archivo de mediana, contra cuatro en el resto.
- **Recién llegado:** quien commitea por primera vez en esa ventana, la misma definición de la variable "Nuevos (commits)" de `export_persona.py`. En la ventana mediana son el 37 % de quienes commitean.
