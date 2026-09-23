# Confirmación de pago en Admisión

Initializer provisiona el atributo desde
[arrival_payment.csv](../../configuration/attributetypes/arrival_payment.csv),
incluido desde `1.25.20`:

- UUID: `090eb9b3-a306-450f-8623-9fc00b8d82fa`.
- Entidad: `Visit`; nombre: `Confirmación de pago en Admisión`.
- Datatype: `org.openmrs.customdatatype.datatype.FreeTextDatatype`.
- Cardinalidad: mínimo 0, máximo 1 valor activo por visita.

El frontend usa `arrivalPaymentVisitAttributeTypeUuid` para persistir un objeto
JSON con `version: 1`, `confirmed: true`, `financingUuid` (UUID normalizado del
financiador), `appointmentUuid`, `confirmedBy` (UUID del usuario) y `confirmedAt`
(fecha y hora ISO 8601). Estos campos expresan la declaración manual del usuario;
la auditoría nativa del backend identifica al autor de la escritura. FreeText
almacena el JSON, pero no valida su esquema ni verifica una transacción de Caja.
No se captura número de boleta en esta versión.

Admisión debe revisar el comprobante y marcar explícitamente la confirmación para
continuar el registro de llegada con un financiador conocido distinto de SIS.
No se precarga una confirmación positiva. SIS mantiene su validación de cobertura.
El frontend debe comprobar la disponibilidad del atributo y su persistencia antes
de completar la llegada; un fallo de guardado no acredita pago.

La metadata es aditiva: no modifica visitas históricas, permisos, financiación ni
FUA. Su ausencia en una visita histórica no significa que el paciente no pagó.
El máximo de un valor activo describe la confirmación vigente de la visita, no un
libro de pagos por cada cita. Una corrección debe conservar la auditoría de OpenMRS.

Antes de habilitar el flujo, verificar en DEV/QLTY con datos sintéticos que el
atributo se carga, que Admisión puede guardarlo y leerlo en una visita nueva y una
existente, que sin marcar el checkbox no continúa y que SIS conserva su flujo.
Las pruebas del paquete no sustituyen esta comprobación del frontend/backend.
Para rollback del frontend, conservar el atributo y sus valores históricos.
