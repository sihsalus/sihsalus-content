# Índice de auditorías

Estas revisiones conservan fuentes, decisiones y resultados de una fecha y un
alcance concretos. Un pendiente histórico no prueba que siga abierto; una prueba
aprobada tampoco acredita otro commit, un despliegue o aceptación clínica.
Los [contratos por dominio](../README.md#contratos-por-dominio) describen los
requisitos del contenido mantenido y el [changelog](../../CHANGELOG.md) su
historial de versiones.

Las rutas `configuration/backend_configuration/` de revisiones anteriores
corresponden al árbol de fuentes de entonces. Hoy las fuentes están directamente
en `configuration/`; el ZIP conserva aquel prefijo. Los comandos adaptados a la
estructura actual lo indican expresamente.

| Fecha | Revisión | Alcance |
| --- | --- | --- |
| 2026-09-23 | [Formularios y reglas clínicas](2026-09-23-forms-clinical-review.md) | 112 JSON, validadores, casos sintéticos, fuentes MINSA y defectos pendientes; distingue alertas heurísticas de problemas confirmados. |
| 2026-09-22 | [Liquibase e Initializer](2026-09-22-liquibase-initializer.md) | Doce changesets publicados, capacidades verificadas y condiciones para reducir SQL. |
| 2026-09-21 | [Mantenibilidad de Admisión](2026-09-21-admission-maintainability.md) | Revisión anterior a `1.25.24`; inventario parcial de artefactos y entornos. |
| 2026-09-12 | [Actualización OCL](2026-09-12-ocl-refresh.md) | Export principal `2026-09-09-1`, exclusiones y suscripción remota. |
| 2026-09-12 | [Export de laboratorio](2026-09-12-ocl-laboratory-refresh.md) | Incompatibilidades de la release evaluada y actualización completa pendiente. |
| 2026-09-12 | [Correcciones remotas OCL](2026-09-12-ocl-remote-corrections.md) | Cambios verificados en HEAD, sin publicar una release de laboratorio. |
| 2026-09-10 | [Rangos de laboratorio, PR #225](2026-09-10-laboratory-reference-ranges-pr-225.md) | Revisión del cambio original; poblaciones, unidades y límites. |
| 2026-07-18 | [Cita, atención y cola](2026-07-18-canonical-care-routing.md) | Decisión canónica y contrato ejecutable de enrutamiento. |
| 2026-07-16 | [Signos vitales y encuentros](2026-07-16-chart-vitals-encounter-contract.md) | Separación entre chart, triaje y atención de emergencia; evidencia del stack ensayado. |
| 2026-07-10 | [Formularios CRED](2026-07-10-cred-nts238-forms.md) | Instrumentos, anemia, antropometría y límites de digitalización. |
| 2026-07-10 | [Integridad de formularios y OCL](2026-07-10-form-ocl-integrity.md) | UUID, datatypes, respuestas, renderers y expresiones. |
| 2026-07-10 | [Importación OCL en OpenMRS](2026-07-10-ocl-openmrs-import-integrity.md) | Colisiones de nombres y reparación de mappings. |
| 2026-07-09 | [Actualización OCL](2026-07-09-ocl-refresh.md) | Inventario, ocupaciones y cobertura terminológica. |
| 2026-07-09 | [Procedimientos y duración](2026-07-09-procedure-status-duration-units.md) | Estados de procedimiento y unidades de duración O3. |
| 2026-07-09 | [Instrumentos de desarrollo](2026-07-09-sihsalus-test-peruano.md) | TPED, CRED y alcance de formularios resumidos. |
| 2026-06-17 | [Rangos de triaje](2026-06-17-triage-reference-ranges-peru.md) | Umbrales de emergencia; actualización técnica del 16 de julio. |
| 2026-06-17 | [Inmunizaciones](2026-06-17-inmunizaciones-nts-246.md) | Brechas identificadas frente a la NTS 246. |
