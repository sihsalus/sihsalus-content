# Contrato de encuentros para signos vitales y triaje de emergencia

## Decisión

SIHSALUS separa tres hechos clínicos que antes podían confundirse:

1. El registro longitudinal de signos vitales y antropometría desde la historia clínica.
2. La clasificación inicial de prioridad dentro del servicio de emergencia.
3. La atención y el manejo clínico posteriores en emergencia.

El tipo histórico `Triaje` se conserva sin modificar para no cambiar el significado visible de
encuentros ya guardados. No se usa para escrituras nuevas una vez migrados los consumidores.

El content package no define formularios JSON de Form Engine para esta captura. Los signos
vitales se registran desde una extensión embebida en el chart, con un contrato explícito de
encuentro, visita, proveedor, ubicación y observaciones.

## Fundamento normativo

La NTS N.° 139-MINSA/2018/DGAIN, con su modificatoria, trata las funciones vitales y la evaluación
antropométrica como parte de los formatos de la historia clínica y mantiene separados los formatos
de emergencia. La NT N.° 042-MINSA/DGSP-V.01 regula la clasificación y atención propias de los
servicios de emergencia. La NTS N.° 021-MINSA/DGSP-V.03 clasifica establecimientos de salud; no
define la semántica del triaje ni del registro longitudinal de signos vitales. La Directiva
Administrativa N.° 373-MINSA/OGTI-2025 y su ampliación de 2026 son el marco de acreditación de
SIHCE: exigen metadata, autorización y trazabilidad auditables sin reemplazar las normas clínicas.

## Metadata canónica

| Uso | Tipo de encuentro | UUID | Rol de proveedor | UUID del rol |
| --- | --- | --- | --- | --- |
| Historia clínica | Registro de signos vitales y antropometría | `20d4a603-8472-484c-b2bf-b45bdecf6b4f` | Responsable del registro de signos vitales | `bebe2266-abbb-4f3c-b28b-a5b47406fff5` |
| Emergencia | Triaje de Emergencia | `978deb64-358e-4c78-bbb0-04cea73df805` | Enfermera de Triaje | `bd16c32b-6784-45e6-9504-df1cfe0b62e5` |
| Emergencia posterior | Atención en Emergencia | `1b70fe57-92c1-4e35-87f7-13d0e04ff12f` | Según la atención | Según la atención |
| Histórico mixto | Triaje | `67a71486-1a54-468f-ac3e-7091a9a79584` | Histórico | Histórico |

El tipo histórico mantiene exactamente su nombre, descripción y privilegios vacíos. Cambiar una
fila de Initializer por UUID actualizaría la metadata existente y podría reetiquetar la lectura de
los registros históricos.

## Contrato del chart

Una escritura nueva de signos vitales desde el chart cumple todo lo siguiente:

- `encounterType.uuid` es `20d4a603-8472-484c-b2bf-b45bdecf6b4f`.
- `visit.uuid` proviene del contexto de visita actual del chart y corresponde a una visita activa
  del paciente; no se elige buscando la primera visita activa.
- `location.uuid` se deriva de `visit.location.uuid`; nunca se solicita al usuario.
- La ubicación está activa y tiene el tag `Visit Location`.
- Existe al menos un proveedor con el rol `bebe2266-abbb-4f3c-b28b-a5b47406fff5`.
- Las observaciones pertenecen a las listas explícitas del handoff; no se infieren del CSV de
  rangos ni del set OCL `Signos Vitales`.
- No incluye prioridad, Glasgow ni transiciones de cola.

Si el chart no aporta una visita actual inequívoca, si la visita ya no está activa, si no tiene
ubicación, o si la ubicación no es de visita, el cliente impide el POST y muestra un error
accionable. No usa como fallback la primera visita activa encontrada, la ubicación del paciente,
una ubicación elegida en el formulario, la raíz del hospital ni una cola.

La ubicación de sesión puede servir para crear o localizar la visita mediante el flujo autorizado,
pero una vez que existe la visita el encuentro hereda su ubicación. Admisión no recibe un selector
para elegir o cambiar la ubicación del encuentro.

## Registro de paciente e identificador

Todos los `PatientIdentifierType` activos de este paquete declaran
`Location behavior = NOT_USED`. Al crear un paciente, cada elemento de `identifiers` omite por
completo la propiedad `location`. No se envía como `null` ni se deriva de la sesión, la visita, la
dirección del paciente o una ubicación fija.

En la API REST de OpenMRS la ubicación del identificador es opcional, pero si la propiedad está
presente su setter intenta resolver `location.getUuid()`; por eso `location: null` produce una
excepción aunque el tipo no use ubicación. Si en el futuro un identificador requiere procedencia
por ubicación, primero se cambia explícitamente su `Location behavior` y se versiona un contrato
distinto.

### Límite de enforcement para visitas

`Admision` conserva `Add Visits` y `Edit Visits` porque opera el ciclo de la visita durante el
check-in. No recibe `Configure Visits`, administración de tipos de visita ni privilegios del
chart. REST no ofrece un privilegio separado por campo y `Edit Visits` permite actualizar
`visit.location`; el content package no puede garantizar por sí solo la inmutabilidad de ese campo
sin retirar funciones legítimas de admisión.

El frontend oculta el selector, preserva la ubicación original en toda actualización y lo cubre
con pruebas E2E. Si se requiere enforcement contra llamadas REST directas, hace falta una política
o validador backend; no se simula con `datafiltermappings` ni con una ubicación por defecto.

## Contrato de emergencia

Una escritura nueva de clasificación de emergencia usa:

