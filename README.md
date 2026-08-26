# SIHSALUS Content Package

SIHSALUS Content Package para OpenMRS, con la versión actual **1.25.14**.

The contents of a typical Content Package are:
* **Configuration**
    * This folder holds [Initializer compatible configuration metadata]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/README.md)) that make up the content package. For example, in the /config directory, this includes:
        * **Forms** (in /ampathforms)
        * **Concepts** (in [/ocl]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/README.md#:~:text=Open%20Concept%20Lab%20(ZIP%20Files))), [/concepts]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/readme/concepts.md)))
        * **Programmatic Metadata** such as:
            * Programs (in [/programs]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/readme/prog.md)))
            * Encounter types (in [/encountertypes]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/readme/et.md)))
            * Workflows (in [/programworkflows]([url](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/readme/prog.md)))
            * Identifiers and other metadata
* **content.properties File**
    * Contents: This file specifies the required ESMs and OMODs (frontend modules and backend modules) that make up the Content Package.
    * Importance:
        * The content.properties file is important because when Implementers add this Content Package to their distribution, the content.properties file will automatically be read and compared with their existing distro.properties file.
        * An automatic distro Build Helper Tool then fetches the content package's information and extracts the content into the Implementation's distro.properties file.
        * **Dependencies** are especially important here, as the Build Helper Tool will add any dependencies from the Content Package into an Implementation's distro.properties file.

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
faltantes, contenido adicional o una versión/source diferente. El source principal `SIHSALUS/sihsalus`
y su suscripción permanecen en `2026-07-16-02`; no se actualizan para incorporar este catálogo local.
OCL conserva los registros retirados en el HEAD de `sihsalus` porque un administrador de la organización
no puede purgar mappings. No se debe publicar ni bundlear una release futura de `sihsalus` que incluya
esos UUIDs retirados hasta que soporte OCL los purgue o el proceso de export los excluya explícitamente.

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
doble importación. El source principal `SIHSALUS/sihsalus` y su suscripción continúan en
`2026-07-16-02`. El contrato verificable está en
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

Versión del paquete: **1.25.14**.

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
