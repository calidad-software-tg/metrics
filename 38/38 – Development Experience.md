# 38 – Development Experience

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 29 - La adopción de nuevas tecnologías                                                                                                                                     |
| **Métrica Original (ISL)** | Technology Adoption Rate / Technology Adoption                                                                                                                             |
| **Métrica Canónica JAIIO 2022** | Development Experience                                                                                                                                                     |
| **Métrica Adoptada / Calculable** | Development Experience                                                                                                                                                     |
| **Dimensiones Asociadas** | Persona, Proceso                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Drive)](https://drive.google.com/file/d/18e1okxN6bE_mMmtgOSghzuyViL8iECoh/view?usp=sharing) |

---

## 1. Observación

La consigna pide medir la **adopción de nuevas tecnologías**. El catálogo canónico de 209 métricas **no contiene una métrica explícita** de adopción tecnológica, innovación o incorporación de nuevas herramientas/frameworks. **Development Experience** es la aproximación más cercana encontrada en el catálogo, aunque el propio catálogo aclara que mide **experiencia acumulada del desarrollador**, no adopción tecnológica — la correspondencia es conceptualmente débil.

Se detecta además una **discrepancia entre lo catalogado y lo efectivamente calculable**, del mismo tipo que la documentada en la métrica 20 (Social Contribution):

- La fórmula asociada al nombre ISL original **"Technology Adoption"** sería del tipo `new_technologies_adopted / time_period` — requiere detectar la incorporación de nuevos frameworks, lenguajes o dependencias funcionales a lo largo del tiempo. Esto **no es calculable** en un repositorio como tldr-pages/tldr (99.5% Markdown, sin stack de tecnologías de aplicación).
- La función efectivamente provista para el cálculo, **`calcular_development_experience`**, no mide adopción tecnológica en absoluto: mide la **antigüedad (longevidad/tenure)** de un desarrollador en el repositorio, a partir del tiempo transcurrido desde su primer commit. Esta función **sí es calculable** desde GitHub, independientemente del stack tecnológico del repositorio, porque solo requiere el historial de commits con su autor y fecha.

> **Conclusión de la sustitución:** se documenta y adopta la métrica efectivamente calculable, **Development Experience**, dejando constancia de que no mide lo que pide la consigna original (adopción de tecnología) sino la antigüedad del desarrollador en el proyecto, y que esta discrepancia deberá validarse posteriormente junto con el resto del catálogo.

---

## 2. Definición de la Métrica

**Development Experience (DE)** mide el **tiempo transcurrido (en meses)** desde la primera contribución (commit) de un desarrollador hasta una fecha de referencia dada, como proxy de su veteranía y conocimiento acumulado del proyecto.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la antigüedad individual de un desarrollador específico dentro del repositorio. |
| **Proceso** | La experiencia acumulada del equipo es un indicador indirecto de la madurez de los procesos de desarrollo y la retención de conocimiento del proyecto. |

No aplica a la dimensión **Producto**: no evalúa ninguna característica del código o del repositorio en sí, solo la trayectoria de las personas que contribuyen a él.

### 2.2 Fundamento Teórico

Según **Eyolfson et al. (2011)** y **Wu et al. (2014)**, el tiempo transcurrido desde la incorporación de un desarrollador al proyecto es un **proxy del conocimiento del dominio** y de las convenciones del equipo. Según **Rahman & Devanbu (2011)**, el momento del primer commit marca el inicio del proceso de aprendizaje del desarrollador en el proyecto. Wu et al. (2014) señalan además que la experiencia acumulada es un factor que **mitiga la propensión a introducir errores**.

---

## 3. Cálculo

La función que implementa esta métrica recibe el historial de commits de un desarrollador y una fecha de referencia, y devuelve un número decimal.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Historial de commits del usuario** | Lista de diccionarios obtenida de la API de GitHub (GraphQL) o GHTorrent. Cada elemento contiene al menos `timestamp` (fecha del commit). |
| **fecha_referencia** | Punto en el tiempo para la medición. Si no se especifica, se usa la fecha actual (en esta implementación, `fecha_fin` del período analizado). |

### 3.2 Lógica del proceso

1. Se identifica la **primera contribución** del desarrollador: el commit con el `timestamp` más antiguo.
2. Se calcula la diferencia entre la `fecha_referencia` y esa primera contribución.
3. La diferencia en días se normaliza a **meses** (dividiendo por 30.44 días/mes) para hacerla comparable entre desarrolladores y con estudios de regresión previos.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Development Experience (meses)** | Número decimal: cantidad de meses transcurridos desde el primer commit del desarrollador hasta la fecha de referencia. |

En otras palabras: la métrica funciona como una **fotografía de la antigüedad** de cada colaborador dentro del repositorio al momento del análisis.

---

## 4. Salida Obtenida

**Repositorio analizado:** tldr-pages/tldr
**Período analizado:** 2025-08-07 → 2026-08-07
**Commits totales obtenidos:** 23.350

> ⚠️ La tabla siguiente corresponde a la corrida **previa a** la normalización de identidades (sección 4.1). Pendiente re-ejecutar `run.py` con `dev_experience.py` actualizado para reemplazar por los valores ya consolidados (ej. `Romain Prieto` + `rprieto` deberían fusionarse en una sola fila).

| Colaborador | Primer commit | Experiencia (meses) |
|---|---|---|
| Romain Prieto | 2013-12-08 | 151.94 |
| rprieto | 2013-12-11 | 151.84 |
| pranavraja | 2013-12-11 | 151.84 |
| Pranav Raja | 2013-12-25 | 151.38 |
| marekhrabe | 2014-01-26 | 150.33 |
| ruyadorno | 2014-01-26 | 150.33 |
| Shrayas Rajagopal | 2014-01-27 | 150.30 |
| andrewboerema | 2014-01-26 | 150.30 |

> Lista completa: 160 páginas de colaboradores (salida truncada acá por espacio).

### 4.1 Normalización de identidades

Se detectó que una misma persona podía aparecer partida en dos identidades — por ejemplo `Romain Prieto` / `rprieto`, o `Pranav Raja` / `pranavraja` — porque GitHub solo vincula un commit a una cuenta cuando el email del commit está verificado en esa cuenta; si la persona usó otro email en algunos commits, esos quedan sin vínculo y se identifican solo por el nombre crudo de `git config`.

**Solución aplicada:** se construye un mapa `nombre de perfil de GitHub → login` a partir de los commits que sí están vinculados a una cuenta (GraphQL expone tanto `user.login` como `user.name`, el nombre de perfil público). Los commits sin vínculo se reasignan al mismo login si su nombre de `git config` coincide (case-insensitive) con el nombre de perfil de un login ya visto. Esto resuelve los casos como el de arriba, donde el nombre de perfil de `rprieto` en GitHub es efectivamente "Romain Prieto".

**Limitación remanente:** este método no reconcilia identidades cuando la persona nunca vinculó ninguno de sus emails a su cuenta de GitHub (no hay ningún commit con `login` desde el cual construir el mapa), ni cuando usó nombres de `git config` distintos entre sí (ej. "R. Prieto" vs "Romain Prieto") sin que ninguno coincida con el nombre de perfil exacto. Estos casos residuales quedan como colaboradores separados.

---

## 5. Referencias

- Eyolfson, J. et al. (2011). Relación entre antigüedad del desarrollador y calidad del código.
- Wu, Y. et al. (2014). La experiencia acumulada como factor mitigante de la propensión a introducir errores.
- Rahman, F. & Devanbu, P. (2011). El primer commit como inicio del proceso de aprendizaje del desarrollador en el proyecto.