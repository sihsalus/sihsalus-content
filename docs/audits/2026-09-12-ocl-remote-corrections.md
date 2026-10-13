# Correcciones aplicadas en OCL remoto

Fuente: `SIHSALUS/laboratorio`, HEAD. Se actualizaron **30 conceptos y 12 mappings**
mediante la API OCL, con respaldo previo y lectura de comprobación tras cada
cambio. No se creó ni publicó una versión de la fuente. El paquete candidato
`1.25.19` conserva laboratorio `2026-07-10-02` mientras se valida la
actualización completa.

## Cambios realizados

- `5282` y `5286` recuperan `Coded`; `2470` recupera `Numeric`, conservando sus
  UUIDs. Se reactivan sus seis respuestas históricas de parasitología, mappings
  `896–901`, y se retiran las seis respuestas codificadas de urobilinógeno,
  `1214–1219`. Los conceptos de respuesta permanecen intactos.
- `5400` recupera nombre, magnitud `mg/24h` y metadata histórica de referencia.
  Esto conserva su significado.
- Los 26 conceptos numéricos que declaraban `Units` pasan a usar `units`:
  `1712`, `5222`, `5241`, `5244–5259`, `5267`, `5360`, `5400`, `5402`,
  `5449–5451`. Se conserva cada valor declarado, salvo la recuperación de
  `mg/24h` para `5400`. Esta corrección permite que OpenMRS lea la unidad.
- `655` conserva sus nombres y descripción inglesa, recibe una descripción
  española con la referencia a la NTS 213 y los cuatro puntos de corte revisados,
  y elimina el máximo absoluto de 20 g/dL incompatible con los CSV.

El [contrato normativo](../contracts/laboratory-reporting.md) distingue estos
puntos de corte de los límites analíticos y de los tipos de dato informáticos.

## Identidades y verificación

OCL ya mostraba diferencias entre los identificadores externos de algunos nombres
en el objeto base HEAD y en la versión publicada. Para PSA `5450` y factor
reumatoide `5451` se conservaron finalmente los identificadores del export
publicado `2026-09-10-3`, además de los UUIDs de los conceptos. La comparación
incluye esa versión; la vista HEAD aislada no basta para comprobar esta identidad.

El inventario posterior contiene 248 conceptos y 1214 mappings: exactamente los
30 conceptos y 12 mappings previstos, sin otros cambios de contenido ni de
extremos de relaciones. Los 420 mappings `CONCEPT-SET` conservan su composición,
siguen existiendo 1035 mappings activos y los 248 conceptos de la release
publicada `2026-09-10-3` mantienen su contenido anterior.

Continúan pendientes las modificaciones de paneles introducidas por la release
de septiembre, el informe completo de parasitología, los criterios de
prematuridad/puerperio y las dos filas CSV de creatinina normalizada que aún usan
el UUID de `mg/24h`.
