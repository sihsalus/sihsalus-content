# Alineación de formularios CRED con NTS 238 y NTS 213 - 2026-07-10

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

## Alcance

Se revisaron `CRED-001`, `CRED-009`, `CRED-010`, `CRED-011`, `CRED-015`, `CRED-026` y `CRED-027` contra:

- NTS N. 238-MINSA/DGIESP-2025 para crecimiento y desarrollo.
- NTS N. 213-MINSA/DGIESP-2024, modificada por RM N. 429-2024/MINSA, para anemia.
- Guía Técnica de Valoración Nutricional Antropométrica aprobada por RM N. 034-2024/MINSA.

## Cambios desplegables con la terminología actual

### CRED-001 - anemia

- Elimina la referencia a NTS 137 y los umbrales fijos impresos en las respuestas.
- Exige edad en meses, hemoglobina medida y altitud aplicable.
- Activa la advertencia de corrección por altitud por encima de 500 m.s.n.m.
- Exige que la clasificación se realice después de ajustar por altitud y aplicar el corte por edad.

El formulario no calcula todavía la hemoglobina ajustada porque el bundle OCL no contiene conceptos separados
para factor de corrección y hemoglobina ajustada. Hasta publicarlos, la selección queda a cargo del profesional y
el formulario la identifica explícitamente como clasificación ajustada.

### CRED-009 - EDI

- Exige edad cronológica y edad corregida cuando corresponde por prematuridad.
- Exige un resumen de los cinco ejes EDI antes de registrar Verde, Amarillo o Rojo.
- Mantiene el plan obligatorio ante resultado Amarillo o Rojo.
- Se presenta expresamente como transcripción auditable, no como aplicación digital completa.

### CRED-010 - M-CHAT-R/F

- Exige edad de 18 a 30 meses, puntaje de 0 a 20 y números de los ítems con respuesta de riesgo.
- Conserva el cálculo automático de bajo, moderado o alto riesgo y el plan obligatorio.
- Se presenta como transcripción auditable del cuestionario oficial.

### CRED-011 - salud mental

- Sustituye el resultado genérico `Normal/Riesgo/Anormal` por instrumento, puntaje y resultado identificables.
- Permite registrar PHQ-9, AUDIT-C mediante el concepto agrupador AUDIT, PSC/PPSC y detección de violencia.
- Estructura el instrumento principal y exige documentar cada instrumento adicional con puntaje y resultado.
- Exige especificar la versión PSC/PPSC y la persona que respondió.
- Mantiene violencia y plan de atención como resultados separados.

### CRED-015 - crecimiento

- Elimina tres clasificaciones que reutilizaban el mismo concepto genérico y generaban observaciones indistinguibles.
- Exige edad en meses y diagnóstico con indicador, z-score y clasificación.
- Mantiene perímetro cefálico en menores de 5 años.
- Calcula IMC y exige perímetro abdominal desde los 5 años.

### CRED-026 - Huanca

- Retira el selector codificado que mezclaba edades Huanca con edades EDI.
- Declara la periodicidad de vigilancia: 2, 3, 4, 7, 12, 15, 21, 24 y 36 meses.
- Exige completar las cinco áreas y detallar cualquier hito no logrado.
- Mantiene resultado e intervención calculados, incluida ATD/EDI.

### CRED-027 - habilidades y conductas

- Agrega edad exacta en meses además de la pauta anual.
- Exige registrar el factor de riesgo y calcula la acción normativa cuando coexisten ausencia de habilidad y
  factor de riesgo: EDI hasta 60 meses o interconsulta después de esa edad.
- Conserva detalles obligatorios por toda área con ausencia.

## Terminología necesaria para digitalización completa

No se crearon UUIDs locales ni se alteró un ZIP OCL publicado. La digitalización ítem por ítem requiere primero
crear y publicar una nueva release del source `SIHSALUS/sihsalus`, y luego descargar su export oficial.

| Formulario | Conceptos OCL pendientes |
| --- | --- |
| CRED-001 | Factor de corrección por altitud, hemoglobina ajustada y, opcionalmente, corte aplicado. |
| CRED-009 | Preguntas binarias y resultados por los cinco ejes EDI, respetando el manual oficial. |
| CRED-010 | Veinte preguntas M-CHAT-R/F con sus respuestas Sí/No y marca de respuesta de riesgo. |
| CRED-011 | Grupo repetible e ítems/resultados específicos de PHQ-9, AUDIT-C, PPSC y PSC-17. |
| CRED-015 | Z-score y clasificación separados para P/E, T/E, P/T, IMC/E y PC/E. |
| CRED-026 | Cada hito Huanca por pauta de edad, con resultado Sí/No y fuente de evaluación. |
| CRED-027 | Cada habilidad/conducta de las tablas de 4 a 11 años, agrupada por edad y área. |

Los ítems protegidos o atribuidos deben incorporarse desde la versión oficial, sin transcripción inventada y con
la revisión de licencia/atribución correspondiente.

## Criterio de aceptación

1. Los formularios deben pasar `validate_ampath_forms.py`.
2. Las reglas clínicas deben pasar `validate_ocl_exports.py`.
3. Una futura digitalización completa no puede publicarse hasta que todos los UUIDs resuelvan en el ZIP OCL
   oficial y los `Q-AND-A` coincidan con las respuestas declaradas por el formulario.
4. Debe probarse en OpenMRS la persistencia de un caso normal y uno de riesgo por formulario.
