# Correcciones aplicadas en OCL remoto

Fecha: **2026-09-12**. Fuente: **SIHSALUS/laboratorio, HEAD**.
Se actualizaron **30 conceptos y 12 mappings** mediante la API OCL
`2.3.201-b92a0036`, con respaldo previo y lectura de comprobación tras cada cambio.
No se creó ni publicó una versión de la fuente. El paquete candidato `1.25.19`
conserva laboratorio `2026-07-10-02` mientras se valida la actualización completa.

## Cambios realizados

- `5282` y `5286` recuperan `Coded`; `2470` recupera `Numeric`, conservando sus
  UUIDs. Se reactivan sus seis respuestas históricas de parasitología, mappings
  `896–901`, y se retiran las seis respuestas codificadas de urobilinógeno,
  `1214–1219`. Los conceptos de respuesta permanecen intactos.
- `5400` recupera nombre, magnitud `mg/24h` y metadata histórica de referencia.
  Esto conserva su significado; no acredita los intervalos para el método local.
- Los 26 conceptos numéricos que declaraban `Units` pasan a usar `units`:
  `1712`, `5222`, `5241`, `5244–5259`, `5267`, `5360`, `5400`, `5402`,
  `5449–5451`. Se conserva cada valor declarado, salvo la recuperación de
  `mg/24h` para `5400`. Esta corrección permite que OpenMRS lea la unidad.
- `655` conserva sus nombres y descripción inglesa, recibe una descripción
  española con la referencia a la NTS 213 y los cuatro puntos de corte revisados,
  y elimina el máximo absoluto de 20 g/dL incompatible con los CSV.

El [contrato normativo](../contracts/laboratory-reporting.md) distingue estos
puntos de corte de los límites analíticos y de los tipos de dato informáticos.
No se convierten resultados ni se consultan pacientes.

## Identidades y verificación

OCL ya mostraba diferencias entre los identificadores externos de algunos nombres
en el objeto base HEAD y en la versión publicada. Para PSA `5450` y factor
reumatoide `5451` se conservaron finalmente los identificadores del export
publicado `2026-09-10-3`, además de los UUIDs de los conceptos. La comparación
incluye esa versión; la vista HEAD aislada no basta para comprobar esta identidad.

- **PASSED:** inventario completo posterior de 248 conceptos y 1214 mappings;
  exactamente los 30 conceptos y 12 mappings previstos, sin cambios adicionales
  de contenido ni de extremos de relaciones. Los 420 mappings `CONCEPT-SET`
  conservan su composición y siguen existiendo 1035 mappings activos.
- **PASSED:** desaparición de `Units` en los numéricos; tipos históricos,
  magnitud de creatinina y ausencia del máximo de Hb de 20 comprobados por GET.
- **PASSED:** los 248 conceptos de la release publicada `2026-09-10-3` mantienen
  su contenido anterior; los doce mappings afectados también conservan sus
  versiones publicadas anteriores.
- **PASSED:** revisión independiente e integridad de mappings, colisiones de
  nombres y contrato de captura, combinando el HEAD corregido con el catálogo
  principal de septiembre. Son comprobaciones de metadata, no pruebas clínicas.
- **NOT RUN:** importación funcional de este HEAD, validación clínica del método,
  publicación de una versión OCL o despliegue.

Continúan pendientes las modificaciones de paneles introducidas por la release
de septiembre, el informe completo de parasitología, los criterios de
prematuridad/puerperio y las dos filas CSV de creatinina normalizada que aún usan
el UUID de `mg/24h`. Las correcciones remotas no autorizan importar todo HEAD como
una release estable ni validan esos elementos pendientes.
