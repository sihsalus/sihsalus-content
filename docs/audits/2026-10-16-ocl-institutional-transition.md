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

Para cerrar el pendiente:

1. Resolver la pérdida de pesos con el responsable de terminología. Contrastar
   por UUID la propuesta con la línea publicada y con los ambientes soportados.
2. Publicar versiones oficiales y descargar sus exports; actualizar juntos los
   ZIP y la suscripción, preservando las identidades y exclusiones históricas.
3. Pasar instalación nueva, actualización desde una versión publicada y reinicio:
   conservar pesos, observaciones y checksums, y guardar/reabrir `30.1 cm`.
4. Verificar acceso autenticado al servidor institucional y aceptación clínica
   antes de desplegar. El secret de CI no cambia `OMRS_OCL_TOKEN` del backend.

Responsables: terminología para el catálogo, módulo OCL para su importación,
distro para el runtime y responsable clínico para la aceptación de #391.
Si algún ambiente recibió el candidato fallido, evaluar su estado antes de
actualizar: retroceder sólo el ZIP o borrar checksums no recupera el orden perdido.
