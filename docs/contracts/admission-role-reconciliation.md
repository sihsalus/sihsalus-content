# Reconciliación de identidades del rol de Admisión

Estado: distribuido en `1.25.24` mediante el PR #233; la publicación y los bytes
del XML se comprobaron en la [revisión del 22 de septiembre](../audits/2026-09-22-liquibase-initializer.md).
La aceptación funcional y la ejecución por ambiente requieren evidencia propia.
Integra la migración propuesta en #234 y retira el suplemento de Admisión de la
propuesta anterior de #233.
La reconciliación `20260907` ya está publicada; se conserva literalmente,
con sus checksums y guardas. Los resultados de CI corresponden al SHA del PR;
no equivalen a un despliegue en el hospital.

## Única fuente de permisos y alias operativo

`configuration/roles/roles-core.csv` define el rol
canónico `Admision` y sus 59 privilegios actuales. La migración publicada
`reconcile-admission-operational-alias-20260921` reconoce una entrada histórica
adicional: `Admision` con su UUID canónico y exactamente los 58 privilegios de
`1.25.15`, junto con `SIHSALUS Admision` con los 55 privilegios exactos de
`admission-operational-legacy-privileges.txt`. Esa fixture reconoce una entrada
de migración; no define un segundo rol ni una política de ejecución.

Después de validar esquema, políticas, UUID, herencias e historial, traslada las
asignaciones de usuarios y las referencias admitidas al rol canónico, y elimina
el alias en una transacción. No copia sus privilegios al rol destino. Conserva
los UUID e información de auditoría de los alcances, evita nuevas referencias
duplicadas y no modifica datos clínicos. Un fallo revierte esa transacción.

El resultado SQL conserva los 58 permisos canónicos; el changeSet publicado
valida ese resultado e Initializer aplica después el CSV actual de 59 permisos.
Respecto de la entrada antigua de 55, la política final retira 15 permisos y
agrega 19. Es una normalización explícita de acceso, no una unión de permisos.
No se mantienen overrides de roles por servidor ni un alias de compatibilidad.

Solo se admite ese conjunto exacto de 55 permisos con un destino canónico de
58; cualquier diferencia, herencia o referencia no soportada bloquea la carga.
Para las entradas originales de 57/58, la preparación de `20260921` no cambia RBAC y
la reconciliación publicada mantiene su validación. El registro de la
preparación sin cambios puede quedar confirmado aunque la guarda posterior
rechace otra entrada: no se promete atomicidad entre changeSets. El historial
anterior nunca se reescribe ni se eliminan checksums.

## Retiro del suplemento hospitalario

`retire-admission-hospital-supplement-20260921`, posterior a la normalización
histórica, retira exclusivamente `SIHSALUS Admision Hospitalaria` con UUID
`5aaa1628-a7be-5a4f-847c-a1c593bd364e` y los 15 privilegios exactos de la fixture
`admission-supplement-privileges.txt`. Esa fixture solo identifica la entrada
legada; el suplemento ya no se provisiona ni se asigna en el contrato funcional.

El destino debe ser `Admision` con el UUID canónico y los 58 privilegios de la
base o los 59 actuales. Cada usuario del suplemento debe tener ya ese rol.
La migración elimina únicamente las asignaciones y privilegios del suplemento
y después su definición, en una transacción; no modifica usuarios ni concede
acceso canónico a una persona que no lo tenía. El alias antiguo debe haberse
reconciliado antes. Una instalación sin suplemento no requiere cambios.

Las guardas rechazan políticas alteradas, identidades ambiguas, referencias o
esquemas desconocidos y herencias. El uso del suplemento en Patient Flags o en
ámbitos de inventario requiere revisión explícita: no se traslada automáticamente
porque podría ampliar visibilidad. Se conserva el historial publicado y se
requiere una ventana exclusiva de mantenimiento de metadatos. Los fallos
inyectados deben revertir también el retiro de asignaciones; repetir una carga
exitosa no modifica datos ni vuelve a crear el suplemento.

El resultado funcional pasa de 91 a 76 permisos efectivos, incluidos login e
implícitos. Esta reducción es deliberada y requiere validación con Admisión;
no se restablecen los 15 permisos mediante un segundo rol de compatibilidad.

