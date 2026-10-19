# Desarrollo, validación y publicación

Ejecutar los comandos desde la raíz del repositorio. Antes de cambiar metadata,
leer [AGENTS.md](../AGENTS.md) y el [contrato correspondiente](README.md#contratos-por-dominio).

## Requisitos

- Python 3.9 o superior para los validadores y pruebas de biblioteca estándar.
- Bash para las comprobaciones de rangos, terminología y publicación.
- Node 24 y npm para ejecutar las expresiones JavaScript de formularios. Las
  regresiones neonatales requieren además el evaluador compilado del frontend
  fijado, instalado con su propio Yarn/lockfile; véase el
  [ensayo de expresiones](../.github/integration/form-expressions/README.md).
  Los validadores Python no ejecutan JavaScript.
- Maven Wrapper fija Maven 3.10.0 para el paquete y su publicación; descarga la
  distribución oficial y comprueba su SHA-256.
- Java: CI usa Java 21 LTS para el paquete, publicación y MariaDB/Liquibase,
  alineado con el backend. El ensayo independiente de autorización de rangos
  mantiene Java 17.
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
# Preparar el evaluador según .github/integration/form-expressions/README.md.
export SIHSALUS_EXPRESSION_EVALUATOR=/ruta/al/frontend/packages/libs/esm-expression-evaluator/dist/index.js
npm test --prefix .github/integration/form-expressions
TZ=America/New_York npm test --prefix .github/integration/form-expressions
```

Las pruebas de regresión usan fixtures sintéticas y copias temporales cuando
necesitan mutar metadata. No requieren servidores del hospital.

Para comprobar las propiedades del paquete y generar el ZIP:

```sh
./mvnw clean verify --batch-mode --file pom.xml
```

Maven no ejecuta las pruebas Python, Bash ni las integraciones de esta guía.
Tampoco formatea ni reescribe fuentes. Los proyectos Java de integración tienen
sus propios POM y no forman parte del artefacto distribuido.

## Contrato de empaquetado

[assembly.xml](../assembly.xml) toma los archivos directamente de `configuration/`
y los ubica bajo `configuration/backend_configuration/` dentro del ZIP, el prefijo
que consume el distro. `content.properties` queda en la raíz con nombre y versión
filtrados desde el POM. Este detalle del artefacto no requiere otra carpeta en el
árbol de fuentes.

Se excluyen `.DS_Store`, `.gitkeep`, la guía `ampathforms/Readme` y los formularios
de `ampathforms/_deprecated/`. Las guías, pruebas y workflows quedan fuera del ZIP.
No renombrar dominios, formularios ni archivos de migración por criterios de estilo.
Una reorganización debe conservar los bytes de la metadata distribuida y las
identidades/checksums de Liquibase.

## Ensayos de integración

| Ensayo | Ejecución y alcance |
| --- | --- |
| [Autorización de rangos](../.github/integration/reference-range-access/README.md) | Core real con datos sintéticos, sin base de datos ni servidor; Java 17. |
| [MariaDB/Liquibase](../.github/integration/admission-role-reconciliation/README.md) | Migración completa contra MariaDB efímero; Java 21. |
| [Expresiones de formularios](../.github/integration/form-expressions/README.md) | Expresiones distribuidas y regresión neonatal con el evaluador real del frontend fijado. |
| [Initializer](../.github/integration/admission-initializer/README.md) | Tres escenarios históricos y dos de transición OCL con runtime actual fijado; runner desechable de GitHub. |

La autorización de rangos se puede ejecutar sin base de datos ni Docker:

```sh
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/reference-range-access/pom.xml test
```

El ensayo completo de MariaDB requiere una base sintética exclusivamente suya;
el de Initializer exige el runner efímero descrito en su README. Ejecutarlos
mediante sus workflows existentes.

## Validación y publicación

El CI ejecuta en paralelo la validación del paquete, la integración
MariaDB/Liquibase, la autorización nativa de rangos y los cinco escenarios de
Initializer: actualización histórica, instalación nueva, alias operativo,
instalación nueva OCL y actualización OCL desde `1.25.34`. Un fallo de
integración no oculta los resultados del build ni cancela los otros escenarios.
La publicación en Maven Central exige que todas estas comprobaciones pasen en
el mismo commit de `main` o `pre-release`; los PR solo validan.

Después de que `publish` confirme el POM y ZIP en Maven Central, el mismo
workflow llama a `Validate with SIHSALUS` con el mismo commit del paquete:
construye el backend con el paquete publicado y arranca `db` y `backend`
mediante el `docker-compose.yml` normal del distro. Sus dependencias incluyen el
generador nativo de `oauth2.properties`, incluso con autenticación local, y la
política `initializer.startup.load=fail_on_error`. No usar el fixture histórico
`docker-compose-no-volumes.yml`: omite esa configuración y puede producir fallos
de módulos y permisos ajenos al paquete. La sonda de arranque se ejecuta dentro
del backend, sin publicar un puerto del host, y el proyecto exclusivo del runner
se elimina con sus volúmenes al terminar. El clasificador conserva el rechazo de
errores de carga aun cuando el endpoint HTTP responda correctamente. El workflow
admite ejecución manual con la entrada `sihsalus_ref` (`main` por defecto); se
omite si `publish` falla o se omite, y un fallo no revierte el artefacto publicado.

### Publicación en Maven Central

El perfil `release` exige Maven 3.10.x mediante Enforcer y firma con Maven GPG;
usar `./mvnw` con Java 21. La publicación usa `maven-deploy-plugin` y JReleaser 1.26.0:

1. `maven-deploy-plugin` deja POM, ZIP y firmas en el repositorio `file:` de
   `target/staging-deploy`, separado del repositorio local de dependencias.
2. `jreleaser:deploy`, enlazado a la fase `deploy`, valida el POM con PomChecker
   (`failOnError=true`, `verifyPom=true`; `strict=false` y `failOnWarning=false`
   admiten los repositorios OpenMRS, que el checker señala como avisos), calcula
   los checksums, crea el bundle y lo publica mediante el Portal.
3. CI espera después que el POM y ZIP sean descargables con `wait_for_maven_central.sh`.

Credenciales: `JRELEASER_MAVENCENTRAL_CENTRAL_USERNAME` y
`JRELEASER_MAVENCENTRAL_CENTRAL_PASSWORD` (en CI, los secretos `CENTRAL_USERNAME`
y `CENTRAL_PASSWORD`); `authorization=BASIC` construye el token Bearer del Portal
a partir de ese par. La firma usa `GPG_PRIVATE_KEY` y `GPG_PASSPHRASE`. Solo se
ejecuta el goal `deploy`; no se crean releases ni tags de GitHub.

```sh
./mvnw -P release clean deploy
bash .github/scripts/wait_for_maven_central.sh <version>
```

`bash .github/scripts/test_maven_central_publication.sh --bundle` ensaya el perfil
real con el `dryRun` nativo de JReleaser y una clave GPG efímera, sin subidas.

Referencias: [publicación con Maven y JReleaser](https://jreleaser.org/guide/latest/examples/maven/maven-central.html),
[configuración del Portal](https://jreleaser.org/guide/latest/reference/deploy/maven/maven-central.html)
y [cambios de Maven 3.10.0](https://maven.apache.org/docs/3.10.0/release-notes.html).
