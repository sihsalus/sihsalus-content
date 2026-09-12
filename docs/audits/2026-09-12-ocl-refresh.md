# Actualización de exports OCL

Revisión del 2026-09-12 desde `0c16cae2088b2dad2e135cfae4c50943836bcd3e`.
Candidata del paquete: **1.25.19**. La organización OCL tiene 17 fuentes.
Se consultaron sus releases publicadas y se descargaron los exports oficiales
de `sihsalus/2026-09-09-1` y `laboratorio/2026-09-10-3`.

## Actualización compatible

El export principal pasa de `2026-07-16-02` a `2026-09-09-1`.
Conserva los 4472 conceptos y 5679 mappings anteriores sin cambios semánticos,
y añade dos conceptos activos:

| Código OCL | Nombre | UUID OpenMRS |
| --- | --- | --- |
| 4474 | 1:512 | `3fb84698-488a-447d-acbc-72e8665cffdc` |
| 4489 | Cuatro cruces | `d14f251d-82a1-4ecf-aa45-f17f57a193db` |

Ambos declaran `datatype: "None"` en OCL. El método
`convertConceptDatatypes` de
[Saver 3.2.0](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java)
lo convierte explícitamente a `N/A`. El arnés de integración verifica
los valores persistidos, clases, nombres, identidad y estado activo de ambos
conceptos, además del catálogo de diez barrios, en instalación nueva,
actualización y reinicio.

El export oficial también añade once conceptos de barrios y diez mappings
retirados. Se excluyen explícitamente porque sus UUID pertenecen al catálogo
independiente `barrios-santa-clotilde`. El
[manifiesto](../contracts/ocl-sihsalus-2026-09-09-1-exclusions.json) fija
fuente, release, IDs, UUIDs y huella de cada registro excluido. El filtro falla
si un registro cambia, se reactiva, falta, se duplica o recibe una referencia
adicional que quedaría colgante. Conserva los demás registros, incluso retirados.

El resultado contiene **4474 conceptos y 5679 mappings**. El validador de CI
verifica el JSON canónico recombinado, además de los contratos de identidad,
formularios y catálogos existentes.

| Artefacto | SHA-256 |
| --- | --- |
| ZIP oficial combinado | `73dc1e9ad96df19495417f510d16332f040417a29a71a826fd0c74ed965295c0` |
| ZIP de conceptos del paquete | `887286a5ce50726c53f884a1fb00a4b9a7b9eb2aef7c57a2b2d528a293b02695` |
| ZIP de mappings del paquete | `3d2d25d21324f9d4b496acbce0a61e364f3b24c9002988c4e2ad161463c5ba9e` |
| JSON filtrado canónico recombinado, sin salto final | `cae14cffdce3d5ed882e97cc3ca6030d798788526b3baded304f472f7779e195` |

Reproducción desde el ZIP descargado del
[export oficial](https://api.openconceptlab.org/orgs/SIHSALUS/sources/sihsalus/2026-09-09-1/export/):

```sh
python3 .github/scripts/split_ocl_export.py oficial.zip \
  configuration/backend_configuration/ocl/10_SIHSALUS_sihsalus_concepts_2026-09-09-1.zip \
  configuration/backend_configuration/ocl/60_SIHSALUS_sihsalus_mappings_2026-09-09-1.zip \
  --exclusions docs/contracts/ocl-sihsalus-2026-09-09-1-exclusions.json
python3 .github/scripts/validate_ocl_exports.py
python3 .github/scripts/test_split_ocl_export.py
```

## Suscripción remota

`openconceptlab.subscriptionUrl` conserva `2026-07-16-02`.
El módulo Open Concept Lab 3.2.0 ejecuta su propio importador y no aplica las
exclusiones locales. Apuntarlo a la nueva release oficial reintroduciría los
UUID retirados de barrios. Su importador procesa los registros presentes;
no elimina conceptos ausentes. Por ello, la suscripción anterior es compatible
con este cambio puramente aditivo de dos conceptos.
[Importer 3.2.0](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Importer.java),
[Saver 3.2.0](https://github.com/openmrs/openmrs-module-openconceptlab/blob/6aecd4b8025f1a5467841a84fd603eb149fcfcb2/api/src/main/java/org/openmrs/module/openconceptlab/importer/Saver.java).

Una futura modificación de registros existentes exige revisar ambos pins:
la suscripción anterior podría sobrescribirlos con su metadata antigua.
Esta separación es específica del delta verificado, no una autorización para
mezclar arbitrariamente versiones.

## Inventario conservado

| Fuentes | Release incluida |
| --- | --- |
| medicamentos, diagnosis, inmunizaciones, prestacionales, etnias, religiones, estado-civil, educacion | 2026-06-30 |
| procedimientos, geografia, lenguas | 2026-07-10-02 |
| ocupaciones | 2026-07-09-01 |
| seguros | 2026-07-17-01 |
| barrios-santa-clotilde | 2026-08-22-01 |
| referencia-institucional | 2026-08-25-01 |
| laboratorio | 2026-07-10-02, actualización pendiente |

Las otras quince fuentes ya coinciden con su última release publicada.
Los 41 conceptos locales definidos por CSV mantienen su mecanismo de carga;
esta actualización no cambia su propiedad ni crea copias en OCL. La presentación
de ácido ursodesoxicólico conserva el concepto y el `Drug` de la versión 1.25.18.
No se realizaron escrituras en OCL ni cambios en entornos clínicos.

## Laboratorio pendiente

La release `laboratorio/2026-09-10-3` se comparó y ensayó estáticamente, pero
no se incorpora: cambia tres datatypes con UUID existentes, contradice el
renderer numérico de Urobilinógeno y modifica la unidad de creatinina urinaria
sin una identidad nueva. También existen incompatibilidades entre límites OCL
y los rangos CSV. El detalle y las correcciones necesarias están en
[la auditoría de laboratorio](2026-09-12-ocl-laboratory-refresh.md).

Los validadores actuales de formularios y rangos pasan incluso con esa release;
por sí solos no detectan estas incompatibilidades. La comparación semántica
y el comportamiento del importador son evidencia necesaria.

## Validación

Evidencia inicial del commit `07758fa`, anterior a las correcciones normativas
descritas en [el contrato de laboratorio](../contracts/laboratory-reporting.md).
La validación de la revisión posterior y su CI se registran en el PR.

- **PASSED:** los 24 comandos estáticos y suites de pruebas del job `build`
  de `.github/workflows/main.yml`, anteriores a Maven. Incluyen las seis pruebas
  nuevas de `python3 .github/scripts/test_split_ocl_export.py`.
- **PASSED:** `python3 .github/integration/admission-initializer/test_harness.py`,
  53 pruebas del arnés; no son una ejecución de backend.
- **PASSED:** `mvn --batch-mode clean verify`, Maven 3.9.16 y Java 21 en macOS
  ARM64; genera `sihsalus-content-1.25.19.zip`. El CI usa Java 8.
- **PASSED:** `actionlint .github/workflows/main.yml`, `git diff --check`,
  reproducción del filtro sobre el export oficial y rechazo de tres alteraciones
  sintéticas del bundle fijado (concepto nuevo ausente, metadata divergente,
  partición incorrecta).
- **NOT RUN localmente:** integración MariaDB e Initializer nuevo/actualizado.
  El resultado del CI sobre el commit final se registra en el PR.
- **NOT RUN:** aceptación clínica, publicación y despliegue.

El CI utiliza datos sintéticos; no acredita aceptación clínica ni despliegue.
La versión candidata no se considera publicada hasta verificar POM y ZIP en
Maven Central.