## Corrección respecto de la primera candidata

Los seis changeSets `20260903` de `9855170` no se publicaron en `main`. Se
sustituyen por `reconcile-admission-role-20260907`, antes de
`normalize-admission-role-name-20260722`. Los changeSets históricos publicados
permanecen intactos: no se cambian checksums ni se usa `clearCheckSums`.

La secuencia anterior podía unir privilegios y herencias no aprobados, convertir
herencias en ciclos y dejar referencias trasladadas tras un fallo posterior.
Además, la normalización histórica podía escribir antes de las comprobaciones
nuevas e intentaba actualizar tablas de módulos ausentes.

La nueva operación comprueba el estado antes de modificar datos del rol y
agrupa la reconciliación en una sola transacción. Las migraciones anteriores de
otros metadatos siguen teniendo sus propias transacciones: no se promete
rollback de todo el changelog ni de toda la carga de contenido.

Una instalación que ejecutó cualquiera de los seis changeSets candidatos de
`20260903` queda fuera del contrato automático y debe revisarse. No se inventa
una reparación de un estado parcialmente migrado ni se borra su historial.

## Contrato de entrada y salida

Se reconocen únicamente `Admision`, `SIHSALUS Admision` y el UUID canónico
`71dcb611-756a-4ad3-a9bb-73b6cfe28066`. El UUID nunca se toma de un tercer rol.

