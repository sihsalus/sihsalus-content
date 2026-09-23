# Contrato de encuentros para signos vitales y triaje de emergencia

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

Fecha: 2026-07-16

## Decisión

SIHSALUS separa tres hechos clínicos que hasta ahora podían confundirse:

1. El registro longitudinal de signos vitales y antropometría desde la historia clínica.
2. La clasificación inicial de prioridad dentro del servicio de emergencia.
3. La atención y el manejo clínico posteriores en emergencia.

El tipo histórico `Triaje` se conserva sin modificar para no cambiar el significado visible de
encuentros ya guardados. No se usará para escrituras nuevas cuando los consumidores hayan sido
migrados.

Esta entrega no agrega ni modifica formularios JSON de Form Engine. La captura de signos vitales
debe implementarse como una extensión embebida en el chart, con un contrato explícito de
encuentro, visita, proveedor, ubicación y observaciones.

## Fundamento normativo

La NTS N.° 139-MINSA/2018/DGAIN, con su modificatoria, trata las funciones vitales y la evaluación
antropométrica como parte de los formatos de la historia clínica y mantiene separados los formatos
de emergencia. La NT N.° 042-MINSA/DGSP-V.01 regula la clasificación y atención propias de los
servicios de emergencia. La NTS N.° 021-MINSA/DGSP-V.03 clasifica establecimientos de salud; no
define la semántica del triaje ni del registro longitudinal de signos vitales.

La Directiva Administrativa N.° 373-MINSA/OGTI-2025 y la ampliación aprobada en 2026 constituyen
el marco vigente de acreditación de SIHCE. Refuerzan la necesidad de metadata, autorización y
trazabilidad auditables, pero no reemplazan las normas clínicas anteriores.

Fuentes oficiales:

- NTS N.° 139: `https://www.gob.pe/institucion/minsa/normas-legales/187487-214-2018-minsa`
- Modificatoria de NTS N.° 139: `https://www.gob.pe/institucion/minsa/normas-legales/187373-265-2018-minsa`
- NT N.° 042: `https://www.gob.pe/institucion/minsa/informes-publicaciones/353462-norma-tecnica-de-salud-de-los-servicios-de-emergencia-nt-n-042-minsa-dgsp-v-01`
- NTS N.° 021: `https://www.gob.pe/institucion/regiontacna-diresa/informes-publicaciones/5225857-resolucion-ministerial-n-546-2011-minsa`
- Directiva Administrativa N.° 373: `https://www.gob.pe/institucion/minsa/normas-legales/6551375-164-2025-minsa`
- Ampliación 2026: `https://www.gob.pe/institucion/minsa/normas-legales/7845808-188-2026-minsa`

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

Una escritura nueva de signos vitales desde el chart debe cumplir todo lo siguiente:

- `encounterType.uuid` es `20d4a603-8472-484c-b2bf-b45bdecf6b4f`.
- `visit.uuid` proviene del contexto de visita actual del chart y corresponde a una visita activa
  del paciente; no se elige buscando arbitrariamente la primera visita activa.
- `location.uuid` se deriva de `visit.location.uuid`; nunca se solicita al usuario.
- La ubicación está activa y tiene el tag `Visit Location`.
- Existe al menos un proveedor con el rol
  `bebe2266-abbb-4f3c-b28b-a5b47406fff5`.
- Las observaciones pertenecen a las listas explícitas de mediciones numéricas y contexto
  definidas en el handoff; no se infieren del CSV de rangos ni del set OCL `Signos Vitales`.
- No incluye prioridad, Glasgow ni transiciones de cola.

Si el chart no aporta una visita actual inequívoca, si la visita ya no está activa, si no tiene
ubicación, o si la ubicación no es de visita, el cliente debe impedir el POST y mostrar un error
accionable. No debe usar como fallback la primera visita activa encontrada, la ubicación del
paciente, una ubicación elegida en el formulario, la raíz del hospital ni una cola.

La ubicación de sesión puede servir para crear o localizar la visita mediante el flujo autorizado,
pero una vez que existe la visita el encuentro hereda su ubicación. Admisión no recibe un selector
para elegir o cambiar la ubicación del encuentro.

## Registro de paciente e identificador

Todos los `PatientIdentifierType` activos de este paquete declaran
`Location behavior = NOT_USED`. Al crear un paciente, cada elemento de `identifiers` debe omitir
por completo la propiedad `location`. No debe enviarla como `null` ni derivarla de la sesión, la
visita, la dirección del paciente o una ubicación hardcodeada.

