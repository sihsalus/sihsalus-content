# Transición institucional de OCL y talla al nacer

**Estado tras la corrección de CI 1.25.40: pendiente y fuera del paquete
operativo.** La propuesta de #269 se integró con la corrección de formularios,
pero su actualización nativa alteraba el orden del catálogo. Se recuperan los
34 ZIP publicados de content `1.25.34` y su namespace OCL Cloud, conservando
las correcciones de formularios de #389/#390 y los cambios posteriores.

La candidata `1.25.41` actualiza únicamente etnias a `2026-10-21-01`, con pesos
explícitos contrastados por UUID en DEV/QLTY. Conserva las otras 32 exportaciones
y el namespace existente; no completa esta transición. Ver el
[contrato de etnias](../contracts/etnias-minsa.md).

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

## Paquete operativo

La referencia es el artefacto publicado `1.25.34`, commit
`b9e93638fd7ed9c8dffe8b48f2be868f3d9b1a10`, cuyo ZIP tiene SHA-256
`6f1fdcf430d6d0cac6e5f71ff9e337c8af8f5c81384cfc0f20e6e62231093b45`.
Se mantienen los 32.551 conceptos y 20.552 mappings de sus 18 fuentes, las
exclusiones históricas de barrios y los checksums originales.

La suscripción conserva el namespace de carga:
`https://api.openconceptlab.org/orgs/SIHSALUS/sources/sihsalus/2026-07-16-02`.
Los ZIP se importan localmente mediante Initializer. La migración al servidor
institucional no está habilitada y no se modificaron credenciales de ambientes.

Los cinco escenarios de CI permanecen activos. `ocl-fresh` y `ocl-upgrade`
comprueban el catálogo operativo sobre el runtime actual fijado, incluyendo
identidades, pesos, observaciones previas, historia y reinicio. El artefacto
temporal de extracción de pesos ya cumplió su función diagnóstica y se retiró;
las comparaciones completas siguen en el ensayo.

## Propuesta que debe retomarse

La API institucional es `https://api.gidis-terminology.duckdns.org`. Se prepararon
estos snapshots con `released: false`; permanecen fuera de `configuration/`:

| Fuente | Candidato | SHA-256 del export oficial combinado descargado |
| --- | --- | --- |
| `sihsalus` | `2026-10-16-1` | `e9fb3c4cefc8435cafd87e3690e7e4c60cf2d2f0e02f991ad9e18f2358373b3a` |
| `anatomia-procedimientos` | `2026-10-16-1` | `f9fe22e1e4545da70cb3a9e892c143885a88c7b20594719e313896571cdf8259` |

La corrección de talla al nacer (#391) está preparada en el concepto
`SIHSALUS/sihsalus:382`, UUID `bf82beb1-d3b8-400e-8160-90869cad8136`:
`allow_decimal: true`, conservando datatype Numeric, unidad cm e identidad.
El catálogo operativo aún mantiene `allow_decimal: false`; no anunciar esa
corrección como disponible ni redondear mediciones para eludirla.

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

**Publicación pendiente:** la propuesta `ocl-publication-proposal-20261022.json`,
SHA-256 `e1502074c599a65901b36db2a8cbe462c8d08373adb3f3d3b5ec3a432a60c31f`,
propone crear seis versiones `2026-10-22-01` y publicar el snapshot existente
`anatomia-procedimientos/2026-10-16-1`. Este último conserva sus 121 conceptos,
266 mappings y configuración, sin cambios clínicos. La propuesta exige comprobar
los exports congelados y la configuración antes de marcar cada versión como
publicada; aún requiere revisión y aprobación humana del responsable del dominio.

La aplicación en HEAD no actualizó el paquete ni publicó versiones. Los pesos
por defecto compatibles se conservaron. La publicación OCL y adopción por
content/distro requieren decisiones separadas. Las diferencias históricas de
QLTY descritas en #269 requieren una revisión propia antes de promover el
catálogo; esta comparación no autoriza sobrescribirlas.

Para cerrar el pendiente:

1. Revisar y aprobar la propuesta de publicación con el responsable de terminología.
2. Publicar versiones oficiales y descargar sus exports; actualizar juntos los
   ZIP y la suscripción, preservando las identidades y exclusiones históricas.
3. Pasar instalación nueva, actualización desde una versión publicada y reinicio:
   conservar pesos, observaciones y checksums, y guardar/reabrir `30.1 cm`.
   Contrastar el estado real de QLTY y resolver sus divergencias antes de promover.
4. Verificar acceso autenticado al servidor institucional y aceptación clínica
   antes de desplegar. El secret de CI no cambia `OMRS_OCL_TOKEN` del backend.

Responsables: terminología para el catálogo, módulo OCL para su importación,
distro para el runtime y responsable clínico para la aceptación de #391.
Si algún ambiente recibió el candidato fallido, evaluar su estado antes de
actualizar: retroceder sólo el ZIP o borrar checksums no recupera el orden perdido.
