# 18 – Social Contributions (SC)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 18 y 19 - La frecuencia de participación en discusiones técnicas |
| **Métrica Original (ISL)** | Developer Skill Communication (alt.: Habilidad de Comunicación del Desarrollador) |
| **Métrica Canónica JAIIO 2022** | Developer Skill Communication |
| **Métrica Adoptada / Calculable** | Social Contributions (SC) |
| **Dimensiones Asociadas** | Persona, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## ⚠️ Métrica reutilizada, no reimplementada

**Esta métrica ya está implementada** en `metrics/20/dc.py` bajo la clase `SocialContribution`, documentada en `metrics/20/20 - Social Contribution.md`, para la consigna 20 ("La contribución a proyectos en su mismo equipo de trabajo").

El algoritmo provisto en **esta** planilla (consigna 18/19) para "Social Contributions (SC)" es **matemáticamente la misma fórmula**, de la misma fuente (Falcão et al., 2020):

```python
def calcular_social_contributions(metadata_usuario_repo):
    issues_abiertos = metadata_usuario_repo.get('issues_opened', 0)
    issues_gestionados = metadata_usuario_repo.get('issues_opened_and_closed', 0)
    prs_abiertas = metadata_usuario_repo.get('pull_requests_opened', 0)
    prs_cerradas = metadata_usuario_repo.get('pull_requests_opened_and_closed', 0)
    prs_fusionadas = metadata_usuario_repo.get('pull_requests_opened_and_merged', 0)
    return issues_abiertos + issues_gestionados + prs_abiertas + prs_cerradas + prs_fusionadas
```

Coincide campo a campo con la lógica ya implementada en `20/dc.py` (`issues_opened`, `issues_opened_closed`, `prs_opened`, `prs_opened_closed`, `prs_opened_merged` — mismos cinco componentes, solo con nombres de clave levemente distintos). Ambas consignas (18/19 "frecuencia de participación en discusiones técnicas" y 20 "contribución a proyectos del equipo") citan la misma métrica del catálogo canónico como la operacionalización calculable más cercana.

### Decisión

En lugar de duplicar ~100 líneas de código (fetch de issues/PRs vía GraphQL + agregación), `metrics/18/sc.py` es un archivo puente que reexporta la clase ya existente:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "20"))
from dc import SocialContribution
```

Esto garantiza que ambas consignas usan **la misma implementación y los mismos resultados** — no hay riesgo de que diverjan con el tiempo por mantenimiento en dos lugares distintos. `run.py` la expone bajo la clave `"sc_disc"` (para distinguirla de `"sc"`, que apunta a la Social Contribution de la consigna 20), pero ambas claves ejecutan literalmente la misma clase.

### Para el análisis de la tesis

Si necesitás reportar el valor de SC para la consigna 18/19, **es el mismo número** que ya obtuviste (o vas a obtener) al correr la métrica bajo la consigna 20 — no hace falta correrla dos veces. Ver `metrics/20/20 - Social Contribution.md`, sección 4 ("Salida Obtenida"), para los valores de referencia ya calculados contra `tldr-pages/tldr`.

---

## Referencias

- Falcão, R. et al. (2020). Definición de las cinco dimensiones de Social Contributions e influencia social en equipos de desarrollo.
- Ver también: `metrics/20/20 - Social Contribution.md` (ficha técnica completa de la métrica).
