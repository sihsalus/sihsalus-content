# Revisión del export OCL de laboratorio — 2026-09-12

## Resultado y alcance

La release `SIHSALUS/laboratorio/2026-09-10-3` no puede sustituir todavía a
`2026-07-10-02` como una actualización compatible. Cambia tres datatypes de UUIDs
existentes, la unidad declarada de creatinina urinaria y el límite absoluto de
hemoglobina; también modifica paneles y respuestas. El paquete conserva los dos
ZIPs de laboratorio anteriores mientras se acuerda una actualización coordinada.

Después de esta revisión se aplicaron
[30 correcciones de conceptos y 12 de mappings en HEAD remoto](2026-09-12-ocl-remote-corrections.md).
La release `2026-09-10-3` examinada aquí conserva su contenido; sus hallazgos no
deben confundirse con el estado posterior de HEAD. La actualización completa
del paquete sigue pendiente de las validaciones descritas.

Esta revisión compara metadata y código. No consultó pacientes ni observaciones
de ningún entorno y no afirma que existan observaciones para los conceptos
afectados. La publicación de una release OCL no acredita su compatibilidad con
OpenMRS, los formularios ni los resultados históricos.

Base de contenido: `0c16cae2088b2dad2e135cfae4c50943836bcd3e` (`1.25.18`).
Los ZIPs anteriores se verificaron mediante `git show` de esa base, sin depender
del estado del worktree durante la preparación de la actualización principal.

La revisión normativa posterior de la candidata `1.25.19` está en
[el contrato de captura](../contracts/laboratory-reporting.md).
Corrige cuatro límites inferiores de hemoglobina a 11/10.5 g/dL y añade guardas
de compatibilidad. Los datatypes, unidades, límites altos y selección de población
descritos como pendientes en esta auditoría no quedan aprobados por esas correcciones.

| Archivo examinado | SHA-256 |
| --- | --- |
| `03_SIHSALUS_laboratorio_concepts_2026-07-10-02.zip` | `2cc76abfcfdbc990dcefc135ccdcbe3486a42951bdbfeeb42ef427a068441cb1` |
| `53_SIHSALUS_laboratorio_mappings_2026-07-10-02.zip` | `4ff33281108a69da3ec512ffd0cab54d687ee852ee90eee367118ed13c6e8f96` |
| Export oficial completo `laboratorio-2026-09-10-3.zip` | `4dc28e0033702ae0a21417ea29c59755e37d2b8fd3d00f25d8b1038a63572511` |

