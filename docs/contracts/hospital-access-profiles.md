# Perfiles funcionales del hospital

La referencia son los permisos efectivos observados en el hospital el
14 de septiembre de 2026. El contrato verificable queda en
[hospital-access-profiles.json](hospital-access-profiles.json).

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
privilegios de `roles-core.csv`. Desde `1.25.24` se retira el suplemento
`SIHSALUS Admision Hospitalaria` y sus 15 capacidades adicionales; los permisos
efectivos del perfil pasan de 91 a 76. La
[migración de admisión](admission-role-reconciliation.md) reconoce su definición
exacta y solo elimina sus asignaciones si cada usuario conserva el rol canónico.
Una política modificada, herencia o uso del suplemento en otro módulo bloquea
la operación para revisión. No se crean ni eliminan cuentas.

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

Ambos perfiles de Laboratorio incluyen `Get Patient Programs`. Los criterios
maternos de los rangos de referencia llaman a
`ProgramWorkflowService.getPatientPrograms`, protegido por ese permiso en Core
2.8.9. Sin él, incluso una mujer sin inscripción materna puede recibir un error
de autorización al guardar temperatura: debe consultarse la inscripción antes
de descartarla. No se conceden creación, edición o purga de inscripciones.
La referencia hospitalaria tenía 69 permisos efectivos; el perfil tiene 70.

Soporte es un perfil administrativo amplio: sus 503 permisos incluyen gestión
de usuarios, roles, módulos, purgas y acceso clínico. Se asigna explícitamente al
genérico `soporte`, nunca como base de admisión o de los perfiles clínicos. No
hereda `System Developer`, `Privilege Level: Full` ni `Privilege Level: High`;
los privilegios que agreguen módulos futuros requieren revisión explícita.
El perfil no tiene `Purge Roles`. Esta homologación reproduce el acceso operativo
observado; la separación entre soporte técnico, administración de identidades y
acceso clínico es una decisión de política institucional pendiente.

## Perfiles de pruebas y diferencias declaradas

`gestion`, `obstetricia`, `cred` y `auditor` conservan sus perfiles de pruebas,
con conjuntos base de 74, 129, 135 y 113 permisos respectivamente. No se encontró
una equivalencia de producción revisada para convertirlos en políticas del
hospital. Se registran en `preservedTestProfiles` para poder detectar diferencias
entre DEV y QLTY sin presentar esos perfiles como una política ya aprobada.

