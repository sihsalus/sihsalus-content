# SIHSALUS Content Package

SIHSALUS Content Package para OpenMRS, versión **1.25.19**.

El paquete reúne la metadata backend que carga Initializer desde
[configuration/backend_configuration](configuration/backend_configuration):

- [Formularios AMPATH](configuration/backend_configuration/ampathforms) y su
  [guía de nombres e identidades](configuration/backend_configuration/ampathforms/Readme).
- Terminología: [exports OCL](configuration/backend_configuration/ocl),
  [conceptos locales](configuration/backend_configuration/concepts) y
  [conjuntos de conceptos](configuration/backend_configuration/conceptsets).
- Metadata de atención: [programas](configuration/backend_configuration/programs),
  [tipos de encuentro](configuration/backend_configuration/encountertypes) y
  [flujos de programas](configuration/backend_configuration/programworkflows).
- Configuración institucional y de acceso, incluidos
  [ubicaciones](configuration/backend_configuration/locations),
  [identificadores de paciente](configuration/backend_configuration/patientidentifiertypes) y
  [roles](configuration/backend_configuration/roles).

[content.properties](content.properties) declara el nombre, la versión y las dependencias del paquete.
Maven toma el nombre y la versión de [pom.xml](pom.xml) al filtrar ese archivo;
[assembly.xml](assembly.xml) define el contenido del ZIP distribuible.

Los [contratos](docs/contracts), las [auditorías históricas](docs/audits) y los
[validadores](.github/scripts) documentan las restricciones y comprobaciones de la metadata.
El [workflow de construcción](.github/workflows/main.yml) contiene los comandos de validación usados en CI.

Las presentaciones adicionales de medicamentos usan los CSV nativos de
Initializer. Sus identidades estables y fuentes están documentadas en
[el catálogo clínico](docs/clinical-drug-catalog.md).

## Identidad institucional del Hospital Santa Clotilde

La ubicación raíz del hospital conserva la división territorial oficial (Loreto, Maynas, Napo,
Santa Clotilde), el teléfono institucional y el Código Único IPRESS como atributos `Location`.
No se provisiona una calle porque la fuente estatal consultada no publica una dirección vial
utilizable. El contrato, sus fuentes y UUIDs estables están documentados en
`docs/contracts/hospital-santa-clotilde-institutional-metadata.md`.

## Catálogos territoriales locales

Los barrios de Santa Clotilde se modelan como un atributo codificado de persona, separado de la
jerarquía RENHICE. El tipo de atributo `Barrio` se define en `personattributetypes`; las opciones y la
pertenencia al catálogo activo se administran exclusivamente en la fuente OCL independiente
`SIHSALUS/barrios-santa-clotilde`. La release bundleada `2026-08-22-01` contiene los conceptos
`SCL-01` a `SCL-10`, el set `SCL-BARRIOS` y exactamente diez mappings `CONCEPT-SET`.

Los exports oficiales deben ubicarse como
`15_SIHSALUS_barrios-santa-clotilde_concepts_2026-08-22-01.zip` y
`65_SIHSALUS_barrios-santa-clotilde_mappings_2026-08-22-01.zip`. El validador rechaza archivos
faltantes, contenido adicional o una versión/source diferente. El paquete incorpora la release
`SIHSALUS/sihsalus/2026-09-09-1` con exclusión explícita de los once conceptos y diez mappings
retirados de barrios. OCL conserva esos registros porque un administrador de la organización no
puede purgar mappings. El proceso reproducible y sus identidades excluidas se documentan en
[la auditoría de actualización OCL](docs/audits/2026-09-12-ocl-refresh.md).

La suscripción remota permanece en `2026-07-16-02`: el importador remoto descarga el export oficial
sin aplicar el filtro del paquete. Sus registros existentes son semánticamente idénticos y no elimina
los dos conceptos nuevos que recibe Initializer. Una actualización posterior debe volver a comprobar
esa compatibilidad antes de cambiar cualquiera de los dos pins.

Este paquete distribuye únicamente la metadata backend y los exports OCL. La configuración efectiva de
registro, búsqueda y banner se mantiene en `sihsalus-frontend/config/frontend.json`; no se empaqueta una
copia desde este repositorio. OCL conserva `ui_color` y `ui_tag_type` solo como metadata descriptiva y no
clínica; no se persisten como valor del atributo ni garantizan su renderizado. El frontend actual no
consume esa metadata. El selector obtiene sus opciones exclusivamente desde `answerConceptSetUuid`, sin
duplicar el catálogo en la configuración.
`ADDRESS_3/Barrio` se retira en este cambio porque se confirmó que no existen datos reales que deban
migrarse. El contrato está documentado en `docs/contracts/santa-clotilde-neighborhoods.md`.