- `encounterType.uuid`: `978deb64-358e-4c78-bbb0-04cea73df805`.
- `visitType.uuid`: `c2a1d3e2-4b8f-4326-94d9-7f6c9a1b7c98` (`Emergencia`).
- `location.uuid`: `35d2234e-129a-4c40-abb2-1ae0b2400003` (`UPSS - EMERGENCIA`),
  validada también contra la ubicación de la visita activa.
- Rol de proveedor: `bd16c32b-6784-45e6-9504-df1cfe0b62e5`.

`UPSS - EMERGENCIA` es una `Visit Location`, no una `Login Location`. La única ubicación de inicio
de sesión es `Hospital Santa Clotilde`; por eso el cliente no puede sustituir la ubicación de la
visita o del encuentro con `sessionLocation`.

El encuentro de triaje puede contener prioridad, Glasgow y signos vitales tomados durante la
clasificación. La transición de una cola es una operación separada; crear el encuentro no mueve
al paciente implícitamente. La atención posterior usa `Atención en Emergencia`, no el tipo de
triaje.

## RBAC

Los tipos de encuentro reutilizan los privilegios funcionales ya publicados por SIHSALUS para que
la autorización del servidor y la capacidad mostrada por el frontend no diverjan:

| Tipo | Lectura | Escritura |
| --- | --- | --- |
| Registro de signos vitales y antropometría | `app:hoja.clinica.signosVitales` | `app:hoja.clinica.signosVitales.editar` |
| Triaje de Emergencia | `app:home.emergencia` | `app:home.emergencia.editar` |

`SIHSALUS Consulta Externa` tiene lectura y edición de signos vitales; `Enfermera` los hereda.
`Personal de Emergencia` conserva los dos pares porque consulta y registra desde el chart además
de operar emergencia. `Admision` no tiene ninguno de esos cuatro privilegios ni permisos para
crear encuentros u observaciones, y no los recibe por esta funcionalidad. No se usa
`Application: Enters Vitals`, porque hereda `Privilege Level: High` y excede este alcance.

## Rangos numéricos

Los rangos de referencia son compartidos por las observaciones; no pertenecen a un tipo de
encuentro. `Normal low/high` es la referencia clínica por edad o condición; `Critical low/high`
es la alerta clínica, incluida la señal de Prioridad I cuando la NT N.° 042 aporta un umbral
explícito; `Absolute low/high` es el límite técnico de captura del `ConceptNumeric` bundleado, o
queda vacío cuando el concepto no define uno.

El frontend no convierte valores normales o críticos en validaciones que bloqueen el guardado.
Solo los límites absolutos técnicos pueden rechazar un valor, y OpenMRS considera válidos los
valores exactamente iguales al mínimo o máximo técnico. La clasificación completa de prioridad no
se deduce de estos rangos. Los umbrales, su codificación entera y los criterios de gestación están
en el [contrato de rangos de triaje](triage-reference-ranges.md).

## Handoff para el frontend

```json
{
  "legacyMixedEncounterTypeUuid": "67a71486-1a54-468f-ac3e-7091a9a79584",
  "chartVitalsEncounterTypeUuid": "20d4a603-8472-484c-b2bf-b45bdecf6b4f",
  "emergencyTriageEncounterTypeUuid": "978deb64-358e-4c78-bbb0-04cea73df805",
  "emergencyCareEncounterTypeUuid": "1b70fe57-92c1-4e35-87f7-13d0e04ff12f",
  "chartVitalsEncounterRoleUuid": "bebe2266-abbb-4f3c-b28b-a5b47406fff5",
  "emergencyTriageEncounterRoleUuid": "bd16c32b-6784-45e6-9504-df1cfe0b62e5",
  "emergencyVisitTypeUuid": "c2a1d3e2-4b8f-4326-94d9-7f6c9a1b7c98",
  "emergencyLocationUuid": "35d2234e-129a-4c40-abb2-1ae0b2400003",
  "patientIdentifierLocationBehavior": "NOT_USED",
  "patientIdentifierLocationPayload": "omit-property",
  "chartVisitSource": "current-chart-visit-context",
  "chartEncounterLocationSource": "active-visit",
  "chartNumericObservationConceptUuids": [
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "1343AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "18fcbd1f-5b4f-44ed-a664-8637a83cc7eb",
    "c4d39248-c896-433a-bc69-e24d04b7f0e5",
    "911eb398-e7de-4270-af63-e4c615ec22a9"
  ],
  "chartContextObservationConceptUuids": [
    "165095AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  ]
}
```

La allowlist numérica corresponde a presión sistólica, presión diastólica, frecuencia respiratoria,
frecuencia cardiaca, temperatura, saturación de oxígeno, perímetro braquial, peso, talla, perímetro
abdominal, perímetro cefálico y perímetro torácico. La lista de contexto conserva la nota general
sin someterla a rangos numéricos. La unión de ambas listas es el contrato completo del encuentro
del chart.

Altura uterina, ganancia de peso gestacional y frecuencia cardiaca fetal tienen rangos de referencia
en este paquete, pero no pertenecen al encuentro genérico del chart; permanecen en un flujo
obstétrico con contrato propio. Disponer de un rango no hace que un concepto pertenezca a este tipo
de encuentro.

La release OCL `2026-07-16-02` deja `Signos Vitales` alineado con el contrato longitudinal: sus 13
miembros activos son los 12 conceptos numéricos de la allowlist y la nota general. Karnofsky y las
cuatro observaciones de Glasgow quedan retirados únicamente de este set y conservan su historia y
sus flujos propios.

No se fija todavía un concepto de prioridad: el paquete contiene un valor binario de cola, un set
de cinco niveles y documentación histórica I-IV. Esa decisión requiere una resolución clínica y
normativa antes de modificar terminología o datos.
