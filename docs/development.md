# Desarrollo, validación y publicación

Ejecutar los comandos desde la raíz del repositorio. Antes de cambiar metadata,
leer [AGENTS.md](../AGENTS.md) y el [contrato correspondiente](README.md#contratos-por-dominio).

## Requisitos

- Python 3.9 o superior para los validadores y pruebas de biblioteca estándar.
- Bash para las comprobaciones de rangos, terminología y publicación.
- Node 24 y npm para ejecutar las expresiones JavaScript de formularios con la
  misma biblioteca de fechas del motor. Esta prueba usa el runner nativo de Node;
  los validadores Python no ejecutan JavaScript.
- Maven 3 y Java: CI usa Java 8 para el paquete, Java 17 para autorización de
  rangos y Java 21 para MariaDB/Liquibase.
- MariaDB y el backend de OpenMRS solo se necesitan en sus ensayos de integración;
  cada ensayo documenta su infraestructura y aislamiento.

## Validación local

El [workflow principal](../.github/workflows/main.yml) es la fuente de los comandos
de CI. Para ejecutar todos sus validadores de metadata y las regresiones locales:

```sh
set -e
for validator in .github/scripts/validate_*.py; do
  python3 "$validator"
done
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
bash .github/scripts/validate_reference_ranges.sh
for regression in .github/scripts/test_*.sh; do
  bash "$regression"
done
python3 -B .github/integration/admission-initializer/test_harness.py
npm ci --prefix .github/integration/form-expressions --ignore-scripts
npm test --prefix .github/integration/form-expressions
TZ=America/New_York npm test --prefix .github/integration/form-expressions
```

Las pruebas de regresión usan fixtures sintéticas y copias temporales cuando
necesitan mutar metadata. No requieren servidores del hospital.

Para comprobar las propiedades del paquete y generar el ZIP:

```sh
mvn clean verify --batch-mode --file pom.xml
```

Maven no ejecuta las pruebas Python, Bash ni las integraciones de esta guía.
Tampoco formatea ni reescribe fuentes. Los proyectos Java de integración tienen
sus propios POM y no forman parte del artefacto distribuido.

Para cambios solo de documentación, revisar el diff, los enlaces y la coherencia
con los archivos referenciados. No se necesitan pruebas nuevas ni subir la
versión del paquete; véase [AGENTS.md](../AGENTS.md#validación-y-revisión).

## Contrato de empaquetado

[assembly.xml](../assembly.xml) toma los archivos directamente de `configuration/`
y los ubica bajo `configuration/backend_configuration/` dentro del ZIP.
`content.properties` queda en la raíz con nombre y versión filtrados desde el POM.

Se excluyen `.DS_Store`, `.gitkeep`, la guía `ampathforms/Readme` y los formularios
de `ampathforms/_deprecated/`. Las guías, pruebas y workflows quedan fuera del ZIP.
No renombrar dominios, formularios ni archivos de migración por criterios de estilo.

Los dos commits históricos fijados por el ensayo de Initializer conservan su
estructura antigua. El arnés reconoce explícitamente esas fuentes y la estructura
actual; ambos producen las mismas rutas de ejecución. Una reorganización debe
conservar los bytes de la metadata distribuida y las identidades/checksums de
Liquibase.

## Ensayos de integración

| Ensayo | Ejecución y alcance |
| --- | --- |
| [Autorización de rangos](../.github/integration/reference-range-access/README.md) | Core real con datos sintéticos, sin base de datos ni servidor; Java 17. |
| [MariaDB/Liquibase](../.github/integration/admission-role-reconciliation/README.md) | Migración completa contra MariaDB efímero; Java 21. |
| [Initializer](../.github/integration/admission-initializer/README.md) | Backend fijado, instalación nueva y dos escenarios de actualización; runner desechable de GitHub. |

Dos comprobaciones Java se pueden ejecutar sin base de datos ni Docker, con la
versión de Java indicada por cada proyecto:

```sh
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/reference-range-access/pom.xml test
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/admission-role-reconciliation/pom.xml \
  -Dtest=HarnessGuardTest test
```

El ensayo completo de MariaDB requiere una base sintética exclusivamente suya;
el de Initializer exige el runner efímero descrito en su README. Ejecutarlos
mediante sus workflows existentes. Las pruebas locales del arnés no demuestran
que el backend arrancó ni que la migración pasó contra MariaDB.

## Validación y publicación

El CI ejecuta en paralelo la validación del paquete, la integración
MariaDB/Liquibase, la autorización nativa de rangos y los tres escenarios de
Initializer: actualización, instalación nueva y alias operativo. Un fallo de
integración no oculta los resultados del build ni cancela los otros escenarios.
La publicación en Maven Central exige que todas estas comprobaciones pasen en
el mismo commit de `main` o `pre-release`; los PR solo validan.

Después de publicar, `Validate with SIHSALUS` construye el backend con el paquete
publicado y arranca `db` y `backend` mediante el `docker-compose.yml` normal del
distro. Sus dependencias incluyen el generador nativo de `oauth2.properties`,
incluso con autenticación local, y la política `initializer.startup.load=fail_on_error`.
No usar el fixture histórico `docker-compose-no-volumes.yml`: omite esa
configuración y puede producir fallos de módulos y permisos ajenos al paquete.
La sonda de arranque se ejecuta dentro del backend, sin publicar un puerto del
host. El proyecto exclusivo del runner se elimina con sus volúmenes al terminar;
no usa datos ni servidores del hospital. El clasificador conserva el rechazo de
errores de carga aun cuando el endpoint HTTP responda correctamente.

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