## Terminología de referencia institucional

Las respuestas `Terrestre`, `Aéreo` y `Fluvial` usadas por la Hoja de Referencia Institucional se
administran exclusivamente en `SIHSALUS/referencia-institucional`. La release bundleada
`2026-08-25-01` conserva los tres UUID OpenMRS y los nombres completos y cortos en español e inglés.
Su export de conceptos se carga desde
`16_SIHSALUS_referencia-institucional_concepts_2026-08-25-01.zip`; la release no contiene mappings.

El CSV temporal `concepts/referral_transport_concepts.csv` debe permanecer ausente para evitar una
doble importación. Este catálogo conserva su release independiente del export principal.
El contrato verificable está en
`docs/contracts/referral-transport-terminology.md`.

Running Spotless
----------------
This project uses Spotless for code formatting. Spotless is embedded in the build process, so when you run `mvn clean package`, Spotless will automatically format your code according to the project's style guidelines.

If you want to run Spotless separately, you can use the following Maven commands:

To apply the formatting:

    mvn spotless:apply

This will automatically format your code according to the project's style guidelines. It's recommended to run this command before committing your changes.

To check if your code adheres to the style guidelines without making any changes, you can run:

    mvn spotless:check

If this command reports any violations, you can then run `mvn spotless:apply` to fix them.

Remember, in most cases, you don't need to run these commands separately as Spotless will run automatically during the build process with `mvn clean package`.

Versión del paquete: **1.25.19**.

La revisión de los rangos de laboratorio y sus bloqueos clínicos se documentan en
[`docs/audits/2026-09-10-laboratory-reference-ranges-pr-225.md`](docs/audits/2026-09-10-laboratory-reference-ranges-pr-225.md).
La subida de versión no acredita su validación clínica ni levanta los controles de Admisión.

La candidata `1.25.19` corrige cuatro puntos de corte inferiores de hemoglobina
según la tabla 13 de la NTS 213 consolidada: 11 g/dL para 24–59 meses y primer/tercer
trimestre, y 10.5 g/dL para segundo trimestre. El
[contrato de captura de laboratorio](docs/contracts/laboratory-reporting.md)
separa estos puntos de corte de los límites analíticos dependientes del método.
CI protege las identidades históricas y la coherencia de límites entre OCL y CSV.
La selección de prematuridad/puerperio y los parámetros del método siguen pendientes;
este cambio no acredita cumplimiento clínico completo.

En OCL remoto también se aplicaron correcciones a 30 conceptos y 12 mappings de
laboratorio. El [registro de cambios y comprobaciones](docs/audits/2026-09-12-ocl-remote-corrections.md)
distingue HEAD actualizado, versiones publicadas y el export que conserva el paquete.

## Validación y publicación

El CI ejecuta en paralelo la validación del paquete, la integración MariaDB/Liquibase
y los escenarios independientes de actualización e instalación nueva con Initializer
real. Un fallo de integración no oculta los resultados del build ni cancela el otro
escenario. La publicación en Maven Central exige que el build, MariaDB/Liquibase y
ambos escenarios pasen en el mismo commit de `main` o `pre-release`; los PR solo validan.

El perfil `release` usa `autoPublish=true` y `waitUntil=validated`: Maven espera
la subida y validación de Sonatype; los errores de cualquiera de ellas bloquean
el workflow. La publicación continúa automáticamente y el paso obligatorio
`Verify Maven Central publication` espera la disponibilidad pública del POM y ZIP.
Así se evita depender de la confirmación final del Portal antes de comprobar los
archivos que consumirá el backend. Un `mvn -P release deploy` exitoso por sí solo
no acredita que ambos archivos ya puedan descargarse; fuera de CI se debe ejecutar
también `.github/scripts/wait_for_maven_central.sh <version>`.

Después de que `publish` confirme el POM y ZIP en Maven Central, el mismo
workflow llama a `Validate with SIHSALUS` usando el mismo commit del paquete.
También valida si la versión ya estaba publicada; se omite si `publish` falla
o se omite. Conserva la ejecución manual y la entrada `sihsalus_ref`, con `main`
como referencia predeterminada del distro. Esta comprobación es posterior a la
publicación: un fallo no revierte el artefacto publicado.