En la API REST de OpenMRS la ubicación del identificador es opcional, pero si la propiedad está
presente su setter intenta resolver `location.getUuid()`. Por eso `location: null` produce la
excepción observada aunque el tipo no use ubicación. Admisión no recibe un selector para elegir o
cambiar este dato. Si en el futuro un identificador requiere procedencia por ubicación, primero se
cambia explícitamente su `Location behavior` y se versiona un contrato distinto.

### Límite de enforcement para visitas

`Admision` conserva `Add Visits` y `Edit Visits` porque necesita operar el ciclo de la
visita durante el check-in. No recibe `Configure Visits`, administración de tipos de visita ni
privilegios del chart. REST no ofrece un privilegio separado por campo y `Edit Visits` permite
actualizar `visit.location`; por tanto, el content package no puede garantizar por sí solo la
inmutabilidad de ese campo sin retirar funciones legítimas de admisión.

El frontend debe ocultar el selector, preservar la ubicación original en toda actualización y
cubrirlo con pruebas E2E. Si se requiere enforcement incluso contra llamadas REST directas, hace
falta una política o validador backend específico; no se debe simular con `datafiltermappings` ni
con una ubicación por defecto.

Código oficial revisado para las versiones de la distribución:

- REST 3.5.0, recurso de identificador: `https://github.com/openmrs/openmrs-module-webservices.rest/blob/3.5.0/omod/src/main/java/org/openmrs/module/webservices/rest/web/v1_0/resource/openmrs1_8/PatientIdentifierResource1_8.java`
- Core 2.8.7, validación por `LocationBehavior`: `https://github.com/openmrs/openmrs-core/blob/2.8.7/api/src/main/java/org/openmrs/validator/PatientIdentifierValidator.java`

Distribución objetivo verificada:

- `sihsalus/sihsalus` commit `46d81b5034a04c3e4097cf86f8595c7393cc82b2`:
  `https://github.com/sihsalus/sihsalus/commit/46d81b5034a04c3e4097cf86f8595c7393cc82b2`
- Imagen backend: `ghcr.io/sihsalus/sihsalus-backend:sha-46d81b5034a04c3e4097cf86f8595c7393cc82b2`.
- OpenMRS Core 2.8.7, REST Web Services 3.5.0 e Initializer 2.12.0.
- El POM de ese commit fija `sihsalus-content` 1.16.3. La imagen derivada de auditoría reemplaza
  únicamente `openmrs_config` con el candidato 1.19.0; la simulación de upgrade usa 1.18.0,
  que es la versión publicada de este repositorio inmediatamente anterior al cambio.
- Se contrastó también `main` en `6a8a275dd2300c8f43cc2c2fa3a2013210e1f3fc`: conserva Core
  2.8.7, REST 3.5.0 e Initializer 2.12.0 y referencia content 1.17.0. Por tanto, las versiones que
  procesan esta metadata coinciden con el código vigente aunque el PowerEdge ejecute el SHA
  desplegado del 10 de julio.

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
clasificación. La transición de una cola sigue siendo una operación separada; crear el encuentro no
debe mover al paciente implícitamente. La atención posterior continúa usando
`Atención en Emergencia`, no el tipo de triaje.

## RBAC

Los tipos de encuentro reutilizan los privilegios funcionales ya publicados por SIHSALUS para que
la autorización del servidor y la capacidad mostrada por el frontend no diverjan:

| Tipo | Lectura | Escritura |
| --- | --- | --- |
| Registro de signos vitales y antropometría | `app:hoja.clinica.signosVitales` | `app:hoja.clinica.signosVitales.editar` |
| Triaje de Emergencia | `app:home.emergencia` | `app:home.emergencia.editar` |

`SIHSALUS Consulta Externa` tiene lectura y edición de signos vitales; `Enfermera` los hereda.
`Personal de Emergencia` conserva los dos pares porque ya puede consultar y registrar desde el
chart además de operar emergencia. `Admision` no tiene ninguno de esos cuatro privilegios,
ni permisos para crear encuentros u observaciones, y no debe recibirlos por esta funcionalidad. No
se debe usar `Application: Enters Vitals`, porque hereda `Privilege Level: High` y excede este
alcance.

## Rangos numéricos

Los rangos de referencia son compartidos por las observaciones, no pertenecen a un tipo de
encuentro. Su semántica queda separada así:

