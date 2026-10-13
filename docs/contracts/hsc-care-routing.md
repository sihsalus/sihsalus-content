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

## Referencias

- La [Resolución Ministerial N.° 625-2026-MINSA](https://www.gob.pe/institucion/minsa/normas-legales/8389687-625-2026-minsa),
  publicada el 16 de julio de 2026, aprueba la NTS N.° 249-MINSA/DGAIN-2026 y publica su anexo
  oficial. Los números y nombres de prestaciones del contrato se verificaron contra el Anexo
  N.° 01 de esa norma.
- La separación técnica se verificó contra OpenMRS Core `2.8.8`, Appointments `2.1.0`, Queue
  `3.0.0` e Initializer `2.12.0`. La NTS define la cartera y las prestaciones; la correspondencia
  con objetos OpenMRS es una decisión de diseño local, no una equivalencia exigida por MINSA.

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