## Permiso de relaciones para Admisión

El rol canónico `Admision` recibe `Delete Relationships` para anular relaciones de
responsables mediante la API de OpenMRS, también al reemplazarlas. La anulación
conserva el registro y no equivale a una purga física (`Purge Relationships`).
Conserva su UUID, nombre, herencias vacías y el resto de su lista explícita de
privilegios. No se modifican otros roles ni se agregan permisos de administración
o purga.

El permiso se publicó separadamente en `1.25.15`. La consolidación adicional
de identidades de Admisión se revisa en la candidata `1.25.16` y requiere los
controles de actualización indicados a continuación antes de aplicar contenido.
La publicación no modifica relaciones existentes ni demuestra autorización en un
backend desplegado; se debe probar el flujo permitido y denegado con datos
sintéticos.

## Reconciliación de identidades de Admisión en borrador

La candidata reemplaza la unión indiscriminada de roles por una reconciliación
transaccional restringida al contrato de Admisión actual o inmediatamente
anterior. Las comprobaciones preceden a la normalización histórica, cuyos
checksums se conservan. Los estados incompatibles requieren revisión, no una
corrección automática de permisos o herencias.

No publicar ni desplegar hasta completar los controles de
`docs/contracts/admission-role-reconciliation.md`: una prueba SQL no demuestra
el resultado de Initializer ni sus permisos efectivos. El modo predeterminado
de Initializer puede continuar tras errores; la configuración de parada ante
errores debe coordinarse y verificarse fuera de este paquete.

EMRAPI mantiene los roles `Privilege Level: Full` y `Privilege Level: High`;
sus dos filas se retiran de `roles-core.csv` para evitar que Initializer también
reescriba sus permisos. Se conservan sus UUID, las referencias por herencia y el
catálogo de privilegios. El [contrato de Admisión](docs/contracts/admission-role-reconciliation.md)
documenta esta responsabilidad y las comprobaciones de actualización e instalación
nueva. Ambos ensayos usan datos sintéticos y no acreditan aceptación clínica ni despliegue.

## Contrato preparatorio para PDF de resultados de laboratorio

El rol canónico `Laboratorio` recibe los marcadores declarativos
`Create Attachments` y `View Attachments`, y conserva `Add Observations` como
parte de su contrato clínico existente. Estos marcadores preparan la integración
coordinada, pero no habilitan el flujo por sí solos. Attachments 4.0.0 no es
compatible y el flujo permanece no operativo con esa versión. El rol legado
`Tecnico de Laboratorio` permanece intacto y no se agrega
`app:hoja.clinica.adjuntos.editar`.

El adjuntador genérico conserva su separación canónica: el rol
`SIH SALUS Hoja Clinica Adjuntos` mantiene `View Attachments`, mientras
`SIH SALUS Hoja Clinica Adjuntos editar` declara `Create Attachments` y
`View Attachments` y conserva sus asignaciones clínicas existentes. No se
amplían otros roles para esta compatibilidad.

El contrato define el PDF como evidencia suplementaria del resultado. Cuando el
flujo sea habilitado, su carga no deberá completar la orden, cambiar su estado
ni sustituir resultados estructurados o su validación clínica. El flujo de
laboratorio deberá seguir finalizando la orden mediante operaciones explícitas.

El flujo requiere una release backend compatible con Attachments
`>=4.0.1-sihsalus.1 <5.0.0`, con autorización server-side y acceso interno
acotado a su configuración. No se debe conceder `Get Global Properties` al rol
ni resolver la compatibilidad ampliando sus privilegios.

`Laboratorio` ya tenía `Edit Observations` y `Delete Observations`. Esta versión
no altera esas asignaciones ni promete impedir el borrado.

## Contrato canónico de Visit Notes

Visit Notes usa el `Form` `c75f120a-04ec-11e3-8780-2b40bef9a44b` y el tipo de
encuentro `d7151f82-c1f3-4152-a605-2f9ea7414a79`. Initializer 2.12 no ofrece un
dominio CSV genérico para `Form`, por lo que Liquibase crea de forma idempotente
la metadata que falta y solo completa una asociación de tipo de encuentro nula.
Un `Form` existente nunca se renombra, publica, retira ni reasocia silenciosamente.

