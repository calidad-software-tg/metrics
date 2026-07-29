def calcular_wiki_presence(metadata_repositorio):
    """
    Calcula la presencia y activación del sistema de Wiki en el repositorio.

    Esta métrica de Producto y Proceso actúa como un proxy de madurez técnica.
    Según la literatura (Jarczyk et al., 2014), la habilitación de una Wiki
    indica una inversión deliberada del equipo en la transferencia de
    conocimiento y el soporte al usuario, factores que correlacionan con la
    popularidad del proyecto.

    Parámetros:
    -----------
    metadata_repositorio : Diccionario.
        Objeto obtenido directamente de la API v3 de GitHub (endpoint /repos/:owner/:repo)
        o de un volcado de GHTorrent, que debe contener:
        - 'has_wiki': Booleano, indica si la funcionalidad de wiki está activa.
        - 'fork': Booleano, para controlar si es un repositorio original o derivado.

    Retorna:
    --------
    presencia_wiki : Int
        Retorna 1 si la Wiki está habilitada y el repositorio no es una
        bifurcación (fork) sin cambios significativos; de lo contrario, retorna 0.
    """

    # El campo 'has_wiki' es un metadato escalar estándar en la API de GitHub.
    # Es fundamental para distinguir proyectos personales de proyectos
    # con estructura de equipo quirúrgico (Brooks, 1975).
    wiki_activa = metadata_repositorio.get('has_wiki', False)

    # En Software Analytics, se debe validar que el repositorio sea la
    # fuente primaria de información, ya que las bifurcaciones (forks) suelen
    # heredar este campo pero ser "dumps" de código inactivos.
    es_fork = metadata_repositorio.get('fork', False)

    if wiki_activa and not es_fork:
        # Se asigna un valor binario para su posterior uso en modelos
        # de regresión logística o redes Bayesianas.
        return 1
    else:
        return 0