# Plan de Terminología OCL — SIHSALUS

> **Documento histórico:** el estado, los inventarios y las releases descritos a continuación
> corresponden a las fechas del plan. Para revisar el contenido de esta rama, consultar los
> [exports OCL incluidos](configuration/backend_configuration/ocl), los
> [contratos del paquete](docs/contracts) y las [auditorías posteriores](docs/audits).
> Las cifras y las tareas pendientes de este documento deben contrastarse con esas fuentes
> antes de reutilizarlas como diagnóstico del paquete actual.

> Documento de plan/arquitectura para la consolidación de conceptos en OpenConceptLab (OCL).
> Última actualización: 2026-06-17. Org OCL activa para el content package: **SIHSALUS** (`https://app.openconceptlab.org/#/orgs/SIHSALUS/`).
> Estado: en progreso. Contiene lo hecho, el plan pendiente, convenciones y **dudas abiertas**.

---

## Estado actual del paquete (2026-06-17)

El content package consume exports OCL released desde la org `SIHSALUS`; el source principal `sihsalus`
usa la release `v2026-06-17-openmrs-order-fix`, `laboratorio` usa `16-06-2026-2`,
`prestacionales` usa `v2026-06-17-openmrs-current` y los otros sources de dominio mantienen
`v2026-06-16-openmrs-current`.
El historial de este documento conserva referencias a `PeruHCE` porque describe el trabajo previo de
reconstrucción y migración.

| Source SIHSALUS | Conceptos | Mappings | Qué es |
|---|---:|---:|---|
| `sihsalus` | 4674 | 6064 | Diccionario clínico principal SIHSALUS |
| `procedimientos` | 12333 | 12331 | Procedimientos CPMS MINSA |
| `diagnosis` | 13484 | 0 | CIE-10 MINSA |
| `medicamentos` | 1001 | 17 | Medicamentos e insumos SIS/Dige |
| `laboratorio` | 246 | 1088 | Pruebas, paneles y resultados de laboratorio |
| `inmunizaciones` | 22 | 60 | Vacunas del esquema nacional |
| `prestacionales` | 66 | 65 | Códigos prestacionales administrativos para historias clínicas y FUAs |

La release base `v2026-06-16-openmrs-current` consolida la limpieza posterior al rebuild: el source `alergias`
queda absorbido por `sihsalus`, conceptos administrativos se movieron fuera de `laboratorio`, 646 insumos de
`medicamentos` quedaron como `Medical supply`, 520 códigos CIE-10 `U*` quedaron como `Misc`, y se normalizó
la página final de `laboratorio` moviendo dos procedimientos clínicos a `sihsalus` y corrigiendo clases/nombres.
También incluye los fixes posteriores de import OpenMRS: `inmunizaciones#584` queda publicado como
`Vacuna antiamarílica`, y las respuestas clínicas de aborto se rewirean desde conceptos locales de `sihsalus`
hacia conceptos canónicos en `diagnosis`.
La release `v2026-06-16-education-mappings-fix` actualiza el source `sihsalus`: `No (respuesta)` queda como
respuesta genérica sin mappings salientes, `Highest education level` recibe sus respuestas educativas y mappings
externos, y `Nivel I-2` queda enlazado como respuesta de `Nivel de Atención`.
La release `v2026-06-16-glasgow-vitals` agrega los 22 conceptos de Escala de Glasgow para triaje de emergencia,
incluyendo las cuatro preguntas usadas por el ESM de signos vitales y sus respuestas Q-AND-A.
La release `v2026-06-16-pns-contact-metadata` agrega conceptos y mappings para metadata de contactos PNS
usada por flujos de ficha familiar, relaciones y notificación de contactos.
La release `v2026-06-16-languages` agrega conceptos de lengua separados de etnia/pueblo: `Idioma` queda con
61 respuestas Q-AND-A, `Lenguas del mundo` tiene 61 miembros, `Lenguas indígenas u originarias del Perú` tiene
las 48 lenguas listadas por BDPI, y se agrega `Otra lengua no codificada`.
La release `v2026-06-16-qanda-cleanup` completa mappings `Q-AND-A` determinísticos para preguntas CRED
con respuestas Sí/No, `Tipo de suplemento`, educación de la madre, grupo sanguíneo ABO, estado/tipo de historia
clínica y estado de acreditación de seguro. La duplicidad controlada de `Sí`/`No` queda pendiente por decisión
explícita; no se tocó en esta ronda. Quedan 26 preguntas `Question/Coded` sin respuestas, listadas en
`reports/sihsalus-coded-without-answers-residual.2026-06-16.csv`, porque requieren revisar formulario o criterio
clínico antes de mapear.
La release `v2026-06-17-openmrs-order-fix` retira el mapping activo `sihsalus:5242`, que apuntaba desde el
concepto retirado `sihsalus:2560`, y el paquete reordena los ZIPs OCL para evitar errores de mappings hacia
conceptos aún no importados. `laboratorio` se carga en dos pasadas: primero un ZIP `concepts-only` para que
`sihsalus` pueda apuntar a pruebas/paneles de laboratorio, y al final el ZIP oficial completo para crear los
mappings de `laboratorio` hacia `sihsalus`. La simulación local de import queda con 0 mappings internos cuyo
origen o destino falte al momento de importarse.
La release `prestacionales/v2026-06-17-openmrs-current` agrega 65 códigos prestacionales como conceptos
`Misc/N/A` y un agrupador `Codigos Prestacionales` como `ConvSet/N/A`, con 65 mappings `CONCEPT-SET`. La release
previa `2026-06-17-01` no se bundlea porque no incluía el agrupador ni los mappings.

