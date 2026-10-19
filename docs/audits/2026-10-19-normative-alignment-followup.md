# Seguimiento de alineación normativa y contratos de frontend

Fecha: 19 de octubre de 2026. Esta revisión complementa el catálogo de
especialidades de [PR 271](https://github.com/sihsalus/sihsalus-content/pull/271),
ya integrado en `main` como `1.25.38`.
La [revisión anterior](https://github.com/sihsalus/sihsalus-content/blob/10a50ce99ac13174443f3d6fe235af71f5e34751/docs/audits/2026-10-19-content-frontend-normative-review.md)
conserva el inventario y la evidencia de los once hallazgos.

## Estado de los hallazgos

«Implementado» describe el cambio propuesto; sigue pendiente su aceptación
clínica e integrada. No significa despliegue ni conformidad normativa integral.

| Hallazgo | Cambio y componente responsable | Pendiente |
| --- | --- | --- |
| 1. Inmunizaciones: conceptos e identidad de Form | Frontend reutiliza conceptos de estado/motivo/contexto de INMU-001 y resolver estricto compartido por nombre/versión; conserva lectura multiversión. Content INMU-001 `1.1.0` separa administración y registro. | Smoke de persistencia/reapertura y rechazo FHIR real. |
| 2. Sujeto y edad del tamizaje mental | Frontend CRED separa PPSC/PSC infantil de la guía para evaluar al adulto identificado. Reutiliza búsqueda de paciente y vínculo nativo sin presumir quién es el cuidador. | Aceptación de flujo con niño y cuidador sintéticos; no automatiza la periodicidad sobre la historia adulta. |
| 3. Gráficas 60–61 meses | Frontend añade las cuatro filas oficiales de mes 60 de OMS AnthroPlus y preserva filas 61–228. | Aceptación clínica de visualización y referencia. |
| 4. Vitamina A | CRED-013 `1.1.0` usa concepto Numeric/UI local nativo, único y verificado contra bundle/HEAD. Conserva Puntaje histórico. | Ensayo nativo fresh/upgrade y aceptación clínica. |
| 5. Prioridad de referencia | CRED-024 `1.1.0` reutiliza `sihsalus:265` y cuatro respuestas Q-AND-A publicadas. | Ensayo nativo y captura clínica. |
| 6. Proveedor de agenda | Frontend aplica off/warn/strict de forma coherente en selección y guardado, incluidos servicios sin categoría. | Smoke con roster y roles operativos. |
| 7. Vitals y roles | Frontend usa tipo/rol longitudinal canónicos, perfil de emergencia específico y preserva payloads offline antiguos. | Triaje ambulatorio conserva contrato histórico y requiere decisión separada; smoke offline y autorización. |
| 8. Calendario y UUID | Frontend usa productos OCL existentes y fechas por meses calendario en el mecanismo actual, con pautas verificadas y sin universalizar grupos especiales. | Validación clínica de pautas y transición NTS 246 completa. |
| 9. Hexavalente/meningococo | [Curación revisable](../terminology/README.md) preparada en formato nativo OCL. HEAD no contiene equivalentes. | **Abierto:** aceptación de las formulaciones/serogrupos ya verificados en la norma, aprobación, importación/publicación y exports oficiales; no se duplicó el catálogo en CSV ni se habilitaron UUIDs inexistentes. |
| 10. ESAVI | Frontend reutiliza resolver estricto y envía visita, ubicación y proveedor/rol explícitos; distingue fecha/hora de reporte del inicio clínico narrado. | Smoke y notificación epidemiológica oficial fuera de este registro. |
| 11. Referencias normativas impropias | Content corrige citas demostrablemente impropias y deja descripciones neutrales donde no se verificó una norma específica. CE-001 `1.0.4` preserva el JSON anterior. | Revisión clínica de metadata; el tipo mixto histórico queda intacto por compatibilidad. |

## Diseño y compatibilidad

Content declara metadata con Initializer: no hay migraciones SQL nuevas ni
cambios a Liquibase publicado. Se conservan UUIDs JSON, nombres y campos de
formularios; las versiones nuevas conservan los esquemas previos y evitan
sobrescribir su historia. El ensayo nativo existente incorpora CRED-013,
CRED-024 e INMU-001 a la comprobación de esquemas e historia y comprueba en
fresh/upgrade/reinicio el datatype y la unidad de vitamina A.

El nuevo concepto de cantidad administrada vive sólo en
`concepts/clinical_measurements.csv`; la capacidad nativa se verificó en el
pin de Initializer. Los validadores de formulario comparten ahora un índice de
OCL y CSV; no se amplió el loader ni se creó otro validador. La futura
transferencia del concepto a OCL conserva el UUID y retira su fila local en el
mismo cambio. Para vacunas se mantiene el catálogo OCL existente y sus Q-AND-A:
la propuesta JSONL está fuera del paquete operativo hasta aprobar/publicar.

Frontend reutiliza workspace de signos vitales, cola offline, componentes de
relación familiar, selector de formularios y mecanismo de pautas de vacunas.
El resolver de formularios se extrae al paquete compartido ya existente. Las
transacciones y autorización efectiva siguen siendo responsabilidad backend;
los roles de registro no asignan profesiones ni privilegios.

## Fuentes primarias y límites

- [NTS 238, edición MINSA 2026](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf): numerales 6.6.3–6.6.5 y 6.8.4/tabla 4. Refieren derivación, sujetos/edades de tamizaje y dosis expresadas en UI.
- [NTS 246 / RM 561-2026](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa): esquema de inmunizaciones, poblaciones y transición de los anexos 1–2.
- [NTS 139 / RM 214-2018](https://cdn.www.gob.pe/uploads/document/file/187992/187487_R.M_214-2018-MINSA2.pdf20180823-24725-1ufma50.pdf): identidad profesional y veracidad del registro clínico.
- [NTS 105 / RM 827-2013](https://www.gob.pe/institucion/minsa/normas-legales/198935-827-2013-minsa), con sus modificatorias: atención materna.
- [NTS 214 / RM 545-2024](https://www.gob.pe/institucion/minsa/normas-legales/5874349-545-2024-minsa): atención neonatal; sustituye la referencia NTS 106.
- [MINSA: tuberculosis](https://www.gob.pe/combatelatuberculosis): NTS 200 / RM 339-2023.
- [OMS AnthroPlus, revisión `7cfcdb3`](https://github.com/WorldHealthOrganization/anthroplus/tree/7cfcdb39026e9a55de55732bc3cf14c82261bcf7/data-raw/growthstandards): filas LMS de mes 60; sin extrapolación.

Los documentos del paquete y los README del frontend detallan los UUIDs y
campos vigentes. Ninguna descripción de metadata acredita por sí sola la
implementación completa de una norma. Las pruebas locales, CI nativo,
validación clínica y aceptación DEV/QLTY son evidencias diferentes; las dos
últimas siguen pendientes. La integración de content no integra ni despliega
automáticamente el frontend coordinado.

## Pendientes al integrar content #273

La integración técnica solicitada corresponde a content `1.25.39`, sobre la
base `1.25.38` de #271 ya integrada. No acredita
aceptación clínica, publicación OCL ni despliegue. La revisión de código de
content `7e12c3cbf46abab69ce5a0e440f939849fa2d976` conserva 168 pruebas Python,
48 pruebas puras del harness, validadores, expresiones en tres zonas horarias
y Maven correctos. En la consulta del 19 de octubre, build, MariaDB, rangos y
`ocl-fresh` habían pasado; los otros escenarios nativos seguían en curso en
[CI del candidato](https://github.com/sihsalus/sihsalus-content/actions/runs/39340566387).
La candidata conjunta `1.25.39`, tras incorporar #271, pasó Maven, los 13
validadores, 176 pruebas Python, 50 pruebas puras del harness, cuatro regresiones
Bash y la validación de rangos. Consultar el resultado final de ese run y el del
commit integrado; una prueba pura del harness no sustituye la ejecución del backend.

| Pendiente | Responsable y condición de cierre |
| --- | --- |
| Frontend coordinado [#1241](https://github.com/sihsalus/sihsalus-frontend/pull/1241) | Frontend: cambios de inmunizaciones conciliados localmente con `main`; 151 pruebas del dominio, TypeScript, lint y build correctos. Gate existente `verify:changed --base origin/main` correcto: 223/223 tareas, 42 desde caché, sobre árbol local `b906dbe7e82a3ca08e5cb93a47f2206ff5860434`. Actualización todavía sin commit/push; PR en borrador. Completar revisión del SHA y smoke integrado antes de habilitarlo. |
| Lectura y edición del legado FHIR | Módulo FHIR2: el release `4.3.0` y el código upstream revisado rechazan la lectura sin administrante y pueden reasignar el grupo al último encuentro de la visita al editar. Hay candidato local en el módulo responsable; faltan ejecutar sus seis regresiones, contribuir el PR, aprobar una versión y verificar su consumo en el distro. La ejecución se detuvo durante la resolución de dependencias Maven; las seis regresiones siguen sin ejecutar. |
| Interoperabilidad de capturas nuevas | Módulo FHIR2 y consumidores: las observaciones REST simples no se traducen a `Immunization` en FHIR2 `4.3.0`. Definir y probar su lectura/exportación en el componente responsable antes de afirmar interoperabilidad; las correcciones locales del legado no agregan esa cobertura. |
| Cartera operativa de agenda | Responsable de cartera y frontend: el catálogo de [#271](https://github.com/sihsalus/sihsalus-content/pull/271) ya está integrado en la base `1.25.38`, con 36 categorías y cinco locales. Faltan aceptación de la cartera y smoke del roster antes del modo `strict`; no asignar especialidades por inferencia. |
| Vacunas todavía sin catálogo publicado | Terminología y responsable clínico: aprobar la [curación OCL](../terminology/README.md), incorporar/publicar en el servicio responsable y obtener exports oficiales. El borrador no forma parte del paquete operativo. |
| Medicamentos y fuentes institucionales | Farmacia: obtener export SISMED vigente y petitorio aprobado, revisar equivalencias y la entrada veterinaria activa. Acceso/cobertura ViDAL sin confirmar; el control RxNorm sólo revisa vigencia de identificadores. Véase [mantenimiento de fuentes](../content-guide.md#procedencia-y-mantenimiento-de-medicamentos). |
| Aceptación de instrumentos, pautas y permisos | Responsables clínicos y de acceso: validar los flujos siguientes con datos sintéticos y dejar la evidencia por versión/ambiente. Los roles nuevos describen responsabilidad del registro; no conceden permisos ni acreditan profesión. |

### Límites verificados de inmunizaciones

La captura nueva INMU-001 usa observaciones REST simples; no es el grupo
CIEL `1421` que traduce FHIR2. FHIR2 `4.3.0` no devuelve esas nuevas capturas
como `Immunization`; la lectura del frontend por REST no demuestra exportación
FHIR. Las dos correcciones locales del módulo no amplían esa cobertura.
Su responsable del registro no demuestra quién administró la vacuna. El frontend no debe copiar al usuario conectado al rol
de administrante ni reparar dosis históricas atribuyéndoselas.

En FHIR2 `4.3.0` (tag `a34ee6a2a666df426876aafcbaafc975f260d2f9`),
`ImmunizationObsGroupHelper.getAdministeringProvider` exige el proveedor del rol
configurado y devuelve 422 si falta. `ImmunizationTranslatorImpl` selecciona el
último encuentro de inmunización de la visita al escribir. Además, una ubicación
omitida puede reemplazarse por la de la visita. El candidato local del módulo
propone omitir el administrante desconocido en lectura y preservar el encuentro
y las ubicaciones originales al editar dentro de la misma visita. No modifica
la GP ni convierte el rol de registro en administrante.

[FHIR R4 permite cero performers](https://hl7.org/fhir/R4/immunization-definitions.html#Immunization.performer).
La corrección corresponde al módulo, sin adaptadores de escritura paralelos en
content o frontend. El candidato todavía no acredita compatibilidad de
PUT/PATCH sin administrante, ubicaciones históricas nulas, creación ni cambio
explícito a otra visita: esos casos también deben probarse.

Código primario verificado:
[helper del release](https://github.com/openmrs/openmrs-module-fhir2/blob/a34ee6a2a666df426876aafcbaafc975f260d2f9/api/src/main/java/org/openmrs/module/fhir2/api/util/ImmunizationObsGroupHelper.java)
y [traductor del release](https://github.com/openmrs/openmrs-module-fhir2/blob/a34ee6a2a666df426876aafcbaafc975f260d2f9/api/src/main/java/org/openmrs/module/fhir2/api/translators/impl/ImmunizationTranslatorImpl.java).

## Flujos a probar en DEV/QLTY

Estado de todos los casos: **pendiente de ejecución integrada y aceptación**.
Usar pacientes, profesionales, visitas y credenciales sintéticos; registrar
SHA/versiones de content, frontend y módulos, resultado y limpieza de recursos.
No deducir estos resultados de CI ni usar pacientes reales para el ensayo.

| Flujo | Comprobación de aceptación |
| --- | --- |
| Instalación y actualización soportada | Ejecutar los cinco escenarios nativos, incluida la transición OCL desde `1.25.34`; comprobar historia de formularios, UUIDs, relaciones, checksums y observaciones previas sin recargas forzadas. |
| CRED-013, vitamina A | Registrar cantidad entera en UI, reabrirla y verificar concepto/unidad. Rechazar texto o decimales; conservar las observaciones históricas de Puntaje y sus esquemas. |
| CRED-024, referencia | Guardar y reabrir cada prioridad con su pregunta y Q-AND-A correctos. No reutilizar severidad ESAVI ni recodificar automáticamente observaciones antiguas. |
| Inmunización nueva REST | Resolver INMU-001 `1.1.0`; registrar una administración anterior al inicio de visita sin retroceder el encuentro. Fecha/hora de registro dentro de visita, fecha de administración separada, una sola escritura y rol de responsable del registro, sin administrante inferido. Formulario/configuración ausente bloquea la escritura. |
| Edición REST y reintento | Editar y reabrir; conservar encuentro, visita, formulario, responsable y fecha de registro originales. Comprobar versionado nativo de observaciones, ausencia de duplicados y comportamiento ante error/reintento. |
| Lectura y edición FHIR heredada | Con el módulo corregido, leer una dosis sin administrante sin inventarlo. Editar por PUT y PATCH una visita con dos encuentros y distintos proveedores/ubicaciones: conservar el encuentro original, su actor/fecha y ubicaciones de grupo y miembros, incluidas las nulas. Verificar por separado ubicación o visita cambiadas explícitamente y creación. |
| Interoperabilidad de capturas nuevas | Conservar la captura única REST y comprobar qué dosis aparecen por REST y por FHIR. Documentar la cobertura de cada consumidor; sólo aceptar exportación y roundtrip FHIR después de una solución del módulo responsable y pruebas de identidad, fechas y actores, sin duplicar escrituras ni convertir automáticamente en el frontend. |
| Historia y errores de inmunización | Mostrar `completed`, `unverified` y `not-done` de un mismo día; calcular la última dosis aplicada sin convertir otras en aplicadas. Un 422/403 o fallo de red debe seguir visible y no presentarse como historia vacía ni producir una reparación automática de proveedor. |
| CE-001 e historia clínica | Abrir la versión nueva `1.0.4`, capturar diagnósticos mediante el flujo nativo y reabrir registros previos con sus esquemas `1.0.3`; no sobrescribir historia. |
| CRED, cuidadores y curvas | Diferenciar paciente infantil y adulto identificado para el tamizaje; no presumir cuidador. Revisar transición de curvas 60/61 meses y pautas por población con el responsable clínico. |
| ESAVI | Guardar/reabrir con visita, ubicación y responsable del registro; distinguir fecha del reporte de la clínica narrada. La notificación epidemiológica oficial se verifica aparte. |
| Agenda, vitales y acceso | Tras integrar el catálogo aprobado, probar `off`/`warn`/`strict` con y sin categorías de proveedor. Verificar encuentros/roles longitudinales y de emergencia, reenvío offline histórico y denegaciones para perfiles sin autorización. Triaje ambulatorio conserva su decisión pendiente. |

La publicación Maven, la publicación OCL y el despliegue tienen evidencias y
decisiones independientes. La integración del PR no da por completada esta matriz.