La [release candidata](https://api.openconceptlab.org/orgs/SIHSALUS/sources/laboratorio/2026-09-10-3/)
declara `released: true` y fecha de creación `2026-09-10T21:56:58.762423Z`.
Contiene 248 conceptos frente a 212: 36 nuevos y 33 existentes modificados.
Entre estos últimos hay tres cambios de datatype y 14 cambios de `extras`.
Los cambios de nombres también incluyen metadata interna de OCL; el total de
33 no equivale a 33 cambios clínicos de significado.

## Datatypes y formulario incompatible

| OCL | UUID OpenMRS | Concepto | Antes → candidato |
| --- | --- | --- | --- |
| `5286` | `a0d91c80-4e2f-4f12-8007-3a5c40931bf8` | Parásitos microscópicos en heces | `Coded` → `Text` |
| `5282` | `6576cf12-ca50-4234-be46-ac74a4e7814d` | Parásitos adultos en heces | `Coded` → `Text` |
| `2470` | `267b3f53-10ff-498f-a37e-f33b945bd1ce` | Urobilinógeno en orina | `Numeric` → `Coded` |

En Core `2.8.9`, `ConceptServiceImpl.saveConcept` rechaza un cambio de datatype
si el concepto tiene alguna observación, incluidas las anuladas. La única
excepción es `Boolean` → `Coded`, que no aplica aquí. Es un bloqueo condicional
a los datos del destino, no una afirmación sobre su existencia.
[Fuente Core, pin `4dda0f50`](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/api/src/main/java/org/openmrs/api/impl/ConceptServiceImpl.java#L1348).

El importador OCL `3.2.0` usa `ValidationType.FULL` por defecto y llama a
`saveConcept`; una suscripción puede configurar otro modo. Desactivar la
validación no constituye una migración de valores y no resuelve la seguridad de
estos cambios. [Importer](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Importer.java#L343),
[Saver](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java#L114).

Ninguno de los tres UUIDs tiene filas en `conceptreferencerange_laboratory.csv`.
Sin embargo, la pregunta `urobilinogeno` de
[`(Página 4 y 5) Puerperio - Laboratorio.json`](../../configuration/ampathforms/%28P%C3%A1gina%204%20y%205%29%20Puerperio%20-%20Laboratorio.json)
mantiene `rendering: "number"`, `step: 1` y `min: "0"`. El candidato exige una
respuesta conceptual, por lo que el formulario resulta incompatible incluso en
una instalación sin historia. No se encontraron referencias directas de los
otros dos UUIDs en formularios ni en los paquetes y documentación del frontend
revisados; el formulario genérico de laboratorio sí consume el datatype remoto.

Resolución necesaria: definir el contrato de captura y lectura histórica para
cada prueba, coordinar el formulario y comprobar el comportamiento de instalación
nueva y actualización. No se asignan UUIDs nuevos ni se convierten o eliminan
observaciones como parte de esta revisión.

## Unidad, rangos y límites

`laboratorio:5400`, UUID `bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88`, cambia el nombre
y la unidad declarada de `mg/24h` a `mg/kg/24h`. También pasa de valores normales
1000–1500 y absoluto alto 5000 a absoluto alto 40, sin rango normal general.
Esto coincide con las etiquetas y límites de las dos filas de creatinina urinaria
del CSV de PR #225, pero cambia la magnitud representada bajo el mismo UUID.
Si existen valores anteriores, requieren un contrato que preserve su
interpretación; cambiar el nombre o la unidad de la metadata no los convierte.
El [bloqueo previo de PR #225](2026-09-10-laboratory-reference-ranges-pr-225.md)
no queda resuelto solamente por alinear las etiquetas.

`laboratorio:655`, UUID `0ffe780c-a3ee-4c9c-b4dd-bf2e0f79dc7f`, añade
`hi_absolute: 20`. Sus 16 filas del CSV conservan crítico alto 22 y absoluto alto
30. El frontend consultado (`1fc71e13d8f9fae2409ae60b6c194b336dcc9345`) obtiene
`hiAbsolute` directamente del concepto y lo aplica tanto a pruebas individuales
como a miembros de paneles: un resultado mayor de 20 fallaría su validación antes
de guardar, aunque el CSV permita valores hasta 30. Hay que acordar y probar un
contrato consistente, sin elegir un nuevo umbral desde esta auditoría.
[Representación REST](https://github.com/sihsalus/sihsalus-frontend/blob/1fc71e13d8f9fae2409ae60b6c194b336dcc9345/packages/apps/esm-patient-orders-app/src/lab-results/lab-results.resource.ts#L13),
[validación numérica](https://github.com/sihsalus/sihsalus-frontend/blob/1fc71e13d8f9fae2409ae60b6c194b336dcc9345/packages/apps/esm-patient-orders-app/src/lab-results/useLabResultsFormSchema.tsx#L107).

Detalle de los 14 cambios de `extras`. Los valores son los declarados por OCL,
no umbrales clínicamente aprobados. `∅` significa que la propiedad se omite.

| OCL / concepto | Cambio declarado | Filas del CSV relacionadas |
| --- | --- | --- |
| `4245` Creatinina sérica | Absoluto alto 15 → 13 | 2; absoluto 13 coincide |
| `4313` Tiempo de coagulación | Normal ∅ → 3–8; absoluto alto ∅ → 15 | 0 |
| `5259` Albúmina sérica | Normal 3.8–5.1 → 3.5–5.2; absoluto alto 10 → 7 | 0 |
| `655` Hemoglobina | Absoluto alto ∅ → 20 | 16; absoluto 30, crítico 22 |
| `5400` Creatinina urinaria | `mg/24h` → `mg/kg/24h`; absoluto alto 5000 → 40; retira normal 1000–1500 y críticos 0/3000 | 2; ver cambio de magnitud |
| `5269` Leucocitos en orina | Normal alto 4 → 8 | 0 |
| `4239` Proteínas totales séricas | Absoluto alto 15 → 12 | 3; absoluto 12 coincide |
| `4133` Plaquetas | Normal ∅ → 150000–450000; absolutos ∅ → 0–1500000 | 0 |
| `2466` Densidad urinaria | Normal ∅ → 1.005–1.03; absolutos ∅ → 1–1.05; permite decimales | 3; absoluto alto CSV 1.04 y normales por edad |
| `5258` Amilasa urinaria | Retira normal 0–460 y críticos 10/1000; conserva absolutos 0–1500 | 2; rangos por sexo conservados |
| `5360` Glucosa basal | Normal bajo 75 → 74; crítico alto 400 → 300; absoluto alto 600 → 400 | 0 |
| `4151` pH urinario | Normal 4.6–8 → 5–9 | 0 |
| `4232` Colesterol total | Normal alto 190 → 200; absoluto alto 600 → 750 | 0 |
| `5270` Eritrocitos en orina | Normal alto 2 → 1 | 0 |

Los límites generales también sirven a consumidores que no evalúan los criterios
del CSV. Core puede seleccionar un rango por paciente y usa los límites generales
como respaldo al crear la referencia de una observación sin rango aplicable.
La omisión de propiedades, por tanto, también es un cambio efectivo.
[ObsValidator](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/api/src/main/java/org/openmrs/validator/ObsValidator.java#L258).

Hay además un defecto de serialización: `5259`, `5400`, `5258` y `5360` escriben
`Units` con mayúscula; los nuevos numéricos `5449` (hemoglobina glicosilada),
`5450` (PSA) y `5451` (factor reumatoide) hacen lo mismo. `OclConcept.Extras`
declara `units` minúscula e ignora propiedades desconocidas; el importador usa un
`ObjectMapper` estándar. `Saver` copia `getUnits()` y los límites, incluso cuando
son nulos. El texto `Units` no garantiza una unidad persistida y no debe usarse
como evidencia de la unidad real del backend. Los cuatro conceptos existentes ya
tenían esta mayúscula en el export anterior; es un defecto previo que el candidato
conserva, además de introducirlo en tres conceptos nuevos.
[Extras](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/client/OclConcept.java#L328),
[deserialización](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Importer.java#L309),
[copia de metadata](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java#L226).

## Relaciones retiradas y paneles

El export pasa de 1050 a 1214 mappings totales: añade 164 y retira 163 existentes.
Incluye otros 16 mappings nuevos ya retirados, por lo que el candidato tiene 179
retirados y 1035 activos. Comparando aristas activas por tipo y extremos, elimina
160 (144 `CONCEPT-SET`, 16 `Q-AND-A`) y añade 145 (91 y 54, respectivamente).
Tres retiros se compensan con una nueva identidad de mapping para la misma arista;
el recuento neto evita confundirlos con una pérdida de relación.

| Set existente | UUID OpenMRS | Miembros directos antes → candidato |
| --- | --- | --- |
| Ordenabilidad de Pruebas (`4318`) | `020e5471-8750-44f6-82dd-af6d8eb63544` | 112 → 45 |
| Hemograma completo (`4137`) | `24305e8e-f3dc-4ac6-bf87-e4f11f3b970e` | 20 → 11 |
| Examen completo de orina (`4148`) | `7e750f3a-8d5c-45b1-8e94-ebf850208e35` | 4 → 3 |
| Examen Microscópico (`4160`) | `b11ad7b6-260f-4f6c-a41c-c3abe7bcc9af` | 11 → 4 |

Ordenabilidad pierde 73 miembros y gana seis; el candidato crea grupos de
hematología, bioquímica, inmunología, microbiología, coproanálisis y uroanálisis.
Es una reorganización funcional del catálogo. Por ejemplo, el hemograma retira
12 miembros, entre ellos recuentos absolutos y varios índices eritrocitarios,
y añade hemoglobina, plaquetas y observaciones.

Los retiros de respuestas incluyen las seis opciones combinadas de los dos
conceptos de parásitos que pasan a texto. También cambian nitritos, el examen
completo de orina, la prueba de proteínas con ácido sulfosalicílico y cetonuria.
No se detectaron respuestas explícitas de los formularios actuales que quedaran
sin mapping por estos retiros, pero los selectores y paneles dinámicos sí reciben
la composición nueva.

OCL aplica `retired: true` quitando el `ConceptSet` o `ConceptAnswer` identificado
por el UUID del mapping. No exige ausencia de observaciones para quitar esa
relación; la operación no elimina las observaciones históricas. Preservar los
conceptos no preserva por sí solo el panel o las opciones de captura anteriores.
[Set members](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java#L541),
[answers](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java#L584).

Resolución necesaria: aprobar la composición final y comprobar solicitud,
captura y lectura de órdenes previas con los consumidores reales. No basta con
verificar que todos los UUIDs sigan resolviendo.

## Dependencias, validación y siguiente cambio

Siete mappings nuevos dependen de dos conceptos ausentes en la fuente principal
de la base examinada: `SIHSALUS/sihsalus:4489` (seis mappings: `1200`, `1210`,
`1219`, `1224`, `1229`, `1234`) y `4474` (mapping `1081`). Una actualización
posterior de laboratorio debe incluir y verificar esas dependencias en el bundle
completo. Esta dependencia no implica que la actualización independiente de la
fuente principal requiera adoptar laboratorio nuevo.

Comprobaciones ejecutadas mediante scripts temporales en memoria, sin editar los
exports ni conectar un backend:

- **PASSED:** comparación de identidades, datatypes, `extras`, aristas activas y
  referencias directas en formularios/consumidores; SHA de los tres ZIPs registrado
  arriba.
- **PASSED con límite de cobertura:** funciones existentes de
  `validate_ampath_forms.py` sobre el bundle y sobre la sustitución en memoria de
  laboratorio: cero errores de formulario en ambos casos. Ese validador comprueba
  referencias y respuestas, pero no detecta `rendering: number` sobre `Coded`;
  no acredita la compatibilidad de Urobilinógeno.
- **FAILED para laboratorio actualizado de forma aislada:** funciones
  `validate_mapping_integrity` y `validate_default_name_collision_safety` del
  validador OCL existente: siete errores por los dos conceptos externos faltantes;
  sin errores de colisión de nombres en esa comprobación.
- **NOT RUN:** importación funcional de este candidato, actualización con historia
  sintética para los tres datatypes, flujos clínicos y validación de umbrales.

La opción mínima para la actualización actual es conservar laboratorio
`2026-07-10-02` y preparar por separado la corrección y aceptación de los cambios
descritos. Si se publica una release compatible con solo incorporaciones, debe
definir explícitamente sus conceptos y relaciones dependientes, corregir las
unidades serializadas y mantener los contratos existentes. No se deriva aquí un
export híbrido mediante eliminación arbitraria de cambios clínicos.
