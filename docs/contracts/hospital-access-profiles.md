# Perfiles funcionales del hospital

La referencia inicial son los permisos efectivos observados en el hospital el
14 de septiembre de 2026. El contrato revisado queda en
[hospital-access-profiles.json](hospital-access-profiles.json); los cambios
posteriores deben revisarse en el repositorio y probarse antes de promoverlos.
Una edición manual de producción requiere comparación y revisión, no una
sincronización automática hacia todos los entornos.

## Alcance y decisiones

| Cuenta funcional | Referencia y composición | Permisos efectivos base |
| --- | --- | ---: |
| `admision` | `Admision` + `SIHSALUS Login` | 76 |
| `consulta.externa` | Perfil de consulta de cuentas hospitalarias activas: `Provider` + `SIHSALUS Consulta Externa` + `SIHSALUS Login` | 169 |
| `enfermeria.triaje` | `Provider` + `SIHSALUS Enfermero Triaje` + `SIHSALUS Login` | 66 |
| `farmacia` | `Farmacia` + `Inventory Dispensing` + `Inventory Manager` + `Inventory Reporting` + `Provider` + `SIHSALUS Login` | 103 |
| `laboratorio` | `Provider` + `SIHSALUS Laboratorio` + `SIHSALUS Login` | 70 |
| `soporte` | `SIHSALUS Soporte` + `SIHSALUS Login` | 503 |

Los conjuntos incluyen la herencia y los permisos implícitos de `Anonymous` y
`Authenticated`. La representación REST de `User.privileges` no incluye estos
roles implícitos: una verificación debe considerar su unión y comprobar la
autorización con sesiones reales. Los totales orientan la lectura; el criterio
de aceptación es la igualdad de los nombres de permisos, sensible a mayúsculas.

Admisión utiliza únicamente el rol funcional canónico `Admision`, con sus 59
privilegios de `roles-core.csv`. La versión `1.25.24` retira el suplemento
`SIHSALUS Admision Hospitalaria` y sus 15 capacidades adicionales; los permisos
efectivos del perfil pasan de 91 a 76. La
[migración de admisión](admission-role-reconciliation.md) reconoce su definición
exacta y solo elimina sus asignaciones si cada usuario conserva el rol canónico.
Una política modificada, herencia o uso del suplemento en otro módulo bloquea
la operación para revisión. No se crean ni eliminan cuentas. Esta reducción de
acceso exige aceptación funcional antes de promover el contenido.

Consulta externa reproduce el perfil activo. La cuenta genérica retirada del
hospital tenía permisos adicionales de FUA y no es la referencia. Su definición
existente en `roles-core.csv` ya corresponde al perfil activo; una desviación
manual debe reconciliarse con esa definición.

Farmacia incorpora las capacidades de dispensación, gestión e informes de
inventario observadas en las cuentas operativas. La asignación de estos roles no
crea almacenes, existencias ni ámbitos de operación de Stock Management.

Laboratorio utiliza el rol hospitalario explícito. El rol `Laboratorio` conserva
su contrato independiente de adjuntos, pero no se asigna al genérico homologado.
Así no se añaden creación/lectura de adjuntos ni el marcador `Delete Observations`
que no forman parte de la referencia hospitalaria. Este marcador no equivale a
prohibir toda anulación: `ObsService.voidObs` utiliza `Edit Observations`, que
el perfil sí conserva. La purga es una operación independiente.

La revisión del 21/09 añade únicamente `Get Patient Programs` a ambos perfiles
de Laboratorio. Los criterios maternos de los rangos de referencia llaman a
`ProgramWorkflowService.getPatientPrograms`, protegido por ese permiso en Core
2.8.9. Sin él, incluso una mujer sin inscripción materna puede recibir un error
de autorización al guardar temperatura: debe consultarse la inscripción antes
de descartarla. No se conceden creación, edición o purga de inscripciones.
La referencia hospitalaria anterior tenía 69 permisos efectivos; desde `1.25.24` el perfil
tiene 70 y necesita aceptación en el entorno. No se presenta como una aplicación
ya realizada ni como una ampliación de permisos para administrar alertas.

Soporte es un perfil administrativo amplio: sus 503 permisos incluyen gestión
de usuarios, roles, módulos, purgas y acceso clínico. Se asigna explícitamente al
genérico `soporte`, nunca como base de admisión o de los perfiles clínicos. No
hereda `System Developer`, `Privilege Level: Full` ni `Privilege Level: High`;
los privilegios que agreguen módulos futuros requieren revisión explícita.
El perfil no tiene `Purge Roles`; la prueba de administración permite crear y
editar un rol temporal, verifica el rechazo de su purga y deja la limpieza al
administrador de la prueba.
Esta homologación reproduce el acceso operativo observado en la revisión; la futura separación
entre soporte técnico, administración de identidades y acceso clínico sigue
siendo una decisión de política institucional.

## Perfiles de pruebas y diferencias declaradas

`gestion`, `obstetricia`, `cred` y `auditor` conservan sus perfiles de pruebas,
con conjuntos base de 74, 128, 134 y 112 permisos respectivamente. No se encontró
una equivalencia de producción revisada para convertirlos en políticas del
hospital. Se registran en `preservedTestProfiles` para poder detectar diferencias
entre DEV y QLTY sin presentar esos perfiles como una política ya aprobada.

