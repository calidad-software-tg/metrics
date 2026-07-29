def calcular_readme_completeness(contenido_readme):
    """
    Calcula el nivel de completitud del archivo README basado en secciones clave.

    Esta métrica de Producto y Proceso evalúa la calidad de la documentación inicial.
    Se basa en las 8 categorías identificadas por Prana et al. (2018) y las
    recomendaciones oficiales de GitHub para un proyecto maduro.

    Parámetros:
    -----------
    contenido_readme : String.
        El texto plano extraído del archivo README.md del repositorio.

    Retorna:
    --------
    indice_completitud : Float.
        Un valor entre 0.0 y 1.0 que representa el porcentaje de secciones
        esenciales detectadas en el documento.
    """
    if not contenido_readme or len(contenido_readme) < 10:
        return 0.0

    # Definición de categorías y palabras clave basadas en el esquema de
    # codificación de Prana et al. [4] y Jarczyk et al. [3].
    secciones_esenciales = {
        'What': ['introduction', 'about', 'overview', 'background'],
        'Why': ['purpose', 'motivation', 'advantages', 'features'],
        'How': ['install', 'usage', 'getting started', 'setup', 'quick start', 'dependencies'],
        'When': ['status', 'roadmap', 'version', 'changelog', 'todo'],
        'Who': ['license', 'author', 'maintainer', 'contact', 'acknowledgement', 'team'],
        'References': ['documentation', 'api', 'links', 'resources', 'related'],
        'Contribution': ['contribute', 'contributing', 'pull request', 'fork']
    }

    texto_limpio = contenido_readme.lower()
    secciones_detectadas = 0
    total_secciones_objetivo = len(secciones_esenciales)

    # Análisis de presencia por categoría
    for categoria, keywords in secciones_esenciales.items():
        # Verificamos si alguna de las palabras clave de la categoría
        # está presente en el cuerpo del README.
        if any(key in texto_limpio for key in keywords):
            secciones_detectadas += 1

    # El índice es la proporción de categorías cubiertas
    return secciones_detectadas / total_secciones_objetivo
