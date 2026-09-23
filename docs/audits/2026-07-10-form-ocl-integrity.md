# Auditoría integral de formularios y OCL - 2026-07-10

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

> Nota posterior: las versiones y totales OCL de este documento fueron sustituidos por la
> [auditoría de integridad de importación OCL](2026-07-10-ocl-openmrs-import-integrity.md).

## Alcance

Se auditaron los 111 formularios AMPATH contra todos los exports OCL bundleados. La revisión cubrió resolución
de UUIDs, datatype y clase de cada pregunta, respuestas explícitas frente a sus mappings `Q-AND-A`, conceptos
de agrupación, expresiones, renderers, encounter types y campos calculados de O3.

El resultado se publicó en tres sources con la misma versión:

| Source | Release | Conceptos | Mappings | Activos |
| --- | --- | ---: | ---: | ---: |
| `sihsalus` | `2026-07-10-01` | 4 471 | 5 675 | 4 469 conceptos / 5 628 mappings |
| `seguros` | `2026-07-10-01` | 16 | 22 | 16 conceptos / 22 mappings |
| `laboratorio` | `2026-07-10-01` | 212 | 1 050 | 212 conceptos / 1 050 mappings |

El bundle completo contiene 32 382 conceptos y 20 261 mappings; 32 379 conceptos y 20 214 mappings están
activos.

## Correcciones terminológicas

- `CE-001` usa ahora las preguntas canónicas de `seguros` y `etnias`. Sus respuestas dejaron de apuntar a la
  propia pregunta; SIS, EsSalud, seguro privado, particular y las siete categorías étnicas resuelven a conceptos
  distintos y cableados.
- `INMU-001` dejó de guardar estado, motivo y contexto de inmunización en los conceptos Apetito, Sed y Sueño.
  Se crearon tres preguntas Text propias.
- PPL/PRU, acompañante de confianza, personal que atendió el parto, estado de ecografía y plan de parto efectivo
  tienen preguntas Coded independientes. Se retiraron de los value sets antiguos solo las relaciones mezcladas.
- Las fechas de referencia y recepción usan preguntas Datetime. Frecuencia respiratoria, frecuencia cardíaca,
  fecha de alta y cantidad de sobres MMN reutilizan preguntas existentes con datatype correcto.
- Se corrigieron respuestas duplicadas por significado: Normal, Madre, Positivo, Reactivo/Arreactivo, Moderado,
  parto eutócico/distócico, procedimientos obstétricos y test estresante fetal usan los conceptos ya cableados o
  el concepto de dominio correspondiente.

## Mappings

Los formularios usaban el par SIHSALUS `4282/4283` para Sí/No, mientras 89 preguntas conservaban mappings hacia
el par legacy `3941/622`. Se retargetearon 173 mappings existentes preservando sus IDs y external UUIDs. No se
agregó `No` a las tres preguntas que solo ofrecen Sí junto con estados de dosis o no aplicabilidad.

Además se crearon 48 mappings `Q-AND-A` y se retiraron 14 relaciones incorrectas: dos autorreferencias de Consulta
Externa, dos respuestas binarias de la pregunta multestado de plan de parto, PPL/PRU dentro de Edema/ROT y ocho
profesiones dentro de la pregunta Parto. Retirar un mapping no elimina el concepto ni invalida observaciones
históricas ya guardadas.

## Lógica y compatibilidad O3

- M-CHAT-R/F calcula Bajo (0-2), Moderado (3-7) o Alto (8-20) desde el puntaje.
- Huanca calcula el total y su clasificación; una evaluación incompleta queda como no concluyente.
- Lista de Habilidades separa siete alertas de las cuatro ausencias que determinan el resultado.
- `CRED-004` acepta edades hasta 143 meses y puntajes acumulados hasta 720.
- El formulario EEDP cuyo archivo histórico dice 21 meses se rotuló como acumulado hasta 24 meses, conservando
  nombre de archivo y UUID para no crear otro formulario.
- Los resultados calculados usan `readonly`, propiedad consumida por el form engine O3. La propiedad legacy
  `editable: false`, que el motor actual ignora, fue eliminada.

Las 12 líneas TPED permanecen opcionales: en esos controles, vacío significa que no se alcanzó ningún hito. Hacer
obligatoria la selección sin una respuesta explícita `Ningún hito/no evaluado` obligaría a registrar falsamente el
primer hito.

## Validación automatizada

El validador `.github/scripts/validate_ampath_forms.py` ahora comprueba el bundle real y falla ante:

- UUIDs inexistentes, retirados o ambiguos;
- respuestas autorreferenciales, repetidas o fuera del `Q-AND-A` de su pregunta, incluso entre sources;
- preguntas de valor con datatype `N/A` y `obsGroup` que no sea `ConvSet/N/A`;
- renderers no soportados y uso de la propiedad `editable` ignorada por O3;
- encounter types discordantes y referencias locales inexistentes en expresiones analizables.

Resultado final:

- 111 formularios validados.
- 3 641 referencias conceptuales resueltas.
- 32 382 conceptos OCL revisados.
- 185 filas de rangos de referencia validadas contra 64 758 identificadores conceptuales bundleados.
- Cero brechas de resolución, `Q-AND-A`, datatype, renderer, encounter o expresión.
