# Contrato del catálogo de barrios de Santa Clotilde

## Alcance y fuente de verdad

El barrio de residencia es un atributo codificado de persona con UUID
`4a182c6e-9a19-4db8-8042-4bbf3b4308c2`. Sus valores activos pertenecen al set
`0fd3e744-6d2c-4cb3-9b7e-1f88899635d9`; el catálogo activo vive exclusivamente en la fuente OCL
`SIHSALUS/barrios-santa-clotilde`.

La primera release aceptada por este paquete es `2026-08-22-01`. Debe contener exactamente los diez
conceptos `SCL-01` a `SCL-10`, el concepto `SCL-BARRIOS` y diez mappings `CONCEPT-SET`. Los UUIDs de
OpenMRS son estables y el validador de CI comprueba IDs, UUIDs, nombres, clase, datatype, membresía,
orden y aislamiento respecto de `SIHSALUS/sihsalus`.

El export oficial combinado de esta release tiene SHA-256
`8430529c7325c11679eedb58e1e86340557523522284acc830c3f365c7d32fda`. El paquete lo divide con
`.github/scripts/split_ocl_export.py`; el JSON canónico recombinado debe conservar SHA-256
`fbcb4f0ed111ceb4c686ac343eee09c2435037f8dceb9b679cee0a226e1c9177`. Se verifica el contenido
canónico porque la metadata ZIP y el formato JSON no son evidencia terminológica.

Los campos OCL `extras.ui_color` y `extras.ui_tag_type` conservan metadata descriptiva de presentación.
No son clínicos, no forman parte del valor persistido y no garantizan su renderizado. El frontend actual
no los consume: obtiene las opciones desde `answerConceptSetUuid` y no duplica el catálogo en
`customConceptAnswers`.

Este paquete solo distribuye la metadata backend y los exports OCL. La configuración efectiva de
registro, búsqueda y banner pertenece a `sihsalus-frontend/config/frontend.json`; no se mantiene ni se
empaqueta una copia de configuración frontend en este repositorio.

## Identidades retiradas en `sihsalus`

El HEAD de `SIHSALUS/sihsalus` conserva retirados once conceptos y diez mappings de un intento
anterior de este catálogo. No forman parte de los exports principales bundleados por este paquete:
el export principal `2026-09-09-1` (desde `1.25.19`) los excluye explícitamente mediante
[las exclusiones reproducibles](ocl-sihsalus-2026-09-09-1-exclusions.json), y el validador bloquea
cualquier duplicación bundleada, incluso retirada. El filtro rechaza registros activos o distintos de
los revisados; no es una eliminación general de registros retirados. No se debe incorporar una release
futura de `sihsalus` que contenga esos UUIDs hasta que se purguen en OCL o el export los excluya.
El manifiesto y la reproducción constan en [la auditoría OCL](../audits/2026-09-12-ocl-refresh.md).

## Corte desde `ADDRESS_3`

`person_address.address3` se utilizó previamente para almacenar el barrio como texto libre. La primera
fase retiró `ADDRESS_3/Barrio` de `addressConfiguration.xml` y del formato visible de la dirección tras
comprobar la ausencia de datos que requirieran migración en el entorno revisado. Este corte no incluye scripts de
migración, aliases ni reconciliación. Si otro entorno contiene datos en ese campo, el
cambio debe bloquearse y rediseñarse; no se debe inferir ni transformar direcciones automáticamente.

## Actualización del catálogo

Para agregar o corregir un barrio:

1. Preservar los IDs y UUIDs existentes; una corrección de nombre no crea un concepto nuevo.
2. Publicar una nueva versión released de `barrios-santa-clotilde`.
3. Descargar los exports oficiales de conceptos y mappings, ubicarlos en los slots `15_` y `65_`, y
   retirar los dos exports de la versión anterior en el mismo cambio.
4. En el repositorio frontend, verificar que registro y búsqueda continúan apuntando al mismo
   `answerConceptSetUuid`; no duplicar respuestas ni metadata de presentación en su configuración.
5. Ejecutar todos los validadores del content package y una importación desde una base limpia antes de
   desplegar.

El global property `openconceptlab.subscriptionUrl` conserva la release
`2026-07-16-02` de OCL Cloud. Esa versión no contiene los UUID de barrios ni
elimina conceptos ausentes: es compatible con los dos conceptos activos
adicionales del export principal `2026-09-09-1`. Los barrios se cargan
exclusivamente desde sus ZIPs estáticos. OCL 3.2.0 usa el host de la suscripción
para resolver también las URLs relativas de los ZIPs locales, por lo que la
transición de la suscripción al servidor institucional sigue pendiente de una
validación nativa de upgrade. El importador remoto no aplica las exclusiones del
paquete: también debe comprobarse el export servido.
