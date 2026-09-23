# CRED: contratos clínicos y dependencias pendientes

Estado comprobado el **23 de septiembre de 2026, 08:17 (America/Lima)**.
Los cambios de curvas y alta neonatal están integrados en `main`; la publicación,
el despliegue y la aceptación clínica se verifican por separado.

## Integración y alcance

| Componente | Cambio integrado | Revisión de integración |
| --- | --- | --- |
| Frontend | [PR #1093](https://github.com/sihsalus/sihsalus-frontend/pull/1093): curvas escolares y primer control neonatal desde el alta. | `84f371aecd9146a88f852e58c6de7ec887c15818` |
| Content | [PR #240](https://github.com/sihsalus/sihsalus-content/pull/240): advertencia de Hb desde 500 m y captura hasta 5500 m en CRED-001 1.2.1. | `28c205d080502f66ce4e2ad1212677f2ff2951e2` |
| Content | [PR #241](https://github.com/sihsalus/sihsalus-content/pull/241): alta neonatal opcional, contrato CRED y versión del paquete 1.25.26. | `931a8a222855e7227b686253d204edf02c3de372` |

La revisión documental usa frontend `37e678e16` y content `c840f35`. Este último
incluye también el [PR #242](https://github.com/sihsalus/sihsalus-content/pull/242),
que evalúa los rangos de hemoglobina con la edad a la fecha de la muestra. Esa
selección de rangos no calcula ni persiste Hb ajustada por altitud; su contrato
pertenece a [laboratorio](laboratory-reporting.md).

Las curvas escolares reutilizan el gráfico Carbon existente y las tablas OMS 2007
para ambos sexos, entre 61 y 228 meses. El IMC exige peso y talla positivos de la
misma atención. No se extrapola al mes 60 ni se persisten z o clasificaciones;
la [procedencia de los datos y el cálculo LMS](https://github.com/sihsalus/sihsalus-frontend/blob/main/packages/apps/esm-crecimiento-desarrollo-app/src/ui/growth-chart/data-sets/WhoReference2007/README.md)
se mantienen en el componente responsable.

El contexto del alta se consulta para el primer control cuando el paciente tiene
menos de 29 días. Un parto institucional exige alta válida y un mínimo exacto de
48 horas; una lectura incompleta o fallida no habilita el control. El segundo
control incluye el día 14 y conserva siete días mínimos desde el control anterior.
La reanudación del mismo control conserva su número. La notificación de parto
extrainstitucional y los registros retrospectivos siguen pendientes en #98.

## Evidencia disponible

Esta tabla conserva el SHA y alcance de las pruebas ejecutadas. No acredita una
nueva ejecución sobre merges posteriores ni sustituye el ensayo con el backend
desplegado. Los estados de CI corresponden a la consulta fechada arriba.

| Estado | Comprobación | Revisión y resultado |
| --- | --- | --- |
| PASSED | Frontend: `yarn verify:changed --base origin/main --head HEAD` | `0ce17cb9b`: 47/47 tareas, 43 de caché; CRED ejecutó 290/290 pruebas en 36 archivos, lint, TypeScript y build. |
| PASSED | Chromium local con datos sintéticos | Componentes de `0ce17cb9b`: 12/12 casos de idioma, sexo y tamaño; IMC/talla, percentiles/z, sin errores JavaScript ni desbordamiento. Backend y permisos simulados; no prueba persistencia. |
| PASSED | CI del [PR frontend #1093](https://github.com/sihsalus/sihsalus-frontend/pull/1093/checks) | Checks técnicos correctos en `0ce17cb9b`; `e2e`, `candidate-quality` y `publish-candidate` omitidos. |
| PASSED | Content: validadores Python, unittest y comprobaciones shell | `906455c`: 112 formularios, 3673 referencias, 130/130 pruebas; sin regresiones sobre las 128 incidencias conocidas de integridad de conceptos. |
| PASSED | Expresiones del formulario: `npm test --prefix .github/integration/form-expressions` | `906455c`: 4/4 casos en America/Lima y 4/4 en America/New_York. Incluye límites de altitud heredados de #240. |
| PASSED | `mvn clean verify --batch-mode --file pom.xml` | `906455c`: ZIP local 1.25.26 validado; no demuestra publicación en Maven Central. |
| NOT RUN | Integración/publicación completa de content 1.25.26 | El [run del merge #241](https://github.com/sihsalus/sihsalus-content/actions/runs/35863976842) fue cancelado. El [run de `c840f35`](https://github.com/sihsalus/sihsalus-content/actions/runs/35864758036) estaba pendiente; no consta resultado final en esta revisión. |
| BLOCKED | Conceptos contra servidor y E2E con rol operativo en QLTY | Sin sesión clínica de prueba ni versión desplegada coordinadas para esta iteración. Guardar, recargar, editar y comprobar permisos sigue pendiente. |
| BLOCKED | Aceptación clínica y digitalización completa | Faltan terminología OCL, versiones aprobadas de instrumentos, acreditación del permiso M-CHAT y revisión funcional. |

Los logs y doce capturas del ensayo local se conservaron en
`Scratch/sihsalus-backlog-production-20260921/cred-clinical-visual/`; esa ruta del
workspace no es un artefacto publicado en GitHub. Los PR registran los comandos y
las advertencias de lint/build. No se utilizó Docker local ni se crearon pacientes
externos en esta iteración.

## Cambios de contenido

`(CRED) Detalles de Nacimiento` incorpora una observación opcional de fecha y hora de
alta del recién nacido. Reutiliza `Fecha de alta` de OCL, UUID
`e911fe60-6d45-40c7-8d65-1ab93b3c77f4`, datatype `Datetime`. Su contexto es el
formulario de nacimiento del paciente, no el alta de la madre ni una hospitalización
posterior. El lugar del parto conserva su única captura en `(CRED) Embarazo y Parto`.

Se conserva la identidad nombre/versión `1.2`, el tipo de encuentro perinatal y todos
los campos anteriores. La adición es opcional y no modifica observaciones históricas.
Initializer actualiza el esquema por su mecanismo AMPATH existente; no se añade SQL,
un segundo formulario publicado con el mismo nombre ni un nuevo loader. En QLTY se
debe comprobar que una atención antigua siga abriendo y que el nuevo dato se pueda
guardar, recargar y corregir sin crear otra atención. El frontend requiere desplegar
primero este contenido para poder completar un alta ausente.

`CRED-001` conserva la hemoglobina medida y la clasificación confirmada por el
profesional. La versión `1.2.1`, incorporada por el [PR #240](https://github.com/sihsalus/sihsalus-content/pull/240),
ya incluye 500 m en la advertencia y admite captura hasta 5500 m,
de acuerdo con la tabla 1 de la [RM 429-2024/MINSA](https://bvs.minsa.gob.pe/local/fi-admin/RM-429-2024-minsa.pdf).
No calcula ni persiste todavía hemoglobina ajustada.

## Estado por issue al 23/09/2026

| Issue | Resultado de esta revisión | Pendiente para cerrar |
| --- | --- | --- |
| [58](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/58) | Frontend incorpora IMC/edad y talla/edad OMS 2007, con cálculo LMS para la interpretación del gráfico. | Publicar conceptos por indicador y persistir resultado, clasificación, referencia y mediciones fuente; aceptación clínica. |
| [98](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/98) | Fecha de alta reutilizable; frontend aplica 48 horas para el primer control institucional y admite el día 14 en la ventana del segundo. | QLTY, captación tardía y registro retrospectivo; concepto y captura de notificación de nacimiento extrainstitucional. |
| [99](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/99) | Revisada la tabla vigente y conservada la corrección de captura/advertencia del PR #240. Hb medida preservada. | Terminología de factor/Hb ajustada y cálculo/persistencia en el componente clínico backend. |
| [93](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/93) | EDI (`CRED-009`) sigue siendo transcripción resumida de cinco ejes, no una aplicación por ítems. | Conceptos individuales, versión clínica aprobada, reglas completas y prueba normal/rezago/riesgo. |
| [94](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/94) | Huanca (`CRED-026`) sigue guardando áreas y detalles; no cada hito por edad. | Conceptos por hito, versión adaptada aprobada y prueba de cada pauta. |
| [96](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/96) | M-CHAT (`CRED-010`) conserva puntaje y resumen; no incluye veinte preguntas ni entrevista R/F. | Permiso de distribución, conceptos por ítem/seguimiento y validación del flujo de dos etapas. |

Los seis issues permanecen abiertos hasta satisfacer su alcance completo. No se
publicaron conceptos OCL ni se alteraron sus ZIP. Se solicitó la ubicación del acceso
autorizado a OCL y la documentación de las versiones/permiso al responsable del proyecto.

## Terminología a preparar en la fuente canónica

El inventario de `configuration/ocl/*concepts*.zip` no contiene conceptos específicos
para estos resultados. No sustituirlos por el concepto de Hb medida, un resultado
nutricional genérico repetido o un UUID inventado en el formulario.

| Dato | Tipo / unidad | Semántica y revisión requerida |
| --- | --- | --- |
| Corrección de hemoglobina por altitud | Numeric, g/dL | Cantidad restada; conservar altitud aplicable, método/tabla y versión. |
| Hemoglobina ajustada por altitud | Numeric, g/dL | Resultado separado de la medición original y ligado a ella. |
| Puntaje z de P/E, T/E, P/T, IMC/E y PC/E | Un Numeric por indicador, sin unidad | Identificador propio por indicador; conservar sexo, edad al medir, referencia y mediciones fuente. |
| Clasificación de cada indicador | Un Coded por indicador | Respuestas compatibles con edad/referencia; no reutilizar indiscriminadamente la clasificación global. |
| Notificación del nacimiento extrainstitucional | Datetime | Fecha de conocimiento del nacimiento, diferente de fecha de nacimiento y de atención. |
| Ítems EDI | Coded por ítem | Mantener código oficial, grupo de edad, eje, observación/pregunta y respuestas completas. |
| Hitos Huanca | Coded por hito | Mantener pauta, área y método de constatación de la adaptación aprobada. |
| Ítems y seguimiento M-CHAT-R/F | Coded por ítem y decisión de seguimiento | Conservar orden, versión, respuestas iniciales, segunda etapa y resultado final diferenciado. |

Antes de asignar UUIDs, el mantenedor de OCL debe buscar equivalencias en HEAD,
reutilizar las existentes y publicar una versión/export oficial con los Q-AND-A.
El paquete debe consumir ese export mediante su procedimiento vigente. La lógica
clínica y la validación de resultados derivados pertenecen al backend responsable;
no se añadirá una segunda regla en SQL, un script de carga o un cálculo AMPATH
para suplir su ausencia. La interpretación de una curva en frontend no acredita
persistencia ni un diagnóstico clínico.

## Siguiente iteración y aceptación en QLTY

1. El mantenedor de OCL debe localizar equivalencias en la fuente canónica y
   publicar los conceptos ausentes con su export. El responsable funcional CRED
   (Gonzalo, según los issues) debe confirmar las versiones de EDI/Huanca y la
   autorización/versionado de M-CHAT-R/F. No hay cuentas GitHub asignadas por inferencia.
2. Con esa terminología, implementar resultados derivados en el backend
   responsable y captura declarativa de instrumentos en content. Conservar la Hb
   original, procedencia de mediciones, referencia, respuestas y resultados de cada
   etapa. La corrección del aviso de altitud no satisface #99.
3. Coordinar en QLTY una versión de content que incluya el campo de alta antes de
   activar el frontend dependiente. Registrar SHA de frontend, versión de content,
   backend/módulos, perfil operativo y paciente sintético. Verificar apertura de
   una atención histórica, guardado, recarga y edición sin duplicar el control.
4. Ejecutar los casos clínicos siguientes y registrar resultado, aprobación
   funcional y limpieza de datos sintéticos. Cerrar cada issue cuando cumpla su
   alcance completo; un merge o un CI técnico correcto no cubre esa aceptación.

## Fuentes y casos de aceptación

- [NTS 238, publicación MINSA de marzo de 2026](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf): numeral 6.4 para controles; anexo 10 para desarrollo. Identifica EDI, segunda edición 2021 de CeNSIA, y la adaptación de Huanca 2023.
- [OMS: cálculo de z y percentiles 2007](https://cdn.who.int/media/docs/default-source/child-growth/growth-reference-5-19-years/computation.pdf): casos de IMC de varones de 11, 16 y 9 años; las pruebas numéricas contrastan resultados publicados con tolerancia de 0.01 por redondeo de los ejemplos.
- [Permisos M-CHAT-R/F](https://mchatscreen.com/wp-content/uploads/2015/09/M-CHAT-R_F_NoShade_Aug2018.pdf): distribuir el cuestionario en software requiere permiso; el acceso público al PDF no acredita ese permiso para SIHSalus. No se contactó a terceros.

En QLTY, con pacientes sintéticos y rol operativo: alta institucional normal y
tardía, 47 h 59 min y 48 h desde el alta, segundo control en día 14, falta de
alta/lugar, parto domiciliario, datos históricos sin los nuevos campos, error de
una página REST y recuperación. Para anemia: bordes de cada intervalo de altitud,
medición original inalterada, edición que recalcula el resultado derivado y ausencia
de clasificación ante edad/altitud incompletas. Para crecimiento: ambos sexos,
frontera de referencias, extremos y ausencia de mediciones compatibles. La captura
íntegra y las decisiones de cada instrumento deben contrastarse con su manual y el
responsable funcional CRED (Gonzalo, según los issues), sin sustituir ese visto bueno
por CI.
