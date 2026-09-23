# Revisión de formularios y reglas clínicas — 2026-09-23

El paquete pasa sus validadores técnicos, pero conserva defectos de rangos,
semántica y captura. **No hay evidencia suficiente para afirmar conformidad
normativa completa ni ausencia de regresiones clínicas.** Esta revisión distingue
defectos reproducibles, brechas de cobertura y alertas que requieren interpretación.

## Correcciones preparadas después de esta revisión

La evidencia diagnóstica que sigue corresponde al commit auditado. El candidato
`1.25.25` corrige el aviso desde 500 m (`CRED-001 1.2.1`) y el cálculo/validación de
fechas (`OBST-002 1.0.2`). Usa la prematuridad registrada y los estados maternos
existentes para seleccionar rangos; desactiva las dos reglas de creatinina con
magnitud incompatible conservando sus UUIDs. Los detalles y límites están en el
[contrato de laboratorio](../contracts/laboratory-reporting.md).

La corrección del permiso de decimales está preparada en el componente responsable,
`sihsalus-frontend`, con pruebas de restricciones del formulario y del concepto.
No se modificó el helper histórico `calcTimeDifference`: el formulario nuevo
reutiliza Day.js, ya expuesto por el motor, con la fecha explícita de atención.
Initializer crea las nuevas versiones y conserva los esquemas anteriores; la
corrección no reescribe encuentros ni elimina sus referencias históricas.

La guarda nueva de Initializer comprueba instalación nueva, actualización y
reinicio: contenido de los dos esquemas, once criterios y conservación de UUID,
ID, versión y hash de esquemas históricos. Los tests locales del arnés no
acreditan la ejecución de esos escenarios con el backend real.

Siguen pendientes la semántica histórica de paridad, los intervalos y método
institucionales de laboratorio, el catálogo de inmunizaciones y las decisiones
clínicas de cobertura CRED. Se conserva OCL publicado y el baseline de alertas.
La aceptación de captura/guardado/edición en DEV/QLTY y la aprobación clínica
siguen pendientes; ninguno de estos cambios constituye una certificación normativa.

## Alcance y evidencia

- Content: `c34601e804f5217e1a15f33a33bf05d1f19a0010`, cuyo árbol coincide con
  `main` en `a54fde1c29aeec14b34d4c423ed890f9dd58d5dc`; paquete `1.25.24`.
- Inventario de los 112 JSON: 2.176 preguntas/grupos/controles, 1.682 campos
  `obs` y 33 expresiones `calculate`. El recorrido incluye grupos anidados.
- Contraste de UUID, datatypes y mappings con los ZIP OCL distribuidos. Lectura
  detallada de anemia, instrumentos CRED, inmunizaciones, obstetricia y rangos
  de laboratorio; no una aprobación clínica individual de los 112 formularios.
- Frontend local, sin modificaciones, en
  `9b434cf8350e5a20db21fb61db66ba8d7ba2f112`: revisión de las funciones que ejecutan
  las expresiones y adaptan las observaciones. No se verificó que ese commit esté
  desplegado en el hospital.
- Consulta de fuentes oficiales MINSA el 23 de septiembre de 2026. Se leyeron
  tablas y anexos, además de las páginas de publicación. La búsqueda no constituye
  una certificación exhaustiva de vigencia o de aplicabilidad institucional.

Se ejecutaron los 14 validadores Python de
[CI](../../.github/workflows/main.yml) y
[`validate_reference_ranges.sh`](../../.github/scripts/validate_reference_ranges.sh):
**15 aprobados**. Sus resultados incluyen 3.672 referencias de conceptos en
formularios, 32.430 conceptos OCL, 20.286 extremos de mappings y 187 filas de rangos.
El validador de integridad devuelve cero infracciones bloqueantes y 128 entradas
conocidas en su baseline; eso no mide conformidad clínica.

También se ejecutaron expresiones extraídas de los JSON con datos sintéticos en
Node, usando `isEmpty` del frontend inspeccionado. Para las funciones TypeScript
se transpilaron los cuerpos existentes; se fijó el reloj al
`2026-09-23T12:00:00Z`. No son pruebas de navegador, persistencia ni del backend
desplegado. No se modificaron formularios, OCL, Liquibase, baseline ni versión.

## Defectos que requieren corrección

P1 identifica problemas que pueden alterar interpretación o impedir captura;
P2 identifica inconsistencias acotadas que también requieren resolución.
La prioridad expresa el riesgo del caso descrito, no acredita un incidente real.

### P1 — Creatinina urinaria: magnitudes incompatibles

