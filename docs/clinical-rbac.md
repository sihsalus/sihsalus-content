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
  por el módulo y marcadores para UI y contratos futuros. Son marcadores
  declarativos, no autorización backend vigente: no habilitan el flujo de
  adjuntos por sí solos ni corrigen la autorización server-side, y con
  Attachments 4.0.0 el flujo no es operativo (véase
  [Compatibilidad de adjuntos](#compatibilidad-de-adjuntos)).

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
además `Create Attachments` y ambos marcadores de forma directa, y conserva
`Add Observations`; `Enfermera` los hereda.

El rol canónico `Laboratorio` (`2049b153-6d8c-4bc1-96ab-f34f0ca43285`)
recibe directamente los marcadores `View Attachments` y `Create Attachments`, y
conserva `Add Observations` como parte de su contrato clínico existente. No recibe
`app:hoja.clinica.adjuntos.editar`. El rol legado `Tecnico de Laboratorio`
(`5a870421-1f01-46a6-8479-e3930266e9c1`) permanece intacto y no recibe los
marcadores de adjuntos.

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
unidad coordinada. Attachments 4.0.0 no es compatible. Se requiere una release
backend compatible con Attachments `>=4.0.1-sihsalus.1 <5.0.0`, con autorización
server-side y acceso interno acotado a la configuración del módulo. No se otorga
`Get Global Properties` a `Laboratorio`.

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
El acceso directo a un workspace por UUID resuelve el formulario y valida el
privilegio antes de montar React Form Entry o HTML Form Entry.

## Límite deliberado

La metadata actual contiene tipos sin `viewPrivilege` o `editPrivilege`, incluido
el UUID histórico mixto de Triaje
`67a71486-1a54-468f-ac3e-7091a9a79584`. No se rellenan en bloque porque:

- Laboratorio agrega resultados al encuentro que originó la orden.
- Farmacia consulta prescripciones creadas desde distintos tipos de encuentro.
- `LAB-001-RESULTADOS DE LABORATORIO - ÁREA HOSPITALIZACIÓN` todavía referencia
  el tipo `Hospitalización`.
- varios consumidores todavía escriben signos vitales al Triaje histórico.

La matriz por dominio debe migrar primero los escritores y después asignar los
privilegios de tipo de encuentro.
