# Revisión de mantenibilidad de Admisión

Revisión del [PR #233](https://github.com/sihsalus/sihsalus-content/pull/233),
commit `6a9b5f38a9f170a48bec6dc32c3d31d2ba452db6`, contra `main`
`6a6121970deda5eda3a37996a259cb76fe165eaa`. Aplica el criterio del
[PR #236](https://github.com/sihsalus/sihsalus-content/pull/236): contenido
declarativo, reutilización y excepciones acotadas. Es una revisión del código;
no acredita qué cambios ejecutó cada entorno ni sustituye su aceptación funcional.

## Hallazgos y siguiente reducción

| Área | Decisión |
| --- | --- |
| Política vigente | Conservar `roles-core.csv` como definición operativa de `Admision`. El JSON de perfiles es una expectativa de prueba, no otro mecanismo de provisión. |
| Entradas históricas | Conservar las fixtures de 58, 55 y 15 permisos que identifican transiciones distintas. Derivarlas del CSV vigente cambiaría las entradas admitidas. |
| Migraciones publicadas | Preservar sus bytes, identidades, orden y checksums. La reconciliación `20260907` ya pertenece a esta historia. |
| Dos migraciones nuevas | El PR añade 911 líneas, con consultas de esquema y SQL sobre tablas de Core, Patient Flags y Stock Management. Su necesidad de compatibilidad no justifica convertir ese patrón en un cargador general. |
| Scripts de pruebas | Eliminar copias de políticas históricas y aserciones sobre la forma de SQL inmutable; reutilizar las fixtures y pruebas del motor real que ya existen. |

Las dos migraciones nuevas reconocen el alias operativo y retiran el suplemento;
la segunda solo admite usuarios que ya tienen `Admision`. No corresponde
sustituirlas por asignaciones automáticas ni por una unión de permisos.

Antes de modificar o retirar esas migraciones, falta inventariar las versiones e
historiales ejecutados en los entornos que realmente necesitan cada transición.
Después se debe justificar cada acceso a tablas de otro módulo y limitar la ruta
soportada a esos estados. Extraer el mismo SQL a otro archivo o generar sus guardas
desde un script no elimina el acoplamiento.

La excepción de migración debe quedar asociada al seguimiento existente de
[permisos operativos #33](https://github.com/sihsalus/sihsalus-frontend.tasktree/issues/33),
con responsable de mantenimiento y condición de cierre explícitos. Esta revisión
no asigna una persona ni declara aprobada esa excepción. La condición propuesta es
concluir las transiciones soportadas y mantener su historia congelada; cualquier
nueva capacidad general debe resolverse en el componente responsable.

## Publicación e inventario comprobados

Comprobación del 21 de septiembre de 2026, entre las 23:10 y 23:17 UTC.
El PR #223 fue fusionado el 8 de septiembre, como
`1025f7339a98ba2a6837dd0f33ed2c2e14d9a436`, cuyo POM declara `1.25.16`.
Sin embargo, los [metadatos de Maven Central](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/maven-metadata.xml)
no incluyen esa versión y su POM devolvió HTTP 404. El
[build de ese merge](https://github.com/sihsalus/sihsalus-content/actions/runs/34186600014)
terminó con fallo. Se inspeccionaron directamente los ZIP publicados:

| Paquete | Changesets | Permisos de `Admision` en CSV | Reconciliación `20260907` |
| --- | ---: | ---: | --- |
| [1.25.15](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/1.25.15/sihsalus-content-1.25.15.zip) | 9 | 58 | Ausente; contiene la normalización `20260722`. |
| [1.25.17](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/1.25.17/sihsalus-content-1.25.17.zip) | 10 | 59 | Presente, con el SHA256 congelado por las pruebas. |
| [1.25.20](https://repo.maven.apache.org/maven2/io/github/proyecto-santaclotilde/sihsalus-content/1.25.20/sihsalus-content-1.25.20.zip) | 10 | 59 | Presente, con el mismo SHA256. |

El bloque literal de la reconciliación tiene SHA256
`d2deb4caccce550305b335840175e769e8bd3d35cd1185de1cd966f715b5eef8`.
El XML completo de `1.25.17` y `1.25.20` también es idéntico. Ninguno de los
tres ZIP inspeccionados contiene las dos migraciones candidatas `20260921`.
Esto demuestra distribución de la migración histórica, no su ejecución por host.

La inspección operativa fue de solo lectura y no devolvió datos clínicos ni
identidades de usuarios. Se verificó OpenVPN conectado y la ruta privada antes
de intentar acceder al servidor del hospital.

| Entorno | Evidencia obtenida | Pendiente |
| --- | --- | --- |
| DEV | SSH disponible; backend saludable con tag `sha-7e09dce7d2dc8ae108435bff515232a5d3ce1812`; MariaDB `10.11.7` saludable. | Historial SQL, metadata instalada y referencias de roles. |
| QLTY | SSH disponible; backend saludable con tag `sha-11fceb91c3c21f1261b88e5c61196be673b88dba`; MariaDB `10.11.7` saludable. | Historial SQL, metadata instalada y referencias de roles. |
| Hospital | OpenVPN conectado; el intento SSH por la ruta privada devolvió `Network is unreachable`. | Identidad y estado del backend, historial y referencias. |

Los comandos de consulta SQL de DEV/QLTY fueron bloqueados por el entorno local
con `Operation not permitted` antes de conectar por SSH. No se obtuvo resultado
SQL y no se aplicó ninguna migración. La imagen del backend y su healthcheck no
demuestran qué metadata pudo cargarse después ni qué cambios fueron ejecutados.

Para cerrar el inventario faltan los IDs, autores, rutas, fechas, estado y
checksums de Admisión en los historiales existentes; las definiciones exactas de
los tres roles implicados; y conteos de asignaciones, herencias y referencias
en Patient Flags/Stock. Debe identificarse también cualquier esquema o trigger
adicional. No hacen falta datos de pacientes, nombres de usuarios ni credenciales
en el informe. Hasta obtener esa evidencia, las dos rutas candidatas conservan
su condición de pendientes; no se eliminan suponiendo que nunca se ejecutaron.

## Limitación verificada de Initializer

Se revisó el código del pin `3077975fb4f58c91ff3113d7fed1e3df88829476`,
correspondiente a `2.13.0-sihsalus.1` en el contrato de integración:

- [RolesCsvParser](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RolesCsvParser.java)
  busca por UUID y después por nombre. Si el UUID existe con otro nombre, rechaza
  la fila. No ofrece una fusión de roles y referencias mediante esa fila CSV.
- [RoleLineProcessor](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/roles/RoleLineProcessor.java)
  reemplaza las herencias y los privilegios del rol al cargarlo. Esta capacidad ya
  resuelve la actualización declarativa de una identidad existente.

Por tanto, cambiar permisos de un rol existente no necesita otra política SQL.
Una consolidación de identidades con referencias exige resolver una necesidad
distinta. Esta revisión no demuestra que un CSV pueda reemplazarla ni propone
relajar las guardas para reducir líneas.

## Primera refactorización

`test_admission_role_reconciliation.py` deja de mantener su propia lista de 58
privilegios. Lee la fixture `admission-role-1.25.15.csv`, compartida con las pruebas
MariaDB, y fija su SHA256. Se verificó que su cabecera y fila provienen del commit
`8000b27f48bf124fe9a553d4ba41c678e9acc231`.

Se retiran seis pruebas de la forma textual del SQL publicado. La comprobación
de integridad existente se amplía a la reconciliación `20260907`; cubre sus
precondiciones, SQL, comentarios y atributo de transacción completos. Permanecen
las pruebas de entradas aceptadas/rechazadas y la ejecución real de MariaDB:

| Comprobación retirada | Evidencia que permanece |
| --- | --- |
| Texto de precondiciones y marcadores | Bytes congelados y rechazos por guarda con RBAC intacto en MariaDB. |
| IDs de historiales retirados en consultas | Bytes congelados y ejecución rechazada de ambos historiales reales. |
| Atributo de transacción y forma de INSERT | Bytes congelados, política final exacta, fallo inyectado y rollback real. |
| Palabras SQL permitidas o prohibidas | Bytes congelados y escenarios que comprueban referencias, permisos y repetición. |

No se modifica la fixture, el XML distribuido, los CSV, los workflows ni el
paquete. Los resultados de ejecución de esta refactorización se registran en su
PR; esta revisión no declara verdes pruebas que todavía no hayan terminado.