El contrato también fija los datatypes de los conceptos consumidos por el frontend
y separa `app:hoja.clinica.resumenConsulta` de
`app:hoja.clinica.resumenConsulta.editar`. Los detalles verificables están en
`docs/contracts/visit-note-content-contract.json`.

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

## Cobertura MINSA (Categoría II)

Este paquete ya incluye formularios para consulta externa, obstetricia, salud mental, laboratorio básico de resultados, vacunación, odontología y hospitalización básica. Varios procesos de MINSA pueden quedar cubiertos por módulos nativos de OpenMRS (por ejemplo, triaje/laboratorios/medicación según configuración), pero se dejó esta lista para identificar brechas de documentación clínica en formularios SIH-SALUS.

Cobertura estimada (categoría II-1 / II-2):

1. Cubierto por formularios o metadata de este paquete
   - Atención ambulatoria y consulta externa: `CE-*`, `PSIC-*`
   - Signos vitales y urgencia: metadata y contrato separados para el registro longitudinal del
     chart, el triaje de emergencia y la atención posterior. La captura debe implementarse en el
     frontend como módulo embebido; este paquete no agrega un formulario JSON en `/ampathforms`.
   - Obstetricia y neonatal: `OBST-*`, partograma, RN y puerperio
   - Hospitalización: `HOSP-001`, `HOSP-004`, `HOSP-008`, `HOSP-009`, `HOSP-012`, `FormularioEpicrisisMédica`
   - Referencia/contrarreferencia: `CE-REF-*`
   - CRED y programas de continuidad: `CRED-*`, incluyendo Huanca Test adaptado (`CRED-026`) y lista de habilidades/conductas esperadas (`CRED-027`)
   - Salud mental: `PSIC-001` a `PSIC-004`
   - Odontología: `ODONT-*`
   - Inmunizaciones: `INMU-001` y `INMU-002`; pendiente alinear el set de vacunas/productos contra la NTS 246-MINSA/DGIESP-2026.

1. Parcial o soportado por OpenMRS nativo (requiere validación local)
   - Prescripción médica: formulario de prescripción + módulos de med list/order
   - Laboratorio: resultados presentes; revisar si el flujo de solicitud/muestra está cubierto nativamente
   - Farmacia: prescripción cubre parte del proceso; validar dispensación y conciliación con flujo nativo
   - Radiología/imagen y patología: validar módulos instalados antes de crear formularios
   - UCI y cirugía/electiva: revisar visittypes y módulos de urgencia/cirugía habilitados

1. Pendientes prioritarios para documentación MINSA por categoría II
   - Documentación completa de urgencia más allá de la metadata de triaje: atención inicial,
     observación/evolución y reanimación
   - Formularios quirúrgicos y anestésicos (pre-operatorio, consentimiento, nota operatoria, anestesia, recuperación)
   - Solicitud de laboratorio + toma y trazabilidad de muestra
   - Solicitud e informe de imagen diagnóstica
   - Solicitud/compatibilidad/administración transfusional
   - Interconsulta y admisión hospitalaria no obstétrica (si aplica)
   - Nutrición clínica y plan hospitalario
   - Farmacia: dispensación y seguimiento farmacéutico en hospitalización
   - Documentos de esterilización de material/central de esterilización
   - II-2: ingreso y monitorización UCI, y soporte crítico (si aplica)

Referencias mínimas
- NTS 021-MINSA/DGSP-V.03 (categorías de establecimientos): https://spij.minjus.gob.pe/Graficos/Peru/2011/Julio/16/RM-546-2011-MINSA.pdf
- NTS 139-MINSA/2018/DGAIN (gestión de historia clínica): https://spij.minjus.gob.pe/Graficos/Peru/2018/Marzo/15/RM-214-2018-MINSA.pdf
- NTS 238-MINSA/DGIESP-2025 (control de crecimiento y desarrollo del niño): https://www.gob.pe/institucion/minsa/informes-publicaciones/7857089-norma-tecnica-de-salud-para-el-control-de-crecimiento-y-desarrollo-del-nino-nts-n-238-minsa-dgiesp-2025
- NTS 246-MINSA/DGIESP-2026 (esquema nacional de inmunizaciones): https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa
- Guía de Vigilancia del Neurodesarrollo - Huanca Payehuanca (manual de aplicación): https://repositorio.essalud.gob.pe/handle/20.500.12959/5846

Antes de crear o modificar formularios clínicos, revisar la norma técnica vigente en fuentes oficiales MINSA/gob.pe. No asumir que una NTS anterior sigue vigente si existe resolución posterior.