### Plan actual para `concepts/` y `conceptsets/`

El repo todavía carga conceptos locales desde `configuration/backend_configuration/concepts/` y relaciones desde
`configuration/backend_configuration/conceptsets/`. El objetivo sigue siendo que OCL sea la fuente de verdad de los
conceptos clínicos; los CSVs deben quedar solo como capa temporal mientras se migra y valida el contenido.

Inventario contra los exports actuales (`sihsalus` en `v2026-06-17-openmrs-order-fix`,
`laboratorio` en `16-06-2026-2` y los otros dominios en `v2026-06-16-openmrs-current`):

| Archivo | Cobertura en OCL por `external_id` | Decisión |
|---|---:|---|
| `concepts-cred-huanca.csv` | 0/77 | Migrar a `SIHSALUS/sihsalus`; son conceptos CRED/Huanca propios con UUID estable. |
| `concepts-odontology.csv` | 0/38 | Migrar a `SIHSALUS/sihsalus`; luego mapear procedimientos recuperativos/preventivos a `procedimientos` cuando aplique. |
| `concepts-psychology.csv` | 0/80 | Migrar a `SIHSALUS/sihsalus`; `Moderado` se reutiliza desde OCL `sihsalus:413` (`external_id` `aed747d5-fba0-49fc-9e29-ebc56b62fb22`). |
| `concepts-form-migration.csv` | 7/20 | Auditar los 13 faltantes; migrar los faltantes y retirar del CSV solo cuando los forms resuelvan por OCL. |
| `concepts-immunization-fhir.csv` | 9/9 | Ya existe en OCL; candidato a retirar después de validar forms/FHIR y set de respuestas. |
| `sihsalus-locale-aliases.csv` | 18/18 | No retirar todavía: validar que OCL conserva los nombres/aliases esperados en `es` y `en`, no solo los UUIDs. |
| `conceptsets/sihsalus-queue-conceptsets.csv` | 18/18 relaciones cubiertas | Candidato a retirar después de prueba de arranque/import en BD limpia. |
| `conceptsets/sihsalus-immunization-conceptsets.csv` | 0/41 relaciones cubiertas | No retirar. El CSV apunta `Vacuna administrada` a 41 productos de `medicamentos`; OCL actualmente usa 22 respuestas `Q-AND-A` hacia `inmunizaciones`. Hay que decidir semántica antes de tocarlo. |

Plan de ejecución:

1. Migrar primero `concepts-cred-huanca.csv`, `concepts-odontology.csv`, `concepts-psychology.csv` y los 13 faltantes
   de `concepts-form-migration.csv` a `SIHSALUS/sihsalus`, preservando el UUID OpenMRS como `external_id`.
   Si un concepto local ya existe semánticamente en OCL, reutilizar el `external_id` existente y actualizar los forms
   en vez de crear un duplicado.