- `Normal low/high`: referencia clínica por edad o condición.
- `Critical low/high`: interpretación o alerta clínica, incluida la señal de Prioridad I cuando la
  NT N.° 042 aporta un umbral explícito.
- `Absolute low/high`: límite técnico de captura; coincide con el límite absoluto del
  `ConceptNumeric` bundleado o queda vacío cuando el concepto no define uno.

El frontend no debe convertir valores normales o críticos en validaciones que bloqueen el guardado.
Solo los límites absolutos técnicos pueden rechazar un valor. La clasificación completa de
prioridad no se deduce de estos rangos. Como los consumidores actuales evalúan `Critical low/high`
de forma inclusiva, los umbrales estrictos de la NT N.° 042 se codifican con una unidad de diferencia
para los conceptos enteros; la tabla exacta y los contextos que no caben en un rango están en la
auditoría de rangos de referencia.

OpenMRS Core 2.8.7 evalúa todos los criterios aplicables y, cuando coinciden varios rangos para un
concepto, sintetiza uno usando el límite más estricto de cada campo. REST 3.5.0 devuelve como máximo
ese rango resuelto por cada concepto solicitado; por tanto, el solapamiento entre edad y gestación no
produce varias filas REST, pero sí combina ambos contratos. Se verificó en el código oficial:

- Resolución de rangos en Core 2.8.7:
  `https://github.com/openmrs/openmrs-core/blob/2.8.7/api/src/main/java/org/openmrs/api/impl/ConceptServiceImpl.java`
- Recurso REST 3.5.0:
  `https://github.com/openmrs/openmrs-module-webservices.rest/blob/3.5.0/omod/src/main/java/org/openmrs/module/webservices/rest/web/v1_0/resource/openmrs2_8/ConceptReferenceRangeResource2_8.java`

Las 26 filas `gestante` usan ahora un contrato operativo y fail-closed: sexo femenino, inscripción
activa en `Madre Gestante` a la fecha del contexto y una observación numérica previa de
`Edad gestacional (semanas actuales)` (`1e35f0dd-...`), producida por siete formularios. Una lista
inline de SpEL resuelve esa observación una sola vez por criterio y divide las bandas en
`[0,14)`, `[14,28)` y `[28,40)`. El marcador `Actualmente embarazada` (`abaf7d91-...`) sigue siendo
una respuesta coded `N/A`; deja de tratarse incorrectamente como una pregunta Boolean. El UUID
`0f053bc0-...`, sin productores bundleados, deja de consumirse.

La frontera PAS gestante también queda inequívoca: `Critical low=89` y `Normal low=90`, codificación
entera de la regla estricta `<90`. Core y el frontend ya no pueden clasificar `90` de forma distinta
por el orden de comparación.

El contrato aún exige disciplina de flujo: la edad gestacional debe estar persistida antes del
vital y la inscripción debe cerrarse al parto/aborto. `getLatestObs` ordena por `dateCreated`, no
limita por episodio ni por `$date`; un registro retrospectivo o un segundo embarazo necesita un
helper backend “as of/episode” para quedar resuelto sin ambigüedad. No se modifica manualmente OCL
ni se migran observaciones históricas en este cambio.

Código oficial relevante:

- `Obs.getValueBoolean()` en Core 2.8.7:
  `https://github.com/openmrs/openmrs-core/blob/2.8.7/api/src/main/java/org/openmrs/Obs.java`
- Resolución e interpretación en Core 2.8.7:
  `https://github.com/openmrs/openmrs-core/blob/2.8.7/api/src/main/java/org/openmrs/validator/ObsValidator.java`

Además, `esm-service-queues-app/src/current-visit/current-visit.resource.ts` interpreta los límites
absolutos con `>=` y `<=`, mientras OpenMRS solo rechaza valores estrictamente mayores o menores. En
el estado actual, SpO2 `100` puede mostrarse como críticamente alta aunque sea exactamente el máximo
válido. El frontend debe corregir esos operadores o dejar de usar límites técnicos como interpretación
clínica antes de consumir esta metadata.

El candidato alinea con OCL y por ello estrecha `Absolute high` en 60 filas: PAS `260→250`, PAD
`200→150`, FR `120→99`, FC `260→230` y temperatura `50→47`. El import no modifica observaciones
históricas, pero una edición o revalidación puede rechazarlas. El PowerEdge está vacío y no mide ese
impacto; antes de release se debe ejecutar una consulta de prevalencia sobre una copia anonimizada
de datos reales.

## Transición de datos

