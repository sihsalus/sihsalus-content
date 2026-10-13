# Sustitución de Liquibase por dominios declarativos de Initializer

Revisión de `configuration/liquibase/liquibase.xml` tras la reorganización de
`configuration/`. Identifica las capacidades que faltan en Initializer y la
compatibilidad necesaria para sustituir SQL por dominios declarativos.

## Publicación

Los doce changesets del XML están distribuidos en la versión publicada `1.25.24`,
incluidos `reconcile-admission-operational-alias-20260921` y
`retire-admission-hospital-supplement-20260921`, añadidos en esa versión. El
inventario por ambiente y las rutas de actualización siguen pendientes; no se
consultaron servidores para esta revisión. El checkout del distro declara content
`1.25.20`, por lo que no todos sus consumidores han pasado necesariamente por
`1.25.24`.

## Capacidad comprobada en la versión consumida

El distro fija Initializer `2.13.0-sihsalus.1`, con el archivo de fuentes fijado
en `backend/omod-sources.lock`. Initializer ya ejecuta este XML mediante
`LiquibaseLoader2_5`. La sustitución buscada es pasar de SQL a sus dominios
declarativos, conservando la semántica y el historial.

| Responsabilidad | Changesets / líneas de sus bloques | Situación y componente responsable |
| --- | ---: | --- |
| Reconciliar roles de Admisión y UUID de Triaje | 4 / 1.382 | Los permisos vigentes ya están en `roles/`. El parser rechaza renombrar una identidad existente y no fusiona asignaciones ni referencias de módulos. Sustituir estas transiciones exige capacidades del backend; también puede evaluarse su retirada cuando dejen de soportarse sus entradas históricas. |
| Normalización antigua de Admisión `20260722` | 1 / 62 | La reconciliación `20260907`, que se ejecuta antes, ya elimina el alias y establece el UUID canónico para las entradas soportadas. Es candidata a retirada por redundancia, sujeta a una estrategia probada de historial; no requiere otro loader. |
| Provisionar y asociar el Form de Visit Notes | 4 / 123 | `encountertypes/` ya declara su tipo de encuentro. Falta un dominio de metadata `Form` con UUID explícito y conservación de entidades existentes. Es la primera capacidad reutilizable que conviene incorporar a Initializer. |
| Retirar CE-001 1.0.1 y comprobar la identidad canónica | 2 / 94 | AMPATH actualiza el recurso de esquema JSON antes de aplicar `retired`. Reintroducir el formulario viejo como JSON para retirarlo sobrescribiría su esquema histórico. Hace falta una operación de metadata que conserve recursos y encuentros. |
| Ampliar `concept_name.name` a 500 caracteres | 1 / 4 | El mapping de Core 2.8.9 declara 255 caracteres; el bundle contiene 443 entradas de nombre OCL que superan 255, con máximo 498. La ampliación sigue siendo necesaria. La capacidad de esquema corresponde a Core, no a un CSV. |

Fuentes revisadas del mismo pin de Initializer:

- `Domain`: no declara un dominio genérico `forms`; Liquibase precede a los
  dominios de metadata.
- `RolesCsvParser`: busca por UUID/nombre y rechaza cambios de nombre; no
  reasigna el UUID de un rol encontrado por nombre.
- `RoleLineProcessor`: reemplaza privilegios y herencias desde el CSV. Este ya es
  el mecanismo vigente para mantener la política.
- `AmpathFormsLoader`: deriva el UUID de nombre/versión y actualiza el recurso de
  esquema existente. No sirve para provisionar el UUID arbitrario de Visit Notes
  ni para retirar un esquema conservando sus bytes.
- `MdsLoader`: importa con `PREFER_THEIRS`, tanto para coincidencias exactas como
  posibles. Aunque admite formularios, esa política no coincide con el contrato de
  Visit Notes, que conserva la metadata existente y solo completa una asociación
  nula.

También se inspeccionó `UserService` de Core `2.8.9`: ofrece guardar/purgar roles
y consultar usuarios por rol, pero no una operación de fusión de roles. Copiar
las consultas a tablas internas de otros módulos dentro de Initializer mantendría
el acoplamiento que se busca eliminar.

## Publicación, necesidad y retirada

Liquibase distingue una modificación de un changeset ejecutado de su ausencia en
el archivo: esta última evita su aplicación en bases futuras, pero obliga a
comprobar las dependencias y la equivalencia de resultados. Véase la
[explicación de Liquibase](https://www.liquibase.com/blog/dealing-with-changing-changesets).
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

Con el pin actual no hay una sustitución completa por CSV: faltan el dominio
`Form` y la operación de identidad de roles. Los doce changesets tampoco tienen
que conservarse activos indefinidamente: hay al menos una normalización
redundante y otros retiros dependen de las rutas de actualización soportadas. El
XML permanece intacto hasta probar una estrategia de reducción que preserve esos
contratos.
