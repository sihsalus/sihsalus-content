# Especialidades y categorías de agenda

Revisión de fuentes: 19 de octubre de 2026.

Este directorio declara el catálogo `AppointmentSpeciality` que carga
Initializer. Los registros operativos están únicamente en los CSV. El
[contrato de cita, atención y cola](../../docs/contracts/hsc-care-routing.md#catálogo-de-categorías-y-especialidades)
explica su relación con servicios, profesionales y enrutamiento; el
[contrato CSV](../../docs/contracts/hsc-care-routing.csv) conserva las
asociaciones por UUID.

## Organización del catálogo

| Archivo | Alcance |
| --- | --- |
| [specialities_medicina.csv](specialities_medicina.csv) | Especialidades médicas del catálogo existente; denominaciones contrastadas con la publicación oficial MINSA. |
| [specialities_enfermeria.csv](specialities_enfermeria.csv) | Las 19 denominaciones de especialidades de enfermería del Anexo 6 de CONAREN. |
| [specialities_odontologia.csv](specialities_odontologia.csv) | Especialidad odontológica de Cirugía Bucal y Maxilofacial. |
| [specialities_categorias_locales.csv](specialities_categorias_locales.csv) | Categorías operativas de agenda, identificadas como locales en el contrato. |

Los archivos forman un solo catálogo. Cada identidad se declara una sola vez;
los UUID existentes y las referencias a ellos se conservan. Estos UUID son
identidades de OpenMRS: no son códigos oficiales MINSA ni números de registro
profesional. La separación utiliza el
[loader nativo de Initializer fijado por la distribución](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/readme/appointmentspecialities.md).

## CRED y enfermería pediátrica

El Anexo 6 de CONAREN distingue estas dos entradas:

| Denominación | UUID del catálogo |
| --- | --- |
| Enfermería en Salud y Desarrollo Integral Infantil: CRED e Inmunizaciones | `84525bee-4d9a-4f80-9762-4667735a4ad1` |
| Enfermería en Pediatría | `0cd6df08-e8a1-4c4c-8fae-ee4cbd496b1d` |

Para identificar la especialidad relacionada específicamente con CRED se usa
la primera denominación. Ambas conservan identidades distintas. La
[NTS 238, aprobada mediante RM 682-2025/MINSA](https://www.gob.pe/institucion/minsa/normas-legales/7281593-682-2025-minsa),
regula la prestación CRED; el catálogo de especialidades no establece por sí
solo un requisito de titulación para realizar esa prestación.

El servicio general de atención por enfermería conserva su alcance profesional
y usa la categoría local «Enfermería» (`83cc14ae-0774-437e-8697-0d93b999ddf3`).
Su asociación no exige una especialidad infantil ni asigna categorías a los
profesionales. Una agenda específica de CRED requiere definir el servicio y su
asociación en el contrato canónico, con validación del responsable de cartera.

## Fuentes oficiales y alcance de la evidencia

- [MINSA: especialidades de «Salud te atiende»](https://www.gob.pe/42558-que-es-salud-te-atiende-especialidades): referencia de las denominaciones médicas normalizadas. Es una publicación informativa; no se presenta como un registro exhaustivo de títulos habilitados.
- [MINSA: fortalecimiento del Residentado en Enfermería, 13 de marzo de 2026](https://www.gob.pe/institucion/minsa/noticias/1365655-mas-enfermeras-especialistas-para-el-peru-minsa-fortalece-el-residentado-en-enfermeria-para-mejorar-la-atencion-a-los-pacientes): informa 19 especialidades aprobadas y ocho en funcionamiento.
- [CONAREN: Reglamento de Admisión 2018, Anexo 6, página 19](https://www.conaren.org.pe/documentos/reglamento_admision_2018.pdf#page=19): fuente de las 19 denominaciones de enfermería y de la distinción CRED/Pediatría.
- [CONAREN: disposiciones complementarias de admisión 2026, Anexo 10, página 30](https://www.conaren.org.pe/documentos/2026/Disposiciones/DISPOSICIONES%20COMPLEMENTARIAS.pdf#page=30): ocho especialidades ofertadas en ese concurso. La oferta anual no equivale al catálogo completo de denominaciones aprobadas.
- [MINSA: RM 466-2016](https://www.gob.pe/institucion/minsa/normas-legales/192189-466-2016-minsa): aprueba el Reglamento Interno de CONAREN.
- [MINSA: NTS 249 / RM 625-2026](https://www.gob.pe/institucion/minsa/normas-legales/8389687-625-2026-minsa): referencia de la cartera de servicios y prestaciones; las asociaciones de agenda corresponden al diseño local documentado.

Registrar una especialidad no acredita el título de un profesional, la oferta
de plazas de residentado ni la habilitación de una prestación en el hospital.
La aceptación del catálogo y de la cartera efectiva corresponde a sus
responsables de dominio.

## Relación con el frontend y mantenimiento

Los servicios y las categorías del profesional se relacionan por UUID. Los
nombres visibles pueden corregirse conservando la identidad; los consumidores
que comparen texto requieren revisar esa dependencia. La interfaz aplica el
modo configurado `off`, `warn` o `strict`; el catálogo no implementa permisos ni
habilitación clínica.

Antes de actualizar los CSV, contrastar las fuentes oficiales y el contrato,
conservar identidades y revisar referencias en content y frontend. El
validador existente comprueba todo el directorio, incluidos nombres duplicados
sin distinguir mayúsculas y categorías inexistentes en los servicios:

```sh
python3 .github/scripts/validate_appointment_queue_integrity.py
```

La revisión de documentación requiere comprobar enlaces y consistencia con los
CSV. Los cambios operativos requieren además las pruebas del dominio y los
ensayos nativos de instalación nueva y actualización del workflow. CI,
aceptación clínica y despliegue son evidencias y decisiones separadas.