Las filas 52–53 de
[`conceptreferencerange_laboratory.csv`](../../configuration/conceptreferencerange/conceptreferencerange_laboratory.csv)
declaran `mg/kg/24h` y límites de 21–26 para hombres y 16–22 para mujeres bajo
el UUID `bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88`. El concepto `laboratorio:5400`
del ZIP `03_SIHSALUS_laboratorio_concepts_2026-07-10-02.zip` declara `mg/24h`,
con límites normales de 1.000–1.500. No son magnitudes intercambiables.

Un resultado sintético de 1.200 mg/24h supera el máximo absoluto CSV de 40 si se
compara directamente con esa fila. Normalizarlo exigiría un peso y una conversión
explícita; cambiar el nombre de la fila no convierte el resultado.
La clave histórica `Units` del export tampoco demuestra que el importador
incorpore la unidad: el contrato ya documenta la diferencia con `units`.

**Responsabilidad:** terminología y rangos de laboratorio, según el
[contrato existente](../contracts/laboratory-reporting.md#urobilinógeno-y-creatinina-urinaria).
Resolver la medición y sus intervalos con el procedimiento institucional,
conservando la identidad y magnitud de resultados históricos. No editar el ZIP
publicado ni inventar una conversión.

### P1 — Los criterios de hemoglobina no identifican la población declarada

En el mismo CSV, las filas 7–9 de prematuridad solo comprueban edad cronológica.
Un recién nacido a término de siete días satisface el criterio de la primera
fila y también el de menores de dos meses. Falta la condición que distingue
prematuridad; la revisión estática no determina cuál fila mostrará cada consumidor.

La fila 22, `1db1f541-ca0b-4f73-9396-f85588ed92a5`, denomina puerperio a una
selección basada en sexo, inscripción en el programa materno y última edad
gestacional entre 40 y menos de 48 semanas. Una gestante de 40 semanas sin parto
cumple ese predicado; no se consulta parto ni estado puerperal. Una puérpera cuyo
último dato gestacional sea 39 semanas no lo cumple.

**Responsabilidad:** selección de rangos y datos clínicos del backend. Reutilizar
el registro canónico de prematuridad y estado obstétrico antes de sustituir
criterios. Son pendientes ya descritos en el
[contrato de laboratorio](../contracts/laboratory-reporting.md#pendientes-de-la-actualización-completa),
confirmados en el contenido actual. Los ensayos de permisos de rangos no validan
la definición de estas poblaciones.

### P1 — OBST-002 calcula contra hoy y rechaza fechas de parto ya pasadas

[`OBST-002`](../../configuration/ampathforms/OBST-002-EMBARAZO%20ACTUAL.json)
usa `calcTimeDifference(fum, 'w')` en `edadGestacionalFUM` (línea 196).
El [helper del frontend inspeccionado](https://github.com/sihsalus/sihsalus-frontend/blob/9b434cf8350e5a20db21fb61db66ba8d7ba2f112/packages/libs/esm-form-engine-lib/src/utils/common-expression-helpers.ts#L588)
usa el reloj actual, redondea semanas y devuelve cero sin FUM.

Caso reproducido: FUM `2026-01-01`, atención `2026-03-12`, captura el
`2026-09-23`. La expresión devuelve **38**, aunque entre FUM y atención hay
**10 semanas**. Sin FUM devuelve **0**, que representa un valor numérico en vez
de ausencia. Esto demuestra el resultado de la expresión; no se probó si una
edición real recalcula y sobrescribe una observación previamente guardada.

Además, `fechaProbableDeParto` (línea 220) falla cuando
`isDateBefore(myValue, today())` es verdadero. FUM `2025-12-01` calcula FPP
`2026-09-07`, que la regla rechaza el 23 de septiembre. Una FPP pasada puede
necesitar registrarse en una atención retrospectiva o una gestación prolongada.

**Responsabilidad:** contrato del formulario y funciones compartidas del motor.
El cálculo debe usar la fecha clínica correspondiente, distinguir vacío de cero
y definir la precisión requerida; la validación debe admitir el registro clínico
legítimo. Verificar alta, edición e historial con fechas sintéticas antes de
publicar el cambio. No convertir estas reglas en SQL del content.

### P1 — Dependencia frontend: se invierte el permiso de decimales

En el [validador numérico inspeccionado](https://github.com/sihsalus/sihsalus-frontend/blob/9b434cf8350e5a20db21fb61db66ba8d7ba2f112/packages/libs/esm-form-engine-lib/src/validators/form-validator.ts#L34),
`disallowDecimals` combina con OR la restricción del formulario y
`Boolean(field.meta.concept.allowDecimal)`. Por tanto, un concepto que permite
decimales activa su prohibición.

Se ejecutó `FieldValidator.validate` con la pregunta real `hemoglobina` de
[`CRED-001`](../../configuration/ampathforms/CRED-001-TAMIZAJE%20DE%20ANEMIA.json),
`meta.concept.allowDecimal: true` y valor **11.5**. Devuelve
`field.outOfBound`, «Decimal values are not allowed for this field».
Solo se sustituyó la traducción del mensaje; se ejecutó la lógica original.

**Responsabilidad:** `esm-form-engine-lib` del frontend, fuera de este repositorio.
La combinación de las restricciones del formulario y del concepto necesita una
corrección reutilizable y pruebas con permiso/prohibición en ambas capas.
Confirmar el commit desplegado y la metadata REST recibida antes de atribuir este
fallo al entorno del hospital. Cambiar todos los formularios no resuelve la causa.

### P2 — El aviso de ajuste de hemoglobina omite exactamente 500 m

En [`CRED-001`](../../configuration/ampathforms/CRED-001-TAMIZAJE%20DE%20ANEMIA.json)
(línea 81), `altitud > 500` produce:

| Altitud sintética | Aviso actual | Ajuste de tabla 1, g/dL |
| --- | --- | --- |
| 499 m | No | 0 |
| 500 m | No | 0,4 |
| 501 m | Sí | 0,4 |

La [RM 429-2024, anexo, tabla 1, PDF p. 4](https://cdn.www.gob.pe/uploads/document/file/6498138/5670414-rm-429-2024.pdf#page=4)
sitúa el primer ajuste no nulo en 500–999 m. El
[validador OCL](../../.github/scripts/validate_ocl_exports.py) (líneas 1432–1434)
exige precisamente `altitud > 500`, por lo que CI protege el límite equivocado
para esa tabla. No se ha demostrado una clasificación incorrecta guardada:
el profesional selecciona el resultado manualmente y tiene instrucciones de ajuste.

**Responsabilidad:** aviso del formulario y su guarda. Alinear ambos con la tabla
específica de ajuste, cubrir 499/500/501 y actualizar la versión del formulario
cuando se publique la corrección. El máximo de captura de 5.000 m también limita
la cobertura frente al último tramo de la tabla; su relevancia local debe definirse.

### P2 — Paridad tiene definiciones incompatibles dentro de OCL

El concepto `sihsalus:915`, UUID `8795c05b-f286-4d70-a1e6-69172e676f05`, tiene
nombre y descripción preferidos en español para partos a término, mientras sus
nombres ingleses y un sinónimo español expresan paridad general. En
[`OBST-010`](../../configuration/ampathforms/OBST-010-SERVICIO%20DE%20OBSTETRICIA.json),
`numeroPartos` y `paridad` lo usan como número de partos (líneas 579 y 717).

Una paciente con un parto pretérmino y ninguno a término permite obtener 1 o 0
según qué definición se siga. La inconsistencia está en la identidad clínica,
no queda resuelta renombrando el campo ni eliminando una alerta del baseline.

**Responsabilidad:** fuente OCL y contrato obstétrico. Determinar la semántica
histórica, revisar consumidores y publicar la corrección terminológica sin
reinterpretar observaciones antiguas de forma silenciosa.

## Cobertura normativa que sigue pendiente

### Inmunizaciones: comprobar el selector, además del catálogo

[`INMU-001`](../../configuration/ampathforms/INMU-001-REGISTRO%20DE%20VACUNACI%C3%93N.json)
usa `select-concept-answers` sobre `sihsalus:4121`, UUID
`f9840000-0000-4000-8000-000000000984`. Los mappings `Q-AND-A` distribuidos
proporcionan **22 respuestas**; no incluyen hexavalente, meningococo ni Nirsevimab.

**Nirsevimab sí existe** como `sihsalus:4205`, UUID
`f0000181-0000-4000-8000-000000000181`, clase `Misc`, datatype `N/A`, sin mappings.
También hay conceptos de procedimientos relacionados con meningococo. No es
correcto afirmar que todos esos términos están ausentes del bundle ni crear
identidades nuevas antes de evaluar los existentes. Su existencia no los hace
seleccionables en la pregunta actual, ni acredita un catálogo de productos completo.

La [NTS 246, parte 1, anexos 1–2, pp. 79–80](https://cdn.www.gob.pe/uploads/document/file/10154198/8265031-nts-n-246-minsa-digiesp-2026-parte-1.pdf#page=79)
incluye las nuevas intervenciones y contempla transiciones: pentavalente/IPV
mientras estén disponibles y sustitución del primer refuerzo DPT por hexavalente
en 2027. La brecha del selector está confirmada; su efecto operativo requiere
conocer productos y cronograma aplicables en el establecimiento.

El formulario registra observaciones. El texto descriptivo de un concepto no
prueba que guardar ese formulario genere un recurso FHIR `Immunization`.
Persistencia, lote, estado, dosis y edición deben ensayarse en el flujo nativo
responsable antes de dar por completo el registro de inmunizaciones.

### CRED: transcripción, rango de edad y decisiones clínicas

Los formularios EDI, M-CHAT y Huanca se describen como resúmenes/transcripciones;
no digitalizan todos los ítems. Esto **no prueba por sí mismo incumplimiento** si
el instrumento oficial se aplica y su evidencia queda trazable. Tampoco acredita
que dicha trazabilidad exista en el despliegue.

[`CRED-010`](../../configuration/ampathforms/CRED-010-TAMIZAJE%20TEA.json) restringe
edad a 18–30 meses. La [NTS 238, anexo 11](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf#page=122)
describe esos supuestos y, en p. 126, indica aplicación antes de los 36 meses
ante sospecha. El formulario rechaza 31–35 meses. Hay que resolver esa cobertura
con el responsable clínico y distinguir tamizaje universal, sospecha y derivación;
ampliar un máximo sin revisar el instrumento no basta.

En `CRED-027`, la acción automática condiciona EDI/interconsulta a ausencia de
habilidades **y** factor de riesgo. El §6.8.3 y el anexo 10 de la misma norma
presentan sus criterios con distinto detalle. Se mantiene como punto de
interpretación clínica pendiente, no como un incumplimiento demostrado.

## Qué está comprobado y qué significan las 128 alertas

Las evaluaciones sintéticas de las expresiones dieron:

| Expresión | Casos ejecutados | Resultado |
| --- | --- | --- |
| Glasgow | 120 combinaciones puntuables y 90 con componente no evaluable | Suma correcta; sin total numérico cuando un componente no es evaluable. |
| M-CHAT | Puntajes enteros 0–20 y vacío | Niveles 0–2 / 3–7 / 8–20; vacío sin puntuación. |
| Huanca | Cinco áreas completas con 0, 1 o 2 hitos no logrados; un área vacía | Total y nivel correspondientes; incompleto sin total numérico. |

Estas pruebas comprueban los casos indicados, no sustituyen la aplicación del
instrumento, la aceptación clínica o el guardado y reapertura del encuentro.

El baseline contiene 66 `duplicate-label`, 32 `answer-set`, 22 `collision` y
8 `code-as-text`. Son **128 alertas heurísticas, no 128 defectos clínicos
confirmados**. Por ejemplo, el código de afiliación SIS puede ser legítimamente
texto; dos subconjuntos de respuestas pueden corresponder a distintos contextos;
y reutilizar un concepto en grupos diferentes no necesariamente duplica datos.

El [adaptador del frontend](https://github.com/sihsalus/sihsalus-frontend/blob/9b434cf8350e5a20db21fb61db66ba8d7ba2f112/packages/libs/esm-form-engine-lib/src/adapters/obs-adapter.ts#L307)
guarda `formFieldPath` y busca por campo y concepto, con fallback por concepto.
Por eso tampoco se sostiene afirmar que todo concepto reutilizado pierde la
distinción al reabrir un formulario. Persisten riesgos para consumidores que solo
usan el concepto y para observaciones antiguas sin esa ruta; requieren pruebas
de ida y vuelta y una clasificación de cada alerta antes de retirar deuda.

## Cierre y condiciones para aceptación

Esta revisión deja documentados los casos reproducibles y sus componentes
responsables. Para cerrar los hallazgos se necesitan cambios acotados con
regresiones de comportamiento, conservación de identidades/historia y pruebas
de captura, guardado, lectura y edición con datos sintéticos en el stack objetivo.
Los intervalos analíticos y decisiones de instrumentos requieren además revisión
del responsable clínico y de los procedimientos institucionales aplicables.

No se evaluaron historias reales, firma, integridad legal del expediente,
privacidad, operación hospitalaria ni el cumplimiento completo de todas las normas
por servicio. El estado de CI y esta auditoría no acreditan esos ámbitos.
Los 12 changesets publicados siguen sujetos a la
[revisión de compatibilidad de Liquibase](2026-09-22-liquibase-initializer.md);
retirarlos no corrige ninguno de estos problemas.
