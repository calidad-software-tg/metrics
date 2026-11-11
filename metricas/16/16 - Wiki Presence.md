# 16 – Wiki Presence

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 18 - La calidad de la documentación                                                                                                                                         |
| **Métrica Original (ISL)** | Documentation Quality                                                                                                        |
| **Métrica Canónica Más Cercana** | Quality of Support                                                                                                     |
| **Métrica Adoptada / Calculable** | Wiki Presence                                                                                                                                                               |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo de 209 métricas** no contiene una métrica explícita denominada *"Documentation Quality"*.

La métrica canónica más cercana es **Quality of Support**, ya que en proyectos OSS la documentación es un componente fundamental del soporte brindado a usuarios y desarrolladores. Sin embargo:

- La correspondencia entre "Documentation Quality" y "Quality of Support" es **débil** y deberá **validarse posteriormente**.
- "Quality of Support" sigue siendo un concepto demasiado abstracto para calcularse directamente desde la metadata de un repositorio.

Por este motivo, se adopta como métrica **efectivamente calculable** a **Wiki Presence**, una métrica binaria que opera como *proxy* de madurez técnica y de inversión deliberada del equipo en documentación extendida.

> **Conclusión de la sustitución:** Wiki Presence se adopta como *proxy* operacional de Documentation Quality / Quality of Support, priorizando un indicador binario y directamente verificable desde la metadata del repositorio sobre un concepto de soporte más amplio y no directamente medible.

---

## 2. Definición de la Métrica

**Wiki Presence** es una métrica binaria que indica si el repositorio **utiliza el sistema de Wiki** de GitHub para documentación extendida (más allá del README).

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Evalúa un atributo del repositorio como artefacto: si cuenta o no con un canal adicional de documentación estructurada. |
| **Proceso** | Refleja una decisión y una práctica deliberada del equipo de invertir en la transferencia de conocimiento y el soporte al usuario. |

### 2.2 Fundamento Teórico

Según **Jarczyk et al. (2014)**, la habilitación de una Wiki indica una inversión deliberada del equipo en la transferencia de conocimiento y el soporte al usuario, factores que correlacionan con la popularidad del proyecto.

Adicionalmente, distinguir entre repositorios originales y *forks* resulta relevante para diferenciar proyectos con estructura de equipo consolidada de proyectos individuales o derivados (en línea con la noción de equipo "quirúrgico" de **Brooks, 1975**).

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un valor binario.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata del repositorio** | Un diccionario obtenido directamente de la API v3 de GitHub (endpoint `/repos/:owner/:repo`) o de un volcado de GHTorrent. Debe contener `has_wiki` (si la funcionalidad de Wiki está activa) y `fork` (si el repositorio es una bifurcación de otro). |

### 3.2 Lógica del proceso

El cálculo revisa dos condiciones sobre la metadata del repositorio:

1. **¿La Wiki está activa?** Se consulta el campo `has_wiki`.
2. **¿El repositorio es un fork?** Se consulta el campo `fork`, ya que las bifurcaciones suelen heredar esta configuración sin representar un uso real y activo de la Wiki.

Solo si la Wiki está activa **y** el repositorio no es un fork, se considera que hay una presencia genuina de documentación extendida.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Presencia de Wiki** | Un valor binario: `1` si la Wiki está habilitada en un repositorio original (no fork); `0` en caso contrario. |

En otras palabras: la métrica funciona como un **indicador booleano compuesto** — combina dos condiciones de la metadata del repositorio para determinar si existe una inversión real en documentación mediante Wiki, filtrando los falsos positivos que introducirían los *forks*.

---
## 4. Salida Obtenida

**Repositorios analizados:** tldr-pages/tldr (original) y calidad-software-tg/tldr (fork)

| Repositorio | ¿Es fork? | Wiki activa | WP |
|---|---|---|---|
| tldr-pages/tldr | No | Sí | **1** |
| calidad-software-tg/tldr | Sí | (heredado) | **0** |

> El repo original `tldr-pages/tldr` invirtió deliberadamente en documentación extendida vía Wiki (guías de contribución, formato, guía de estilo, etc.). El fork de `calidad-software-tg` hereda pasivamente esa configuración sin representar una inversión propia del equipo, por lo que la métrica correctamente lo discrimina con WP = 0. La métrica distingue así entre inversión genuina en documentación estructurada y herencia pasiva de configuración por fork.

## 5. Limitación del Indicador

`has_wiki=True` solo indica que la funcionalidad está **habilitada** en la configuración del repositorio — no informa qué tan completa, actualizada o utilizada está esa Wiki. Por tratarse de una métrica binaria, funciona como un *proxy* crudo de inversión en documentación, no como una medición de calidad real de su contenido.
---

## 5. Referencias

- Jarczyk, O. et al. (2014). Relación entre habilitación de Wiki, transferencia de conocimiento y popularidad del proyecto en GitHub.
- Brooks, F. P. (1975). *The Mythical Man-Month* — noción de equipo "quirúrgico" aplicada a la estructura de proyectos.