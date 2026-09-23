# Guía de contenido por dominio

Esta guía conserva los contratos de formularios y las notas de alcance que no
tienen documento propio. El [índice de contratos](README.md#contratos-por-dominio)
enlaza las definiciones de catálogos, institución, Admisión e historia social.
Las presentaciones adicionales de medicamentos se describen en el
[catálogo clínico](clinical-drug-catalog.md).

## Contrato canónico de Visit Notes

Visit Notes usa el `Form` `c75f120a-04ec-11e3-8780-2b40bef9a44b` y el tipo de
encuentro `d7151f82-c1f3-4152-a605-2f9ea7414a79`. El pin comprobado de Initializer
`2.13.0-sihsalus.1` no ofrece un dominio CSV genérico para `Form`;
la [revisión de Liquibase](audits/2026-09-22-liquibase-initializer.md) documenta
la limitación y las alternativas. Liquibase crea de forma idempotente la metadata
que falta y solo completa una asociación de tipo de encuentro nula.
Un `Form` existente nunca se renombra, publica, retira ni reasocia silenciosamente.

El contrato también fija los datatypes de los conceptos consumidos por el frontend
y separa `app:hoja.clinica.resumenConsulta` de
`app:hoja.clinica.resumenConsulta.editar`. Los detalles verificables están en
[visit-note-content-contract.json](contracts/visit-note-content-contract.json).

## Contrato de diagnóstico de CE-001

`CE-001-CONSULTA EXTERNA` no captura diagnósticos. El diagnóstico CIE-10 se registra exclusivamente mediante Visit Notes como diagnóstico nativo del encuentro; no deben reintroducirse observaciones de texto, certeza u ocurrencia que simulen esa estructura.

El esquema corregido usa la versión `1.0.2`. `AmpathFormsLoader` deriva la identidad persistida del nombre y la versión. En upgrades, una migración idempotente retira y despublica exclusivamente el `Form` `1.0.1` con UUID persistido `da631d8c-c695-3c4a-9d77-19bbbf0174e3`; no elimina ni modifica sus encuentros históricos. La identidad canónica `1.0.2` es `df1a34b4-0e8f-3564-84d9-55ce9e4284bd` y es la única que puede permanecer publicada. El `uuid` incluido en el JSON no es la identidad persistida y no debe usarse como contrato de integración.

Para rollback no se debe volver a publicar el JSON con la versión `1.0.1`, porque reutilizaría y sobrescribiría el recurso histórico que contiene la captura de diagnóstico obsoleta. Se revierte el frontend coordinadamente, sin reactivar el formulario retirado y conservando sus encuentros para lectura histórica.

## Contrato de examen físico de Consulta Externa

`CE-SOAP-001-NOTA SOAP` versión `1.1.0` conserva la versión histórica `1.0.0` y segmenta el examen
general y regional. Estado general, conciencia y orientación, piel y faneras y cada sistema regional
usan su concepto de texto canónico existente. El estado general solicita consignar hidratación y
nutrición cuando sean pertinentes; el resumen regional conserva el campo objetivo SOAP histórico.
Los consumidores identifican cada dato por su `formFieldPath`, no por la posición de la observación.

El formulario no propone ni persiste hallazgos normales automáticamente. El estado general y el
resumen regional/objetivo son obligatorios; los sistemas específicos se registran según pertinencia clínica.
La versión nueva preserva los encuentros y el esquema `1.0.0` para lectura histórica.

## Rangos de laboratorio

El [contrato de captura](contracts/laboratory-reporting.md) concentra datatypes,
unidades, puntos de corte de hemoglobina y pendientes de selección de población
y método. La [auditoría de rangos](audits/2026-09-10-laboratory-reference-ranges-pr-225.md)
y el [registro OCL](audits/2026-09-12-ocl-remote-corrections.md) conservan la evidencia
fechada. Las comprobaciones de coherencia del paquete no acreditan validación clínica.

## Contrato preparatorio para PDF de resultados de laboratorio

La [línea base de acceso clínico](clinical-rbac.md) define los marcadores de
adjuntos, la versión backend requerida y las pruebas de autorización pendientes.
El PDF es suplementario: su carga no completa la orden, cambia su estado ni
sustituye resultados estructurados o su validación clínica. Los permisos
declarados por este paquete no habilitan por sí solos el flujo.

## Base reproducible de Stock Management

El paquete provisiona los catálogos controlados de unidades de empaque y
dispensación, motivos de ajuste y toma física, tipos de fuente y categorías de
artículos. Los UUID se coordinan con
`sihsalus-frontend/config/frontend.json`; un validador bloquea divergencias entre
catálogos, propiedades globales y roles canónicos del módulo.

Esta base instala metadata y permisos, no inventario. Un despliegue limpio debe
comenzar con cero artículos y cero existencias hasta cargar un conteo físico
aprobado. Tampoco habilita el descuento automático desde dispensación: esa
integración requiere una transacción clínica/inventario recuperable antes de
considerarse segura.

## Alcance clínico documentado

El inventario siguiente orienta la revisión de formularios para categoría II-1 /
II-2. No certifica cobertura normativa ni que un flujo esté habilitado en el
hospital. Antes de implementar cambios, comprobar el contrato del dominio, los
módulos del distro y la norma vigente en fuentes oficiales.

### Formularios y metadata incluidos

| Área | Contenido y límites |
| --- | --- |
| Consulta externa y salud mental | `CE-*` y `PSIC-001` a `PSIC-004`. Los diagnósticos se registran mediante Visit Notes. |
| Signos vitales y emergencia | Metadata separada para el chart, triaje y atención posterior; el [contrato de encuentros](audits/2026-07-16-chart-vitals-encounter-contract.md) requiere captura embebida en el frontend. No hay un JSON AMPATH adicional. |
| Obstetricia y neonatal | `OBST-*`, partograma, recién nacido y puerperio. |
| Hospitalización | `HOSP-001`, `HOSP-004`, `HOSP-008`, `HOSP-009`, `HOSP-012` y `FormularioEpicrisisMédica`. |
| Referencia | `CE-REF-*` y [catálogo de transporte](contracts/referral-transport-terminology.md). |
| CRED | `CRED-*`, incluidos Huanca adaptado (`CRED-026`) y habilidades/conductas (`CRED-027`); la [revisión CRED](audits/2026-07-10-cred-nts238-forms.md) delimita los instrumentos resumidos. |
| Odontología | `ODONT-*`; el odontograma es un componente separado. |
| Inmunizaciones | `INMU-001` e `INMU-002`; la [auditoría NTS 246](audits/2026-06-17-inmunizaciones-nts-246.md) registra brechas de vacunas y productos. |
| Laboratorio | Formularios de resultados y rangos con los límites del [contrato de laboratorio](contracts/laboratory-reporting.md). |

### Flujos que requieren comprobación o desarrollo coordinado

| Área | Revisión pendiente documentada |
| --- | --- |
| Emergencia | Atención inicial, observación, evolución y reanimación, además de la metadata de triaje. |
| Prescripción y farmacia | Verificar los módulos nativos de órdenes, dispensación y conciliación; completar seguimiento farmacéutico en hospitalización. |
| Laboratorio y transfusión | Solicitud, toma y trazabilidad de muestra; solicitud, compatibilidad y administración transfusional. |
| Imagen y patología | Comprobar módulos instalados y completar solicitud e informe. |
| Cirugía y anestesia | Evaluación preoperatoria, consentimiento, notas operatoria y anestésica, recuperación. |
| Hospitalización y cuidados críticos | Interconsulta, admisión no obstétrica, nutrición clínica y plan hospitalario; para II-2, ingreso y monitorización UCI según alcance aprobado. |
| Esterilización | Documentos de material y central de esterilización. |

### Referencias documentadas

- [NTS 021-MINSA/DGSP-V.03: categorías de establecimientos](https://spij.minjus.gob.pe/Graficos/Peru/2011/Julio/16/RM-546-2011-MINSA.pdf).
- [NTS 139-MINSA/2018/DGAIN: gestión de historia clínica](https://spij.minjus.gob.pe/Graficos/Peru/2018/Marzo/15/RM-214-2018-MINSA.pdf).
- [NTS 238-MINSA/DGIESP-2025: crecimiento y desarrollo del niño](https://www.gob.pe/institucion/minsa/informes-publicaciones/7857089-norma-tecnica-de-salud-para-el-control-de-crecimiento-y-desarrollo-del-nino-nts-n-238-minsa-dgiesp-2025).
- [NTS 246-MINSA/DGIESP-2026: esquema nacional de inmunizaciones](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa).
- [Guía de Vigilancia del Neurodesarrollo de Huanca Payehuanca](https://repositorio.essalud.gob.pe/handle/20.500.12959/5846).

Estas referencias conservan el contexto de las revisiones documentadas; no se
ha realizado una nueva auditoría normativa como parte de esta limpieza.
