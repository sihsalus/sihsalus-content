# Revisión normativa de content y frontend

La configuración revisada conserva incompatibilidades clínicas y operativas entre el
contenido y sus consumidores. El PR de especialidades preserva las identidades y las reglas
de llegada, pero no acredita la conformidad del conjunto. La prioridad es corregir la
persistencia alternativa de inmunizaciones y la selección de instrumentos CRED, coordinando
content, frontend, terminología y responsables clínicos.

## Alcance y versiones

Revisión del 19 de octubre de 2026 con tres agentes y consolidación independiente:

- Content: `d41d25bebbe7610a9814ea0c86f2ee86795c226e`, base del PR #271.
- Frontend: checkout limpio `2ab15da9b680cfc2f4897ba2898851a0bdb2ac77`.
- Distro: checkout `bdfa1bb78095e59fc24eb655bb39aa352fdf5681`; declara content
  `1.25.34`, Initializer `2.13.0-sihsalus.2`, Appointments `2.2.0` y FHIR2 `4.3.0-sihsalus.1`.

El inventario contiene 113 JSON AMPATH, 58 CSV y 63 tipos de encuentro. Se contrastaron los
28 formularios CRED, los contratos de agenda, vitales, inmunizaciones y sus conceptos OCL;
otros dominios se revisaron selectivamente. Los SHA identifican código local, no un despliegue.
No se consultaron historias clínicas ni ambientes DEV/QLTY. No es una auditoría exhaustiva de
todos los requisitos de todas las normas aplicables.

## Hallazgos confirmados

P1 indica un problema de captura o interpretación clínica que debe corregirse antes de
habilitar la ruta afectada. P2 indica una incompatibilidad operativa, terminológica o de
trazabilidad que requiere una corrección coordinada. Todos los hallazgos siguientes son
anteriores al cambio de especialidades del PR #271.

| Hallazgo | Prioridad | Componente responsable | Efecto o condición |
| --- | --- | --- | --- |
| 1 | P1 | Frontend de inmunizaciones | Persistencia alternativa con conceptos e identidad de formulario incompatibles. |
| 2 | P1 | Frontend CRED y flujo del adulto | El tamizaje del cuidador continúa ofreciendo un formulario exclusivamente infantil. |
| 3 | P1 | Frontend CRED | Las curvas excluyen la medición del control de 60 meses. |
| 4 | P2 | Content y OCL | La dosis de vitamina A se registra como puntaje sin unidad UI. |
| 5 | P2 | Content y OCL | La prioridad de referencia se registra como severidad ESAVI. |
| 6 | P2 | Agenda frontend y backend | Tres servicios generales no permiten asignar o conservar un prestador. |
| 7 | P2 | Frontend de vitales | Los escritores conservan el tipo histórico y el rol Unknown. |
| 8 | P2 | Frontend y calendario de inmunizaciones | Las secuencias predeterminadas usan UUID distintos de los productos distribuidos. |
| 9 | P2 | Programa de inmunizaciones y OCL | El selector no cubre hexavalente ni meningococo cuando su administración sea aplicable. |
| 10 | P2 | Frontend ESAVI | La resolución de formularios acepta resultados ambiguos o versiones inadecuadas. |
| 11 | P2 | Content y responsables de dominio | Varias descripciones atribuyen la captura a normas de otra materia. |

### 1 Persistencia alternativa de inmunizaciones

