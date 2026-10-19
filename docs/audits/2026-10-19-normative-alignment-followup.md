# Seguimiento de alineación normativa y contratos de frontend

Fecha: 19 de octubre de 2026. Esta propuesta parte de `main` y es independiente
del catálogo de especialidades de [PR 271](https://github.com/sihsalus/sihsalus-content/pull/271).
La [revisión anterior](https://github.com/sihsalus/sihsalus-content/blob/10a50ce99ac13174443f3d6fe235af71f5e34751/docs/audits/2026-10-19-content-frontend-normative-review.md)
conserva el inventario y la evidencia de los once hallazgos.

## Estado de los hallazgos

«Implementado» describe el cambio propuesto; sigue pendiente su aceptación
clínica e integrada. No significa despliegue ni conformidad normativa integral.

| Hallazgo | Cambio y componente responsable | Pendiente |
| --- | --- | --- |
| 1. Inmunizaciones: conceptos e identidad de Form | Frontend reutiliza conceptos de estado/motivo/contexto de INMU-001 y resolver estricto compartido por nombre/versión; conserva lectura multiversión. Content INMU-001 `1.1.0` separa administración y registro. | Smoke de persistencia/reapertura y rechazo FHIR real. |
| 2. Sujeto y edad del tamizaje mental | Frontend CRED separa PPSC/PSC infantil de la guía para evaluar al adulto identificado. Reutiliza búsqueda de paciente y vínculo nativo sin presumir quién es el cuidador. | Aceptación de flujo con niño y cuidador sintéticos; no automatiza la periodicidad sobre la historia adulta. |
| 3. Gráficas 60–61 meses | Frontend añade las cuatro filas oficiales de mes 60 de OMS AnthroPlus y preserva filas 61–228. | Aceptación clínica de visualización y referencia. |
| 4. Vitamina A | CRED-013 `1.1.0` usa concepto Numeric/UI local nativo, único y verificado contra bundle/HEAD. Conserva Puntaje histórico. | Ensayo nativo fresh/upgrade y aceptación clínica. |
| 5. Prioridad de referencia | CRED-024 `1.1.0` reutiliza `sihsalus:265` y cuatro respuestas Q-AND-A publicadas. | Ensayo nativo y captura clínica. |
| 6. Proveedor de agenda | Frontend aplica off/warn/strict de forma coherente en selección y guardado, incluidos servicios sin categoría. | Smoke con roster y roles operativos. |
| 7. Vitals y roles | Frontend usa tipo/rol longitudinal canónicos, perfil de emergencia específico y preserva payloads offline antiguos. | Triaje ambulatorio conserva contrato histórico y requiere decisión separada; smoke offline y autorización. |
| 8. Calendario y UUID | Frontend usa productos OCL existentes y fechas por meses calendario en el mecanismo actual, con pautas verificadas y sin universalizar grupos especiales. | Validación clínica de pautas y transición NTS 246 completa. |
| 9. Hexavalente/meningococo | [Curación revisable](../terminology/README.md) preparada en formato nativo OCL. HEAD no contiene equivalentes. | **Abierto:** formulación/serogrupos, aprobación, importación/publicación y exports oficiales; no se duplicó el catálogo en CSV ni se habilitaron UUIDs inexistentes. |
| 10. ESAVI | Frontend reutiliza resolver estricto y envía visita, ubicación y proveedor/rol explícitos; distingue fecha/hora de reporte del inicio clínico narrado. | Smoke y notificación epidemiológica oficial fuera de este registro. |
| 11. Referencias normativas impropias | Content corrige citas demostrablemente impropias y deja descripciones neutrales donde no se verificó una norma específica. CE-001 `1.0.4` preserva el JSON anterior. | Revisión clínica de metadata; el tipo mixto histórico queda intacto por compatibilidad. |

## Diseño y compatibilidad

Content declara metadata con Initializer: no hay migraciones SQL nuevas ni
cambios a Liquibase publicado. Se conservan UUIDs JSON, nombres y campos de
formularios; las versiones nuevas conservan los esquemas previos y evitan
sobrescribir su historia. El ensayo nativo existente incorpora CRED-013,
CRED-024 e INMU-001 a la comprobación de esquemas e historia y comprueba en
fresh/upgrade/reinicio el datatype y la unidad de vitamina A.

El nuevo concepto de cantidad administrada vive sólo en
`concepts/clinical_measurements.csv`; la capacidad nativa se verificó en el
pin de Initializer. Los validadores de formulario comparten ahora un índice de
OCL y CSV; no se amplió el loader ni se creó otro validador. La futura
transferencia del concepto a OCL conserva el UUID y retira su fila local en el
mismo cambio. Para vacunas se mantiene el catálogo OCL existente y sus Q-AND-A:
la propuesta JSONL está fuera del paquete operativo hasta aprobar/publicar.

Frontend reutiliza workspace de signos vitales, cola offline, componentes de
relación familiar, selector de formularios y mecanismo de pautas de vacunas.
El resolver de formularios se extrae al paquete compartido ya existente. Las
transacciones y autorización efectiva siguen siendo responsabilidad backend;
los roles de registro no asignan profesiones ni privilegios.

## Fuentes primarias y límites

- [NTS 238, edición MINSA 2026](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf): numerales 6.6.3–6.6.5 y 6.8.4/tabla 4. Refieren derivación, sujetos/edades de tamizaje y dosis expresadas en UI.
- [NTS 246 / RM 561-2026](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa): esquema de inmunizaciones, poblaciones y transición de los anexos 1–2.
- [NTS 139 / RM 214-2018](https://cdn.www.gob.pe/uploads/document/file/187992/187487_R.M_214-2018-MINSA2.pdf20180823-24725-1ufma50.pdf): identidad profesional y veracidad del registro clínico.
- [NTS 105 / RM 827-2013](https://www.gob.pe/institucion/minsa/normas-legales/198935-827-2013-minsa), con sus modificatorias: atención materna.
- [NTS 214 / RM 545-2024](https://www.gob.pe/institucion/minsa/normas-legales/5874349-545-2024-minsa): atención neonatal; sustituye la referencia NTS 106.
- [MINSA: tuberculosis](https://www.gob.pe/combatelatuberculosis): NTS 200 / RM 339-2023.
- [OMS AnthroPlus, revisión `7cfcdb3`](https://github.com/WorldHealthOrganization/anthroplus/tree/7cfcdb39026e9a55de55732bc3cf14c82261bcf7/data-raw/growthstandards): filas LMS de mes 60; sin extrapolación.

Los documentos del paquete y los README del frontend detallan los UUIDs y
campos vigentes. Ninguna descripción de metadata acredita por sí sola la
implementación completa de una norma. Las pruebas locales, CI nativo,
validación clínica y aceptación DEV/QLTY son evidencias diferentes; las dos
últimas siguen pendientes y ambos PR permanecen en draft.
