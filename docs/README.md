# Documentación

El [README principal](../README.md) describe el paquete y su estructura.
Consultar [AGENTS.md](../AGENTS.md) antes de contribuir.

## Guías

| Documento | Contenido |
| --- | --- |
| [Desarrollo y validación](development.md) | Requisitos, comandos locales, empaquetado y publicación. |
| [Contenido por dominio](content-guide.md) | Contratos de formularios, catálogos y alcance clínico documentado. |
| [Formularios AMPATH](../configuration/ampathforms/Readme) | Nombres, versiones e identidad persistida. |
| [Medicamentos](content-guide.md#presentaciones-adicionales-de-medicamentos) | Conceptos y presentaciones adicionales mediante CSV nativos. |
| [Acceso clínico](clinical-rbac.md) | Roles, privilegios y restricciones por ámbito. |

## Contratos por dominio

| Dominio | Contrato |
| --- | --- |
| Identidad institucional | [Hospital Santa Clotilde](contracts/hospital-santa-clotilde-institutional-metadata.md) |
| Catálogo territorial | [Barrios de Santa Clotilde](contracts/santa-clotilde-neighborhoods.md) |
| Referencias institucionales | [Terminología de transporte](contracts/referral-transport-terminology.md) |
| Procedimientos | [Sitios anatómicos en español](contracts/procedure-anatomy.md) |
| Admisión | [Reconciliación de roles](contracts/admission-role-reconciliation.md), [confirmación de pago](contracts/arrival-payment.md) |
| Perfiles del hospital | [Criterios y decisiones](contracts/hospital-access-profiles.md), [contrato verificable](contracts/hospital-access-profiles.json) |
| Visit Notes | [Identidades y datatypes](contracts/visit-note-content-contract.json) |
| Consulta externa | [Diagnóstico CE-001](content-guide.md#contrato-de-diagnóstico-de-ce-001), [examen físico](content-guide.md#contrato-de-examen-físico-de-consulta-externa) |
| Historia social | [Alcohol y tabaco](contracts/social-history.md) |
| CRED | [Alta neonatal, hemoglobina y terminología pendiente](content-guide.md#contrato-clínico-de-cred) |
| Laboratorio | [Captura y rangos](contracts/laboratory-reporting.md) |
| Signos vitales | [Contrato de encuentros](contracts/chart-vitals-encounter-contract.md) |
| Triaje | [Rangos de referencia](contracts/triage-reference-ranges.md) |
| Enrutamiento de atención | [Catálogo canónico](contracts/hsc-care-routing.csv), [contrato](contracts/hsc-care-routing.md) |
| Catálogos OCL | [Transición institucional](audits/2026-10-16-ocl-institutional-transition.md), [exclusiones históricas](contracts/ocl-sihsalus-2026-09-09-1-exclusions.json) |

## Historia

El [índice de auditorías](audits/README.md) organiza las revisiones fechadas por
tema. El [CHANGELOG](../CHANGELOG.md) registra los cambios por versión y su
estado de publicación.
