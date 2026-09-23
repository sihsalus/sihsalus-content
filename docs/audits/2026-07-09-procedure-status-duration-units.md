# Auditoría OCL: estados de procedimiento y unidades de duración

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

- Fecha: 2026-07-09
- Source: `SIHSALUS/sihsalus`
- Release publicada: `2026-07-09-02`

## Fuentes verificadas

- [CIEL 170800 - Procedure status](https://app.openconceptlab.org/#/orgs/CIEL/sources/CIEL/concepts/170800/).
- [CIEL 1732 - Duration units](https://app.openconceptlab.org/#/orgs/CIEL/sources/CIEL/concepts/1732/).
- [openmrs-content-referenceapplication-demo#77](https://github.com/openmrs/openmrs-content-referenceapplication-demo/pull/77), que incorporó `CIEL 170800` al contenido de referencia.
- Export oficial [OpenMRS `procedures` v11](https://github.com/openmrs/openmrs-content-referenceapplication-demo/tree/main/configuration/backend_configuration/ocl), generado desde CIEL el 2026-05-30.
- [API de exports versionados de OCL](https://docs.openconceptlab.org/en/latest/oclapi/apireference/exportapi.html).

La API de CIEL se consultó además con autenticación para contrastar el HEAD vigente con el export `procedures`
v11. No se incorporó `CIEL 167157 - Medication dispense status`, porque corresponde a medicamentos y no a
procedimientos.

## Procedure status

El concepto local `4451` conserva el UUID OpenMRS canónico
`f0d47b45-8303-4cdc-a9f2-c37135a3700f`, clase `Question`, datatype `Coded` y nombre preferido
`Estado del procedimiento`.

| Orden | ID SIHSALUS | CIEL | UUID OpenMRS | Nombre preferido en español |
| ---: | ---: | ---: | --- | --- |
| 1 | 4452 | 167153 | `167153AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Preparación |
| 2 | 4453 | 163723 | `163723AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | En progreso |
| 3 | 4454 | 1118 | `1118AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | No realizado |
| 4 | 4455 | 167154 | `167154AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | En espera |
| 5 | 4456 | 167155 | `167155AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Discontinuado |
| 6 | 4457 | 1267 | `1267AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Completado |
| 7 | 4458 | 162983 | `162983AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Registrado por error |
| 8 | 4459 | 1067 | `1067AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Desconocido (procedimiento) |

Los ocho miembros son `Misc/N/A` en la fuente local y están conectados desde `4451` mediante `Q-AND-A` con
pesos 1 a 8. El concepto principal conserva además un único mapping `NARROWER-THAN` a SNOMED CT `416342005`.

Decisiones de localización y colisiones:

- `En espera` es el nombre preferido; no se importó la frase de dosificación que CIEL marca erróneamente como
  preferida para `167154`.
- `No realizado` y `Completado` concuerdan con el sustantivo “procedimiento”. Los nombres ingleses `Not done` y
  `Completed` se conservaron como sinónimos no preferidos porque SIHSALUS ya tiene conceptos distintos con esos
  fully specified names y OCL prohíbe duplicarlos dentro del mismo source.
- SIHSALUS ya usa `3644 - Desconocido` como respuesta genérica en decenas de sets. Para no cambiar su UUID ni sus
  consumidores, `4459` usa `Desconocido (procedimiento)` como preferido y conserva `Desconocido` como sinónimo.

## Duration units

El concepto local `612` conserva el UUID `1732AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`, se localiza como
`Unidades de duración` y se mantiene como `ConvSet/N/A`, que es la representación consumida por
`order.durationUnitsConceptUuid` en OpenMRS. No se duplicaron los mappings `Q-AND-A` históricos de CIEL: para esta
configuración el contrato operativo es el `CONCEPT-SET`.

| Orden | ID SIHSALUS | CIEL | UUID OpenMRS | Nombre preferido en español |
| ---: | ---: | ---: | --- | --- |
| 0 | 615 | 162583 | `162583AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Segundos |
| 1 | 609 | 1733 | `1733AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Minuto |
| 2 | 603 | 1822 | `1822AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Horas |
| 3 | 610 | 1072 | `1072AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Días |
| 4 | 611 | 1073 | `1073AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Semanas |
| 5 | 613 | 1074 | `1074AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Meses |
| 6 | 608 | 1734 | `1734AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Años |
| 7 | 614 | 162582 | `162582AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | Cantidad de veces |

Los ocho conceptos existentes conservaron sus IDs locales y mappings clínicos previos; se corrigieron siete UUIDs
OpenMRS —`Días` ya era canónico— y se añadió el mapping faltante hacia `614`. No existen referencias en los
formularios del repositorio a los UUIDs locales reemplazados.

## Export y controles

El export oficial de la release contiene 4 459 conceptos (4 457 activos) y 5 635 mappings (5 602 activos). Se
derivaron los artefactos separados requeridos por el orden de carga del content package:

- `10_SIHSALUS_sihsalus_concepts_2026-07-09-02.zip`: 4 459 conceptos y 0 mappings.
- `60_SIHSALUS_sihsalus_mappings_2026-07-09-02.zip`: 0 conceptos y 5 635 mappings.

El validador CI comprueba UUIDs, clases, traducciones preferidas, cardinalidad y orden de ambos sets, el mapping
SNOMED y la exclusión del set de estados de dispensación.
