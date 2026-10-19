# Changelog

Cambios del paquete y sus herramientas, agrupados por versión. Cada entrada describe el contenido de esa revisión;
el estado actual está en la [guía de desarrollo](docs/development.md) y los [contratos](docs/README.md).

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Categoría local de Enfermería (candidata 1.25.38)

- Asocia la atención ambulatoria por enfermería a la categoría local «Enfermería», conservando su UUID de servicio y la cola compartida de Consulta Externa.
- Mantiene separadas la categoría general y las especialidades de CRED/Pediatría; no asigna categorías a profesionales ni concede permisos o habilitación clínica.
- Documenta el cambio de agenda y añade regresiones de referencias y enrutamiento. Requiere aceptación del responsable de cartera y revisión del modo off/warn/strict antes del despliegue.

### Especialidades y categorías de agenda (candidata 1.25.36)

- Distribuye el catálogo de citas en medicina, enfermería, odontología y categorías locales mediante CSV nativos de Initializer.
- Conserva los 16 UUID históricos y normaliza cinco denominaciones médicas contra la publicación oficial de MINSA.
- Añade 19 especialidades de CONAREN con identidades propias, incluida la denominación específica de CRED e Inmunizaciones.
- Mantiene el contrato de servicios y enrutamiento; valida referencias y duplicados entre todos los CSV del dominio, incluidos nombres que solo difieren por mayúsculas.
- La versión evita la `1.25.35` propuesta por los PR de CRED abiertos; la habilitación de cartera, aceptación clínica y despliegue siguen pendientes de sus responsables.

### Roles de atención CRED (candidata 1.25.34)

- Publicación pendiente de los cambios integrados en #265: añade `Enfermería Responsable` y precarga el selector de rol
  en 29 formularios CRED, conservando la selección explícita, los UUID, nombres y versiones de formularios.
- Asigna una versión nueva porque `1.25.33` ya está publicada en Maven Central y su artefacto no contiene esos cambios.
- La publicación no actualiza el paquete fijado por la distribución ni acredita su carga o aceptación clínica en QLTY.

### Nombres españoles de anatomía (candidata 1.25.33)

- Export de `SIHSALUS/anatomia-procedimientos` `2026-10-11-02`: ano, mama y páncreas añaden «(sitio anatómico)» al nombre preferido
  para no colisionar con Año, Mamá y PANCREAS en comparación insensible a acentos; los nombres comunes quedan como sinónimos.
- Añade regresiones de colisiones españolas al validador y al ensayo nativo de Initializer.

### Publicación nativa (candidata 1.25.32)

