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