No hay migración automática del tipo histórico. El orden de despliegue es:

1. Publicar el content package con los tipos y el rol nuevos.
2. Verificar la carga de Initializer, la disponibilidad REST y un segundo arranque idempotente.
3. Cambiar el chart para escribir únicamente el nuevo tipo longitudinal.
4. Cambiar emergencia para escribir únicamente el nuevo tipo de triaje.
5. Monitorear que no aparezcan escrituras nuevas con el UUID histórico.
6. Generar un informe de los encuentros históricos antes de cualquier reclasificación.

Durante la transición, la lectura longitudinal incluye el tipo nuevo y el tipo histórico, marcado
como legado. Emergencia incluye el tipo nuevo y solo los históricos clasificables de forma
determinística. La presencia de prioridad o Glasgow puede ser evidencia de emergencia; signos
vitales, fecha o ubicación por sí solos no lo son. Los registros ambiguos permanecen históricos y
no se duplican en ambos dominios.

Un rollback detiene las nuevas escrituras de los consumidores, pero no borra ni retira la metadata
nueva ni reescribe encuentros ya creados.

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
que el widget actual ya permite registrar, pero no la somete a rangos numéricos. La unión de ambas
listas es el contrato completo del encuentro del chart.

Altura uterina, ganancia de peso gestacional y frecuencia cardiaca fetal tienen rangos de referencia
en este paquete, pero eso no las autoriza automáticamente en el encuentro genérico del chart. Deben
permanecer en un flujo obstétrico con contrato propio. Del mismo modo, disponer de un rango no hace
que un concepto pertenezca a este tipo de encuentro.

La release OCL `2026-07-16-02` deja `Signos Vitales` alineado con el contrato longitudinal: sus 13
miembros activos son los 12 conceptos numéricos de la allowlist y la nota general. Reutiliza los
conceptos existentes de perímetro abdominal y torácico; Karnofsky y las cuatro observaciones de
Glasgow quedan retirados únicamente de este set y conservan su historia y sus flujos propios. Los
tres conceptos obstétricos con rangos tampoco pertenecen al set ni al contrato genérico del chart.

Tampoco se fija todavía un concepto de prioridad: el paquete contiene un valor binario de cola, un
set de cinco niveles y documentación histórica I-IV. Esa decisión requiere una resolución clínica
y normativa antes de modificar terminología o datos.

## Deuda explícita restante

- Implementar en `sihsalus-frontend` el payload sin `identifiers[].location`, la ubicación del
  encuentro derivada de la visita y las allowlists separadas, con aserciones de red en Playwright.
- Añadir un validador o política backend si “admisión nunca cambia `visit.location`” también debe
  resistir llamadas REST directas; el content package solo puede garantizar RBAC por recurso.
- Resolver clínicamente el concepto y las reglas completas de prioridad de emergencia, incluidos
  los contextos que no caben en `conceptreferencerange`.
- Automatizar el cierre de `Madre Gestante` al parto/aborto y agregar un helper backend que resuelva
  edad gestacional por episodio y fecha clínica; el criterio actual falla cerrado, pero depende de
  una observación previamente persistida.
- Hacer conscientes de fecha las bandas etarias y auditar observaciones históricas contra los
  nuevos límites absolutos antes de release.
- Corregir en `esm-service-queues-app` la interpretación inclusiva de límites absolutos; el servidor
  considera válidos los valores exactamente iguales al mínimo o máximo técnico.
- Mover la validación runtime de SIHSALUS a un gate previo a publicación/merge. El workflow actual
  de distribución consume el artefacto después de publicarlo; esta auditoría aporta mientras tanto
  una ejecución aislada en PowerEdge, pero no sustituye un gate automático de PR.

## Criterios de aceptación

- El tipo histórico conserva su fingerprint exacto.
- Los dos tipos nuevos y el rol longitudinal se cargan de forma idempotente.
- Los privilegios de cada tipo existen y admisión no los recibe.
- Ningún formulario JSON referencia los UUID nuevos.
- El registro de paciente omite `identifiers[].location`; nunca envía un valor nulo.
- Chart y emergencia escriben tipos distintos y nunca envían una ubicación nula.
- Admisión no cambia `visit.location` desde UI; el enforcement REST por campo queda como hardening
  backend explícito.
- Las allowlists del encuentro y los conceptos con rangos se validan como contratos independientes.
- Los rangos absolutos no sustituyen los umbrales normales o críticos.
- No se reclasifica automáticamente ningún encuentro histórico.