El [contrato frontend](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-patient-immunizations-app/src/immunizations/ampath-form-immunization-config.ts#L6)
usa el UUID del JSON `c1120000-0000-4000-8000-000000000011` como identidad del `Form`.
Initializer deriva `15058601-2fae-3a0b-8d50-24f108f729f7` del nombre y versión `1.0.1` de
[INMU-001](../../configuration/ampathforms/INMU-001-REGISTRO%20DE%20VACUNACIÓN.json).

En ese mismo contrato, líneas 16–18, los UUID `f0000182…`, `f0000183…` y `f0000184…`
representan estado, motivo y contexto de vacunación. El export principal OCL los identifica
como **Apetito**, **Sed** y **Sueño SIH.SALUS**, códigos `sihsalus:4206–4208`.
El JSON INMU-001 utiliza las preguntas correctas `af2ec074…`, `9dab3f0d…` y `5c45d979…`,
códigos `sihsalus:4460–4462`.

El [workspace](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-patient-immunizations-app/src/immunizations/immunizations-form.workspace.tsx#L366)
activa la ruta AMPATH ante determinados errores FHIR; el
[mapper](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-patient-immunizations-app/src/immunizations/ampath-form-immunization-mapper.ts#L109)
construye esas observaciones. En una instalación nativa puede fallar primero la referencia
al formulario; si ese obstáculo se resuelve aisladamente, quedan expuestas las observaciones
con significado incorrecto. Deben corregirse identidad y conceptos juntos, sin reasignar UUID
de OCL. La NTS 139, numeral 4.2.8, exige veracidad del registro.

### 2 Instrumento infantil ofrecido para evaluar al cuidador

El [selector CRED por edad](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-crecimiento-desarrollo-app/src/utils/cred-nts238-form-groups.ts#L68)
ofrece `childMentalHealthForm` al mes de vida y también a los 12–14 y 24–29 meses.
[CRED-011](../../configuration/ampathforms/CRED-011-SALUD%20MENTAL%20NIÑO%20Y%20CUIDADOR.json),
versión `1.3.1`, ya retiró correctamente los resultados del adulto y conserva PPSC/PSC-17.

La NTS 238, 6.6.4, página 24, programa instrumentos del cuidador al mes, a los doce meses
y anualmente entre dos y cuatro años; 6.6.5, página 25, inicia PPSC infantil a los tres años
y PSC a los seis. Para un lactante de un mes, la acción ofrecida conduce al instrumento
infantil y no permite capturar la evaluación del cuidador que motivaba esa entrada. Deben
actualizarse selección, rótulo y acceso a la historia del adulto identificado, conservando
la separación de sujetos y los registros históricos.

### 3 Interrupción de curvas entre 60 y 61 meses

[growth-chart.component.tsx](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-crecimiento-desarrollo-app/src/ui/growth-chart/growth-chart.component.tsx#L75)
cambia exclusivamente a las tablas escolares al cumplir 60 meses. Esas tablas comienzan
en 61 y el [filtro](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-crecimiento-desarrollo-app/src/ui/growth-chart/growth-chart-utils.ts#L160)
excluye expresamente edades menores. La medición del control de cinco años queda fuera
del gráfico seleccionado cuando se realiza desde los 60 meses y antes de los 61. NTS 238,
6.4.d, página 22, incluye ese control y 6.6.7.d,
página 26, requiere graficar y valorar los indicadores. La corrección corresponde a la
transición de referencias del frontend, sin extrapolar tablas fuera de su rango.

### 4 Dosis de vitamina A persistida como puntaje

[CRED-013](../../configuration/ampathforms/CRED-013-ADMINISTRACIÓN%20DE%20VITAMINA%20A.json),
líneas 49–59, pregunta una dosis en UI pero guarda `f0000007…`, **Puntaje SIH.SALUS**,
Numeric sin unidad en OCL. `formFieldPath` conserva la identidad del campo al reabrirlo,
pero no transforma ese puntaje en una dosis para reportes e interoperabilidad.
NTS 238, 6.8.4 y tabla 4, página 37, expresa esta administración en UI. Se necesita buscar
una equivalencia canónica, acordar la transición y versionar el formulario preservando historia.

### 5 Prioridad de referencia codificada como severidad ESAVI

[CRED-024](../../configuration/ampathforms/CRED-024-INTERCONSULTA%20DERIVACIÓN%20REFERENCIA.json),
líneas 50–68, persiste prioridad bajo **Resultado de tamizaje SIH.SALUS** y respuestas
`f0000161…`, `f0000162…`, `f0000163…`, que OCL identifica como **Severidad ESAVI
leve, moderada y severa**. Es una colisión semántica comprobada entre dominios.
NTS 238, 6.6.3.c, página 24, exige registrar riesgo y derivación, pero no define ahí ese
catálogo de prioridades. Debe reutilizarse el contrato canónico de referencias y resolver
la terminología antes de introducir otra versión de captura.

### 6 Asignación de prestadores en servicios sin especialidad

Content declara sin especialidad la atención por enfermería, obstetra y farmacia en
[servicedefinitions.csv](../../configuration/appointmentservicedefinitions/servicedefinitions.csv),
filas 4, 6 y 14. El [filtro frontend](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-appointments-app/src/form/provider-scheduling-category.ts#L106)
devuelve cero profesionales ante esa condición en `off`, `warn` y `strict`.
La misma lista condiciona selector y guardado, incluso al conservar un prestador previo
durante la edición. Crear una cita sin prestador sigue siendo posible.

Un probe con el helper TypeScript real, las tres filas del catálogo y un prestador sintético
reprodujo `eligible=0` en los tres modos, mientras la evaluación devolvía `shouldBlock=false`.
El frontend debe distinguir servicios profesionales sin categoría de una configuración
incompleta y usar una evaluación coherente para selector y guardado. La decisión de
habilitación corresponde al dominio de citas; no debe suplirse con especialidades ficticias.

### 7 Escritores de signos vitales pendientes de migración

Los [defaults de vitales](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-patient-vitals-app/src/config-schema.ts#L93)
conservan el tipo histórico mixto `67a71486…` y rol `Unknown`, sin override en
`config/frontend.json`. La escritura y sincronización offline usan esos valores.
El [contrato vigente](../contracts/chart-vitals-encounter-contract.md) exige
`20d4a603…` y rol `bebe2266…`, ya declarados en content.

Es una migración de tipo y atribución pendiente, también reconocida en
[clinical-rbac.md](../clinical-rbac.md); no demuestra por sí sola valores clínicos erróneos.
Deben coordinarse escritores, lectores, offline, profesional y ubicación, conservando lectura
histórica. El triaje ambulatorio no debe convertirse automáticamente en Triaje de Emergencia.

### 8 Secuencias de inmunizaciones desconectadas del catálogo

El [calendario predeterminado](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-patient-immunizations-app/src/config-schema.ts#L132)
usa BCG `886AAAA…`, hepatitis B `782AAAA…` y pentavalente `1685AAAA…`; los productos
del ZIP de inmunizaciones tienen UUID `b328841a…`, `7a5c2fbc…` y `41844230…`.
De las 22 definiciones predeterminadas de producto, solo VRS coincide con ese ZIP; Nirsevimab está
en el export principal.

El workspace usa esos defaults si no existe un calendario publicado; la búsqueda de
secuencia compara UUID exactos. Content no provisiona `vaccinationschedule.schedule.PE`
y `frontend.json` no lo sobrescribe. En ese escenario los avisos no se enlazan con esos
productos. Debe reconciliarse el contrato del calendario; la falta de automatización por
sí sola no demuestra incumplimiento normativo.

### 9 Productos pendientes del esquema de inmunizaciones

La pregunta `sihsalus:4121` usada por INMU-001 tiene 22 respuestas en el export de mappings,
sin hexavalente ni meningococo. No se encontró hexavalente entre los ZIP; los conceptos
de procedimientos meningocócicos no están conectados al selector de productos.
La NTS 246, anexos 1 y 2, páginas 79–80, incorpora hexavalente y regula su transición:
mantiene pentavalente e IPV mientras estén disponibles y sustituye el primer refuerzo DPT
por hexavalente en 2027. MINSA también identifica meningococo para niños con VIH.

La brecha afecta la captura cuando corresponda administrar esos productos en el hospital;
requiere decisión del programa y terminología, cronograma y stock aplicables.
**Nirsevimab sí se ofrece como opción en la UI**: el frontend lo incorpora como producto
suplementario y OCL ya contiene `sihsalus:4205`. Su ausencia del conjunto de respuestas
no debe volver a reportarse como ausencia del flujo.

### 10 Resolución ambigua de formularios ESAVI

[adverse-reaction.resource.ts](https://github.com/sihsalus/sihsalus-frontend/blob/2ab15da9b680cfc2f4897ba2898851a0bdb2ac77/packages/apps/esm-crecimiento-desarrollo-app/src/well-child-care/workspace/adverse-reaction/adverse-reaction.resource.ts#L99)
acepta un UUID sin verificar o el primer resultado aproximado de búsqueda, sin comprobar
publicación, retiro o versión. La existencia de dos versiones puede seleccionar la
inadecuada; debe reutilizarse la resolución estricta disponible en el frontend.

El POST omite visita y `encounterProviders`. Debe ensayarse su atribución real antes de
afirmar pérdida de asociación: el backend puede completar parte del contexto. NTS 139,
4.2.1 y 4.2.10, distingue identidad del profesional, registro clínico y remisión a
farmacovigilancia. INMU-002 declara expresamente que no sustituye la notificación oficial.

### 11 Atribuciones normativas incorrectas en metadata

En [encountertypes.csv](../../configuration/encountertypes/encountertypes.csv), filas 2,
10, 15, 19–20, 24, 26–27, 32–33 y 49, y en la descripción de
[CE-001](../../configuration/ampathforms/CE-001-CONSULTA%20EXTERNA.json), aparecen
atribuciones que no sustentan la materia específica descrita:

- NTS 029 corresponde a auditoría de calidad; se cita como base de Consulta Externa.
- NTS 050 corresponde a acreditación; se cita como base específica de parto, controles y ecografía.
- NTS 123 corresponde a farmacovigilancia y tecnovigilancia; se cita para el esquema de vacunas.
- NTS 102 corresponde a VIH pediátrico; se cita para referencias, traslados y anemia general.

Las resoluciones oficiales de estas normas se enlazan abajo. Corregir estas descripciones
no acredita el contenido clínico de cada formulario: hace falta contrastar su contrato con
la norma realmente aplicable. Deben conservarse UUID, versiones históricas y recursos de
formularios publicados al preparar cualquier cambio de esquema.

## Compatibilidad comprobada y corrección del PR

- Las 13 reglas habilitadas de llegada coinciden entre el CSV canónico y `frontend.json`
  en servicio, ubicación, política, cola y tipo de visita. Los nombres médicos renombrados
  no mostraron un consumidor ejecutable por texto; se conservan los UUID.
- Coinciden los seis UUID de catálogos de stock; la deducción automática está desactivada.
- Anamnesis CE `1.1.1` y examen físico `1.0.1` coinciden con la selección del frontend.
- Ya están corregidos el sujeto adulto de CRED-011, la captura antropométrica desde cinco
  años en CRED-015, edad a fecha de atención en OBST-002 y separación de biometría neonatal
  en HOSP-010. No se reabren esos hallazgos históricos.
- Compartir Notas clínicas o Plan de manejo entre campos no demuestra pérdida de identidad:
  el motor usa `formFieldNamespace` y `formFieldPath`.

La revisión detectó además una omisión propia del nuevo validador: aceptaba dos categorías
con nombres que diferían solo por mayúsculas. El
[parser de Initializer fijado](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/api/src/main/java/org/openmrs/module/initializer/api/appt/specialities/SpecialitiesCsvParser.java)
busca primero UUID y después nombre mediante `equalsIgnoreCase`, conservando la identidad
encontrada. Se añadió rechazo de colisiones de nombre sin distinguir mayúsculas para el
catálogo español y una regresión entre archivos. No cambia la metadata ni los UUID.

## Observaciones y validación pendiente

La fecha de próxima Hb es una estimación por intervalos de edad y la UI la identifica como
orientativa, con confirmación profesional. No incorpora la pauta real de suplementación;
no debe usarse como seguimiento individual. RM 429, tablas 4 y 8, vincula mediciones al
inicio y término de la suplementación. Es una limitación condicionada, no evidencia de que
se haya creado una cita o aplicado una pauta incorrecta.

Se ejecutó el probe sintético de agenda y se contrastaron CSV, JSON y conceptos de los ZIP.
Las seis regresiones del catálogo y su validador pasan. No se ejecutó Vitest en frontend:
el checkout no tiene `node_modules`. El guardado y reapertura FHIR/AMPATH, la transición de
curvas y la atribución ESAVI requieren ensayos integrados con datos sintéticos sobre los
SHA corregidos. La aceptación del responsable clínico y el despliegue siguen siendo
decisiones separadas del CI y de esta revisión.

## Fuentes oficiales

- [NTS 238 edición 2026](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf?v=1773347457),
  aprobada por RM 682-2025-MINSA. Descarga HTTP 200, SHA256
  `415f543cf91709d4139c15bac81f285054cabeb18e2ea37897a3d6fc6d995c71`, idéntica a la copia
  del frontend. La búsqueda no localizó otra modificatoria; no acredita una revisión jurídica exhaustiva.
- [NTS 139 y RM 214-2018-MINSA](https://cdn.www.gob.pe/uploads/document/file/187992/187487_R.M_214-2018-MINSA2.pdf20180823-24725-1ufma50.pdf),
  numerales 4.2.1, 4.2.8 y 4.2.10, páginas internas 9–10.
- [NTS 246 parte 1](https://cdn.www.gob.pe/uploads/document/file/10154198/8265031-nts-n-246-minsa-digiesp-2026-parte-1.pdf),
  anexos 1–2; [comunicación oficial MINSA del esquema](https://www.gob.pe/institucion/minsa/noticias/1406009-minsa-fortalece-la-salud-publica-con-la-aprobacion-del-nuevo-esquema-nacional-de-inmunizaciones-uno-de-los-mas-completos-de-la-region).
- [RM 429-2024-MINSA](https://cdn.www.gob.pe/uploads/document/file/6498138/5670414-rm-429-2024.pdf),
  tablas 4 y 8, páginas 6–7 del PDF.
- [RM 502-2016 y NTS 029](https://www.gob.pe/institucion/minsa/normas-legales/192132-502-2016-minsa),
  [RM 456-2007 y NTS 050](https://www.gob.pe/institucion/minsa/normas-legales/249702-456-2007-minsa),
  [RM 539-2016 y NTS 123](https://www.gob.pe/institucion/minsa/normas-legales/192066-539-2016-),
  [RM 567-2013 y NTS 102](https://www.gob.pe/institucion/minsa/normas-legales/239918-567-2013-minsa).
- Para continuar otros dominios: [NTS 105 de salud materna](https://www.gob.pe/institucion/minsa/normas-legales/198935-827-2013-minsa)
  con sus modificatorias; [NTS 214 neonatal](https://www.gob.pe/institucion/minsa/normas-legales/5874349-545-2024-minsa),
  que derogó la NTS 106; [NTS 188 de odontograma](https://www.gob.pe/institucion/minsa/normas-legales/3304261-559-2022-minsa).
  La revisión selectiva no acredita conformidad integral en obstetricia, odontología o medicamentos.
