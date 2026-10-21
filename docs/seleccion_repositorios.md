# Selección del repositorio de trabajo

Después de descartar tldr-pages/tldr, que es documentación y no un producto de software, se compararon diez repositorios candidatos para elegir sobre cuál calcular las 26 métricas. Este documento resume la comparación y la decisión. El análisis completo, con los datos de cada criterio, está en [SELECCION_REPOSITORIO.md](../SELECCION_REPOSITORIO.md).

Datos relevados con la API de GitHub en septiembre de 2026.

## 1. Los diez candidatos

| # | Repositorio | Tamaño | Commits | Contribuyentes | Issues abiertas | Releases / tags | Lenguajes principales | Resultado |
|---|---|---|---|---|---|---|---|---|
| 1 | [VS Code / Code-OSS](https://github.com/microsoft/vscode) | 1,46 GB | 165.345 | 3.235 | 21.138 | 239 / 390 | TypeScript 96 % | Mejor rankeado, no elegido |
| 2 | [CPython](https://github.com/python/cpython) | 855 MB | 133.194 | 4.040 | 9.638 | 0 / 668 | Python 61 %, C 34 % | Finalista |
| 3 | [Next.js](https://github.com/vercel/next.js) | 2,5 GB | 35.676 | 4.154 | 3.362 | 3.849 / 4.051 | JavaScript 46 %, TypeScript 31 %, Rust 13 % | **Elegido** |
| 4 | [Home Assistant Core](https://github.com/home-assistant/core) | 876 MB | 116.895 | 5.815 | 3.531 | 1.644 / 1.645 | Python 99,99 % | Finalista |
| 5 | [TensorFlow](https://github.com/tensorflow/tensorflow) | 1,35 GB | 198.969 | 5.318 | 3.146 | 222 / 226 | C++ 58 %, Python 26 %, otros | Elegible |
| 6 | [Flutter](https://github.com/flutter/flutter) | 461 MB | 91.537 | 2.406 | 13.176 | 7 / 1.115 | Dart 69 %, C++ 15 % | Elegible |
| 7 | [GIMP](https://gitlab.gnome.org/GNOME/gimp) (GitLab) | — | — | — | — | 31 / 292 | C | En observación |
| 8 | [raylib](https://github.com/raysan5/raylib) | 411 MB | 10.163 | 1.018 | 13 | 25 / 25 | C | Excluido |
| 9 | [tldr-pages/tldr](https://github.com/tldr-pages/tldr) | 63 MB | 23.752 | 3.478 | 270 | 6 / 11 | Markdown 99,5 % | Excluido (repositorio original) |
| 10 | [freeCodeCamp](https://github.com/freeCodeCamp/freeCodeCamp) | 567 MB | 42.630 | 6.813 | 207 | 0 / 0 | Contenido curricular 92 % | En observación |

## 2. Pros y contras

| Repositorio | A favor | En contra |
|---|---|---|
| **VS Code** | Un solo lenguaje dominante (TypeScript). Producto bien delimitado. Adopción tecnológica real y fechable (CLI en Rust). Comunidad sana: nadie supera el 9 % de los commits. Tiene wiki | Es el de mayor volumen de actividad: 165.000 commits y más de 235.000 issues cerradas. Tiene tres quiebres estructurales en su historia (flujo de PRs en 2022, cambio en cómo se cierran las issues, releases semanales desde 2026). Hay que definir si `extensions/` (37 % del código) es parte del producto |
| **CPython** | El mejor documentado (PEPs, proceso formal). Comunidad repartida. Varios cambios tecnológicos fechados (JIT, modo sin GIL) | Mezcla Python y C. No usa los Releases de GitHub: hay que deducir las versiones de los tags |
| **Next.js** | Miles de releases con una marca confiable de estable o preliminar. La mejor historia de adopción tecnológica de los diez: reescribió su compilador en Rust. Comunidad sana (el principal autor tiene el 9,2 % de los commits). Volumen de actividad manejable | El 87 % de los releases recientes son canary (preliminares) y hay que separarlos. Un bot de releases figura entre los principales autores y hay que filtrarlo. Mezcla JavaScript, TypeScript y Rust |
| **Home Assistant** | Prácticamente un solo lenguaje (Python). Releases mensuales con marca de preliminar confiable. Comunidad grande y repartida | No es un único producto: son unas 1.000 integraciones casi independientes, y 855 tienen un solo dueño. Eso vuelve ambiguas las métricas de código |
| **TensorFlow** | Producto de software claro. Comunidad amplia | El más heterogéneo en lenguajes (C++, Python, MLIR, Starlark, Go, Java, Swift), lo que complica todas las métricas de código |
| **Flutter** | Producto claro. Casos reales de adopción tecnológica (motor Impeller) | Releases mal etiquetados: el filtro de estable o preliminar no es confiable. Los dos autores con más commits son bots |
| **GIMP** | Producto de software válido y acotado | Está en GitLab: el pipeline solo soporta GitHub y habría que construir otro extractor |
| **raylib** | Producto limpio, en un solo lenguaje, bien documentado | Una sola persona hizo el 67 % de los commits. Solo 25 releases, insuficientes para un estudio longitudinal |
| **tldr** | La comunidad más distribuida y el pipeline ya armado | No es software ejecutable sino documentación de herramientas de otros: las métricas de Producto no tienen sobre qué medirse |
| **freeCodeCamp** | Comunidad enorme | El 92 % de los archivos es contenido curricular, no código. No tiene ni un release ni un tag |

## 3. Por qué Next.js

En el ranking por criterios quedó primero **VS Code**: es el único candidato sin problemas de delimitación del producto, casi en un solo lenguaje y con un cambio tecnológico fechable. Pero la decisión práctica, confirmada con el director, fue **Next.js**. El motivo principal fue el **tamaño del trabajo de cálculo**.

**El tamaño que importa es el de la actividad, no el de los archivos.** En disco Next.js es más pesado (2,5 GB contra 1,46 GB), pero la mayoría de las métricas no recorre archivos. Recorren commits, issues, pull requests y comentarios, y la mayor parte de esos datos se descarga de la API de GitHub, que permite unas 5.000 consultas por hora. En ese volumen la diferencia es grande:

| | VS Code | Next.js | Diferencia |
|---|---|---|---|
| Commits | 165.345 | 35.676 | 4,6 veces más en VS Code |
| Issues abiertas | 21.138 | 3.362 | 6,3 veces más |

A eso se suman las más de 235.000 issues cerradas de VS Code, que MTTR, NCI y otras métricas tienen que descargar con sus comentarios y eventos. Correr las 26 métricas de punta a punta, en cada ventana de release y dos veces (estables y canary), sobre la historia de VS Code habría llevado semanas de descargas. Sobre Next.js era viable con el tiempo y las cuotas del equipo.

Además, Next.js tiene otras ventajas que pesan para este análisis:

1. **Muchas ventanas de release.** Con 3.849 releases y una marca confiable de estable o preliminar, salen dos series: 271 ventanas entre releases estables y 3.785 entre canary. La serie canary sirve como réplica independiente. VS Code tiene 239 releases.
2. **Adopción tecnológica real.** La reescritura del compilador en Rust (SWC) da señal a métricas como Development Experience, que en tldr valían cero.
3. **Comunidad sin dueños dominantes y sin bots en la cima**, una vez filtrado el bot de releases. Eso es clave para las métricas de Persona.
4. **Ninguna métrica queda sin datos.** No tiene wiki activa, pero Wiki Presence es binaria y vale 0 o 1 según el período (next.js tuvo wiki entre 2016 y 2020).

Las contras de Next.js se resolvieron en el cálculo:
- los releases canary van en su propia serie;
- los bots se filtran en todas las métricas;
- la mezcla de lenguajes se trata excluyendo el código de terceros y el compilado.
