# Revisión de rangos de laboratorio del PR #225

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

Fecha: 2026-09-10. Revisión del cambio original `e654276` desde su base común
`1025f73`; `origin/main` observado: `1371ca3`. Versión candidata:
**1.25.17**, no publicada.

**El cambio necesita correcciones y validación clínica antes de integrarse.**
Que el CSV se importe y el paquete se construya no demuestra que sus umbrales,
unidades o poblaciones sean correctos. Los valores propuestos por el autor se
conservan pendientes de esa revisión; esta auditoría no los aprueba.

La versión `1.25.17` se publicó posteriormente; véase el
[changelog](../../CHANGELOG.md#12517---2026-09-12). Los requisitos mantenidos y las
correcciones posteriores se describen en el [contrato de laboratorio](../contracts/laboratory-reporting.md).
Esa publicación no convierte esta revisión inicial en aceptación clínica.

## Comentarios del PR

| Comentario | Resultado de la revisión |
| --- | --- |
| [Escape CSV](https://github.com/sihsalus/sihsalus-content/pull/225#discussion_r3984186620) | Corregidas las comillas de seis criterios y retiradas tres filas vacías que incumplían el ancho del CSV. |
| [Prematuridad](https://github.com/sihsalus/sihsalus-content/pull/225#discussion_r3984186645) | Pendiente: la edad cronológica no identifica prematuridad. Las tres filas coinciden con bebés a término y se superponen con las bandas generales. |
| [Embarazo activo](https://github.com/sihsalus/sihsalus-content/pull/225#discussion_r3984186672) | Incorporada la inscripción activa en `Madre Gestante` evaluada en `$date`; las filas no gestantes usan su negación. La observación gestacional se obtiene una vez y se comprueban valores nulos. Persisten las limitaciones de episodio descritas abajo. |
| [Proteínas pediátricas](https://github.com/sihsalus/sihsalus-content/pull/225#discussion_r3984186691) | Corregida la banda a `>= 3 && < 18`, con etiqueta de 3 a 17 años, sin solapamiento con adultos. |

## Bloqueos que requieren completar el cambio

1. **Prematuridad y semanas de vida.** Debe definirse un dato fiable producido
   por el flujo neonatal y comprobarse que las bandas son excluyentes. Además,
   `getAgeInWeeks()` devuelve semanas completas: los criterios `<2`, `>=2 && <5`
   y `>=5 && <9` no representan primera, segunda a cuarta y quinta a octava
   semanas de vida. No se agrega un UUID sin contrato ni se presume prematuridad
   a partir de la edad.

2. **Puerperio.** La fila `1db1f541-ca0b-4f73-9396-f85588ed92a5` sigue usando
   edad gestacional entre 40 y 48 semanas. Una gestante de 40 semanas puede
   coincidir sin haber dado a luz; un parto a las 36 semanas no coincide. La
   guarda de programa activo evita clasificar por una observación antigua tras
   cerrar la inscripción, pero no convierte este criterio en uno de puerperio.
   Hace falta el evento de culminación del embarazo y su fecha, o retirar esta
   propuesta conservando un comportamiento clínico aprobado.

3. **Unidades de creatinina urinaria.** Las filas `45c9787e-...` y `90a78c49-...`
   expresan `mg/kg/24h`, pero el concepto OCL `bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88`
   expresa `mg/24h`. No se puede aplicar 21–26 o 16–22 a resultados registrados
   en otra unidad. El concepto existente no debe cambiar de unidad en silencio;
   se debe acordar la medición, el concepto y la captura correspondientes.

4. **Ácido úrico Monlab.** El inserto del fabricante indica mujeres
   2,5–6,8 mg/dL y hombres 3,6–7,7 mg/dL, coincidentes con la base. El PR propone
   mujeres 3,7–7,7 y hombres 2,5–6,2. Se debe restaurar lo anterior o adjuntar el
   respaldo del método y los intervalos aprobados por el laboratorio.

5. **Límites de hemoglobina.** La tabla 13 de la RM 429-2024 identifica ausencia
   de anemia desde 11,0 g/dL en 24–59 meses y primer/tercer trimestre, y desde
   10,5 g/dL en segundo trimestre. El PR usa 11,1 y 10,6. Debe verificarse la
   frontera inclusiva; un umbral de anemia tampoco justifica por sí solo los
   límites altos, críticos o absolutos. Los cambios de hematocrito, proteínas,
   VSG, depuración y amilasa necesitan igualmente respaldo del laboratorio.

6. **Retirada de transaminasas.** Se eliminan cuatro filas de ALT/AST con
   piridoxal fosfato cuyos conceptos permanecen activos. Initializer crea o
   actualiza los UUID presentes: quitar filas no retira las ya importadas.
   Una instalación nueva y una actualización pueden conservar rangos distintos.
   Debe aclararse si la retirada es intencional y definir su migración, o
   conservar las filas.

7. **Autorización para consultar el programa.** La guarda `isEnrolledInProgram`
   consulta `ProgramWorkflowService.getPatientPrograms`, que en OpenMRS 2.8.9
   exige `Get Patient Programs` sin elevar privilegios internamente. El rol
   `Laboratorio` carece de ese permiso y no tiene herencias. Por tanto, la
   corrección lógica de embarazo sigue bloqueada para ese rol hasta acordar
   el soporte y la autorización acotada correspondientes. Esta revisión no
   amplía permisos. Los fixtures del arnés no prueban autorización real.

La selección gestacional mantiene una limitación ya documentada en
[la auditoría de triaje](2026-06-17-triage-reference-ranges-peru.md):
`getLatestObs` no resuelve el episodio ni la observación a la fecha histórica.
La inscripción debe cerrarse al culminar el embarazo; las capturas retrospectivas
y los embarazos sucesivos necesitan un contrato adicional.

## Evidencia local

- **PASSED:** arnés temporal con OpenCSV 4.5, SpEL 5.3.30 y
  `ConceptReferenceRangeUtility` de OpenMRS 2.8.9: 69/69 criterios parsean y
  110 aserciones sintéticas comprueban las fronteras pediátricas, programa
  activo/inactivo, sexo, fechas y observaciones ausentes o nulas. Solo las
  funciones que consultan la base usan fixtures. El original tenía seis
  criterios inválidos; la negación de `Obs` también fallaba como booleano.
  Es una comprobación local del motor, no una nueva suite integrada en CI.
- **PASSED:** los 23 comandos de validación y pruebas de `.github/workflows/main.yml`
  anteriores a Maven, incluidos 80 casos de `unittest` y tres suites shell.
  El ancho de 50 CSV y las referencias de 187 rangos pasan sus validadores.
- **PASSED:** `mvn --batch-mode clean verify`, con Maven 3.9.16 y Java 21 en
  macOS ARM64. Genera `sihsalus-content-1.25.17.zip`. El CI usa Java 8, por lo
  que esta evidencia local no sustituye su ejecución.
- **FAILED, anterior a estas correcciones:** el CI del commit original agota
  el tiempo de la fase baseline de `admission-initializer / initializer-upgrade`
  con `initializer_lifecycle_not_proven_before_timeout`; el build queda omitido.
  [Ejecución](https://github.com/sihsalus/sihsalus-content/actions/runs/34534865316).
- **NOT RUN:** aprobación clínica de los intervalos y prueba del paquete en un
  backend desplegado. No se accedió a pacientes ni se publicaron artefactos.

## Fuentes

- [Inserto de ácido úrico MonlabTest](https://monlab.es/document/Bioquimica/Bioquimica%20rutina/Substratos/IFU%20Acido%20Urico%20monlabtest.pdf).
- [RM 429-2024 MINSA, tabla 13](https://bvs.minsa.gob.pe/local/fi-admin/RM-429-2024-minsa.pdf).
  Tabla consultada en el texto indexado; la descarga directa devolvió 403.
- [Cálculo de edad en OpenMRS 2.8.7](https://github.com/openmrs/openmrs-core/blob/2.8.7/api/src/main/java/org/openmrs/Person.java).
- [Carga de rangos en Initializer](https://github.com/mekomsolutions/openmrs-module-initializer/blob/main/api-2.7/src/main/java/org/openmrs/module/initializer/api/conceptreferencerange/ConceptReferenceRangeParser.java).
- Metadatos de los conceptos numéricos en los exports OCL versionados de
  `configuration/backend_configuration/ocl`.
