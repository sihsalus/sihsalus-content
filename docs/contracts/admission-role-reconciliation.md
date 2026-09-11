# Reconciliación de identidades del rol de Admisión

Estado: CANDIDATA EN REVISIÓN — NO PUBLICAR NI DESPLEGAR.

El PR #223 se revisa separadamente del permiso `Delete Relationships`, publicado
en #222 / `1.25.15`. La candidata `1.25.16` requiere CI del SHA final, aprobación
independiente y los controles de actualización siguientes. Declarar una versión
en esta rama no la reserva en Maven Central ni aprueba su publicación.

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

Cada identidad existente debe tener exactamente los 58 privilegios del rol
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
establece esa configuración. Esta rama no modifica el distro ni ningún host.

No se deben borrar checksums, modificar el historial o relajar las
precondiciones para conseguir un arranque verde.

## Validación reproducible y límites

Las pruebas Python comprueban la estructura del changelog y las consultas de
política compatibles con SQLite. No traducen la migración para simular
transacciones MariaDB ni presentan ese modelo como una prueba de Liquibase.

El harness de integración usa MariaDB `10.11.7`, Liquibase `4.32.0` y JDBC
MariaDB `3.5.4`, correspondientes al stack examinado de OpenMRS `2.8.9`.
Ejecuta el changelog completo sobre un esquema mínimo sintético, con estados
históricos y fallos inducidos. No inicia OpenMRS, no ejecuta Initializer y no
valida permisos efectivos de cuentas clínicas.

El ensayo adicional `admission-initializer.yml` usa el backend publicado fijado
por digest y bases desechables en un runner GitHub hospedado. Conserva la
configuración ajena al paquete SIH de esa imagen y sustituye únicamente archivos
propios verificados. Arranca la baseline `1.25.15`, conserva su historial y
checksums reales y prueba por separado el CSV histórico sin cambios y el CSV
actualizado con lectura de bitácora. Incluye
rechazo de una política incompatible, un CSV canario posterior que debe quedar
sin cargar, reintento sin borrar checksums e idempotencia. La prueba REST acotada
comprueba lectura, denegación de borrado permanente y anulación de una relación
sintética activa. Sus resultados deben leerse por fase: definir el ensayo no
equivale a haberlo aprobado ni sustituye aceptación clínica o revisión operativa.

Consultar el [README del ensayo de Initializer](../../.github/integration/admission-initializer/README.md)
para los pins, aislamiento, aserciones y límites. No ejecutarlo contra una
instalación existente ni trasladar sus credenciales sintéticas a otro entorno.

Comprobaciones rápidas desde la raíz:

```sh
python3 .github/scripts/test_admission_role_reconciliation.py
python3 .github/scripts/validate_liquibase.py
python3 .github/scripts/validate_csv_widths.py
python3 .github/scripts/test_csv_widths.py
mvn --batch-mode --no-transfer-progress spotless:check clean verify --file pom.xml
git diff --check origin/main...HEAD
```

El comando del harness es:

```sh
mvn --batch-mode --no-transfer-progress --file .github/integration/admission-role-reconciliation/pom.xml test
```

Requiere exclusivamente la base desechable sintética descrita en el README del
harness. El workflow `admission-role-reconciliation.yml` la crea aislada en CI;
no utilizar credenciales, servicios ni bases de instalaciones existentes. El
job de build/publicación depende de este workflow: no basta que una prueba
independiente termine después de publicar el paquete.

Cada ejecución debe registrar `PASSED`, `FAILED`, `NOT RUN` o `BLOCKED`, comando,
SHA y entorno. No atribuir CI de un SHA anterior al candidato corregido. El
workflow `Validate with SIHSALUS` actual valida un artefacto ya publicado; no
es un gate de actualización del PR ni sustituye este harness.

## Gates antes de merge, publicación y actualización

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
5. Confirmar que la versión candidata sigue inédita antes del merge y coordinar
   el pin del distro solo tras completar los controles. No reutilizar una
   versión publicada ni desplegar directamente desde esta rama.

No hay un rollback automático que reconstruya qué identidad tenía cada usuario
antes de consolidarlas. Revertir el paquete no deshace una migración confirmada.
La recuperación debe usar el respaldo y procedimiento coordinados, no borrar
roles o referencias a mano. Todas las pruebas son con datos sintéticos y sin
acceso a producción, pacientes reales ni secretos.
