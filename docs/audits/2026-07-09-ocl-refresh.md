# Auditoria OCL - 2026-07-09

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

## Alcance

Se revisaron las versiones publicadas de los sources OCL de la organizacion `SIHSALUS` usadas por el content package y se regeneraron los ZIPs bundleados desde los exports vigentes. El repositorio mantiene los exports separados por orden de carga: primero conceptos (`00` a `14`) y luego mappings (`50` a `64`).

## Versiones publicadas vigentes

| Source | Version | Conceptos | Mappings |
| --- | --- | ---: | ---: |
| `medicamentos` | `2026-06-30` | 1001 | 17 |
| `procedimientos` | `2026-06-30` | 12311 | 12331 |
| `diagnosis` | `2026-06-30` | 13484 | 0 |
| `laboratorio` | `2026-06-30` | 212 | 1044 |
| `inmunizaciones` | `2026-06-30` | 22 | 60 |
| `prestacionales` | `2026-06-30` | 66 | 65 |
| `geografia` | `2026-06-30` | 196 | 364 |
| `etnias` | `2026-06-30` | 62 | 64 |
| `seguros` | `2026-06-30` | 14 | 20 |
| `religiones` | `2026-06-30` | 12 | 24 |
| `sihsalus` | `2026-07-09-02` | 4459 | 5635 |
| `lenguas` | `2026-06-30-02` | 63 | 121 |
| `ocupaciones` | `2026-07-09-01` | 448 | 447 |
| `estado-civil` | `2026-06-30` | 6 | 8 |
| `educacion` | `2026-06-30` | 12 | 13 |

Total bundleado: 32368 conceptos OCL.

## ZIPs refrescados

Solo se reemplazaron los ZIPs con diferencias reales de contenido, ignorando cambios triviales de `export_time`:

- `01_SIHSALUS_procedimientos_concepts_2026-06-30.zip`
- `51_SIHSALUS_procedimientos_mappings_2026-06-30.zip`
- `03_SIHSALUS_laboratorio_concepts_2026-06-30.zip`
- `53_SIHSALUS_laboratorio_mappings_2026-06-30.zip`
- `56_SIHSALUS_geografia_mappings_2026-06-30.zip`
- `10_SIHSALUS_sihsalus_concepts_2026-07-09-02.zip`
- `60_SIHSALUS_sihsalus_mappings_2026-07-09-02.zip`
- `61_SIHSALUS_lenguas_mappings_2026-06-30-02.zip`
- `12_SIHSALUS_ocupaciones_concepts_2026-07-09-01.zip`
- `62_SIHSALUS_ocupaciones_mappings_2026-07-09-01.zip`

### Correccion de ocupaciones

El primer refresh encontro que tanto HEAD como la release `2026-06-30-02` de `ocupaciones` contenian solo
12 conceptos y 11 mappings: el agrupador, los 10 grandes grupos, una opcion retirada y las relaciones base. El ZIP
granular que habia estado bundleado localmente no provenia del estado publicado en OCL y sus 436 nombres marcados
como `es` conservaban el texto en ingles.

Se reconstruyo el catalogo remoto con la estructura oficial
[CIUO-08 en espanol de la OIT](https://webapps.ilo.org/public/spanish/bureau/stat/isco/isco08/) y se publico la
release `2026-07-09-01`:

- 436 grupos unitarios de cuatro digitos, desde `0110` hasta `9629`.
- Un nombre preferido oficial en `es`, el nombre ISCO-08 en `en` y el codigo como nombre corto para cada grupo.
- 436 mappings `CONCEPT-SET` directos desde `Ocupaciones CIUO-08`, ademas de los 11 mappings base.
- UUIDs OpenMRS de conceptos, nombres, descripciones y mappings preservados desde el export granular anterior.

El resultado publicado y bundleado contiene 448 conceptos (447 activos y uno retirado) y 447 mappings activos.

### Terminología de procedimientos O3

Se incorporó el set `CIEL 170800 - Procedure status` con su UUID OpenMRS canónico, ocho respuestas locales con
UUIDs CIEL/OpenMRS, nombres preferidos en español y mappings `Q-AND-A` ordenados. También se completó
`CIEL 1732 - Duration units`: sus ocho miembros usan ahora UUIDs canónicos y mappings `CONCEPT-SET` con el orden
oficial. El detalle de localización y las colisiones controladas se documenta en
[`2026-07-09-procedure-status-duration-units.md`](2026-07-09-procedure-status-duration-units.md).

## Cobertura de formularios

Se cruzaron 111 formularios AMPATH contra los conceptos bundleados en OCL:

- Referencias unicas de conceptos en formularios: 1839.
- Referencias sin concepto bundleado: 0.

## Cobertura de nombres en espanol

Conceptos activos revisados: 32365.

No quedan conceptos activos sin al menos un nombre en locale `es`. El concepto `4306 - Fetal lie`, señalado en
la primera pasada de la auditoría, llegó retirado en la release `sihsalus/2026-07-09-02` y ya no constituye una
brecha activa del bundle.
