def calcular_rosi(ale_sin_medida, ale_con_medida, costo_solucion):
    """
    Calcula el Retorno de la Inversión en Seguridad (ROSI).

    Esta métrica de Proceso (Gestión) permite a los líderes de proyecto
    determinar si una inversión en seguridad es económicamente viable.
    Según Colakoglu et al. (2021) [fuente 74], ROSI es una métrica clave
    para cuantificar la eficiencia de la gestión de riesgos técnicos.

    Fórmula utilizada: ROSI = ((ALE_evitado * Mitigación) - Costo) / Costo
    Donde ALE es la Expectativa de Pérdida Anual (Annual Loss Expectancy).

    Parámetros:
    -----------
    ale_sin_medida : Float
        Pérdida anual esperada por riesgos de seguridad sin la solución.
    ale_con_medida : Float
        Pérdida anual esperada remanente tras implementar la solución.
    costo_solucion : Float
        Costo total de adquisición, implementación y operación de la medida.

    Retorna:
    --------
    rosi_score : Float
        Porcentaje de retorno de la inversión. Un valor > 0 indica que
        la medida ahorra más dinero del que cuesta.
    """

    # 1. Calculamos el riesgo mitigado (ALE evitado)
    # Representa el ahorro bruto generado por la solución de seguridad.
    riesgo_mitigado = ale_sin_medida - ale_con_medida

    # 2. Validación de costo para evitar división por cero
    if costo_solucion <= 0:
        return 0.0

    # 3. Aplicación de la fórmula de rentabilidad económica
    # Restamos el costo del beneficio y dividimos por el costo para obtener el ratio.
    beneficio_neto = riesgo_mitigado - costo_solucion
    rosi_score = beneficio_neto / costo_solucion

    # Retornamos el valor en formato decimal (ej: 0.15 para 15%)
    return round(rosi_score, 4)