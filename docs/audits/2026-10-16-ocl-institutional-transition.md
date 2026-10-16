# Transición institucional de OCL y talla al nacer

Fecha: 16 de octubre de 2026. Paquete candidato: **1.25.35**.
Relacionados: `sihsalus/sihsalus#391` y PR de content #269.
Estado: preparación autorizada; **sin publicación de los candidatos OCL,
merge ni despliegue**. Los cambios pertenecen a content y a su fuente de
terminología. No se modifica código, dependencias ni configuración de ningún
backend en ejecución.

## Corrección y procedencia

El concepto `SIHSALUS/sihsalus:382`, talla al nacer, conserva el UUID
`bf82beb1-d3b8-400e-8160-90869cad8136`, el datatype `Numeric`, la unidad `cm`,
nombres y mappings. La corrección aprobada cambia exclusivamente
`extras.allow_decimal` de `false` a `true`. Se aplicó mediante la API nativa al
borrador institucional; su nueva versión de concepto es `382/67749`.
No se redondean mediciones ni se modifican observaciones existentes.

Servidor API: `https://api.gidis-terminology.duckdns.org`.
La web institucional `https://sih-terminology.inf.pucp.edu.pe/` declara esa API.
El token institucional no autentica contra `api.openconceptlab.org`.

Se descargaron los exports oficiales de las 18 fuentes institucionales y se
compararon con el catálogo previo de content. La comparación semántica del
reconciliador existente de terminología comprobó códigos, UUID externos,
datatypes, clases, nombres, descripciones, estado, extras y relaciones. Las
18 versiones originales coincidieron sin diferencias clínicas. Después se
compararon los dos candidatos: solo cambia el booleano del concepto 382.
Se mantienen **32.551 conceptos y 20.552 mappings en 34 archivos**.

Los exports no son idénticos en sus metadatos internos de servidor. En 576
referencias externas CIEL, `to_concept_url` y el nombre resuelto pasan a `null`
(291 `SAME-AS`, 192 `NARROWER`, 89 `BROADER` y 4 `Associated`).
Se conservan fuente, código de destino, tipo y UUID: la rama de referencias
externas de `Saver` 4.0.0 usa fuente+código. Ningún mapping `Q-AND-A` o
`CONCEPT-SET`, que sí necesita URL de destino, pierde esa URL. Los campos
derivados de propietario no forman parte del modelo `OclMapping` importado.

| Fuente | Versión preparada | Conceptos | Mappings |
| --- | --- | ---: | ---: |
| medicamentos | 2026-06-30 | 1001 | 17 |
| procedimientos | 2026-07-10-02 | 12333 | 12331 |
| diagnosis | 2026-06-30 | 13484 | 0 |
| laboratorio | 2026-07-10-02 | 212 | 1050 |
| inmunizaciones | 2026-06-30 | 22 | 60 |
| prestacionales | 2026-06-30 | 66 | 65 |
| geografia | 2026-07-10-02 | 196 | 364 |
| etnias | 2026-06-30 | 62 | 64 |
| seguros | 2026-07-17-01 | 25 | 33 |
| religiones | 2026-06-30 | 12 | 24 |
| sihsalus | **2026-10-16-1, sin publicar** | 4474 | 5679 |
| lenguas | 2026-07-10-02 | 63 | 121 |
| ocupaciones | 2026-07-09-01 | 448 | 447 |
| estado-civil | 2026-06-30 | 6 | 8 |
| educacion | 2026-06-30 | 12 | 13 |
| barrios-santa-clotilde | 2026-08-22-01 | 11 | 10 |
| referencia-institucional | 2026-08-25-01 | 3 | 0 |
| anatomia-procedimientos | **2026-10-16-1, sin publicar** | 121 | 266 |

Las otras 16 versiones ya están publicadas en el servidor institucional.
Los dos candidatos se crearon con `released: false` y se descargaron mediante
el endpoint oficial de export. No se inventó una versión dentro de los ZIP.

| Export oficial candidato combinado | SHA-256 del ZIP descargado |
| --- | --- |
| `sihsalus/2026-10-16-1` | `e9fb3c4cefc8435cafd87e3690e7e4c60cf2d2f0e02f991ad9e18f2358373b3a` |
| `anatomia-procedimientos/2026-10-16-1` | `f9fe22e1e4545da70cb3a9e892c143885a88c7b20594719e313896571cdf8259` |

El splitter existente separa conceptos y mappings, conserva los slots de carga
`00`–`17` y `50`–`67`, y genera los ZIP de forma reproducible. El
[validador OCL](../../.github/scripts/validate_ocl_exports.py) fija versiones,
conteos, estado de publicación y huellas del JSON recombinado de cada fuente.
Esas huellas son distintas del SHA-256 del archivo ZIP combinado de la tabla.

## Compatibilidad del cambio de servidor

En Open Concept Lab 4.0.0, `Importer.run(ZipFile)` obtiene el host de
`openconceptlab.subscriptionUrl` y lo antepone a las URLs relativas del export.
Esta ruta de carga local no descarga fuentes ni consume el token remoto.
`Saver` resuelve conceptos por su UUID externo; las relaciones entre fuentes
dependen de los items importados bajo el mismo namespace.

Cambiar únicamente la propiedad o los dos ZIP principales deja los demás
archivos sin cargar porque sus checksums no cambian. Por eso se sustituyen
juntos los 34 exports y se fija la suscripción a:

```text
https://api.gidis-terminology.duckdns.org/orgs/SIHSALUS/sources/sihsalus/2026-10-16-1
```

Los dos ZIP de anatomía `2026-10-11-02` resultaron idénticos byte por byte a
los ya distribuidos. Se preparó la nueva versión oficial `2026-10-16-1` para
registrar la transición institucional. Se compararon tanto HEAD antes de crear
el snapshot como el snapshot exportado: conserva sus 121 conceptos y 266
mappings sin diferencias clínicas. Su carga se realiza mediante el mecanismo
nativo de archivos versionados, sin borrar checksums, renombrar bytes antiguos
para provocar una recarga, ni introducir SQL o loaders propios.

La fuente principal institucional ya excluye los once conceptos y diez mappings
retirados de barrios descritos en la [auditoría anterior](2026-09-12-ocl-refresh.md).
Se conserva ese manifiesto como evidencia histórica; no se aplica su huella
Cloud a registros institucionales distintos. El validador exige que esos UUID
no reaparezcan en la fuente principal. `barrios-santa-clotilde` sigue siendo
su única definición operativa.

## Evidencia de ambientes y credenciales

Consulta de solo lectura el 16/10/2026:

| Propiedad | DEV | QLTY |
| --- | --- | --- |
| Suscripción | OCL Cloud, `sihsalus/2026-07-16-02` | OCL Cloud, `sihsalus/2026-07-16-02` |
| `scheduledDays` | `0` | `0` |
| `scheduledTime` | `0:0` | `0:0` |
| `subscribedToSnapshot` | `false` | `false` |
| `validationType` | `FULL` | `FULL` |

No hay días configurados para una descarga automática. El pin antiguo podría
restaurar `allow_decimal: false` en una importación remota manual; por eso la
propuesta actualiza el pin en content. No se alteraron estas propiedades en
los ambientes ni se consultó el valor de su token.

El secret `OCL_API_TOKEN` y la variable `OCL_API_URL` del repositorio de content
están preparados para la API institucional. Esto **no modifica** el valor
`OMRS_OCL_TOKEN` de un backend. El placeholder `${OMRS_OCL_TOKEN}` se conserva.
La compatibilidad de una descarga remota autenticada queda pendiente: requiere
comprobar la credencial del entorno y autorización operativa aparte. Las
pruebas de importación local no acreditan ese acceso remoto.

## Pruebas y límites de la evidencia

La comparación estática de las 18 fuentes y los candidatos pasó. Las regresiones
del validador cubren la procedencia, integridad y decimales del concepto 382,
además de los contratos de laboratorio, barrios, referencia y anatomía.
El estado de CI y los resultados nativos se registran en el PR #269; mientras
no terminen, no se considera probado el upgrade institucional.

Se añaden escenarios al arnés existente de Initializer para instalación nueva
y actualización desde content **1.25.34 publicado**, con reinicio posterior:
conservar checksums e historia, comprobar identidades y mappings, namespace de
las 18 fuentes, una observación sintética previa y aceptación/persistencia de
`30.1 cm`. El backend publicado se usa exclusivamente como fixture inmutable
en CI; no se construye ni cambia un backend del sistema.

La imagen actual verificada es
`ghcr.io/sihsalus/sihsalus-backend@sha256:72c0c4cedfd5ba4b3eb1a3fabd8d1f4e9222548ce49ba06dd7ac2c3a00282414`,
revisión de distro `bdfa1bb78095e59fc24eb655bb39aa352fdf5681`, Core
`2.8.10-sihsalus.4`, OCL `4.0.0`, Initializer `2.13.0-sihsalus.2`.
Los escenarios históricos conservan su imagen anterior; su resultado por sí
solo no prueba compatibilidad con este runtime.

El ZIP publicado `1.25.34` tiene SHA-256
`6f1fdcf430d6d0cac6e5f71ff9e337c8af8f5c81384cfc0f20e6e62231093b45`.
Sus archivos coinciden con la fuente `b9e93638`; `78178494` añade cambios en
roles/privilegios bajo la misma versión de POM y no es idéntico al artefacto
publicado. No se presentan ambos como una misma línea base.

No se realizaron pruebas clínicas de estas correcciones en DEV/QLTY ni se
cambiaron datos clínicos, cuentas, permisos o migraciones de los ambientes.

## Decisiones pendientes y recuperación

1. Revisar y autorizar la publicación de ambos candidatos OCL. Descargar de
   nuevo los exports publicados, verificar la misma diferencia clínica y
   actualizar las huellas/estado esperados antes de aprobar el SHA final de content.
2. Revisar resultados de instalación nueva, upgrade e idempotencia, además de
   aceptación clínica con datos sintéticos. Un CI verde no acredita aceptación.
3. Aprobar por separado el merge de content: el workflow de main puede publicar
   `1.25.35` en Maven Central. El despliegue requiere otra decisión.
4. Antes de cualquier futura aplicación, guardar y verificar respaldo de datos,
   configuración y artefactos. La recuperación del cambio de namespace exige
   restaurar una copia consistente con sus checksums; no basta cambiar el pin
   o retroceder solo el ZIP. Si ya hay mediciones decimales nuevas, conservarlas
   y revisar su recuperación clínica antes de volver a la restricción anterior.

La asignación del rol existente para #387 permanece como intervención de un
administrador autorizado, documentada en el contrato de perfiles. Esta
transición de terminología no asigna roles ni modifica autorizaciones.
