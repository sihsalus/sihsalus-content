# Transición institucional de OCL y talla al nacer

**Estado: versiones OCL publicadas y verificadas; content 1.25.42 candidata,
sin desplegar.** La primera transición de #269 alteraba el orden al importar y
se retiró de la configuración en 1.25.40, conservando las correcciones de
formularios. Content 1.25.41 incorporó únicamente las equivalencias MINSA y
los pesos explícitos de etnias; sigue siendo la versión observada en DEV/QLTY.

La candidata 1.25.42 actualiza conjuntamente la suscripción y los 34 exports
de las 18 fuentes al servidor institucional. Conserva los 32.551 conceptos y
20.610 mappings de 1.25.41, las exclusiones históricas y los UUID. Reutiliza las
versiones oficiales publicadas después de corregir los 2.862 pesos ausentes;
la única modificación clínica adicional es habilitar decimales en talla al nacer.
La [integración de etnias](../contracts/etnias-minsa.md) conserva su release.

## Fallo verificado

[CI 39340566387](https://github.com/sihsalus/sihsalus-content/actions/runs/39340566387)
comprobó que el cambio de servidor conservaba UUID y extremos de relaciones,
pero convertía a `NULL` el `sort_weight` de **2.922 respuestas** y cambiaba a
`1` el de **dos miembros de conjuntos**. El control de compatibilidad rechazó
la actualización. Ese criterio sigue activo.

OCL `4.0.0` aplica valores por defecto al actualizar relaciones cuyo export
omite `sort_weight`. Cambiar los ZIP y el host obliga a reimportarlos; la
igualdad de conceptos, nombres y mappings no demuestra que se conserve el
orden persistido. Reordenar los arrays del ZIP tampoco resuelve el problema.
La corrección debe hacerse en la fuente o importador responsable, sin SQL de
reparación ni un segundo loader en content.

## Referencia histórica de compatibilidad

La referencia es el artefacto publicado `1.25.34`, commit
`b9e93638fd7ed9c8dffe8b48f2be868f3d9b1a10`, cuyo ZIP tiene SHA-256
`6f1fdcf430d6d0cac6e5f71ff9e337c8af8f5c81384cfc0f20e6e62231093b45`.
Se mantienen los 32.551 conceptos y 20.552 mappings de sus 18 fuentes, las
exclusiones históricas de barrios y los checksums originales.

El baseline publicado utiliza el namespace de carga:
`https://api.openconceptlab.org/orgs/SIHSALUS/sources/sihsalus/2026-07-16-02`.
Los ZIP se importan localmente mediante Initializer. La candidata cambia el
namespace conjuntamente con sus exports; no modifica credenciales de ambientes.

Los seis escenarios de CI permanecen activos. `ocl-fresh`, `ocl-upgrade` y
`ocl-latest-upgrade`
comprueban el catálogo operativo sobre el runtime actual fijado, incluyendo
identidades, pesos, observaciones previas, historia y reinicio. El artefacto
temporal de extracción de pesos ya cumplió su función diagnóstica y se retiró;
las comparaciones completas siguen en el ensayo.

## Antecedente de la corrección decimal

La API institucional es `https://api.gidis-terminology.duckdns.org`. Se prepararon
estos snapshots con `released: false`; las huellas de esta tabla corresponden
a sus descargas anteriores a la publicación:

| Fuente | Candidato | SHA-256 del export oficial combinado descargado |
| --- | --- | --- |
| `sihsalus` | `2026-10-16-1` | `e9fb3c4cefc8435cafd87e3690e7e4c60cf2d2f0e02f991ad9e18f2358373b3a` |
| `anatomia-procedimientos` | `2026-10-16-1` | `f9fe22e1e4545da70cb3a9e892c143885a88c7b20594719e313896571cdf8259` |

La corrección de talla al nacer (#391) está preparada en el concepto
`SIHSALUS/sihsalus:382`, UUID `bf82beb1-d3b8-400e-8160-90869cad8136`:
`allow_decimal: true`, conservando datatype Numeric, unidad cm e identidad.
DEV y QLTY devolvían `allowDecimal:false` incluso después de adoptar content
1.25.41 el 22 de octubre; no anunciar la corrección como disponible ni redondear
mediciones para eludirla. La candidata consume `sihsalus/2026-10-22-01`; el
snapshot de sihsalus del 16 de octubre permanece sin publicar y no se distribuye.

### Revisión de la fuente institucional: 22 de octubre

La descarga autenticada del candidato `sihsalus/2026-10-16-1` sigue teniendo
la huella indicada arriba y `released: false`. La lectura de QLTY previa al
despliegue de content 1.25.41 devolvió `allowDecimal: false` para talla al nacer;
el paso `0.1` del formulario no cambia esa restricción del concepto. #391
continúa pendiente de adopción y aceptación clínica.

Se recuperó el [artefacto de orden del baseline publicado](https://github.com/sihsalus/sihsalus-content/actions/runs/38976229948/artifacts/12079867361)
y se contrastó su descarga con el digest de GitHub:
`a7d018dc762b99b294fa82c412cfccf721be56c8a78c5caa22d0ff72a625b9c2`.
Contiene 17.404 relaciones de `1.25.34`, sin pacientes. Las lecturas nativas de
HEAD confirman que los 62 pesos de etnias ya son explícitos y coinciden con
esa referencia. Se identificaron **2.862 propiedades `sort_weight` ausentes**:

| Fuente | Respuestas | Miembros de conjuntos |
| --- | ---: | ---: |
| sihsalus | 2.451 | 2 |
| laboratorio | 358 | 0 |
| educacion | 13 | 0 |
| seguros | 19 | 0 |
| religiones | 12 | 0 |
| estado-civil | 7 | 0 |

La propuesta offline `ocl-order-native-proposal-20261022.json`, retenida por
el operador, tiene SHA-256
`effc7b31b91e571ea0444f7a15fe5ab0db1d6efcf084572c9b66bf4230a16416`.
Se comprobaron UUID, tipo y extremos contra el baseline y content
`0b9dd4fd6aeb07f8329cc79c925d71186ff137fc`; no contiene sustituciones de
identidad ni otros cambios clínicos. Cada entrada identifica la versión
nativa esperada y propone exclusivamente el peso, mediante el API existente
de mappings.

**Aplicación autorizada y verificada:** el usuario aprobó esa propuesta concreta
y se aplicaron los 2.862 pesos mediante PUT nativo. Cada escritura comprobó
previamente versión, identidad, extremos, retiro y peso; la lectura posterior
verificó el resultado y la conservación de los demás campos estables. El
manifiesto de finalización tiene SHA-256
`1b8dfaa9483fffc9f514c371ba6af7d91fea95929b5989ba8d0886f9b876a323`:
2.862 registros verificados, cero errores. El operador conserva privadamente
las lecturas anteriores y posteriores y una copia local comprobada de los
journals; no contienen pacientes ni credenciales.

Los seis exports oficiales de HEAD conservan **4.741 conceptos y 6.807 mappings**.
La comparación completa reutiliza el comparador de catálogos de terminology:
coinciden con content publicado, incorporando exclusivamente esos pesos y el
cambio decimal de `sihsalus:382` ya preparado. La configuración de las fuentes
coincide mediante GET de SourceDetail; el export HEAD omite las opciones de
generación de IDs y no permite verificarlas por sí solo.

| Fuente | SHA-256 del export HEAD verificado |
| --- | --- |
| educacion | `e58e41d632678d1218933d65c826e5e95aa0004c34c42a349093ba8358a1aa4e` |
| estado-civil | `71b109ae842b4b0d9939bf2b882c9381e8adad9588dae45554145b8a8f9c7460` |
| laboratorio | `db65ea05784aae88f2b9089437d6921484bf0e0e5fd155ad3c89dcfdf62c5a9a` |
| religiones | `a3b1b766ee7ccb3b2ff4c461ba02b0c86df3cfd26bd378b660935a8c3f2739e7` |
| seguros | `82035160f1230585e7e31c0d046f760ac95ae9136f7aa1f870f97be304b4ef5a` |
| sihsalus | `c038346003fb9f096e99c3a949285babe13641ba97be2f1a17f34c93a7c714d7` |

**Publicación autorizada y verificada:** el usuario aprobó la propuesta
`ocl-publication-proposal-20261022.json`, SHA-256
`e1502074c599a65901b36db2a8cbe462c8d08373adb3f3d3b5ec3a432a60c31f`.
Se crearon secuencialmente seis versiones `2026-10-22-01` y se publicó el
snapshot existente `anatomia-procedimientos/2026-10-16-1`, sin modificar sus
121 conceptos ni 266 mappings. Antes de publicar cada versión se comparó el
export congelado completo y la configuración con la propuesta; después se
volvió a descargar su export oficial con `released:true` y se repitió la comparación.

El manifiesto de finalización tiene SHA-256
`27a09723f08bd4b1dde564498efb94b5d9fda6f3f8bfe5b8b1423c1217c05d34`:
siete versiones, 4.862 conceptos y 7.073 mappings verificados. Los journals
privados preservan intención, respuesta, identidad y huellas por operación.

| Fuente | Versión publicada | SHA-256 del export oficial publicado |
| --- | --- | --- |
| educacion | `2026-10-22-01` | `6b3c6b2303afc12ba448907fe6d01f8425f03839666dddc004a0f62e0e175376` |
| estado-civil | `2026-10-22-01` | `8120c3a10302ce54d7258c3852442be1eab027c6ce134149ab358441884c51ec` |
| laboratorio | `2026-10-22-01` | `e2d213a0c8851c113cff26f925f7258cda3bdb404f9e3a9acd3415ce9fda13d2` |
| religiones | `2026-10-22-01` | `c2a12142f927cafde5ac167b9b6249b47b456ecad4236e06b25af509369da2ca` |
| seguros | `2026-10-22-01` | `11bb4c5b9d503d2b000d4fad61a37ab74fd235d43aa9b9b8d866478777f41e67` |
| sihsalus | `2026-10-22-01` | `229e14daad838ff81dbe53ca5a08ec85483b86d4fd2e5a0c83baee20cb86bb64` |
| anatomia-procedimientos | `2026-10-16-1` | `8a382a84acb7b5f86fcc6589c9c9041f5d16cae9de56eb01a402e673b29767ee` |

Para preparar content se descargaron también los otros once exports publicados.
La comparación de las 18 fuentes con 1.25.41, mediante el reconciliador existente,
conserva todos los registros y la configuración, salvo los pesos autorizados y
`allow_decimal:true` de talla al nacer. El splitter existente produce los 34 ZIP;
no se modifica manualmente el estado de publicación ni se incorporan exports HEAD.
En la ruta desde 1.25.41, los dos ZIP de etnias tienen bytes idénticos y el loader
los omite por su checksum. Sus items nativos ya cargados conservan el namespace
anterior; el ensayo deriva esa expectativa de los archivos y la suscripción del
baseline, conservando UUID, versión y estado de importación. Cada archivo que
cambia debe cargar con el namespace nuevo. No se fuerza la recarga ni se altera
el catálogo para provocar un checksum distinto.

La suscripción candidata es
`https://api.gidis-terminology.duckdns.org/orgs/SIHSALUS/sources/sihsalus/2026-10-22-01`.

### Ensayo de actualización y checksum del XML

El [primer CI de la candidata](https://github.com/sihsalus/sihsalus-content/actions/runs/39870634999)
pasó instalación nueva, los tres escenarios históricos y las validaciones del
paquete. Las dos actualizaciones OCL confirmaron el catálogo, su orden y
`allowDecimal:true`, pero fallaron al exigir el checksum del XML original.
El hook nativo del distro fijado elimina la propiedad de token antes de cargar
ese archivo: su hash no es el del template. Se reprodujo con el hook del commit
`bdfa1bb78095e59fc24eb655bb39aa352fdf5681`, sin credenciales.

El ensayo reutiliza ese hook de la imagen sobre una copia privada, sin red y
con token vacío, para obtener el checksum esperado de archivos modificados.
Conserva la comparación exacta de archivos sin cambios e historia, exige los
checksums de todos los ZIP y rechaza el hash crudo o cualquier otro valor.
No altera la configuración ni los checksums del backend probado. Los seis
escenarios deben repetirse sobre el SHA final; el CI anterior sigue fallido.

### Pendientes y flujos de aceptación

1. Ejecutar CI del SHA final de content 1.25.42. Los escenarios de instalación,
   actualización desde 1.25.34/1.25.41 y reinicio deben conservar el catálogo completo,
   pesos, UUID, observaciones previas e historia/checksums; guardar 30.1 cm por
   REST y recuperarlo sin redondeo tras reiniciar.
2. Revisar la divergencia histórica de QLTY descrita en #269 antes de promover.
   La comparación canónica no autoriza sobrescribir su estado persistido.
3. Obtener revisión humana de la candidata y aprobación de su publicación.
   Actualizar después el pin del distro y coordinar el artefacto y ambiente de
   despliegue, la credencial institucional y el acceso remoto. El secret de CI
   no cambia `OMRS_OCL_TOKEN` del backend. Publicación OCL, paquete y despliegue
   son decisiones separadas.
4. En CRED, con cuenta autorizada y paciente sintético propio: abrir Detalles de
   Nacimiento, guardar 30.1 cm, recargar y editar para verificar el valor, el UUID
   y la observación histórica; rechazar texto inválido y limpiar/verificar los
   recursos creados. La aceptación clínica y el cierre de #391 siguen pendientes.
5. Etnias (#400): buscar `2`/`Aimara` y `Aguaruna`/`Awajun`, seleccionar, guardar
   y reabrir comprobando el UUID; verificar valor histórico, código desconocido
   y etnias sin equivalencia. `Aymara` no es un sinónimo publicado en esta release.
6. Permisos (#387/#402): tras una prueba positiva y negativa con una réplica
   sintética del perfil aprobado, `cred` se modificó nuevamente el 22/10 a las
   22:34 UTC. El usuario indicó conservar el acceso actual mientras se coordina.
   Ambos issues permanecen reabiertos; no restaurar roles automáticamente ni
   atribuir la validación anterior al perfil reducido posterior.

Responsables: terminología para el catálogo, módulo OCL para su importación,
distro para el runtime y responsable clínico para la aceptación de #391.
Si algún ambiente recibió el candidato fallido, evaluar su estado antes de
actualizar: retroceder sólo el ZIP o borrar checksums no recupera el orden perdido.
