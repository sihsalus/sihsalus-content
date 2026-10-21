# Etnias y códigos HIS MINSA

Content candidata `1.25.41` incorpora la versión publicada
`SIHSALUS/etnias/2026-10-21-01` del OCL institucional. Seguimiento:
[sihsalus/sihsalus#400](https://github.com/sihsalus/sihsalus/issues/400).
La [documentación de terminología](https://github.com/sihsalus/sihsalus-terminology/pull/13)
registra la tabla revisada, fuentes oficiales y decisiones clínicas pendientes.

## Identidades y carga

El export tiene 62 conceptos y 122 mappings: conserva las 64 relaciones
anteriores y añade 58 equivalencias `SAME-AS` con `MINSA-ETNIAS`. Aimara mantiene
el ID clínico `4` y UUID `c79ac7a1-1cef-4524-bbc4-bb21fd5d5331`; su código
MINSA es la cadena `2`. Cinco nombres alternativos se incorporan como sinónimos
nativos: Aguaruna, Chayawita, Ticuna, Amuesha y Jebero.

Los 62 mappings `Q-AND-A` declaran sus pesos explícitamente en OCL. Se
contrastaron por UUID y destino mediante consultas de solo lectura en DEV y
QLTY: conservan los pesos `1` a `62` del catálogo publicado. El export anterior
omitía esos valores; reimportarlo podía sustituir el orden persistido por `NULL`.
Los pesos se corrigen en la fuente canónica y quedan en la nueva versión.

Initializer y el módulo OCL cargan los dos ZIP separados por la herramienta
existente `split_ocl_export.py`. Las equivalencias crean términos de referencia
y mappings nativos de OpenMRS. Los 60 conceptos de la referencia MINSA no se
añaden como otros conceptos clínicos ni como nuevas respuestas.

Las otras 32 exportaciones y la suscripción remota conservan sus bytes y pins.
El loader completa las URLs relativas con el namespace OCL Cloud configurado;
la procedencia de esta nueva versión es el servidor institucional. La
[transición completa de host](../audits/2026-10-16-ocl-institutional-transition.md)
sigue pendiente y requiere comprobar el orden de todos los catálogos.

## Fuente y artefactos

Los códigos proceden de MINSA, *Atención Materna*, segunda edición, marzo de
2023, Anexo 1, página PDF 55, disponible en el
[servidor oficial de GERESA Arequipa](https://saludarequipa.gob.pe/HIS/Manuales_y_Sintaxis/2023/Manual-atenci%C3%B3n_materna-2023.pdf).
La referencia local publicada `MINSA-ETNIAS/2026-10-21-01` contiene los 60 códigos.

| Artefacto | SHA-256 |
| --- | --- |
| Export nativo combinado de etnias | `6c5728c4e521159b371aafb3bbd65d772176ebd69b70a57ce26716ec82ec5c14` |
| ZIP de conceptos | `9f832f74ccd9a8e719ad94d6e4b7869ecce9b9b2fef3f70b9d02d58a086680b7` |
| ZIP de mappings | `3d7006eb38ca184dd538e70640854dca806546acaa5c623a4f575f6d1e0e535d` |
| JSON canónico recombinado | `de970dad05398ca1e85fadf1627944143e4a67be836d603235cf938c845e1738` |
| Export nativo de la referencia MINSA | `5bec1789937bee9bd36419d52eb7d6b03c56bac2fd6008fa4bf9e58ee7f08d68` |

## Consumo y validación

Después de cargar content, la consulta nativa OpenMRS
`GET /ws/rest/v1/concept?source=MINSA-ETNIAS&code=2` debe devolver Aimara.
Una búsqueda de texto o un ID interno sin fuente no resuelve un código oficial.
Frontend y cada integración deben utilizar la fuente y el código; este cambio
de metadata no implementa sus selectores ni sus payloads.

El validador verifica la huella del export recombinado. Las regresiones rechazan
alteraciones de código, nombre, peso y versión. Los escenarios existentes
`ocl-fresh` y `ocl-upgrade` comprueban los términos y mappings persistidos,
nombres, búsqueda por código/sinónimo y reinicio. La actualización solo admite
las 58 relaciones, 58 términos y una fuente nuevos, además del concepto de
vitamina A previamente declarado; conserva todas las filas históricas de la
comparación, incluidos IDs, UUID y pesos de respuestas.

La integración requiere CI del SHA candidato. La revisión clínica institucional
y los flujos del frontend siguen pendientes: buscar y seleccionar por código y
sinónimo, guardar/reabrir una selección previa y presentar códigos desconocidos
o sin equivalencia. Andino, Afro Descendiente e Indígena Amazónico no tienen
mapping; Ashaninka y Otro aún requieren decidir su incorporación clínica.
DEV/QLTY conservan content `1.25.40` hasta un despliegue aprobado.

La versión OCL `2026-06-30` y los artefactos publicados anteriores permanecen
disponibles. Retirar la candidata antes de desplegar no requiere modificar datos.
Después de una carga, evaluar el estado persistido y restaurar un respaldo
compatible si procede: volver al ZIP antiguo no retira los mappings añadidos y
puede perder pesos al reimportarlo. Conservar historia y checksums.
