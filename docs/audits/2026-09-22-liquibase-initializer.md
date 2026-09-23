# Sustitución de Liquibase por dominios declarativos de Initializer

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

Revisión del 22 de septiembre de 2026 sobre el contenido de `main` `c4abc8f`,
con la reorganización local de `configuration/`. Esta revisión identifica las
capacidades que faltan y la compatibilidad necesaria; no implementa la sustitución
ni acredita la ejecución de migraciones en un entorno.

## Evidencia de publicación

Los [metadatos de Maven Central](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/maven-metadata.xml)
anuncian `1.25.24`, con `lastUpdated=20260922215347`. Se descargó e inspeccionó el
[ZIP publicado](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/1.25.24/sihsalus-content-1.25.24.zip).
Su archivo `configuration/backend_configuration/liquibase/liquibase.xml` es
idéntico, byte por byte, a `configuration/liquibase/liquibase.xml` de este checkout:

```text
SHA256 d451be48e756d3b03d5b76244316f51231caafe8de4b109367c33450180fd0a0
```

Los doce changesets están distribuidos, incluidos los dos que la
[revisión del día anterior](2026-09-21-admission-maintainability.md) identificaba
como candidatos. Sus hashes literales son:

| Changeset añadido en 1.25.24 | SHA256 del bloque completo |
| --- | --- |
| `reconcile-admission-operational-alias-20260921` | `66684444789d2e0676ebd0ed79915a67487821d11860aa8bb4bc348557e78ef6` |
| `retire-admission-hospital-supplement-20260921` | `28ad32c1c5c5b745230347aeba266ea99029f7179b8cc535c1921c6d3839ea39` |

La publicación no demuestra qué ambientes los ejecutaron. El inventario por
ambiente y las rutas de actualización siguen pendientes; no se consultaron
servidores para esta revisión. El checkout local del distro declara content
`1.25.20`, por lo que tampoco demuestra que todos sus consumidores hayan pasado
por `1.25.24`.

## Capacidad comprobada en la versión consumida

El distro fija Initializer `2.13.0-sihsalus.1`, compilado desde
`3077975fb4f58c91ff3113d7fed1e3df88829476`. Se descargó el archivo de fuentes de
ese commit y se verificó el SHA256 fijado por `backend/omod-sources.lock`:

```text
a750faaa6485b7f5716db8dcd94552102710cd9af0a80b067982133b02365e69
```

Initializer ya ejecuta este XML mediante
[LiquibaseLoader2_5](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api-2.5/src/main/java/org/openmrs/module/initializer/api/loaders/LiquibaseLoader2_5.java).
La sustitución buscada es pasar de SQL a sus dominios declarativos, conservando
la semántica y el historial.

| Responsabilidad | Changesets / líneas de sus bloques | Situación y componente responsable |
| --- | ---: | --- |
| Reconciliar roles de Admisión y UUID de Triaje | 4 / 1.382 | Los permisos vigentes ya están en `roles/`. El parser rechaza renombrar una identidad existente y no fusiona asignaciones ni referencias de módulos. Sustituir estas transiciones exige capacidades del backend; también puede evaluarse su retirada cuando dejen de soportarse sus entradas históricas. |
| Normalización antigua de Admisión `20260722` | 1 / 62 | La reconciliación `20260907`, que se ejecuta antes, ya elimina el alias y establece el UUID canónico para las entradas soportadas. Es candidata a retirada por redundancia, sujeta a una estrategia probada de historial; no requiere otro loader. |
| Provisionar y asociar el Form de Visit Notes | 4 / 123 | `encountertypes/` ya declara su tipo de encuentro. Falta un dominio de metadata `Form` con UUID explícito y conservación de entidades existentes. Es la primera capacidad reutilizable que conviene incorporar a Initializer. |
| Retirar CE-001 1.0.1 y comprobar la identidad canónica | 2 / 94 | AMPATH actualiza el recurso de esquema JSON antes de aplicar `retired`. Reintroducir el formulario viejo como JSON para retirarlo sobrescribiría su esquema histórico. Hace falta una operación de metadata que conserve recursos y encuentros. |
| Ampliar `concept_name.name` a 500 caracteres | 1 / 4 | El mapping de Core 2.8.9 declara 255 caracteres; el bundle contiene 443 entradas de nombre OCL que superan 255, con máximo 498. No se ha demostrado que esta ampliación sea prescindible. La capacidad de esquema corresponde a Core, no a un CSV. |

Fuentes revisadas del mismo pin:

- [Domain](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/Domain.java): no declara un dominio genérico `forms`; Liquibase precede a los dominios de metadata.
- [RolesCsvParser](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RolesCsvParser.java): busca por UUID/nombre y rechaza cambios de nombre; no reasigna el UUID de un rol encontrado por nombre.
- [RoleLineProcessor](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RoleLineProcessor.java): reemplaza privilegios y herencias desde el CSV. Este ya es el mecanismo vigente para mantener la política.
- [AmpathFormsLoader](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/loaders/AmpathFormsLoader.java): deriva el UUID de nombre/versión y actualiza el recurso de esquema existente. No sirve para provisionar el UUID arbitrario de Visit Notes ni para retirar un esquema conservando sus bytes.
- [MdsLoader](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/loaders/MdsLoader.java): importa con `PREFER_THEIRS`, tanto para coincidencias exactas como posibles. Aunque admite formularios, esa política no equivale al contrato de Visit Notes, que conserva la metadata existente y solo completa una asociación nula.

