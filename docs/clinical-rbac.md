# Línea base RBAC clínica y de adjuntos

Este contenido provisiona capacidades de lectura para formularios clínicos y
tareas, además de marcadores declarativos para adjuntos. No provisiona
privilegios genéricos de mutación para formularios o tareas ni modifica
masivamente los privilegios de los tipos de encuentro: OpenMRS aplica
`viewPrivilege` y `editPrivilege` en el servidor, y hacerlo sin una matriz
aprobada rompería flujos de Emergencia, Laboratorio, Farmacia y Hospitalización.

## Capacidades y marcadores provisionados

- `app:hoja.clinica.formulariosClinicos` permite abrir el catálogo de
  formularios.
- `app:hoja.clinica.resumenConsulta` permite consultar el resumen clínico;
  `app:hoja.clinica.resumenConsulta.editar` autoriza por separado su registro y
  edición.
- `app:hoja.clinica.listaTareas` permite consultar tareas.
- `View Attachments` y `Create Attachments` son nombres de privilegio declarados
  por el módulo y marcadores para UI/contratos futuros. No deben describirse
  como autorización backend vigente ni habilitan el flujo por sí solos.

Los roles canónicos del adjuntador genérico mantienen responsabilidades
separadas:

- `SIH SALUS Hoja Clinica Adjuntos`
  (`46d700c7-71a7-486f-8467-e85f2a08678e`) conserva
  `View Attachments` y no recibe `Create Attachments`.
- `SIH SALUS Hoja Clinica Adjuntos editar`
  (`ceaf46f8-6f27-4da5-885a-5d830cfc059c`) declara
  `Create Attachments` y `View Attachments`, y conserva `Add Observations` y
  `Delete Observations` como parte de su contrato existente.

La lectura declarativa de adjuntos forma parte de
`Application: Uses Patient Summary`. El rol `SIHSALUS Consulta Externa` recibe
además `Create Attachments` y ambos marcadores de forma directa; `Enfermera` los
hereda. Estas asignaciones preservan compatibilidad de UI, pero no corrigen la
autorización server-side. El validador protege las asignaciones declarativas y
`Add Observations` de Consulta Externa sin afirmar autorización efectiva.

El rol canónico `Laboratorio` (`2049b153-6d8c-4bc1-96ab-f34f0ca43285`)
recibe directamente los marcadores `View Attachments` y `Create Attachments`, y
conserva `Add Observations` como parte de su contrato clínico existente. No recibe
`app:hoja.clinica.adjuntos.editar`. El rol legado `Tecnico de Laboratorio`
(`5a870421-1f01-46a6-8479-e3930266e9c1`) permanece intacto. Ninguna de estas
asignaciones vuelve operativo el flujo con Attachments 4.0.0.

`Laboratorio` conserva `Edit Observations` y `Delete Observations`. Declarar los
marcadores de adjuntos no elimina capacidades de borrado existentes, ni en este
rol ni en el editor genérico. El perfil hospitalario `SIHSALUS Laboratorio` tiene
una composición distinta, documentada en el
[contrato de perfiles](contracts/hospital-access-profiles.md).

El contrato define el archivo PDF como suplemento documental. Cuando el flujo
sea habilitado, su carga no deberá completar la orden, modificar su estado ni
sustituir observaciones estructuradas o la aprobación del resultado. Esas
transiciones deberán seguir ocurriendo mediante acciones explícitas del módulo
de laboratorio.

## Compatibilidad de adjuntos

El frontend, esta metadata y la corrección backend deben publicarse como una
unidad coordinada. Attachments 4.0.0 no es compatible y el flujo permanece no
operativo con esa versión. Se requiere una release backend compatible con
Attachments `>=4.0.1-sihsalus.1 <5.0.0`, con autorización server-side y acceso
interno acotado a la configuración del módulo. No se debe otorgar
`Get Global Properties` a `Laboratorio`; el validador rechaza explícitamente
esa ampliación.

## Formularios, encuentros y Visit Notes

Cuando un tipo de encuentro declara un privilegio específico, el frontend exige
ese privilegio. La ausencia de metadata no equivale a acceso público y este
paquete no provisiona una capacidad genérica de mutación como reemplazo.
El rol funcional de edición del resumen incluye explícitamente las capacidades
de formularios, ubicaciones, proveedores, observaciones y diagnósticos que
requiere Visit Notes; el acceso de lectura por sí solo no habilita el guardado.
En OpenMRS 2.8.9, `Edit Diagnoses` autoriza crear, actualizar y anular un
diagnóstico. No existe `Add Diagnoses`, y `Delete Diagnoses` queda fuera del rol
granular porque autoriza la purga física, operación que Visit Notes no realiza.

## Límite deliberado

La metadata actual contiene tipos sin `viewPrivilege` o `editPrivilege`, incluido
el UUID histórico mixto de Triaje
`67a71486-1a54-468f-ac3e-7091a9a79584`. No se rellenan en bloque porque:

- Laboratorio agrega resultados al encuentro que originó la orden.
- Farmacia consulta prescripciones creadas desde distintos tipos de encuentro.
- `LAB-001-RESULTADOS DE LABORATORIO - ÁREA HOSPITALIZACIÓN` todavía referencia
  el tipo `Hospitalización`.
- varios consumidores todavía escriben signos vitales al Triaje histórico.

Por ello, estos marcadores de interfaz no demuestran que exista
segregación completa en backend. La matriz por dominio debe migrar primero los
escritores y después asignar los privilegios de tipo de encuentro.

## Despliegue y reversión

El contenido debe mantenerse sincronizado con el frontend. Retirar una fila del
catálogo evita que Initializer vuelva a provisionarla, pero no elimina de la base
de datos un privilegio creado por una versión anterior. Si se necesita borrarlo
físicamente de una instalación existente, debe hacerse mediante una migración
explícita y controlada.

## Validación operativa requerida

- Consulta Externa y Enfermería: conservan los marcadores declarativos previos;
  no se asume autorización backend con Attachments 4.0.0.
- Adjuntador genérico: con la [versión backend requerida](#compatibilidad-de-adjuntos),
  el rol lector debe conservar acceso de lectura y
  el editor debe conservar lectura y creación, sin requerir
  `Get Global Properties`.
- Laboratorio: con esa versión compatible, se debe probar
  con usuario sintético la autorización server-side, la ausencia de
  `Get Global Properties` y que la carga no cambia el estado de la orden.
- `Tecnico de Laboratorio`: conserva exactamente su contrato previo y no recibe
  los marcadores de adjuntos.
- Los roles no reciben privilegios genéricos de mutación para formularios o
  tareas desde este paquete.
- Acceso directo a un workspace por UUID: se resuelve el formulario y se valida
  el privilegio antes de montar React Form Entry o HTML Form Entry.
- La autorización server-side debe probarse por rol; ocultar controles en el
  frontend no reemplaza la autorización del servidor.

[validate_csv_widths.py](../.github/scripts/validate_csv_widths.py)
verifica la estructura de los CSV, que
`SIHSALUS Consulta Externa` conserve sus asignaciones declarativas previas y
que los roles canónicos lector/editor del adjuntador conserven su separación, y
que únicamente el rol canónico de Laboratorio reciba sus marcadores
preparatorios dentro de los roles de laboratorio. Rechaza la pérdida de
`Add Observations`, la concesión a Laboratorio de
`app:hoja.clinica.adjuntos.editar` o `Get Global Properties`, y la ampliación del
rol legado. La autorización backend y la matriz de tipos de encuentro requieren
las comprobaciones operativas anteriores.
