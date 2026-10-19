# Contrato canónico de cita, atención y cola

## Alcance

Este contrato separa los conceptos que antes se repetían en especialidad, tipo de servicio,
`VisitType`, `EncounterType` y cola. La fuente ejecutable es
[`hsc-care-routing.csv`](hsc-care-routing.csv); este documento explica sus reglas. Cualquier
cambio de cartera modifica primero el CSV y pasa
`.github/scripts/validate_appointment_queue_integrity.py`; editar solo el frontend o una base de
datos no es una configuración reproducible.

## Decisiones

1. `AppointmentServiceDefinition` representa el servicio programable de la cartera local.
2. `AppointmentSpeciality` se usa como categoría de agenda. Puede corresponder a una especialidad
   reconocida o a una categoría local explícitamente identificada como tal.
3. `VisitType` representa solamente el ámbito de atención: ambulatorio, hospitalización,
   emergencia, extramural o sesión grupal.
4. `EncounterType` representa el evento clínico y no la especialidad de la agenda.
5. `Queue` representa una línea de espera operativa por ubicación. Varios servicios pueden
   compartirla sin perder su contexto, porque la cita conserva el servicio.
6. `Queue.service` siempre es un `Concept` dedicado. Nunca se reutiliza el UUID de un servicio de
   cita como si fuera un Concept.
7. La llegada se resuelve mediante una regla exacta por UUID de servicio y ubicación. No se
   infieren equivalencias por nombre.
8. La validación de la categoría del profesional es configurable en `off`, `warn` y `strict`,
   sin comparar nombres. El modo inicial es `warn`: hace visible una discordancia pero no bloquea
   la agenda mientras el hospital completa el catálogo.

## Odontología

`Cirujano dentista` es una profesión; `Cirugía Bucal y Maxilofacial` es una especialidad. El
servicio general queda asociado a la categoría local `Odontología general`. La categoría no se
presenta como especialidad RNE y CBMF queda disponible únicamente para una futura agenda de
especialistas habilitados.

## Cartera HSC II-1

El contrato incluye los 16 registros existentes: 13 programables y tres retirados. La referencia
a un ítem de la NTS 249 identifica la prestación usada para modelar cada servicio, pero no declara
por sí sola que el hospital tenga habilitada toda la cartera nacional. Horarios, cupos,
profesionales y servicios adicionales siguen siendo configuración local.

Los flujos no programables quedan fuera de citas:

- urgencias y emergencias se inician como atención inmediata;
- atención inmediata del recién nacido se vincula al parto;
- aplicación de inyectables permanece retirada hasta confirmar la UPSS Tópico de Atención de
  Salud y la cartera aprobada del establecimiento.

## Catálogo de categorías y especialidades

Los CSV de `configuration/appointmentspecialities/` forman un solo catálogo de
`AppointmentSpeciality`; cada UUID y nombre aparece una sola vez entre archivos.
La distribución conserva los 16 UUID históricos y añade 19 identidades de enfermería:

| Archivo | Contenido |
| --- | --- |
| `specialities_medicina.csv` | Once especialidades médicas del catálogo histórico. |
| `specialities_enfermeria.csv` | Diecinueve especialidades de enfermería de CONAREN. |
| `specialities_odontologia.csv` | Cirugía Bucal y Maxilofacial. |
| `specialities_categorias_locales.csv` | Medicina General, Odontología general, Salud Mental y Nutrición como categorías de agenda. |

El catálogo médico normaliza las denominaciones
Ginecología y Obstetricia, Ortopedia y Traumatología, Radiología, Patología Clínica y Medicina
Física y Rehabilitación según la publicación oficial del MINSA «Salud te atiende».
Las profesiones y los agrupadores locales mantienen una identidad propia y se declaran aparte
de las especialidades profesionales. La base de cada categoría usada por un servicio sigue
explícita en el contrato CSV. Renombrar o separar un archivo no cambia esa base, los servicios,
la habilitación de profesionales ni el registro de especialidad de una persona.

`specialities_enfermeria.csv` contiene las 19 denominaciones del Anexo 6 del Reglamento de
Admisión de CONAREN de 2018, con UUID locales nuevos e independientes de medicina. Solo se
normalizan las tildes y se omite el punto final de «Enfermería en Gestión y Políticas de Salud».
La publicación del MINSA del 13 de marzo de 2026 confirma 19 especialidades aprobadas y ocho
en funcionamiento. El Anexo 10 de las disposiciones de CONAREN para la admisión 2026 enumera
esas ocho; el catálogo incluye también las otras once denominaciones aprobadas, sin afirmar
que tengan plazas de residentado vigentes ni oferta habilitada en el hospital.

