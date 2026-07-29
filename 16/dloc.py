def calcular_dloc(metadata_archivos):
    """
    Calcula las Líneas de Código de Documentación (DLOC).

    Esta métrica mide de forma objetiva el volumen de soporte técnico y
    documentación externa del proyecto, diferenciándola del código fuente
    ejecutable para evaluar la exhaustividad del material de soporte [1, 2].

    Parámetros:
    -----------
    metadata_archivos : Lista de diccionarios.
        Cada diccionario representa un archivo en el repositorio y debe contener:
        - 'nombre': Str, el nombre completo del archivo (incluyendo extensión).
        - 'lineas': Int, la cantidad total de líneas físicas o lógicas del archivo.

    Retorna:
    --------
    total_dloc : Int
        Suma agregada de las líneas de todos los archivos identificados
        estrictamente como documentación.
    """

    # Se definen las extensiones de archivos que las fuentes categorizan
    # como documentación técnica fuera del código fuente [1, 4].
    extensiones_documentacion = ('.md', '.txt', '.rst', '.pdf', '.doc', '.docx')

    total_dloc = 0

    # Iteración sobre la metadata de cada archivo para garantizar
    # la trazabilidad del cálculo.
    for archivo in metadata_archivos:
        nombre_archivo = archivo['nombre'].lower()

        # Se verifica si el archivo cumple con el criterio de ser documentación
        if nombre_archivo.endswith(extensiones_documentacion):
            # Acumulación de líneas de soporte técnico [3]
            total_dloc += archivo['lineas']

    return total_dloc