# Revisión semántica acotada de CRED

Revisión de CRED-001, CRED-002, CRED-003 y CRED-005 con datos sintéticos y
lectura de metadata.

## Fuentes primarias

- [RM 682-2025/MINSA](https://busquedas.elperuano.pe/dispositivo/NL/2447144-1),
  artículos 1 y 2: aprueba NTS 238 y deroga las resoluciones de NTS 137 y su
  modificatoria. Se conserva la procedencia histórica de los formularios.
- [NTS 238, edición MINSA 2026](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf),
  numerales 6.8.2 y 6.8.4: consejería y entrega de suplementos conforme a la
  normativa aplicable; el control no determina por sí mismo una pauta universal.
- [RM 251-2024/MINSA](https://busquedas.elperuano.pe/dispositivo/NL/2277624-1):
  aprueba NTS 213 para prevención y control de anemia.
- [RM 429-2024/MINSA](https://bvs.minsa.gob.pe/local/fi-admin/RM-429-2024-minsa.pdf),
  subnumeral 6.1.1.B, tabla 8, página 7 del PDF, revisada visualmente: distingue
  dosis y duración preventiva por edad; para MMN de 24 a 59 meses indica dos
  sobres, con duración diferente entre 24–35 y 36–59 meses. No sustenta una
  instrucción universal de un sobre diario desde los seis meses.
- [RM 055-2016/MINSA](https://www.gob.pe/institucion/minsa/normas-legales/192708-055-2016-minsa):
  identifica la Directiva 068 como origen del formulario de suplementación.
  Esta revisión no afirma su derogación expresa.

## Correcciones de presentación

| Archivo | Antes | Después y alcance |
| --- | --- | --- |
| CRED-001 | Sección «Tratamiento Indicado» con cantidad de sobres MMN y observaciones. | «Entrega de micronutrientes»: describe lo efectivamente registrado, una entrega, no un tratamiento prescrito ni completado. |
| CRED-002 | Descripción atribuida solamente a Directiva 068. | Conserva el origen Directiva 068 y distingue el marco actual NTS 213, modificado por RM 429. |
| CRED-003 y CRED-005 | Descripciones «según NTS 137». | Conservan NTS 137 como origen e identifican NTS 238/RM 682 como marco CRED actual. |

Los cuatro JSON conservan nombre, versión, UUID, conceptos, respuestas,
validadores, obligatoriedad, mediciones y expresiones.

## Semántica y reutilización verificadas

El export canónico incluido `10_SIHSALUS_sihsalus_concepts_2026-09-09-1.zip`
identifica `f0000007-0000-4000-8000-000000000007` como **Puntaje SIH.SALUS**,
`f0000002-0000-4000-8000-000000000002` como **Notas clínicas SIH.SALUS** y
`f0000003-0000-4000-8000-000000000003` como **Plan de manejo SIH.SALUS**.
El motor `@sihsalus/esm-form-engine-lib` 4.1.0 conserva la identidad de cada campo
mediante `formFieldNamespace: rfe-forms` y `formFieldPath: rfe-forms-${field.id}`:
`constructObs` y `editObs` los escriben; `findObsByFormField` prioriza la identidad
y el concepto al reabrir. Compartir un concepto sin `obsGroup` no implica por sí
mismo pérdida de la distinción. La lectura del encuentro pide ambos campos.

| Formulario | Captura comprobada | Pendiente |
| --- | --- | --- |
| CRED-013 | `dosisUi` usa el concepto Puntaje para dosis de vitamina A. | Buscar una dosis canónica con unidad UI y definir la transición compatible. La identidad del campo no convierte un puntaje en una dosis. `lote` y `observaciones` comparten Notas clínicas con IDs distintos: su repetición no basta para exigir conceptos nuevos. |
| CRED-014 | `pielFaneras`, `cabezaCuello`, `ojosOidosNarizGarganta`, `toraxCardiorespiratorio`, `abdomen`, `genitourinario`, `osteomuscular`, `neurologico` y `hallazgosRelevantes` usan Notas clínicas con IDs distintos. | Reutilización compatible con la identidad nativa de campos. Conservar los UUID; comprobar la persistencia y reapertura en el backend desplegado, sin inferir un defecto por repetición del concepto. |
| CRED-022 | `temasTratados`, `acuerdosFamilia`, `practicasPriorizadas` y `fechaProximoControl` usan Plan de manejo con IDs distintos. | Reutilización compatible con la identidad nativa de campos. El próximo control sigue siendo texto de indicación, no fecha estructurada. No requiere una migración sólo por compartir concepto. |
| CRED-011 | PHQ-9/AUDIT-C del cuidador y PSC/PPSC del niño comparten instrumento, puntaje y resultado en la atención del paciente CRED. No existe un campo estructurado que identifique al sujeto evaluado; observaciones sólo pide quién respondió para PSC/PPSC. | Definir el sujeto clínico y su relación con el niño; reutilizar la relación madre/niño canónica y persistir el resultado en el sujeto correcto. No deducir que el cuidador es la madre ni que el puntaje pertenece al niño por el encounter. |

Los registros históricos sin `formFieldPath` conservan el fallback por concepto;
no se han revisado datos reales. La dosis de vitamina A y el sujeto evaluado en
CRED-011 requieren revisión terminológica/clínica; no se resuelven renombrando
conceptos generales ni reinterpretando observaciones históricas.

Siguen pendientes la Hb ajustada trazable, la periodicidad completa de tamizaje,
la transición antropométrica de 60/61 meses y la edad/flujo de aplicación de
M-CHAT-R/F.