2. Para cada concepto codificado, crear mappings externos solo cuando la equivalencia sea defendible:
   `procedimientos` para CPMS, `diagnosis` para CIE-10, `laboratorio` para pruebas/resultados y
   `inmunizaciones` para vacunas clínicas. No mapear campos operacionales por aproximación.
3. Convertir `conceptsets/*.csv` a mappings OCL (`CONCEPT-SET` o `Q-AND-A`) después de que todos los miembros
   existan en OCL. La excepción actual es inmunización: primero hay que decidir si "Vacuna administrada" debe
   responder con conceptos clínicos de `inmunizaciones`, productos de `medicamentos`, o dos preguntas distintas.
4. Re-exportar release OCL, reemplazar ZIPs, y recién entonces retirar filas/archivos CSV ya cubiertos.
5. Agregar guardas de CI antes de retirar contenido: todo UUID de `concepts/*.csv` debe estar en el export por
   `external_id` o estar listado explícitamente como local-only; todo par de `conceptsets/*.csv` retirado debe
   existir como mapping OCL equivalente.

Criterios para eliminar un CSV o filas:

- El export OCL released contiene el concepto por `external_id`, con clase/tipo de dato correctos.
- Las relaciones de answer-set/concept-set están presentes en OCL y resuelven a los miembros esperados.
- Initializer corre en BD limpia sin duplicados de FSN/UUID.
- Los formularios y global properties que referencian esos UUIDs siguen resolviendo después de quitar el CSV.
- Para aliases/locales, OCL conserva los nombres necesarios en los locales usados por el frontend.

---

## 1. Dirección arquitectónica

**OCL como fuente única de verdad de TODOS los conceptos.** Se está deprecando el patrón de
definir conceptos en CSVs del initializer (`configuration/backend_configuration/concepts/*.csv`)
y consolidando todo en sources de OCL.

**Regla de mapeo de terminología:**
- Concepto **estándar / compartible** → mapear a la terminología de referencia correspondiente.
- Concepto **codificable por el MINSA** → mapear a la terminología MINSA (CIE-10, CPMS, etc.).
- Campo **operacional / específico de la app** (snapshots, índices, motivos, groupers) → concepto propio
  en OCL sin mapping externo (no existe estándar para ellos).

---

## 2. Inventario de sources OCL (PeruHCE) — estado 2026-06-01 (post-rebuild, ver §3.4)

