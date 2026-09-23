# CRED: contratos clínicos y dependencias pendientes

Revisión del 23 de septiembre de 2026 sobre content `a54fde1` y frontend `41926436d`.
Esta revisión y sus pruebas locales no constituyen aceptación clínica ni evidencia de QLTY.

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
profesional. Su advertencia incluye ahora 500 m y la captura admite hasta 5500 m,
de acuerdo con la tabla 1 de la [RM 429-2024/MINSA](https://bvs.minsa.gob.pe/local/fi-admin/RM-429-2024-minsa.pdf).
No calcula ni persiste todavía hemoglobina ajustada.

## Estado por issue

| Issue | Resultado de esta revisión | Pendiente para cerrar |
| --- | --- | --- |
| [58](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/58) | Frontend incorpora IMC/edad y talla/edad OMS 2007, con cálculo LMS para la interpretación del gráfico. | Publicar conceptos por indicador y persistir resultado, clasificación, referencia y mediciones fuente; aceptación clínica. |
| [98](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/98) | Fecha de alta reutilizable; frontend aplica 48 horas para el primer control institucional y admite el día 14 en la ventana del segundo. | QLTY, captación tardía y registro retrospectivo; concepto y captura de notificación de nacimiento extrainstitucional. |
| [99](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/99) | Revisada la tabla vigente y corregido el rango de captura/advertencia. Hb medida preservada. | Terminología de factor/Hb ajustada y cálculo/persistencia en el componente clínico backend. |
| [93](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/93) | EDI sigue siendo transcripción resumida de cinco ejes, no una aplicación por ítems. | Conceptos individuales, versión clínica aprobada, reglas completas y prueba normal/rezago/riesgo. |
| [94](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/94) | Huanca sigue guardando áreas y detalles; no cada hito por edad. | Conceptos por hito, versión adaptada aprobada y prueba de cada pauta. |
| [96](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/96) | M-CHAT conserva puntaje y resumen; no incluye veinte preguntas ni entrevista R/F. | Permiso de distribución, conceptos por ítem/seguimiento y validación del flujo de dos etapas. |

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