Para la reconciliación publicada, cada identidad restante debe tener exactamente los 58 privilegios del rol
canónico de `1.25.15`, o esa misma lista sin `Delete Relationships`
(el contrato inmediatamente anterior a #222). La fixture histórica está fijada
en `admission-role-1.25.15.csv` y no se deriva del CSV actual. No se admiten otros permisos,
subconjuntos arbitrarios ni herencias que entren o salgan de cualquiera de las
dos identidades. Una diferencia se rechaza, no se considera autorización para
ampliar accesos ni para descartar excepciones operativas.

La salida SQL converge en esa lista histórica de 58 privilegios **solo después de
validar ambas identidades**. Si falta `Delete Relationships`, agrega únicamente
ese permiso, ya publicado en #222 / `1.25.15`. No crea privilegios nuevos ni
acepta excepciones fuera de la lista. Esto evita depender de que Initializer
vuelva a cargar un CSV idéntico al que ya tiene registrado por checksum.

El CSV actual tiene 59 privilegios: #224 añadió exclusivamente
`app:home.libroAtenciones`. Initializer aplica esa política declarativa después
de la reconciliación SQL cuando carga el CSV actualizado. No se añade lectura de
bitácora a la allowlist histórica ni se permite su edición o la purga de relaciones.
Un rol con esa concesión posterior pero sin haber ejecutado la reconciliación
queda fuera de la entrada automática y requiere revisión; no se relaja el guard
para aceptar una secuencia de actualización distinta.

| Estado inicial admitido                                                            | Resultado SQL                                                  |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Ninguna identidad existe                                                           | Sin crear roles; Initializer podrá cargar el CSV               |
| Solo existe la identidad histórica                                                 | Identidad canónica con sus usuarios y referencias              |
| Ambas existen, sin herencias y con políticas admitidas                             | Un único rol canónico, referencias compartidas sin duplicación |
| Solo existe `Admision` con UUID desactualizado                                     | Normalización del UUID, conservando las referencias por nombre |
| UUID canónico de un tercero, política incompatible o historial candidato ejecutado | Error antes de escribir datos de Admisión                      |

Las tablas existentes afectadas deben usar InnoDB. Las referencias conocidas
son `user_role.role`, `role_privilege.role`, ambas columnas de `role_role`,
`patientflags_tag_role.role` y `stockmgmt_user_role_scope.role`. Las dos últimas
son opcionales. Una FK hacia `role` fuera del contrato se rechaza, incluso si
no contiene datos. No se deshabilitan FKs ni se utiliza `INSERT IGNORE` para
ocultar incompatibilidades.

Las referencias legadas de Patient Flags se trasladan sin crear duplicados por
etiqueta/rol; no se eliminan duplicados canónicos preexistentes. Los alcances
de Stock Management conservan sus identificadores, UUID y demás columnas; solo
cambia el nombre de rol. La ausencia de FKs desconocidas no prueba la ausencia
de referencias lógicas o efectos de triggers en módulos personalizados: el
inventario de módulos, triggers y esquemas sigue siendo un requisito de
actualización. No se declara soporte automático para esquemas personalizados.

## Propiedad de los roles Full y High

Este paquete deja a EMRAPI la definición y el mantenimiento de `Privilege Level:
Full` y `Privilege Level: High`; se retiran únicamente esas dos filas de
`roles-core.csv`.
Su [activador fijado](https://github.com/openmrs/openmrs-module-emrapi/blob/a06a2efd651435609a1c4b39ef35501b3401ff5d/api/src/main/java/org/openmrs/module/emrapi/EmrApiActivator.java#L78)
crea los roles ausentes y mantiene sus privilegios en cada arranque. Las
[constantes del mismo pin](https://github.com/openmrs/openmrs-module-emrapi/blob/a06a2efd651435609a1c4b39ef35501b3401ff5d/api/src/main/java/org/openmrs/module/emrapi/EmrApiConstants.java#L79)
conservan los UUID `ab2160f6-0941-430c-9752-6714353fbd3c` y
`f089471c-e00b-468e-96e8-46aea1b339af`, respectivamente. Las herencias de otros
roles siguen resolviéndose por esos nombres.

Omitir estas filas no elimina los roles ni sus asignaciones existentes. Tampoco
retira privilegios del catálogo: el parser de roles solo
[busca privilegios existentes](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/utils/Utils.java#L461).
Los demás roles conservan su definición CSV. Full y High siguen incluidos en
las comparaciones completas del ensayo; no se excluyen roles, tablas ni grupos
de permisos para aceptar una actualización.

## Liquibase no garantiza la parada de Initializer

La revisión del pin de Initializer
`3077975fb4f58c91ff3113d7fed1e3df88829476` (`2.13.0-sihsalus.1`) confirma que:

- el modo predeterminado de carga es `continue_on_error`;
- `BaseFileLoader` puede capturar un error y continuar;
- un CSV sin cambios puede omitirse por checksum;
- cuando se procesa, `RoleLineProcessor` sustituye los privilegios y herencias
  por los declarados en el CSV, no los une con los anteriores.

En este stack, `LiquibaseLoader2_5` no escribe nuevos checksums de archivo: la
ejecución de changeSets queda en `liquibasechangelog`. No debe confundirse ese
historial con los checksums de CSV. El lector sí puede omitir un XML si encuentra
un checksum de archivo heredado coincidente; no se presume que siempre ejecute
el changelog ni se borra ese archivo para forzar una prueba.

Fuentes fijadas: [configuración de Initializer](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/InitializerConfig.java),
[carga y checksums](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/loaders/BaseFileLoader.java)
y [asignación de roles](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RoleLineProcessor.java).
La distinción entre historiales se verifica en
[LiquibaseLoader2_5](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api-2.5/src/main/java/org/openmrs/module/initializer/api/loaders/LiquibaseLoader2_5.java)
y [ConfigDirUtil](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/ConfigDirUtil.java).

Por ello, `onFail="HALT"` / `onError="HALT"` en Liquibase no demuestran que
Initializer ni la aplicación dejen de arrancar. Antes de habilitar esta
migración se debe coordinar y verificar
`initializer.startup.load=fail_on_error` en las propiedades de runtime/sistema,
y probar su efecto real en el backend. Una global property del contenido no
establece esa configuración. Este paquete no configura esas propiedades de
runtime ni modifica hosts.

No se deben borrar checksums, modificar el historial o relajar las
precondiciones para conseguir un arranque verde.

## Validación reproducible y límites

Cada capa aporta una evidencia distinta. Los comandos comunes están en la
[guía de desarrollo](../development.md); los README de integración fijan pins,
aislamiento, aserciones y límites.

| Capa | Contrato comprobado |
| --- | --- |
| [Pruebas Python](../../.github/scripts/test_admission_role_reconciliation.py) | Orden y bytes de los doce changesets publicados; SHA256 de la fixture histórica `admission-role-1.25.15.csv`; aceptación y rechazo de consultas de política compatibles con SQLite. No simulan transacciones MariaDB. |
| [MariaDB/Liquibase](../../.github/integration/admission-role-reconciliation/README.md) | Changelog completo sobre esquema sintético, referencias, estados históricos, transacciones, fallos y reintentos. No inicia OpenMRS ni comprueba autorización efectiva. |
| [Initializer](../../.github/integration/admission-initializer/README.md) | Backend fijado por digest, carga real, checksums, instalación nueva y actualización, reinicio y autorización REST con usuarios sintéticos. Solo en runners desechables de GitHub. |

Los tres escenarios de Initializer son independientes y deben pasar en el mismo
SHA antes de publicar:

- `upgrade`: baseline `1.25.15`, reinicio intacto, CSV histórico sin cambios,
  transición SQL de 57 a 58 permisos y carga posterior del CSV de 59. Compara
  todas las filas RBAC y referencias admitidas, incluidos Full/High. Comprueba
  rechazo, bloqueo del CSV canario y reintento sin borrar checksums.
- `operational`: baseline `1.25.15`, alias de 55 permisos y suplemento reconocidos;
  traslado de referencias, retiro del suplemento y reinicio idempotente.
- `fresh`: paquete completo sobre base vacía, historial real, UUID de Full/High y
  59 permisos de Admisión.

En los tres casos se exige lectura REST, purga denegada con 403 sin alterar la
relación activa y anulación con 204 que persiste `voided=1`. El atributo de pago
debe estar activo, ser FreeText y tener cardinalidad 0..1. HTTP 200 por sí solo
no satisface estos contratos.

Para las comprobaciones específicas locales, desde la raíz:

```sh
python3 .github/scripts/test_admission_role_reconciliation.py
python3 .github/scripts/validate_liquibase.py
```

No ejecutar fixtures de integración contra instalaciones existentes ni usar sus
credenciales. Cada resultado debe registrar `PASSED`, `FAILED`, `NOT RUN` o
`BLOCKED`, comando, SHA y entorno. No atribuir CI de un SHA anterior al candidato
corregido. Definir un ensayo tampoco equivale a haberlo aprobado.

`Validate with SIHSALUS` se invoca después de confirmar el artefacto público, o
manualmente. No sustituye estos ensayos ni la aceptación funcional; véase el
[flujo de publicación](../development.md#validación-y-publicación).

## Requisitos para cambios y actualizaciones

1. CI y revisión del diff final, sin alterar permisos declarativos ajenos a
   esta reconciliación. Una aprobación independiente es obligatoria; no usar
   el bypass del autor ni el modo administrador.
2. Probar el artefacto candidato con el Initializer exacto y su configuración
   de parada: CSV nuevo, checksum ya aplicado, precondición rechazada y
   recuperación después de un fallo. Verificar que no continúe una carga
   parcial ni se marque como aplicado un archivo fallido.
3. Validar con cuentas sintéticas los accesos permitidos y denegados después de
   toda la carga, junto con usuarios, etiquetas y alcances. La allowlist SQL
   no constituye una prueba de autorización OpenMRS.
4. Aprobar inventario de módulos/referencias, ventana sin cambios concurrentes
   de roles, respaldo recuperable y procedimiento de recuperación. El lock de
   Liquibase no bloquea a administradores que editen roles en paralelo.
5. Si cambia la metadata distribuida, usar una versión aún no publicada y
   coordinar el pin del distro tras completar los controles. `1.25.24` ya está
   publicada: no se reemplaza su artefacto. Los cambios solo de documentación
   no requieren una versión nueva. La actualización del entorno es una acción
   separada de publicar el paquete.

No hay un rollback automático que reconstruya qué identidad tenía cada usuario
antes de consolidarlas. Revertir el paquete no deshace una migración confirmada.
La recuperación debe usar el respaldo y procedimiento coordinados, no borrar
roles o referencias a mano. Todas las pruebas son con datos sintéticos y sin
acceso a producción, pacientes reales ni secretos.
