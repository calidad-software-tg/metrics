# 21 – Return on Security Investment (ROSI)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 26- La implementación de buenas prácticas de seguridad                                                                                                                      |
| **Métrica Original (ISL)** | Application Security Practices / Security Best Practices Adoption (alt.: Secure Development Practices)                                                                      |
| **Métrica Canónica JAIIO 2022** | Return on Security Investment                                                                                   |
| **Métrica Adoptada / Calculable** | ROSI (Return on Security Investment)                                                                                                                                        |
| **Dimensiones Asociadas** | Proceso (Gestión)                                                                                                                                                           |
| **Orden ISL** | TBD                                                                                                                                                                         |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo canónico de 209 métricas** prácticamente no contiene métricas explícitas de seguridad. **Return on Security Investment (ROSI)** es la única métrica claramente vinculada al dominio de seguridad encontrada en la lista.

Sin embargo:

- ⚠️ ROSI mide la **rentabilidad económica de las inversiones en seguridad**, no la **implementación de buenas prácticas** en sí (que era el foco original de la consigna).
- La correspondencia es **débil**, y esta consigna debería **marcarse para revisión posterior**.

> **Conclusión de la sustitución:** ROSI se adopta como única *proxy* disponible dentro del catálogo para el dominio de seguridad, priorizando la justificación económica de las medidas de seguridad sobre la medición directa de la adopción de buenas prácticas.

---

## 2. Definición de la Métrica

**ROSI (Return on Security Investment)** evalúa la **rentabilidad de las inversiones en seguridad**, comparando la reducción del riesgo esperado con el costo de la medida implementada.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso (Gestión)** | Permite a los líderes de proyecto determinar si una inversión en seguridad es económicamente viable, apoyando decisiones de gestión de riesgos y presupuesto. |

### 2.2 Fundamento Teórico

Según **Colakoglu et al. (2021)**, ROSI es una métrica clave para cuantificar la eficiencia de la gestión de riesgos técnicos. Está clasificada en el estudio mapeado como una **métrica de nivel de gestión de proyectos**, siendo vital para justificar presupuestos de ciberseguridad.

La fórmula se basa en el concepto de **ALE (Annual Loss Expectancy)** — la pérdida anual esperada por riesgos de seguridad — comparando el escenario sin la medida de mitigación contra el escenario con dicha medida implementada.

---

## 3. Cálculo

La función que implementa esta métrica recibe tres elementos de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **ALE sin medida** | Pérdida anual esperada por riesgos de seguridad, sin haber implementado la solución. |
| **ALE con medida** | Pérdida anual esperada remanente, luego de implementar la solución de seguridad. |
| **Costo de la solución** | Costo total de adquisición, implementación y operación de la medida de seguridad. |

### 3.2 Lógica del proceso

El cálculo primero determina el **riesgo mitigado**, es decir, cuánta pérdida anual esperada se evita gracias a la solución (la diferencia entre el ALE sin medida y el ALE con medida). Este valor representa el ahorro bruto generado por la inversión.

Si el costo de la solución es cero o negativo, el cálculo no es válido y se retorna 0.0 para evitar una división inválida.

En caso contrario, se calcula el **beneficio neto** restando el costo de la solución al riesgo mitigado, y ese beneficio neto se divide por el costo de la solución, obteniendo así el ratio de retorno.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **ROSI (score)** | Un valor decimal que representa el porcentaje de retorno de la inversión en seguridad. Un valor mayor a 0 indica que la medida ahorra más dinero del que cuesta implementarla. |

En otras palabras: la métrica funciona como un **análisis costo-beneficio** — compara cuánto riesgo económico se evita gracias a una medida de seguridad contra cuánto cuesta implementarla, expresando el resultado como un ratio de rentabilidad.

---

## 4. Referencias

- Colakoglu, N. et al. (2021). ROSI como métrica clave para cuantificar la eficiencia de la gestión de riesgos técnicos [fuente 74].