Para CRED, la denominación específica del cuadro es **Enfermería en Salud y Desarrollo
Integral Infantil: CRED e Inmunizaciones**. **Enfermería en Pediatría** es otra entrada del
mismo cuadro. La NTS N.° 238-MINSA/DGIESP-2025 regula la prestación de control de crecimiento y
desarrollo; catalogar una especialidad no establece por sí solo un requisito de titulación
para prestar CRED. El servicio general «Atención ambulatoria por enfermera(o)» conserva su
base `profession` y no se restringe a una especialidad infantil. Habilitar una agenda
específica exige definir el servicio y su enrutamiento en el contrato canónico.

El loader nativo de Initializer admite varios CSV de especialidades. La separación de
archivos conserva el encabezado `Uuid,Void/Retire,Name` y las referencias por UUID; el
validador comprueba el catálogo completo y detecta identidades o nombres duplicados entre
archivos. Los UUID son identidades de OpenMRS, no códigos oficiales de MINSA o CONAREN.

## Referencias

- La [Resolución Ministerial N.° 625-2026-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/8389687-625-2026-minsa),
  publicada el 16 de julio de 2026, aprueba la NTS N.° 249-MINSA/DGAIN-2026 y publica su anexo
  oficial. Los números y nombres de prestaciones del contrato se verificaron contra el Anexo
  N.° 01 de esa norma.
- MINSA, [«Salud te atiende»: especialidades](https://www.gob.pe/42558-que-es-salud-te-atiende-especialidades),
  actualización del 14 de enero de 2024: fuente de las cinco denominaciones médicas normalizadas.
- MINSA, [fortalecimiento del Residentado en Enfermería](https://www.gob.pe/institucion/minsa/noticias/1365655-mas-enfermeras-especialistas-para-el-peru-minsa-fortalece-el-residentado-en-enfermeria-para-mejorar-la-atencion-a-los-pacientes),
  13 de marzo de 2026: confirma el alcance de 19 especialidades aprobadas y ocho en funcionamiento.
- CONAREN, [Reglamento de Admisión 2018, Anexo 6, página 19](https://www.conaren.org.pe/documentos/reglamento_admision_2018.pdf#page=19):
  fuente de las 19 denominaciones, incluidas las entradas distintas de CRED y Pediatría.
- CONAREN, [Disposiciones complementarias 2026, Anexo 10, página 30](https://www.conaren.org.pe/documentos/2026/Disposiciones/DISPOSICIONES%20COMPLEMENTARIAS.pdf#page=30):
  especialidades ofertadas en el concurso de admisión 2026. El
  [Reglamento Interno de CONAREN](https://www.gob.pe/institucion/minsa/normas-legales/192189-466-2016-minsa)
  fue aprobado mediante la R. M. N.° 466-2016-MINSA.
- MINSA, [R. M. N.° 682-2025-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/7281593-682-2025-minsa)
  y [NTS N.° 238-MINSA/DGIESP-2025 en el repositorio institucional](https://repositorio.minsa.gob.pe/handle/MINSA/81953):
  norma de la prestación CRED, diferenciada del catálogo de especialidades profesionales.
- Initializer, [formato nativo de especialidades](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/readme/appointmentspecialities.md),
  revisión fijada para `2.13.0-sihsalus.2` en el distro: admite varios CSV en el mismo dominio.
- La separación técnica se verificó contra OpenMRS Core `2.8.8`, Appointments `2.1.0`, Queue
  `3.0.0` e Initializer `2.12.0`. La NTS define la cartera y las prestaciones; la correspondencia
  con objetos OpenMRS es una decisión de diseño local, no una equivalencia exigida por MINSA.

La revisión del catálogo y sus fuentes se realizó el 19 de octubre de 2026. La cartera de
servicios se mantiene referida a la NTS 249 y CRED a la NTS 238. La existencia de una categoría
no incorpora automáticamente una prestación a la cartera HSC ni define tiempos de atención,
calendarios o criterios clínicos. La cobertura clínica pendiente de CRED e inmunizaciones se
describe en la [guía de contenido](../content-guide.md#alcance-clínico-documentado).

## Llegada

Las políticas son:

- `queue-optional`: Admisión puede registrar atención directa o incorporar al paciente a la cola;
- `queue-required`: la llegada debe crear una entrada de cola;
- `direct`: inicia la atención sin cola física;
- `not-applicable`: el servicio no puede programarse.

En el contrato actual hay 11 reglas `queue-optional`, dos `direct` y tres retiradas. La ubicación
de la cola debe coincidir con la ubicación de la cita. Toda regla habilitada exige un `VisitType`
de ámbito, incluso cuando no usa cola. Una regla faltante o ambigua bloquea la operación con un
error en español y no crea datos parciales.