También se inspeccionó `UserService` del artefacto Core `2.8.9` usado por las
pruebas: ofrece guardar/purgar roles y consultar usuarios por rol, pero no una
operación de fusión de roles. Copiar las consultas a tablas internas de otros
módulos dentro de Initializer mantendría el acoplamiento que se busca eliminar.

## Publicación, necesidad y retirada

Estar publicado no demuestra que cada changeset siga siendo necesario ni impide
técnicamente retirarlo del changelog activo. Liquibase distingue una modificación
de un changeset ejecutado de su ausencia en el archivo: esta última evita su
aplicación en bases futuras, pero obliga a comprobar las dependencias y la
equivalencia de resultados. Véase la [explicación de Liquibase](https://www.liquibase.com/blog/dealing-with-changing-changesets).
En este repositorio, `AGENTS.md` exige además preservar el historial publicado y
definir y probar expresamente cualquier transición.

La normalización `20260722` ilustra esa diferencia: su precondición requiere el
alias que elimina `20260907`. Las pruebas existentes de historia pendiente
comprueban que termina como `MARK_RAN`, y las de historia aplicada conservan su
checksum. Esto identifica una redundancia para las entradas soportadas; todavía
no prueba un changelog reducido. Su retirada debe ensayar instalación nueva,
normalización pendiente/ejecutada/`MARK_RAN` y reinicio, sin reescribir registros
anteriores. No se necesita inventariar una capacidad nueva de Initializer para
evaluar este caso.

## Secuencia de sustitución

1. Incorporar en el proyecto de Initializer una capacidad de metadata `Form`
   reutilizando `FormService` y sus cargadores existentes: UUID explícito,
   asociación a un encounter type ya cargado y operaciones que preserven esquema,
   encuentros y metadata existente según el contrato de Visit Notes/CE-001.
   Probar creación, reinicio, actualización, asociaciones nulas/incompatibles y
   retiro con recursos históricos intactos. No añadir todavía un CSV `forms/`
   al content: el pin actual no lo procesaría.
2. Para roles, resolver primero la operación de identidad en el componente que
   la mantiene. Reutilizar los CSV actuales para la política de destino y las
   fixtures existentes para reconocer entradas históricas. Conservar las
   condiciones de rechazo, la atomicidad, las asignaciones y los datos auditables
   de cada módulo. No convertir Initializer en otro reconciliador SQL de tablas
   ajenas ni copiar listas operativas de permisos.
3. Publicar/adoptar la versión de backend que incorpore las capacidades probadas.
   Establecer qué versiones de content pueden actualizar directamente y si hace
   falta una versión puente. Inventariar el historial real de los consumidores
   antes de retirar una ruta de actualización.
4. Cambiar el content en una versión nueva, con una sola definición operativa por
   entidad y una estrategia explícita para conservar el historial publicado.
   No modificar sus hashes, marcar cambios como ejecutados ni forzar recargas.
   Separar o archivar XML por sí solo no reemplaza su responsabilidad.
5. Usar los ensayos existentes de instalación nueva, actualización, reinicio,
   fallo/reintento y autorización. Comprobar los mismos UUID, referencias,
   recursos de formulario y filas del historial Liquibase antes de retirar SQL.

No se ha demostrado una sustitución completa por CSV con el pin actual.
Tampoco se ha demostrado que los doce changesets deban conservarse activos
indefinidamente: hay al menos una normalización redundante y otros retiros
dependen de las rutas de actualización soportadas. El XML permanece intacto
hasta probar una estrategia de reducción que preserve esos contratos.

## Validación de la reorganización

Evidencia local del [PR #238](https://github.com/sihsalus/sihsalus-content/pull/238),
hasta el commit `c38e044`. Los resultados siguientes no se extienden a commits posteriores.

El ZIP construido con `mvn clean verify --batch-mode --file pom.xml` conserva
las rutas y los bytes de los 207 archivos del ZIP público `1.25.24`, descargado
de nuevo para esta comprobación. Por ello se conserva la versión del paquete.
El SHA256 del ZIP público es
`75149b19e284c1b72d8065d4a642d659a68add0110b59b6278768c9195fb3309`;
la comparación se hizo por entrada, sin exigir igualdad de fechas o compresión.

Pasaron los 14 validadores Python, la validación de rangos, las cuatro regresiones
Bash, 128 pruebas Python de dominio, 66 del arnés y nueve pruebas Java
(`HarnessGuardTest` y `ReferenceRangeAccessTest`, ejecutadas localmente con Java 21).
El arnés también extrajo correctamente los dos commits históricos fijados,
`57690d4` y `8000b27`, con sus 200 archivos por escenario y las rutas de ejecución
esperadas. Se revisaron el diff y los enlaces locales de documentación.

Las seis regresiones de AMPATH comprueban con archivos sintéticos la identidad
persistida, las versiones distintas y el rechazo de entradas vacías o inválidas.
Antes de corregir el validador, se reprodujo que aceptaba dos JSON con el mismo
nombre/versión y UUID JSON distintos, y también una carpeta sin formularios.
El cálculo de identidad se comparte con CE-001 e historia social.

Los ensayos completos de MariaDB e Initializer no se ejecutaron localmente:
Docker no tenía un daemon disponible y el arnés de Initializer exige un runner
desechable de GitHub. Consultar los checks del PR para el SHA que se desea integrar.
La igualdad del paquete no sustituye la evidencia de instalación nueva,
actualización y reinicio.
