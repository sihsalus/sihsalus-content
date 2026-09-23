# Auditoría y cableado de instrumentos de desarrollo SIHSALUS - 2026-07-09

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

## Alcance

Se auditó y corrigió la cobertura terminológica y funcional del Test Peruano de Evaluación del Desarrollo del
Niño (TPED), junto con los instrumentos de desarrollo de la NTS N.° 238, en el source OCL
`SIHSALUS/sihsalus` y en los formularios AMPATH del content package.

La línea base fue la release `2026-06-30-02`. El resultado se publicó inicialmente en OCL como `2026-07-09-01`;
el bundle final usa la release acumulativa `2026-07-09-02`, que conserva este cableado y agrega la terminología
de procedimientos O3.

Fuentes normativas revisadas:

- [NTS N.° 238-MINSA/DGIESP-2025](https://www.gob.pe/institucion/minsa/informes-publicaciones/7857089-norma-tecnica-de-salud-para-el-control-de-crecimiento-y-desarrollo-del-nino-nts-n-238-minsa-dgiesp-2025),
  aprobada por la [RM N.° 682-2025-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/7281593-682-2025-minsa).
- NTS N.° 137-MINSA/2017/DGIESP, que contiene la descripción y lámina histórica del TPED en su Anexo N.° 18.

## Decisión funcional adoptada

Se mantienen habilitados EEDP, TEPSI y TPED como instrumentos legados para continuidad clínica e histórica.
No se presentan como exigencias de la NTS N.° 238.

También permanecen habilitados los instrumentos vigentes:

- `Test de Vigilancia del Neurodesarrollo (Huanca Test)` hasta los 36 meses.
- `Prueba de Evaluación del Desarrollo Infantil (EDI)` entre 1 y 60 meses.
- `Lista de Habilidades y Conductas Esperadas por Edad` desde los 4 hasta los 11 años, 11 meses y 29 días.
- `M-CHAT-R/F versión peruana` para detección de riesgo de TEA.

## Resultado ejecutivo

La brecha terminológica del TPED quedó resuelta:

- El instrumento `3798` conserva el UUID `c4010013-0000-4000-8000-000000000013`, ahora es `ConvSet / N/A` y
  su nombre preferido es `Test Peruano de Evaluación del Desarrollo del Niño (TPED)`.
- `Test abreviado peruano (TA)` se conserva como alias histórico.
- Las 12 líneas se reclasificaron como `Question / Coded`.
- Los 89 hitos quedaron normalizados como respuestas `Misc / N/A`.
- Se crearon 89 mappings `Q-AND-A`, uno por cada hito.
- Se crearon 14 mappings `CONCEPT-SET`: 12 líneas, resultado global y fuente de evaluación.
- Cada hito incluye metadata `tped_line` y `tped_order`.
- Se agregó `CRED-028-TPED`, con 12 preguntas estructuradas y exactamente 89 respuestas posibles, para guardar el
  mayor hito alcanzado por cada línea.

La release final contiene 4 459 conceptos, 5 635 mappings totales y 5 602 mappings activos. De los mappings
incorporados en `2026-07-09-01`, 103 corresponden directamente al TPED.

## Cobertura TPED por línea

| Línea | ID OCL | Nombre | Hitos | Estado |
| --- | ---: | --- | ---: | --- |
| A | `90` | Control de cabeza y tronco sentado | 5 | `Question/Coded`, cableado |
| B | `96` | Control de cabeza y tronco rotaciones | 3 | `Question/Coded`, cableado |
| C | `100` | Control de cabeza y tronco de marcha | 6 | `Question/Coded`, cableado |
| D | `109` | Uso de brazo y mano | 11 | `Question/Coded`, cableado |
| E | `141` | Visión | 3 | `Question/Coded`, cableado |
| F | `145` | Audición | 3 | `Question/Coded`, cableado |
| G | `149` | Lenguaje comprensivo | 9 | `Question/Coded`, cableado |
| H | `159` | Lenguaje expresivo | 8 | `Question/Coded`, cableado |
| I | `168` | Comportamiento social | 11 | `Question/Coded`, cableado |
| J | `180` | Alimentación, vestido e higiene | 9 | `Question/Coded`, cableado |
| K | `190` | Juego | 10 | `Question/Coded`, cableado |
| L | `201` | Inteligencia y aprendizaje | 11 | `Question/Coded`, cableado |
| **Total** |  | **12 líneas** | **89** | **Completo** |

El concepto `102 - Tremores` no pertenece a los 89 hitos TPED y no fue conectado a la línea C.

## Curación terminológica TPED

Se corrigieron los nombres preferidos de los conceptos `155`, `156`, `157`, `158`, `162` y `211`, incluyendo
tildes, puntuación y errores de transcripción. El concepto `187 - Avisa sus necesidades` se normalizó de
`Question / N/A` a `Misc / N/A` para que tenga el mismo rol que los otros hitos.

## Instrumentos de la NTS N.° 238

Los conceptos de instrumento se reutilizaron como raíces `ConvSet`, sin cambiar sus UUID clínicos:

| Instrumento | ID OCL | Mappings `CONCEPT-SET` | Formulario |
| --- | ---: | ---: | --- |
| Huanca Test | `1070` | 29 | `CRED-026` |
| Lista de Habilidades y Conductas | `1071` | 22 | `CRED-027` |
| EDI | `4167` | 3 | `CRED-009` |
| M-CHAT-R/F | `4168` | 4 | `CRED-010` |

También se corrigió lo siguiente:

- Huanca usa la etiqueta `Pauta 30 a 36 meses` y distingue `Desarrollo esperado` de los hallazgos positivos por
  uno o por dos o más hitos no logrados.
- EDI dejó de reutilizar el concepto genérico que contenía mappings de ESAVI. Ahora tiene una pregunta propia y
  respuestas `Verde`, `Amarillo` y `Rojo`.
- El tamizaje genérico de TEA se identificó como `M-CHAT-R/F versión peruana`, con puntaje de 0 a 20 y resultados
  `Bajo riesgo`, `Riesgo moderado` y `Riesgo alto`.
- `CRED-004` conserva los siete instrumentos y distingue explícitamente cuáles son vigentes y cuáles legados.

## Límite funcional explícito

El cableado implementado estructura los registros que actualmente existen en el repositorio. No convierte los
formularios resumidos en reproducciones completas de todos los ítems oficiales:

- `CRED-009` registra la clasificación global EDI; no contiene todavía todos los ítems de sus cinco ejes.
- `CRED-010` registra puntaje y riesgo M-CHAT-R/F; no contiene el cuestionario oficial de 20 preguntas.
- `CRED-026` registra conteos y detalle por área Huanca; no registra cada hito como una observación independiente.
- `CRED-027` registra ausencia y detalle por área; no registra individualmente todas las habilidades por edad.

Estas limitaciones están declaradas en las descripciones de los formularios para evitar presentar un resumen como
si fuera la aplicación clínica completa del instrumento. El TPED sí quedó estructurado a nivel de sus 12 líneas y
89 hitos existentes.

## Validación automatizada

`.github/scripts/validate_ocl_exports.py` ahora verifica:

- cinco instrumentos `ConvSet` con nombres preferidos esperados;
- 12 líneas TPED, 89 hitos únicos, metadata de línea/orden y cardinalidad exacta de cada `Q-AND-A`;
- membresía exacta de los cinco sets de instrumentos;
- respuestas normativas de EDI y M-CHAT-R/F;
- resolución de UUID y cobertura `Q-AND-A` de `CRED-009`, `CRED-010` y `CRED-028`;
- 12 preguntas y 89 respuestas en el formulario TPED.