El contrato de pruebas de DEV conserva `Record Clinical Audit Events` para admisión, consulta, triaje,
farmacia, laboratorio, obstetricia y CRED, mediante el rol de pruebas existente.
El auditor conserva además `View Clinical Audit Events`. El contrato de QLTY usa los conjuntos
base. Esta declaración de permisos no certifica el funcionamiento del receptor
de auditoría ni su aceptación clínica.

No se incluyen cuentas personales, contraseñas, hashes, identificadores de
pacientes ni exportaciones de usuarios. La provisión de credenciales sigue el
mecanismo de cada entorno; este contenido no cambia contraseñas.

## Propiedad de los metadatos y aplicación

Initializer carga los dos roles de `roles_hospital_operations.csv` y las cinco
definiciones de `privileges_hospital_compatibility.csv`. Estas últimas conservan
nombres de permisos de interfaz de la referencia hospitalaria; declararlos no
implementa nuevas operaciones de backend. El contenido no asigna automáticamente
los roles a personas ni sobreescribe roles de pruebas locales.

Los UUID de roles nuevos son estables; laboratorio y soporte utilizan los de la
referencia hospitalaria. Para instalaciones existentes, Initializer primero
busca por UUID y luego por nombre, conservando el UUID local cuando ya existe
ese nombre. QLTY ya tenía `SIHSALUS Soporte` con otro UUID: se conserva esa
identidad y se reconcilian sus permisos. No se borra/recrea el rol ni se modifican
sus claves mediante SQL. Este comportamiento corresponde al
[cargador nativo fijado de Initializer](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RolesCsvParser.java).

Para reconciliar una instalación existente:

1. Capturar roles, privilegios, herencia y asignaciones sin material de
   autenticación; comprobar qué usuarios dependen de cada rol que cambiará.
2. Comparar con el contrato. Si hay identidades en conflicto o una modificación
   concurrente, detener esa operación y revisar el delta.
3. Aplicar los metadatos con Initializer en el despliegue de contenido. Para una
   reconciliación puntual, la API nativa permite crear los mismos UUID y guardar
   los conjuntos completos de permisos y herencias; las cuentas existentes se
   actualizan por su UUID conservando sus demás propiedades.
4. Asignar explícitamente los roles del contrato a los genéricos del entorno.
   Los nombres genéricos no autorizan modificar una cuenta ajena a la cohorte.
5. Abrir sesiones nuevas, comparar los conjuntos efectivos, probar operaciones
   permitidas y denegadas, y comprobar que las asignaciones ajenas no cambiaron.
   Repetir la reconciliación no debe producir nuevas escrituras.

La operación puntual no introduce un job ni una dependencia de scripts en el
servicio. Un reinicio de la misma versión conserva los cambios persistidos; una
promoción de contenido debe incorporar estas declaraciones. Los checksums de
Initializer pueden omitir archivos sin cambios: no basta reiniciar para corregir
una edición manual de un rol ya cargado.

El respaldo previo permite restaurar primero las asignaciones y después los
conjuntos de los roles mediante la API. Antes de retirar metadatos creados por
la operación se comprueba que no tengan referencias. No se eliminan cuentas ni
registros de pacientes para revertir accesos.

## Verificación del repositorio

`validate_hospital_access_profiles.py` calcula herencia e implícitos y compara
los seis perfiles con la referencia completa. Rechaza ciclos, identidades
duplicadas, permisos desconocidos, superroles y contaminación administrativa de
los perfiles funcionales. Los tests introducen desviaciones deliberadas para
comprobar estas barreras. Los allowlists de colas y FUA incluyen únicamente los
UUID adicional revisado de soporte. El suplemento de Admisión queda prohibido
en los CSV de provisión y en el contrato funcional.

La integración existente con Initializer incorpora el delta exacto de estos
dos roles a su comparación completa de tablas, incluyendo una identidad de
soporte preexistente con UUID diferente. EMRAPI clasifica los nombres `app:` en
minúsculas como permisos de API y agrega las cinco definiciones nuevas a sus
roles Full/High en el siguiente arranque; esa transición se declara expresamente
en el resultado esperado. Los genéricos no heredan esos roles. La integración
conserva las comprobaciones de referencias ajenas y multiplicidades y exige que
el siguiente arranque conserve ese estado. Una fase posterior carga el CSV
actual y permite únicamente el permiso de Libro de Atenciones de Admisión y
la lectura de programas del rol canónico de Laboratorio. El escenario operativo
crea el alias antiguo y el suplemento conocidos, comprueba su retiro y verifica
que un reinicio no los vuelva a crear.
Solo se ejecuta en contenedores desechables propiedad del runner de GitHub.

```sh
python3 .github/scripts/validate_hospital_access_profiles.py
python3 .github/scripts/test_hospital_access_profiles.py
```

Ejecutar también las [comprobaciones comunes](../development.md#validación-local).

La validación de metadatos y API no sustituye pruebas completas de atención,
dispensación con existencias ni validación del receptor de auditoría. Los
resultados de cada aplicación se adjuntan al PR sin datos personales.

La atribución previa del 403 a Patient Flags se basó en el texto «evaluating
criteria». La regresión de
[`reference-range-access`](../../.github/integration/reference-range-access/README.md)
reproduce ese texto y la excepción de autorización con el evaluador nativo de
rangos de referencia, sin cargar Patient Flags. Esto corrige el diagnóstico de
esa reproducción local; sigue pendiente repetir el guardado REST en DEV/QLTY.