- Fija Maven 3.10.0 con el Wrapper oficial y exige Maven `[3.10.0,4.0.0)` en el perfil `release`; `build` y `publish` usan Java 21 (#259, #260).
- Añade una regresión del bundle real de Central sin subida, conservando la firma y los controles del workflow.

### Sitios anatómicos de procedimientos (candidata 1.25.32)

- Añade 133 sitios anatómicos humanos de HL7 v2-0550 (4.0.0 / THO 7.4.0, CC0) con nombres en español SIHSALUS: 13 conceptos históricos y 120 nuevos.
- Exports OCL versionados con la fuente asociada al URI HL7 vía `fhirconceptsources`; requiere el selector por conjunto con `q` + `memberOf`.
- El ensayo de Initializer comprueba pertenencia, nombres, equivalencias HL7, asociación FHIR, búsqueda y estabilidad en fresh y upgrade.

### Captura CRED y materna (candidata 1.25.31)

- CRED-001 distingue la entrega de micronutrientes del tratamiento de anemia; CRED-002, CRED-003 y CRED-005 aclaran su procedencia normativa.
- CRED-011 `1.3.1` retira PHQ-9, AUDIT-C y la detección de violencia de la madre o cuidador del encuentro del niño; conserva PPSC/PSC-17.
- HOSP-010 `1.0.2` retira del encuentro materno los seis campos del grupo Recién Nacido, que se registran en la historia del niño.
- OBST-006 `1.0.2` reúne responsable, ubicación y rol en una página; OBST-001 `1.0.1` admite «Ninguna» en antecedentes sin combinarla con enfermedades.
- La vía de parto, nacidos vivos/muertos y peso del RN se capturan aparte del contador de partos a término (`8795c05b-f286-4d70-a1e6-69172e676f05` en revisión).
- OBST-013 retira los puntos de corte universales de las etiquetas de anemia; la clasificación confirmada requiere trimestre y altitud.

### Compatibilidad de la suscripción OCL (candidata 1.25.31)

- Restaura `openconceptlab.subscriptionUrl` a la release `2026-07-16-02` de OCL Cloud; el host institucional de #254 abortaba los upgrades.

### Relación madre-hijo (candidata 1.25.30)

- Añade el mapeo nativo EmrApi `emr.motherChildRelationshipType` al tipo de relación Madre→Hijo existente.

### Consulta externa (candidata 1.25.28)

- `CE-001` `1.0.3` elimina la página SOAP del formulario general; el loader retira la versión anterior y conserva su esquema y encuentros.
- `CE-EXF-001-EXAMEN FISICO` `1.0.1`: formulario propio de examen general y por sistemas, sin Subjetivo, Objetivo, Apreciación ni Plan duplicados.
- `CE-ANAM-001-ANAMNESIS` `1.1.1`: ocho selectores explícitos, tres campos de texto y funciones biológicas contraídas; conserva conceptos Text.
- Ambos fijan `maxLength` 4000 en textos libres y profesional responsable de solo lectura (#252); retira y despublica `CE-SOAP-001-NOTA SOAP` `1.2.0`.

### Agregado

- Captura opcional de fecha/hora de alta neonatal en el formulario de nacimiento y contrato de dependencias clínicas de CRED.

### Cambiado

- Organiza las fuentes bajo `configuration/`, conservando rutas y bytes de los 207 archivos del ZIP publicado `1.25.24`.
- Simplifica el build y los validadores, retira configuración de formato sin uso y reúne las instrucciones de mantenimiento en `docs/`.

### Corregido

- CRED-001 `1.2.1` activa el aviso de ajuste de hemoglobina desde 500 m e incluye hasta 5.500 m.
- OBST-002 `1.0.2` calcula semanas completas a la fecha de atención, conserva el vacío sin FUM y admite fechas probables de parto pasadas.
- Los rangos de hemoglobina neonatal exigen prematuridad explícita y usan la edad a la fecha de la muestra; los maternos distinguen prenatal y posparto.
- `1.25.26` extiende la edad a la fecha de la muestra a las siete bandas restantes de hemoglobina.
- Desactiva las dos reglas de creatinina normalizada por peso aplicadas a la medición absoluta de 24 horas; Core vuelve a los límites del concepto.
- Añade regresiones de expresiones y selección nativa de rangos; el validador AMPATH rechaza colisiones de identidad persistida, nombres o versiones
  vacíos y carpetas sin formularios.

## [1.25.24] - 2026-09-22

### Agregado

- Formulario canónico de [historia social](docs/contracts/social-history.md) para alcohol y tabaco, preparado como `1.25.23` en el PR #235.
- Roles operativos de Laboratorio y Soporte del [contrato de perfiles hospitalarios](docs/contracts/hospital-access-profiles.md).

### Corregido

- Reconcilia el alias operativo exacto de Admisión y retira su suplemento hospitalario, rechazando entradas fuera del contrato.
- Concede `Get Patient Programs` a ambos perfiles de Laboratorio para la evaluación nativa de rangos maternos; integración de autorización con Core.

## [1.25.20] - 2026-09-14

### Agregado

- Atributo de visita de [confirmación de pago en Admisión](docs/contracts/arrival-payment.md), opcional y de cardinalidad máxima uno.

## [1.25.19] - 2026-09-12

### Cambiado

- Export principal OCL `2026-09-09-1`, con exclusiones reproducibles de las identidades retiradas del catálogo de barrios; conserva la release de laboratorio.

### Corregido

- Alinea cuatro límites inferiores de hemoglobina con el [contrato de laboratorio](docs/contracts/laboratory-reporting.md); el CI espera la
  disponibilidad pública del POM y ZIP tras la validación de Sonatype.

## [1.25.18] - 2026-09-12

### Agregado

- Ácido ursodesoxicólico como concepto local y presentación ordenable de 250 mg en tableta mediante CSV nativos, con pruebas de carga, reinicio y búsqueda.

## [1.25.17] - 2026-09-12

### Corregido

- Revisa rangos de laboratorio, corrige criterios y diagnóstico del arranque de Initializer (PR #225) y publica la reconciliación de Admisión de `1.25.16`.

## [1.25.16] - No publicada

### Corregido

- Sustituye la reconciliación candidata de Admisión por una operación transaccional que rechaza políticas, herencias, identidades y referencias no admitidas.
- Añade controles estructurales y un harness de MariaDB/Liquibase con datos sintéticos; requisitos en el
  [contrato de Admisión](docs/contracts/admission-role-reconciliation.md). Maven Central no contiene `1.25.16`; se distribuyó desde `1.25.17`.

## [1.25.15] - 2026-09-07

### Corregido

- Agrega `Delete Relationships` únicamente al rol canónico `Admision` para retirar o reemplazar relaciones de responsables; las regresiones rechazan
  la pérdida del permiso, privilegios adicionales, herencia y cambios de identidad del rol.

## [1.25.14] - 2026-08-26

### Agregado

- Marcadores declarativos `Create Attachments` y `View Attachments` en el rol canónico `Laboratorio`; el flujo requiere Attachments `>=4.0.1-sihsalus.1 <5.0.0`.
- Contrato del adjuntador genérico: el rol lector conserva `View Attachments` y el rol editor recibe `Create Attachments` y `View Attachments`.

### Seguridad

- Mantiene fuera del rol el marcador general `app:hoja.clinica.adjuntos.editar`; el rol legado `Tecnico de Laboratorio` permanece intacto.
- Rechaza `Get Global Properties` y fija en CI el contrato declarativo de Laboratorio; la futura carga PDF no deberá completar ni cambiar la orden.

## [1.25.13] - 2026-08-26

### Corregido

- Completa el rol `Farmacia` con `Edit Medication Dispense` (FHIR2 lo exige para crear y actualizar dispensaciones); conserva `Get Medication Dispense`.

## [1.25.12] - 2026-08-25

### Agregado

- Tipo de identificador técnico y fuente secuencial `RU-` de la Receta Única Estandarizada; `1.25.11` se publicó sin esos metadatos.

## [1.25.11] - 2026-08-25

### Corregido

- Retira y despublica de forma idempotente el `Form` persistido de `CE-001-CONSULTA EXTERNA` `1.0.1`, sin modificar sus encuentros.
- Falla de forma cerrada si los UUID de `1.0.1` o `1.0.2` no corresponden a sus identidades o si otra versión de `CE-001` sigue publicada junto a `1.0.2`.

## [1.25.10] - 2026-08-25

### Corregido

- Ubicación canónica del Hospital Santa Clotilde: Loreto (región), Maynas (provincia), Napo (distrito) y Santa Clotilde (centro poblado); calle vacía.

### Agregado

- Teléfono institucional `965 336 199` y Código Único IPRESS `00000066` como atributos de `Location`; `drugOrder.requireOutpatientQuantity=true`.

## [1.25.9] - 2026-08-25

### Cambiado

- Migra `Terrestre`, `Aéreo` y `Fluvial` al source OCL aislado `SIHSALUS/referencia-institucional` (release `2026-08-25-01`), con sus UUID OpenMRS;
  el source principal `sihsalus` sigue en `2026-07-16-02`.

### Retirado

- `concepts/referral_transport_concepts.csv`, para que Initializer y OCL no importen los mismos conceptos en paralelo.

## [1.25.8] - 2026-08-25

### Cambiado

- `CE-REF-001-REFERENCIA-CONTRARREFERENCIA` `1.1.0`: destino, especialidad, prioridad, condición de salida y motivo; retira el diagnóstico de texto duplicado.

### Agregado

- Respuestas terrestre, aérea y fluvial para el concepto existente `Modo de transporte`.

## [1.25.7] - 2026-08-25

### Corregido

- Completa el rol `Farmacia` con los privilegios mínimos de lectura de fuentes de conceptos y dispensaciones que exige la consulta FHIR de recetas.

## [1.25.6] - 2026-08-24

### Agregado

- `CE-SOAP-001-NOTA SOAP` `1.1.0` con examen físico general y regional por sistemas (NTS 139); estado general y resumen regional obligatorios; conserva `1.0.0`.

## [1.25.5] - 2026-08-24

### Corregido

- Retira de `CE-001-CONSULTA EXTERNA` la página de diagnóstico y las observaciones de texto, certeza y ocurrencia; el CIE-10 se registra solo por Visit Notes.
- Publica el esquema corregido como `1.0.2`, con identidad persistida distinta de `1.0.1`, preservando los encuentros históricos.

## [1.25.4] - 2026-08-24

### Agregado

- Seis catálogos mínimos de Stock Management, reutilizando unidades clínicas y agregando motivos, fuentes y categorías; saldos negativos deshabilitados.
- Roles canónicos del módulo de inventario; Consulta Externa y Farmacia solo leen la disponibilidad en la ubicación de dispensación.

## [1.25.3] - 2026-08-24

### Corregido

- Retira del rol de edición de Visit Notes el privilegio inexistente `Add Diagnoses` y la purga `Delete Diagnoses` (OpenMRS 2.8.9 usa `Edit Diagnoses`);
  protege el contrato RBAC y conserva los changeSets de `1.25.1`.

## [1.25.1] - 2026-08-23

### Corregido

- Provisiona de forma idempotente la metadata canónica de `Visit Note` y valida el contrato de formulario, tipo de encuentro y datatypes clínicos.
- Restaura `app:hoja.clinica.resumenConsulta.editar` con su UUID histórico, separado de lectura, y completa el rol funcional granular.

## [1.25.0] - 2026-08-22

### Cambiado

- Paquete exclusivamente backend: el ensamblado incluye solo `backend_configuration` y los exports OCL; el SPA usa `sihsalus-frontend/config/frontend.json`.

### Retirado

- `configuration/frontend_configuration/config.json` y sus validaciones acopladas; la distribución no lo sirve al navegador.

### Agregado

- Catálogo local de barrios de Santa Clotilde como atributo codificado de persona en `SIHSALUS/barrios-santa-clotilde/2026-08-22-01`; retira `ADDRESS_3/Barrio`.
- `ODONTOLOGIA GENERAL` (`5fe6c774-f888-40e5-b54f-e308e5fa26c8`) como miembro del set `Tipo de Servicio` (`4bf3f465-…`) de interconsultas y colas.
- Rol `SIHSALUS Enfermero Triaje` (`c3c9b940-156f-4eaf-83b7-f11db420c51c`) con 45 privilegios, incluidos `Edit Visits` y la lectura de la cita vinculada;
  una migración normaliza al UUID canónico las copias manuales y `validate_appointment_queue_integrity.py` lo admite en `Manage Queue Entries`.
- Pregunta `Código prestacional de la consulta SIH.SALUS` (`34630b86-5106-4aea-8382-f55c02e4ba2c`, Question/Coded) para el resumen de consulta.

### Corregido

- `Edit People` en `SIHSALUS Consulta Externa` y privilegio `app:hoja.clinica.estadoVitalPaciente` para registrar el fallecimiento; sin `Add People`.
- La validación de integridad deja de exigir `app:hoja.clinica.resumenConsulta.editar` y autoriza a `SIH SALUS Colas de atención editar` a registrar
  acompañantes y limpiar entradas activas.

## [1.24.2] - 2026-08-10

### Corregido

- Máximo absoluto de `Proteinas Totales sericas g/dl` (`811c9d4f…`, `6012769e…`): 15 a 12 g/dl; `Creatinina en Suero` (`26801d9a…`, `74380209…`): 15.0 a 13.0 mg/dl.

## [1.24.1] - 2026-08-05

### Corregido

- `Prescripción de medicamentos`: «Observaciones» usa «Instrucciones de prescripción, no codificadas» (`480ab6d3…`) en vez de
  «Evolución obstétrica» (`dfdc2f61…`); el lanzador de suplementos usa `workspaceProps` y aplica «Suplementos para gestantes» (`1ecc7738…`).
- `Financiador` (`3a988e33…`) referencia el set `Tipo de seguro` (`6b932638…`) en lugar del concepto inexistente `355ee63a…`.
- Rol `Admision` (antes `SIHSALUS Admision`, UUID conservado) con allowlist de registro, citas y check-in: `Get Encounters`, `Get Concept Attribute Types`,
  `Get Beds`, `Get Admission Locations`, `Get Providers`, `Get Concept Sources`, `Get Concepts`, `app:home.colasAtencion` y `app:home.colasAtencion.editar`.
- Edición separada de la lectura: `app:hoja.clinica.formulariosClinicos.editar`, `app:hoja.clinica.listaTareas.editar` y `app:hoja.clinica.resumenConsulta.editar`
  (Consulta Externa y Enfermería); `app:appointments.startDate.edit` (Admisión, Consulta Externa, citas) y `app:appointments.issueDate.edit` (solo Admisión).
- Adjuntos: lectura en `Application: Uses Patient Summary`, creación y lectura en `SIHSALUS Consulta Externa`; `app:opciones.registrarAcompanante` para
  `Admision` y `Personal de Emergencia`; `app:home.colasAtencion.limpiar` solo en `Application: Gestionar Colas Servicio`.
- RBAC cita-visita-cola: retira `Manage Appointment Queue Lifecycle`; `Manage Queue Entries` solo para admisión, citas, colas, emergencia, consulta externa y
  administración técnica; `Generate Fua from Visit` sin `Manage Fua`; `Personal de Emergencia` como rol operativo directo con `Get Patient Programs`.
- Tag `Care UPSS` solo en las once UPSS que inician atención; citas de cirujano dentista general en la cola compartida con ámbito `Atención Ambulatoria`.
- Rangos de signos vitales alineados con cada `ConceptNumeric`, crítico alto de saturación vacío y Prioridad I de la NT 042 en enteros (`<50` como `low=49`,
  `>150` como `high=151`); 26 reglas obstétricas activadas por la inscripción `Madre Gestante`, con PAS `<90` crítico (`89`).
- Set OCL `Signos Vitales` con 13 miembros: reutiliza perímetro abdominal y torácico y retira Karnofsky y Glasgow; emergencia cita la NT N.° 042-MINSA/DGSP-V.01.
- Identificadores con `Location behavior = NOT_USED` omiten `identifiers[].location`; la migración de Admisión ordena precondiciones antes del comentario
  (Liquibase 1.9); los logs con bytes NUL se tratan como texto y los errores de `BaseFileLoader` bloquean.

### Agregado

- `validate_form_concept_integrity.py` bloquea conceptos inexistentes y renderings codificados sobre `Text`; la deuda previa queda en un baseline que solo encoge.
- Atributos de visita `Acompañante de consulta` (`710da0b9-e15f-47f0-827a-e97f1937c81d`), `Número de turno de cola`, `UUID de cita vinculada` y `Procedencia`;
  propiedad global del turno; zona operativa `America/Lima`.
- Contrato `docs/contracts/hsc-care-routing.csv` para 16 servicios (13 programables, 11 con cola, dos directos); conceptos dedicados para `Queue.service`;
  categoría local `Odontología general` y atributo multivaluado de proveedor (`off`, `warn`, `strict`).
- Seguros: `Método de Verificación de Seguro` (`bc1e5c92-e46a-4bc9-8cba-d9093a0eb659`); `Tipo de seguro` suma EPS, SOAT/AFOCAT, Prepaga, Autoseguro y Sanidad
  de las Fuerzas Armadas; `Producto SIS` (`72b9edbf-1ec8-4b1a-8957-b1597aab8757`) con Gratuito, Semicontributivo, Emprendedor, Para Todos, Independiente
  y Microempresas; export `SIHSALUS/seguros` `2026-07-17-01`.
- `Cola de Triaje de Emergencia` (`b1c5bb01…`, set `Clasificación Pre-Triaje` `3f4db8e2-241c-45ef-8e52-cea8dc4118f0`) y `Cola de Atención de Emergencia`
  (`ebd44a3d…`, Prioridades I a IV).
- Exports OCL `SIHSALUS/sihsalus` `2026-07-16-02` (4 472 conceptos, 5 679 mapeos) y suscripción a esa versión, tras `2026-07-10-03`, `2026-07-10-01` y
  `2026-07-09-02`; `procedimientos`, `laboratorio`, `lenguas` y `geografia` `2026-07-10-02`; `ocupaciones` `2026-07-09-01` (436 grupos CIUO-08).
- `CIEL 170800 - Procedure status` (SNOMED CT `416342005`), `CIEL 1732 - Duration units` como `CONCEPT-SET`, `CRED-028-TPED` (12 líneas, 89 hitos),
  `proceduretypes` EMR API y concepts faltantes de inmunizaciones, referencias, acompañamiento, PPL/PRU, parto y ecografía.
- Encuentros y roles de proveedor que separan signos vitales longitudinales del triaje de emergencia; servicios de cita de Rehabilitación, Hemodiálisis y Nutrición.
- Privilegios frontend de consultas activas, resumen, formularios clínicos, órdenes, tareas, `app:adt`, citas, colas, `app:immunization` y FUA
  (`Fua Privilege`, `Read Fua`, `Manage Fua`, `Update Fua`); roles `Laboratorista`, `Farmacia`, navegación operativa y vacunación.
- Validación CI de OCL y formularios (`Q-AND-A`, renderers, expresiones, encounter types), regresiones CRED-001/009/010/011/015/026/027 y rangos de referencia.

### Cambiado

- `VisitType` representa solo el ámbito (Atención Ambulatoria, Sesión Grupal Ambulatoria, Hospitalización, Emergencia, Atención Extramural).
- `Hospital Santa Clotilde` como única ubicación de inicio de sesión; obstetricia y nutrición en UPSS Consulta Externa, cirugía general en
  UPSS Hospitalización, Hemodiálisis en UPSS Diálisis, `UPSS - FARMACIA` para dispensación y Emergencia fuera de las citas programadas.
- Productos SIS pasan del primer nivel de `Tipo de seguro` a respuestas de `Producto SIS`; `DIE` se presenta como cédula de identidad del país de origen.
- Formularios CRED alineados con NTS 238 y NTS 213/RM 429-2024: sin umbrales fijos de anemia, EDI Verde/Amarillo/Rojo, M-CHAT-R/F 0 a 20, Huanca 30 a 36 meses.
- 111 formularios alineados con 3 641 referencias conceptuales: par Sí/No unificado, campos cruzados corregidos, `readonly: true` en calculados, IDs AMPATH en
  ASCII camelCase y `workspace-launcher` sin `obs`; `CE-ANAM-001-ANAMNESIS` `1.0.3`; `CRED-004` hasta 143 meses.
- Curación OCL: `procedimientos` (CPMS) y `medicamentos` como fuentes canónicas; `prestacionales` `2026-06-18-01`; `laboratorio` `24-06-2026-2`; exports
  `v2026-06-16-*` y `v2026-06-17-openmrs-order-fix`; `inmunizaciones#584` como `Vacuna antiamarílica`; ZIPs con prefijo numérico.
- Dispositions con conceptos locales; `Application: Registers Patients` limitado a registro; `UBIGEO de Nacimiento` sustituye a `Lugar de Nacimiento`;
  Patient Flags en `flagpriorities`, `flagtags` y `flags`; el ZIP excluye `.DS_Store`, `.gitkeep`, `ampathforms/Readme` y `_deprecated`.

### Retirado

- Servicios de cita de emergencia, atención inmediata del RN e inyectables; `VisitType` con especialidades, `Parent Visit Type` y tipos de servicio uno-a-uno.

## [1.11.0] - 2026-06-09

### Agregado

- Privilegios granulares CRED (`app:cred.antecedentes`, `.cursoVida`, `.earlyStim`, `.immunization`, `.neonatal`, `.nutrition`, `.wellChild` y variantes `.edit`).
- Roles `CRED lectura` y `CRED lectura y edicion` en `roles-core.csv`.

## [1.9.6] - 2026-06-04

### Corregido

- Migra referencias de formularios a conceptos SIHSALUS V4 (Sí/No, Otro, Normal, Ninguno, diagnóstico, laboratorio y opciones que apuntaban a CIEL antiguos).
- Agrega conceptos internos `SIH.SALUS - ...` para campos sin equivalente directo en SIHSALUS V4.

## [1.9.4] - 2026-06-04

### Corregido

- Alinea las opciones de `ODONT-003`, `PSIC-001`, `PSIC-002` y `PSIC-004` con UUIDs canónicos y elimina conceptos locales duplicados que fallaban en `es`.
- Agrega los conceptos y mappings `CIEL` requeridos por FHIR2 `Immunization`, incluido el set `CIEL:984` con vacunas MINSA para `INMU-001`.

## [1.8.32] - 2026-05-28

### Agregado

- Formulario `ODONT-003-ATENCIÓN ODONTOLÓGICA` (motivo, CPO-D/ceo-d, IHOS, riesgo estomatológico, CIE-10, actividades, plan y disposición) con el encounter
  type `Atención de Odontología`, y sus conceptos en `concepts-odontology.csv`.

## [1.8.31] - 2026-05-13

### Corregido

- Membresías `conceptsets` para `Tipo de Servicio`, `Estado de la Cola` y `Prioridad` antes del dominio `queues`; corrige el rechazo de las 16 colas.

## [1.8.30] - 2026-05-12

### Cambiado

- Export OCL SIHSALUS-v4 `12-05-2026-1`; el programa Tuberculosis usa el concepto OCL `Programa de Tuberculosis` de clase `Program`.

## [1.8.29] - 2026-05-12

### Corregido

- Corrige filas mal escapadas en rangos de referencia de laboratorio que rompían `conceptreferencerange`.

## [1.8.28] - 2026-05-12

### Corregido

- Alinea el export OCL SIHSALUS-v4 con los servicios de Queue y reemplaza códigos numéricos OCL por UUIDs OpenMRS estables en queues y propiedades globales.

## [1.8.27] - 2026-05-12

### Corregido

- Nueva publicación porque `1.8.25` y `1.8.26` existen en Maven Central con configuración de Queue no reproducible; colas con UUIDs estables de OCL.

## [1.8.25] - 2026-05-12

### Corregido

- Alinea las colas de atención con los conceptos importados desde OCL para evitar errores en el dominio `queues`.

## [1.8.24] - 2026-05-11

### Cambiado

- Publicación estable con carga controlada de conceptos SIH.SALUS en OCL y alineación de configuración frontend/CI.

## [1.8.20] - 2026-04-30

### Cambiado

- Publicación con las correcciones recientes de metadata y limpieza de configuración frontend obsoleta.

### Agregado

- Workflow de GitHub Actions que valida el content package contra la distro SIHSALUS y exige 0 errores de CSV/Initializer.

## [1.6.0] - 2026-02-11

### Corregido

- Regenera 43 UUIDs inválidos en encounter types, encounter roles, service definitions, visit types, programs, person attribute types, order frequencies
  y metadata term mappings; actualiza 33 formularios AMPATH y las colas que los referencian.
- `HOSP-010` apunta a Epicrisis Médica HSC; corrige el UUID duplicado entre Profesión y Colegio Médico y el UUID placeholder de Fast Data Entry.

## [1.5.0] - 2026-02-11

### Agregado

- Traducciones i18n al español (`messages_es.properties`) con terminología MINSA.
- 3 puntos de caja (Admisión, Farmacia, Emergencia), 14 servicios facturables alineados con las UPSS y 3 cohort attribute types.

## [1.4.0] - 2026-02-11

### Agregado

- URLs FHIR para los identificadores peruanos (DNI/RENIEC, CE, Pasaporte, CNV, Historia Clínica), requeridas por RENHICE (Ley 30024).
- Dispositions clínicas (Admitir, Alta, Transferir, Fallecido, Observación) para O3; requieren en OCL CIEL 164180, 1654, 1655, 1656, 1657, 159791 y 160473.

## [1.3.0] - 2026-02-11

### Agregado

- Encounter type Sesión de Psicoprofilaxis (RM 361-2011), 5 formularios AMPATH para CRED y Madre Gestante y nuevos códigos en `conceptsources.csv`.
- Programas MINSA: Tuberculosis (NTS 200), VIH/SIDA (NTS 169), Adulto Mayor (NTS 207), Planificación Familiar (NTS 124), Enfermedades No Transmisibles
  (PP 0018, PP 0024) y Metaxénicas y Zoonosis (PP 0017).
- Encounter types MINSA: Diagnóstico y Seguimiento de Tuberculosis, Tamizaje de VIH, TARGA, VACAM, Consejería en Planificación Familiar, Tamizaje de
  Cáncer Cervical PAP/IVAA, Enfermedades Metaxénicas y Atención Integral del Adolescente (NTS 157).
- Metadata alineada con referenceapplication: `cohorttypes/cohorttypes.csv`, `concept.true`, `concept.false`, `visits.assignmentHandler`,
  `visits.allowOverlappingVisits` y el privilegio `O3 Implementer Tools`.

### Corregido

- El workflow CI apunta a las ramas `main` y `pre-release`.

## [1.1.1] - 2026-01-13

### Corregido

- Vacía `sihsalus-programworkflows.csv` y `sihsalus-programworkflowstates.csv` (solo cabeceras): los conceptos `Estado de Control CRED` y
  `Estado de Gestación` no existen y rompían la inicialización; los 8 programas funcionan sin workflows hasta crearlos en OCL.

## [1.1.0] - 2026-01-12

### Corregido

- Regenera UUIDs únicos para las 16 colas de `sihsalus-queues.csv` y las vincula a servicios existentes de `appointmentservicedefinitions`.

### Agregado

- Workflows `Estado de Control CRED`, `Estado de Gestación` y `Estado de Vacunación Infantil` con 11 estados en `sihsalus-programworkflowstates.csv`.

## [1.0.0] - Fecha no registrada

### Agregado

- Configuración inicial: 38 módulos de configuración OpenMRS, 56 formularios AMPATH, 17 ubicaciones hospitalarias, 30 tipos de visita y 8 programas clínicos.
- Base geográfica del Perú (94 924 registros), 495 medicamentos del petitorio nacional, 6 paquetes OCL (~12.7 MB) y FHIR con CIEL, LOINC y SNOMED CT.
