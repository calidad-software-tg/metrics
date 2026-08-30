-- Seed de metrica: generado desde Metricas.xlsx (Hoja 1, 39 filas -> 43 tras separar filas compuestas)
-- Filas compuestas separadas: MTTR/MTTF/MTBF, Social Contributions(SC)/Developer Contribution(DC), CFDR/Number of Bugs Detected by Users

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'anmcc',
    'ANMCC (Número Promedio de Componentes Modificados por Commit)',
    TRUE, TRUE, FALSE,
    TRUE,
    '10', '52', 'La utilización eficiente de recursos', 'CPU Usage'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'mttr',
    'MTTR (Tiempo Medio de Reparación)',
    TRUE, TRUE, FALSE,
    TRUE,
    '10', '52', 'La utilización eficiente de recursos', 'CPU Usage'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'mttf',
    'MTTF (Tiempo Medio de Falla)',
    TRUE, TRUE, FALSE,
    TRUE,
    '10', '52', 'La utilización eficiente de recursos', 'CPU Usage'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'mtbf',
    'MTBF (Tiempo Medio entre Fallas)',
    TRUE, TRUE, FALSE,
    TRUE,
    '10', '52', 'La utilización eficiente de recursos', 'CPU Usage'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'learning_easy',
    'Learning Easy',
    TRUE, FALSE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'skill_similarity',
    'Skill Similarity',
    FALSE, FALSE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'rexp',
    'REXP (Experiencia Reciente)',
    FALSE, FALSE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'fexp',
    'FEXP (Experiencia en Archivos)',
    FALSE, FALSE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'exprev',
    'EXPRev (Experiencia en Revisión de Código)',
    FALSE, TRUE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'rexprev',
    'REXPRev (Experiencia en Revisión de Código)',
    FALSE, TRUE, TRUE,
    TRUE,
    '15', '15', 'La capacidad de aprender nuevas habilidades técnicas', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'contribution_diversity',
    'Contribution Diversity (Diversidad de Contribución)',
    FALSE, TRUE, TRUE,
    TRUE,
    '15', '18', 'La calidad de la documentación', 'Contribution Diversity'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'cd',
    'CD (Comment Densitiy)',
    TRUE, FALSE, TRUE,
    TRUE,
    '16', '18', 'La calidad de la documentación', 'Documentation Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'readme_completeness',
    'README Completeness',
    TRUE, TRUE, FALSE,
    TRUE,
    '16', '18', 'La calidad de la documentación', 'Documentation Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'wiki_presence',
    'Wiki Presence',
    TRUE, TRUE, FALSE,
    TRUE,
    '16', '18', 'La calidad de la documentación', 'Documentation Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'doc_issue_survival',
    'Doc Issue Survival',
    FALSE, TRUE, FALSE,
    TRUE,
    '16', '18', 'La calidad de la documentación', 'Documentation Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'dloc',
    'DLOC',
    TRUE, FALSE, FALSE,
    TRUE,
    '16', '18', 'La calidad de la documentación', 'Documentation Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_comments',
    'Number of Comments (NC)',
    FALSE, TRUE, TRUE,
    TRUE,
    '18', '9', 'La frecuencia de participación en discusiones técnicas', 'Developer Skill Communication'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'discussion_centrality',
    'Discussion Centrality',
    FALSE, FALSE, TRUE,
    TRUE,
    '18', '9', 'La frecuencia de participación en discusiones técnicas', 'Developer Skill Communication'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'social_contributions_sc',
    'Social Contributions (SC)',
    FALSE, TRUE, TRUE,
    TRUE,
    '18, 20', '9, 11', 'La frecuencia de participación en discusiones técnicas, La contribución a proyectos en su mismo equipo de trabajo', 'Developer Skill Communication, Team Contribution'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'developer_contribution_dc',
    'Developer Contribution (DC)',
    FALSE, TRUE, TRUE,
    TRUE,
    '18, 20', '9, 11', 'La frecuencia de participación en discusiones técnicas, La contribución a proyectos en su mismo equipo de trabajo', 'Developer Skill Communication, Team Contribution'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'rosi',
    'ROSI (Return on Security Investment)',
    FALSE, TRUE, FALSE,
    FALSE,
    '21, 36', '26, 27', 'La implementación de buenas prácticas de seguridad, La respuesta a incidentes de seguridad', 'Secure Development Practices, Security Incident Response Time'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'schedule_compliance',
    'Schedule Compliance',
    FALSE, TRUE, FALSE,
    TRUE,
    '23', '51', 'El cumplimiento de plazos de entrega', 'Schedule Compliance'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'cfdr',
    'Customer Found Defects and Regressions',
    TRUE, TRUE, FALSE,
    TRUE,
    '39, 27', '35, 22', 'Número de Bugs detectados por Usuarios, La calidad de las soluciones implementadas', 'User-Detected Bugs, Solution Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_bugs_detected_by_users',
    'Number of Bugs Detected by Users',
    TRUE, TRUE, FALSE,
    TRUE,
    '39, 27', '35, 22', 'Número de Bugs detectados por Usuarios, La calidad de las soluciones implementadas', 'User-Detected Bugs, Solution Quality'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_open_issues',
    'Number of Open Issues (NOI)',
    TRUE, TRUE, FALSE,
    TRUE,
    '28, 40', '43, 47', 'Cantidad de problemas (issues) abiertos en su repositorio, La adhesión a las prácticas / políticas de desarrollo definidas', 'Number of Open Issues, Process Compliance'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_closed_issues',
    'Number of Closed Issues (NCI)',
    FALSE, TRUE, FALSE,
    TRUE,
    '35, 40, 43', '21, 47, 46', 'Tiempo promedio de resolución de issues, La adhesión a las prácticas / políticas de desarrollo definidas, El tiempo promedio de resolución de problemas', 'Issue Resolution Time, Process Compliance, Average Problem Resolution Time'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'development_experience',
    'Development Experience',
    FALSE, TRUE, TRUE,
    TRUE,
    '38', '29', 'La adopción de nuevas tecnologías', 'Technology Adoption Rate'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'development_process_performance',
    'Development Process Performance',
    FALSE, TRUE, FALSE,
    TRUE,
    '40', '47', 'La adhesión a las prácticas / políticas de desarrollo definidas', 'Process Compliance'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_branches',
    'Number of Branches',
    TRUE, TRUE, FALSE,
    TRUE,
    '42', '41', 'Cantidad de branches de desarrollo activas que existen en su repositorio principal', 'Number of Active Development Branches'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'tasa_de_exito_de_jarczyk',
    'Tasa de Éxito de Jarczyk',
    FALSE, TRUE, FALSE,
    TRUE,
    '43', '46', 'El tiempo promedio de resolución de problemas', 'Average Problem Resolution Time'
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'lines_of_code',
    'Lines of Code (LOC)',
    TRUE, FALSE, FALSE,
    NULL,
    'Sofia', '44', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_collaborators',
    'Number of Collaborators',
    FALSE, FALSE, FALSE,
    NULL,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'commit_frequency',
    'Commit Frequency',
    FALSE, FALSE, FALSE,
    TRUE,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'commit_entropy',
    'Commit Entropy',
    TRUE, FALSE, FALSE,
    NULL,
    'Sofia', '61', 'Evalúa la variabilidad en los commits realizados.', NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'continuous_integration',
    'Continuous Integration',
    TRUE, FALSE, FALSE,
    NULL,
    'Sofia', '15', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'developer_contribution',
    'Developer Contribution (Number of Commits)',
    FALSE, TRUE, FALSE,
    NULL,
    'Sofia', '61', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'developer_ownership',
    'Developer Ownership',
    FALSE, FALSE, FALSE,
    NULL,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'lineas_anadidas_cambiadas_y_eliminadas',
    'Líneas Añadidas, Cambiadas y Eliminadas (Promedio y Máximo por Commit)',
    FALSE, FALSE, FALSE,
    NULL,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_forks',
    'Number of Forks',
    FALSE, FALSE, FALSE,
    NULL,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'total_de_issues',
    'Total de Issues',
    FALSE, FALSE, FALSE,
    NULL,
    'Sofia', NULL, NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'pull_requests_summary',
    'Pull Requests Summary',
    FALSE, FALSE, TRUE,
    NULL,
    'Sofia', '20.33', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_pull_requests_of_core_devs',
    'Number Of Pull Requests of Core Devs',
    FALSE, FALSE, TRUE,
    NULL,
    'Sofia', '33', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;

INSERT INTO metrica (metrica_id, nombre, dim_producto, dim_proceso, dim_persona, calculable, id_registro, id_consigna, texto_consigna, metrica_original_isl)
VALUES (
    'number_of_pull_request_of_core_developers_rejected',
    'Number of Pull Request of Core Developers Rejected',
    FALSE, FALSE, TRUE,
    NULL,
    'Sofia', '33', NULL, NULL
)
ON CONFLICT (metrica_id) DO UPDATE SET
    nombre = EXCLUDED.nombre, dim_producto = EXCLUDED.dim_producto,
    dim_proceso = EXCLUDED.dim_proceso, dim_persona = EXCLUDED.dim_persona,
    calculable = EXCLUDED.calculable, id_registro = EXCLUDED.id_registro,
    id_consigna = EXCLUDED.id_consigna, texto_consigna = EXCLUDED.texto_consigna,
    metrica_original_isl = EXCLUDED.metrica_original_isl;