La revisión del 12/10 añade únicamente `View Metadata Via Mapping` a los conjuntos
de `obstetricia`, `cred` y `auditor`. Estos perfiles ya permiten leer neonatal
(`app:hoja.clinica.cred.neonatal`) o parto/puerperio
(`app:hoja.clinica.partoPuerperio`), donde el frontend consulta los vínculos
madre–niño. EMRAPI `3.5.1-sihsalus.1` resuelve el tipo de relación mediante
`getMetadataItem`; [Metadata Mapping 2.0.0 exige ese permiso de lectura](https://github.com/openmrs/openmrs-module-metadatamapping/blob/2.0.0/api/src/main/java/org/openmrs/module/metadatamapping/api/MetadataMappingService.java#L464).
El permiso nativo permite resolver metadatos por mapping en general; no tiene
alcance exclusivo al vínculo madre–niño. No concede `Manage Metadata Mapping`,
escritura de relaciones ni administración de roles. Los perfiles hospitalarios
y `gestion` conservan exactamente sus conjuntos anteriores; Soporte ya tenía
este permiso.

Los roles `SIHSALUS CRED - Pruebas`, `SIHSALUS OBSTETRICIA - Pruebas` y
`SIHSALUS Auditor - Pruebas` pertenecen al entorno y no tienen filas de provisión
en los CSV. La dependencia se declara en sus `expectedPrivileges` existentes,
sin crear otro rol ni extender Login, Triaje o Consulta Externa. La promoción
del paquete no modifica esos roles locales: el administrador debe comparar sus
permisos efectivos, respaldar el estado y añadir únicamente la lectura faltante
mediante la API nativa, conservando asignaciones y demás privilegios. Se verifica
después con una sesión nueva y el GET de
`emrapi/maternal/mothersAndChildren`, además de las operaciones denegadas; la
declaración del contrato no acredita el resultado operativo. La reversión restaura
el conjunto respaldado, sin tocar vínculos ni otros datos clínicos.

Un HTTP 200 con una excepción serializada no demuestra lectura correcta. El
frontend debe conservar el estado de error si la respuesta carece de `results`;
no se modifica para ocultar un fallo de autorización. Los permisos observados en
la sesión y el resultado del endpoint se verifican por separado.

El contrato de pruebas de DEV conserva `Record Clinical Audit Events` para admisión, consulta, triaje,
farmacia, laboratorio, obstetricia y CRED, mediante el rol de pruebas existente.
El auditor conserva además `View Clinical Audit Events`. El contrato de QLTY usa los conjuntos
base.

No se incluyen cuentas personales, contraseñas, hashes, identificadores de
pacientes ni exportaciones de usuarios. La provisión de credenciales sigue el
mecanismo de cada entorno; este contenido no cambia contraseñas.

### Inscripciones de CRED — reporte #387

La decisión del 16/10/2026 permite registrar, editar y anular inscripciones con
el perfil CRED. Se reutiliza `SIH SALUS Hoja Clinica Programas editar`, ya
provisionado por `roles-core.csv` (UUID `d80bc4fd-7781-4eca-9404-4d9dc061a800`).
El contrato del perfil añade ese rol y cuatro permisos efectivos:
`app:hoja.clinica.programas.editar`, `Add Patient Programs`,
`Edit Patient Programs` y `Delete Patient Programs`. `Get Programs` ya estaba
incluido. No se añade purga de inscripciones ni administración de usuarios.

Estos privilegios nativos permiten operar inscripciones de programas en general;
no tienen un alcance exclusivo a Control de Niño Sano. El frontend conserva las
reglas de elegibilidad y los controles de acceso registrados.

**Aplicación pendiente:** el contrato no asigna roles a usuarios y publicar
content no modifica el rol local de pruebas. Un administrador autorizado debe
respaldar las asignaciones de la cuenta CRED y añadir únicamente el rol existente,
sin sustituir sus otros roles. Esta tarea no ejecuta esa operación ni modifica
cuentas en DEV/QLTY. Validar después con una sesión nueva de CRED: creación,
edición y anulación de una inscripción sintética, además de denegación para un
perfil de consulta. Revertir retirando solo la asignación añadida.

## Propiedad de los metadatos y aplicación

Initializer carga los dos roles de `roles_hospital_operations.csv` y las cinco
definiciones de `privileges_hospital_compatibility.csv`. Estas últimas conservan
nombres de permisos de interfaz de la referencia hospitalaria; declararlos no
implementa nuevas operaciones de backend. El contenido no asigna automáticamente
los roles a personas ni sobreescribe roles de pruebas locales. EMRAPI clasifica
los nombres `app:` en minúsculas como permisos de API y los agrega a sus roles
Full/High en el siguiente arranque; los genéricos no heredan esos roles. Cada
nombre `app:` que introduce una revisión del contenido se declara además en
`CURRENT_EMRAPI_ADDITIONS` del ensayo de Initializer, de modo que esa concesión
del reinicio quede revisada en el diff en lugar de aparecer como un cambio RBAC
no aprobado.

Los UUID de roles nuevos son estables; laboratorio y soporte utilizan los de la
referencia hospitalaria. Para instalaciones existentes, Initializer primero
busca por UUID y luego por nombre, conservando el UUID local cuando ya existe
ese nombre. QLTY ya tenía `SIHSALUS Soporte` con otro UUID: se conserva esa
identidad y se reconcilian sus permisos. No se borra/recrea el rol ni se modifican
sus claves mediante SQL. Este comportamiento corresponde al
[cargador nativo fijado de Initializer](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RolesCsvParser.java).
Los checksums de Initializer pueden omitir archivos sin cambios: no basta
reiniciar para corregir una edición manual de un rol ya cargado.

## Validación local

```sh
python3 .github/scripts/validate_hospital_access_profiles.py
python3 .github/scripts/test_hospital_access_profiles.py
```

Ejecutar también las [comprobaciones comunes](../development.md#validación-local).