| Source | Conceptos | Mappings | Qué es |
|---|---:|---:|---|
| `SIHSALUS-v4` | ~4355 | ~5424 | Source principal — **reconstruido por proceso externo** (§3.4) |
| `diagnosis` | 15751 | 14977 | **CIE-10 MINSA** (diagnósticos) |
| `CPMS` | 12333 | 12331 | **Procedimientos CPMS MINSA** (incluye estomatología D####) |
| `medicamentos` | 1003 | 0 | **PNUME MINSA** (productos/biológicos) |
| `allergies` | 177 | 280 | Alergias |
| `laboratorio` | ~186 | 786 | Laboratorio (no creado en este trabajo) |
| `vacunas` | 22 | 60 | **NUEVO** — vacunas con mappings a CPMS+medicamentos |

### Terminologías externas (viven en SUS orgs, NO en PeruHCE)
| Terminología | URL OCL |
|---|---|
| CIEL | `/orgs/CIEL/sources/CIEL/` |
| RxNORM | `/orgs/NLM/sources/RxNORM/` |
| SNOMED-CT | `/orgs/IHTSDO/sources/SNOMED-CT/` |
| HL-7-CVX | `/orgs/HL7/sources/HL-7-CVX/` |
| WHOATC | `/orgs/WHO/sources/WHOATC/` |

### Collection `PeruHCE/CIEL` ("SIH SALUS CIEL", autoexpand) — **NECESARIA, NO eliminar**
Provee al bundle el subset de CIEL que SIHSALUS-v4 usa como **respuestas reales** (no solo reference-terms).
SIHSALUS-v4 tiene ~645 mappings Q-AND-A/CONCEPT-SET → CIEL, que colapsan en **25 conceptos CIEL distintos**.
~640 de esos usos son **9 respuestas universales**: Yes(1065), No(1066), Unknown(1067), Other(5622),
Negative(664), Positive(703), Normal(1115), None(1107), Not applicable(1175). Esos son los 8-9 del "stub CIEL"
del bundle. **Conservar la collection** — esas respuestas booleanas/genéricas son CIEL canónico; reinventarlas
como conceptos propios sería mala práctica. Los ~1073 SAME-AS → CIEL son reference-terms y NO requieren la collection.
Al re-exportar el bundle (§6), regenerar el zip CIEL desde esta collection, no desde CIEL completo.

---

## 3. Trabajo completado (2026-06-01)

### 3.1 Source `vacunas` (22 conceptos, 60 mappings)
Diseño: **cada vacuna = 1 concepto (clase Drug)** con dos mappings principales:
- `→ CPMS` con map_type **"Associated with"** (el acto de vacunación)
- `→ medicamentos` con map_type **"SAME-AS"** (el producto/biológico PNUME)

Composición:
- **6 migrados desde SIHSALUS-v4 preservando `external_id`/uuid** (verificado coinciden), luego
  **retirados (retired=true) en v4**: `599` HepB, `584` fiebre amarilla, `1726` BCG, `1206` VPH bivalente,
  `1205` VPH tetravalente, `f0000180` VSR. Sus mappings externos (CIEL/RxNORM/SNOMED/HL-7-CVX/WHOATC) se recrearon.
- **16 nuevos** del Esquema Nacional (NTS 196-MINSA/DGIESP-2022) con códigos `5323`–`5340`.
- **4 referencias internas de v4 repuntadas a `vacunas`** antes del retiro (para no romper sets/forms):
  `1204`→(CONCEPT-SET)→1205/1206, `607`→(Associated with)→584, `688`→(SAME-AS)→1726.

Huecos conocidos (no errores):
- VPH bivalente (`1206`): sin producto en PNUME (solo existe tetravalente).
- VSR (`f0000180`): sin código en CPMS ni en medicamentos (vacuna nueva).

### 3.2 Migración de conceptos de inmunización (CSV → OCL)
Los 12 conceptos de `concepts-immunization-fhir.csv` se movieron a OCL y **el CSV se eliminó**:
- **9** en `SIHSALUS-v4` con `SAME-AS CIEL` (scaffolding FHIR Immunization: Vacuna administrada, Fecha,
  Número de dosis, Fabricante, Lote, Vencimiento, Comentario, Próxima dosis, grouper SIHCE-INMUNIZACIÓN).
- **"Vacuna administrada"** (`f9840000…984`) no tenía answer-set; se pobló con **22 mappings Q-AND-A**
  hacia los 22 conceptos de `vacunas`.
- **3** (`f0000182/183/184` — Estado/Motivo/Contexto): preguntas específicas de inmunización; su código
  `SIHSALUS:IMMUNIZATION_*` **se dropeó** (no tiene consumidor en sihsalus-core; quedan solo por uuid).

### 3.3 Correcciones
- 19 mappings externos de `vacunas` apuntaban por error a `/orgs/PeruHCE/sources/{CIEL,RxNORM,…}/`
  (orgs inexistentes) → recreados apuntando a las orgs correctas.
- Source `PeruHCE/SIHSALUS` **creado por error y luego eliminado** (ver §4).

### 3.4 Rebuild de SIHSALUS-v4 por proceso externo (2026-06-01, posterior a §3.1–3.3)
Un **proceso externo** (otro pipeline del equipo) reconstruyó `SIHSALUS-v4`: encogió (~4445→~4355 conceptos,
~7119→~5424 mappings), **reasignó códigos numéricos a conceptos distintos** y **cambió uuids a lo ancho**.
Ejemplos de reasignación: `599`→"Cardiac insufficiency" (era HepB), `584`→"Ninguna" (era fiebre amarilla),
`1726`→"derrame pleural" (era BCG), `f0000182`→"Apetito SIH.SALUS" (era Estado de aplicación de vacuna).

**Coexistencia con el trabajo de vacunas — verificado consistente tras el rebuild:**
- ✅ `vacunas` intacto e independiente (22 conceptos / 60 mappings). Las vacunas viven SOLO ahí (uuids originales);
  **no hay duplicación** — v4 reusó esos códigos para otros conceptos.
- ✅ "Vacuna administrada" (`f9840000…984`) + sus **22 Q-AND-A → `vacunas`** sobrevivieron.
- ✅ Los 4 repuntes siguen válidos: conceptos origen intactos (1204="E", 607="Responsable del establecimiento",
  688="Proveedor de atención prenatal") apuntando a destinos correctos en `vacunas`.
- ⚠️ Casualties del rebuild (asumidos por el proceso externo): los códigos vacuna en v4 (599/584/1726) y los
  3 de estado de inmunización (`f0000182/183/184`) fueron reasignados/clobbered. A esos 3 ya se les había
  dropeado el código, así que sin pérdida relevante.

**Implicación:** el rebuild cambió uuids de v4 → impacta el re-export del bundle (§6) y la continuidad en
OpenMRS si hay obs/forms que referencian uuids viejos. Eso lo gobierna el proceso externo de rebuild, no este trabajo.

---

## 4. Convenciones y lecciones aprendidas (IMPORTANTE)

1. **Trampa de colisión de códigos.** SIHSALUS-v4 reutilizó códigos numéricos bajos para conceptos propios
   que chocan con códigos de CIEL/procedures. Ej.: CIEL `970`=Mother pero v4 `970`="recién nacido de muy bajo
   peso"; `1175`, `47`, `315`, `52`, `1116`, `3483` igual. **Al internalizar conceptos NO se debe conservar el
   código de origen ni hacer find-replace de source** — el importer enlazaría silenciosamente al concepto
   equivocado (sin error). Asignar códigos nuevos y reescribir `to_concept_code` + `to_source`.

2. **Terminologías externas viven en sus orgs**, no en PeruHCE (ver tabla §2). Un mapping a CIEL debe usar
   `/orgs/CIEL/sources/CIEL/`, no `/orgs/PeruHCE/sources/CIEL/`.

3. **Reference-terms self-namespace (`SIHSALUS:CODE`) NO van como source OCL aparte.** El `SIHSALUS` es un
   **ConceptSource** ya definido en `conceptsources.csv` (`bd290180-…`, "Local SIH.SALUS content package concept
   mappings"). Crear un source OCL `PeruHCE/SIHSALUS` con conceptos fue un error (se eliminó). Odontología y
   psicología usan este patrón `SIHSALUS:*` vía CSV. **Cómo representarlo correctamente en OCL es una DUDA ABIERTA (§7).**

4. **Clase `Drug` es correcta para vacunas.** CIEL clasa todas las vacunas como Drug/N-A. La búsqueda de
   medicamentos de OpenMRS usa la tabla **`Drug`** (`drugs/minsa-drugs.csv`), que referencia conceptos de
   `medicamentos` — **NO** la clase de concepto. Los conceptos `vacunas` (sin formulación Drug) no se cuelan
   en el order entry. Riesgo solo si un form busca conceptos por clase=Drug (no se encontró ninguno en los 107 ampathforms).

5. **El `id` (mnemónico) de un concepto debe ser SECUENCIAL NUMÉRICO; el uuid va en `external_id`.**
   NO usar el uuid como `id` primario. (Error cometido y corregido: creé 9 conceptos de inmunización con
   uuid-como-id; se recrearon con id secuencial — VSR→`5341` en vacunas, los 8 FHIR→`5358`–`5365` en v4,
   preservando external_id y mappings.) El `id` de OCL es inmutable (no se renombra con PUT; requiere
   delete+recreate **retire-first** porque la validación de v4 exige FSN único entre activos). OpenMRS
   resuelve por `external_id`/uuid, así que el id es convención, pero seguir el secuencial. Verificar por `external_id`, no asumir.

6. **El backend usa OCL vía .zip ESTÁTICOS**, no fetch en vivo (ver §6 CAVEAT crítico).

7. **SIHSALUS-v4 es inestable: códigos y uuids cambian con rebuilds (§3.4).** Un proceso externo reconstruye
   v4 reasignando códigos numéricos y uuids. **No referenciar conceptos de v4 por código numérico desde otros
   sources** asumiendo estabilidad — `599` puede ser HepB hoy y "Cardiac insufficiency" mañana. Para integraciones
   estables (answer-sets, repuntes) preferir conceptos con **uuid f-prefijado estable** o sources independientes
   (como `vacunas`). Verificar integridad después de cada rebuild externo.

---

## 5. Plan pendiente por dominio

### 5.1 Odontología (`concepts-odontology.csv`, 43 conceptos)
- Hoy: 100% `SIHSALUS:*` (14 reference-terms) o sin mapping. Campos: Snapshot de odontograma, Tipo de registro,
  Índice CPO-D/ceo-d, Riesgo estomatológico, etc.
- **Estándares MINSA aplicables:**
  - Diagnósticos (caries K02…) → **CIE-10** (`diagnosis`) ✅ ya existe
  - Procedimientos (profilaxis, destartraje D####) → **CPMS** ✅ ya existe
  - **Hallazgos del odontograma** (caries, obturado, ausente, corona, sellante, prótesis, fractura, movilidad,
    diastema, giroversión, RR, implante…) → **NTS N° 188-MINSA/DGIESP-2022 "Uso del Odontograma"** ❌ no digitalizado
  - Índices CPO-D/ceo-d → metodología WHO (son números, no códigos)
  - Snapshot JSON / tipo de registro → app-specific, sin estándar
- **Plan:** mover los 43 a OCL (SIHSALUS-v4) + **crear source `odontograma`** con la nomenclatura de la NTS 188.
  Bloqueado por: necesito la **tabla de hallazgos de la NTS 188** (PDF escaneado, requiere OCR/transcripción).

### 5.2 Psicología (`concepts-psychology.csv`, 80 conceptos pendientes)
- Hoy: **sin mappings**. Campos: grouper SIHCE-PSICOLOGIA, Modalidad de ingreso a salud mental, Motivo de
  atención psicológica, Antecedentes de salud mental, etc.
- **Estándares MINSA aplicables:**
  - Diagnósticos (depresión F32-F34, ansiedad F40-F48, conducta suicida X60-X84) → **CIE-10** (`diagnosis`) ✅
  - **No existe** terminología de salud mental distinta a CIE-10 (ni DSM-5, ni SNOMED, ni LOINC — el MINSA usa CIE-10).
  - **HIS Salud Mental** (MANUAL_HIS_SM2016): es una capa de **registro operacional** sobre CIE-10 —
    códigos "Lab", tipo de Dx (P/D/R), actividades/tamizajes. Esos códigos NO son CIE-10 y serían digitalizables,
    pero son difusos. **Valor cuestionable vs esfuerzo (DUDA, §7).**
  - Campos operativos (modalidad de ingreso, motivo de atención) → app-specific, sin estándar
- **Plan:** mover los 80 conceptos propios a OCL (`SIHSALUS/sihsalus`); apuntar answer-sets de Dx a `diagnosis`
  (CIE-10). Reutilizar conceptos existentes cuando aplique; `Moderado` ya se repuntó al concepto OCL `413`.
  NO digitalizar HIS-SM salvo decisión explícita.

### 5.3 Decisión transversal para mover odontología/psicología
Misma fórmula que inmunización: mover conceptos a OCL preservando uuid; los códigos `SIHSALUS:*` se **dropean**
(como en inmunización) **A MENOS QUE** se resuelva la representación correcta del namespace (§7, duda #1).

---

## 6. Operativa de exports OCL

⚠️ El import OCL del backend usa los **`.zip` ESTÁTICOS** en
`configuration/backend_configuration/ocl/`; no consume OCL en vivo.

<<<<<<< HEAD
Estado 2026-06-17: el repo incluye el export released
`10_SIHSALUS_sihsalus_v2026-06-17-openmrs-order-fix.zip` para el source principal y
`20_SIHSALUS_laboratorio_16-06-2026-2.zip` para laboratorio. Además incluye
`03_SIHSALUS_laboratorio_16-06-2026-2-concepts-only.zip` como preseed de conceptos de laboratorio,
necesario para resolver el ciclo de mappings `sihsalus <-> laboratorio`. Los 4 sources de dominio restantes
siguen en `SIHSALUS_*_v2026-06-16-openmrs-current.zip`, y `prestacionales` se importa como
`05_SIHSALUS_prestacionales_v2026-06-17-openmrs-current.zip` antes de `sihsalus`.
=======
Estado 2026-06-15: el repo incluye exports released
`SIHSALUS_*_v2026-06-15-final.zip` para los 6 sources activos de la org `SIHSALUS`.
>>>>>>> 2c881d1 (chore: update OCL exports to final release)

Para cada siguiente migración de conceptos/sets:
1. Crear o actualizar el contenido en OCL.
2. Crear un release explícito del source afectado.
3. Descargar el export oficial de ese release con:
   `https://api.openconceptlab.org/orgs/SIHSALUS/sources/<source>/<version>/export/`.
   Ese endpoint responde con un redirect a S3; descargar con `curl -L`.
4. Reemplazar el `.zip` correspondiente en `configuration/backend_configuration/ocl/`.
5. Correr validaciones locales y CI antes de retirar filas CSV cubiertas por OCL.

Validaciones mínimas aprendidas:

- `unzip -tq <export.zip>` debe pasar.
- `export.json` debe tener un solo objeto `Source Version`, con arrays `concepts` y `mappings`.
- Para UUIDs esperados por frontend/forms, validar por `external_id` dentro del export; la búsqueda `?q=<uuid>`
  de OCL no es confiable para `external_id`.
- Para duplicados aparentes en la UI, validar el concepto activo con `GET /concepts/<id>/` y con el export
  versionado: la UI puede mostrar versiones históricas del mismo ID.
- Los answer sets y concept sets se representan como mappings `Q-AND-A` o `CONCEPT-SET`; no usar `references`
  en source exports.
- Importar conceptos antes que mappings. Si se encolan tareas dependientes, usar la misma cola para preservar orden.
- Después de migrar un CSV a OCL, no dejarlo también en `concepts/` o `conceptsets/`: el paquete no debe importar
  el mismo contenido por OCL ZIP y por CSV Initializer al mismo tiempo.

---

## 7. DUDAS ABIERTAS (a resolver con el equipo)

1. **Representación del namespace `SIHSALUS` en OCL.** Los reference-terms `SIHSALUS:CODE` (self-namespace)
   no tienen representación limpia en OCL. En inmunización se dropearon. Odontología tiene **14** de estos.
   ¿Se dropean también, o hay una forma correcta de representar el ConceptSource SIHSALUS en OCL
   (p.ej. mapear el source OCL SIHSALUS-v4 al ConceptSource SIHSALUS)? **Sin resolver.**

2. **Proceso de re-export del bundle.** Resuelto para operación manual: crear release en OCL, esperar
   `processing=false`, descargar `/export/` con `curl -L`, reemplazar el ZIP estático y validar el paquete.
   Pendiente automatizarlo en CI/script.

3. **¿El frontend o el módulo de calendario SIHSALUS usa los códigos `SIHSALUS:IMMUNIZATION_*`?**
   Se confirmó que sihsalus-core (backend) no los usa, pero no se revisó el frontend. Si los usa, el drop los rompe.

4. **map_type "Associated with" para vacuna→CPMS.** Se usó porque aparece en datos v4 originales. ¿El importer
   OCL→OpenMRS lo acepta para los conceptos nuevos? ¿Es la semántica deseada (acto vs producto)? Validar en build.

5. **Los 10 mappings huérfanos de `procedures` (pregunta 1106 "Nivel I-3").** Source `procedures` muerto (404),
   códigos no recuperables (3492, 7893, 7898, 7911, 7922, 7923, 7924, 7928; solo 3483="Otros" está en v4).
   Requiere redefinir manualmente qué procedimientos CPMS ofrece un Nivel I-3. **Sin resolver.**

6. **Los ~30 mappings rotos restantes en SIHSALUS-v4** (independientes de vacunas): 12 con `from_concept`
   inexistente (3689/3690/3692), 10 con `to_concept` colgado interno (3549/3587/3588/3656), 8 refs externas
   SNOMED/ICD sin `to_source` (344-346, 400-405). **No abordados aún.**

7. **¿Digitalizar HIS-SM y NTS 188 odontograma?** Odontograma (NTS 188) = candidato claro y acotado.
   HIS-SM Lab codes = difuso, valor cuestionable. Falta la lista real de códigos (PDFs escaneados, sin OCR aquí).

8. **Vacunas — completar huecos:** VPH bivalente sin producto PNUME; VSR sin CPMS/medicamentos. Mantener así
   o crear códigos cuando existan.

9. **¿Hasta dónde llega "todo a OCL"?** ¿También se mueven a OCL otros CSVs del initializer (drugs, conceptsets,
   etc.) o solo los `concepts/*.csv`? Definir el alcance de la consolidación.

10. **Coordinación con el proceso externo de rebuild de SIHSALUS-v4 (§3.4).** Hay otro pipeline que reconstruye
    v4 (reasigna códigos/uuids). ¿Cuál es su contrato? ¿Cómo se evita que pise el trabajo manual en v4 (p.ej.
    conceptos de inmunización clobbered)? Definir si v4 lo gobierna SOLO ese proceso (y el trabajo manual va a
    sources independientes como `vacunas`) o cómo se sincronizan. **Riesgo de pisarse mutuamente.**

## 8. Notas operativas

- **Acceso OCL API actual:** `https://api.openconceptlab.org/orgs/SIHSALUS/sources/<src>/...`, header
  `Authorization: Token <token>`. Usar `OCL_API_TOKEN` o un secreto local no versionado; nunca commitear tokens.
- **OCL vivo no basta para OpenMRS:** el backend consume los ZIPs estáticos del repo. Todo cambio en OCL debe cerrar
  con release, descarga del export oficial, reemplazo del ZIP y build/validación del content package.
- **Revisión semántica antes de mover:** si un concepto cambia de source/clase, revisar mappings salientes y entrantes.
  Ejemplo aprendido: `No (respuesta)` debía quedar como respuesta genérica sin mappings salientes; `Highest education
  level` debía poseer sus Q-AND-A educativos.
- **Glasgow:** los UUIDs `glasgowEyeOpeningUuid`, `glasgowVerbalResponseUuid`, `glasgowMotorResponseUuid` y
  `glasgowTotalUuid` viven en OCL desde la release `v2026-06-16-glasgow-vitals`; los CSVs temporales fueron eliminados
  para evitar doble import.
- **Scripts y catálogos** generados en `~/sihsalus/tmp/ocl-fix/`:
  `create_vacunas.py`, `migrate_phase5.py`, `fix_vacunas_maps.py`, `migrate_immunization.py`,
  `cpms_oficial_RM550-2023.xlsx/.csv`, `cpms_catalog.csv`, `vacunas_source_propuesta.csv`,
  `vacunas_cpms.csv`, `vacunas_medicamentos.csv`, `ciel_renumber.csv`, `ciel_mapping_rewrite.csv`.
- **Catálogo CPMS oficial:** NTS RM550-2023, `files.minsa.gob.pe/s/dKEnmyJcG5HXCHK` (requiere User-Agent de navegador).

## 9. Referencia de terminologías MINSA

| Dominio | Documento / norma | Source OCL |
|---|---|---|
| Diagnósticos | CIE-10 (OMS, adoptado MINSA) | `diagnosis` |
| Procedimientos | CPMS — NTS RM550-2023 | `CPMS` |
| Medicamentos/biológicos | PNUME | `medicamentos` |
| Vacunas (esquema) | NTS N° 196-MINSA/DGIESP-2022 + RM 218-2024/474-2025/709-2025/403-2026 | `vacunas` (nuevo) |
| Odontograma | **NTS N° 188-MINSA/DGIESP-2022** (reemplaza RM 593-2006) | pendiente (`odontograma`) |
| Salud mental (registro) | Manual HIS Salud Mental (sobre CIE-10) | no aplica / pendiente |
