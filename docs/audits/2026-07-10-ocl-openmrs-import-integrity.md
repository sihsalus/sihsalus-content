# Integridad de importación OCL en OpenMRS - 2026-07-10

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

## Incidente

Un arranque limpio de OpenMRS reportó 2 545 ítems OCL fallidos: un concepto y 2 544 mappings. El concepto
`laboratorio:5405` colisionaba, sin distinguir mayúsculas, con el nombre `Prueba de Embarazo` de
`laboratorio:4305`; los mappings contenían además extremos de concepto vacíos o fuentes destino sin nombre.

La release previa `laboratorio/2026-07-10-01` ya había diferenciado el concepto `5405` como
`Prueba de embarazo cualitativa`, restaurado sus cinco mappings dependientes y vuelto a enlazar los cinco
mappings que OCL había asociado al código inexistente `4161` con su origen correcto `5269`.

## Releases publicadas

| Source | Release | Conceptos | Activos | Mappings | Activos |
| --- | --- | ---: | ---: | ---: | ---: |
| `procedimientos` | `2026-07-10-02` | 12 333 | 12 333 | 12 331 | 12 331 |
| `laboratorio` | `2026-07-10-02` | 212 | 212 | 1 050 | 1 050 |
| `lenguas` | `2026-07-10-02` | 63 | 63 | 121 | 121 |
| `geografia` | `2026-07-10-02` | 196 | 196 | 364 | 364 |
| `sihsalus` | `2026-07-10-03` | 4 471 | 4 469 | 5 675 | 5 628 |

El borrador `sihsalus/2026-07-10-02` capturó un estado intermedio de seis mappings retirados y se desactivó sin
marcarlo como release. La versión pública y consumible es `2026-07-10-03`.

## Reparaciones

- `procedimientos` recupera 22 conceptos de subsección omitidos por la release anterior. Sus 2 412 mappings
  descendentes y las 22 relaciones desde los agrupadores vuelven a tener URLs completas. También se restauran
  las URLs de 750 relaciones cuyos tres conceptos origen sí estaban presentes.
- `lenguas` recupera `to_concept_url` en 22 relaciones `CONCEPT-SET` y `geografia` en otras dos.
- `sihsalus` recupera la fuente destino de 70 mappings externos (`SAME-AS` y `NARROWER-THAN`) a partir de sus
  mismos `external_id` históricos. Se completan ambos extremos de seis mappings odontológicos retirados porque el
  importador OpenMRS resuelve el origen antes de comprobar el estado retirado.
- `laboratorio` recupera las fuentes destino `SNOMED-CT` e `IMO-ProcedureIT` de los mappings `667` y `668`.

## Resultado bundleado

El bundle contiene 32 404 conceptos (32 401 activos) y 20 261 mappings (20 214 activos). La suscripción principal
apunta a `SIHSALUS/sihsalus/2026-07-10-03`.

La validación conjunta de todos los ZIPs queda en cero para:

- mappings sin `from_concept_url`;
- `Q-AND-A` o `CONCEPT-SET` sin `to_concept_url`;
- mappings externos sin nombre, URL o código de fuente destino;
- extremos internos que no resuelven contra un concepto bundleado;
- colisiones case-insensitive de nombres por defecto que puedan dejar un concepto sin alternativa para
  `FULLY_SPECIFIED`.

El validador `.github/scripts/validate_ocl_exports.py` ejecuta estas comprobaciones sobre mappings activos y
retirados, reproduciendo las precondiciones que aplica el módulo OpenMRS OCL antes de persistirlos.
