# Guía de contenido por dominio

Esta guía conserva los contratos de formularios y las notas de alcance que no
tienen documento propio. El [índice de contratos](README.md#contratos-por-dominio)
enlaza las definiciones de catálogos, institución, Admisión e historia social.

## Contrato canónico de Visit Notes

Visit Notes usa el `Form` `c75f120a-04ec-11e3-8780-2b40bef9a44b` y el tipo de
encuentro `d7151f82-c1f3-4152-a605-2f9ea7414a79`. El pin comprobado de Initializer
`2.13.0-sihsalus.1` no ofrece un dominio CSV genérico para `Form`;
la [revisión de Liquibase](audits/2026-09-22-liquibase-initializer.md) documenta
la limitación y las alternativas. Liquibase crea de forma idempotente la metadata
que falta y solo completa una asociación de tipo de encuentro nula.
Un `Form` existente nunca se renombra, publica, retira ni reasocia silenciosamente.

El contrato también fija los datatypes de los conceptos consumidos por el frontend
y separa `app:hoja.clinica.resumenConsulta` de
`app:hoja.clinica.resumenConsulta.editar`. Los detalles verificables están en
[visit-note-content-contract.json](contracts/visit-note-content-contract.json).

## Contrato de diagnóstico de CE-001

`CE-001-CONSULTA EXTERNA` no captura diagnósticos. El diagnóstico CIE-10 se registra exclusivamente mediante Visit Notes como diagnóstico nativo del encuentro; no deben reintroducirse observaciones de texto, certeza u ocurrencia que simulen esa estructura.

La versión `1.0.3` elimina la página SOAP completa del formulario general y conserva los demás campos. La versión `1.0.2` corrigió anteriormente el diagnóstico. `AmpathFormsLoader` deriva la identidad persistida del nombre y la versión. En upgrades, una migración idempotente retira y despublica exclusivamente el `Form` `1.0.1` con UUID persistido `da631d8c-c695-3c4a-9d77-19bbbf0174e3`; no elimina ni modifica sus encuentros históricos. La migración publicada conserva su contrato original con `1.0.2` (`df1a34b4-0e8f-3564-84d9-55ce9e4284bd`) y no se modifica. Después, el loader nativo retira esa versión y crea `1.0.3` (`a43f4ba0-1d01-3533-aa96-927ad602851a`) sin sobrescribir los esquemas anteriores. En instalación limpia crea únicamente `1.0.3`. El `uuid` incluido en el JSON no es la identidad persistida y no debe usarse como contrato de integración.

No se vuelve a publicar el JSON con una versión histórica: reutilizaría y sobrescribiría el recurso que contiene la captura de diagnóstico obsoleta. El formulario retirado no se reactiva; sus encuentros se conservan para lectura histórica.

## Contrato de examen físico de Consulta Externa

`CE-EXF-001-EXAMEN FISICO` versión `1.0.1` es el formulario propio de examen físico ambulatorio. Conserva los diez conceptos e identificadores de examen general y regional ya existentes; no incluye Subjetivo, Objetivo, Apreciación ni Plan. Estado general sigue siendo obligatorio y los sistemas específicos se registran según pertinencia clínica, sin completar hallazgos normales automáticamente. Anamnesis, diagnóstico y tratamiento mantienen sus formularios y servicios existentes.

El frontend debe resolver `formsList.physicalExamForm` por ese nombre, con la cabecera **Examen físico**. No se usa el antiguo formulario como alternativa cuando falta el nuevo.

`CE-SOAP-001-NOTA SOAP` `1.2.0` se despublica y retira declarativamente. Conserva nombre, versión, UUID, preguntas, conceptos y campos obligatorios; únicamente cambian `published` y `retired` en su esquema. No se elimina ni reasocia ningún encuentro u observación y no se usa una migración SQL. Los formularios propios de Hospitalización no cambian.

## Anamnesis breve de Consulta Externa

`CE-ANAM-001-ANAMNESIS` `1.1.1` reduce de once a tres los campos clínicos de texto
libre: motivo de consulta, tiempo de enfermedad y detalle breve opcional.
Inicio, evolución y las seis funciones biológicas usan selectores; estas últimas
quedan en una sección inicialmente contraída. Ninguna opción se selecciona ni
se copia desde otra consulta automáticamente. Vacío no significa normal.

Los selectores reutilizan el soporte nativo `answers[].value` de O3 y conservan
las observaciones **Text** existentes. Las opciones son valores de texto, no
UUID de respuesta ni nuevos diagnósticos codificados; no cambia ningún datatype
ni se convierte contenido histórico. El motor debe incluir la corrección de
lectura/visualización de valores literales del frontend coordinado.

Las versiones `1.1.1` de anamnesis y `1.0.1` de examen físico limitan cada
área de texto a 4000 caracteres y muestran el contador en el motor de formularios.
El profesional responsable se muestra como dato de solo lectura: el motor toma
el proveedor clínico de la sesión al crear y conserva el proveedor del encuentro
al editar. La autorización del rol sigue siendo responsabilidad del backend.

El frontend no abre la captura anterior si falta la versión esperada. Si una
visita abierta ya contiene un formulario anterior, conserva su lectura histórica
y bloquea una segunda captura; no reasigna ni duplica ese encuentro.

## Rangos de laboratorio

El [contrato de captura](contracts/laboratory-reporting.md) concentra datatypes,
unidades, puntos de corte de hemoglobina, selección de población y pendientes de
método. El [registro OCL](audits/2026-09-12-ocl-remote-corrections.md) documenta
las correcciones aplicadas en HEAD remoto.

## Contrato preparatorio para PDF de resultados de laboratorio

La [línea base de acceso clínico](clinical-rbac.md) define los marcadores de
adjuntos y la versión backend requerida. El PDF es suplementario: su carga no
completa la orden, cambia su estado ni sustituye resultados estructurados o su
validación clínica.

## Presentaciones adicionales de medicamentos

Initializer carga los principios activos de
[clinical_drug_concepts.csv](../configuration/concepts/clinical_drug_concepts.csv)
antes de las presentaciones de [clinical-drugs.csv](../configuration/drugs/clinical-drugs.csv).
Los UUID son estables y las referencias son explícitas; estos archivos pertenecen
al catálogo local SIHSALUS y una futura incorporación al diccionario OCL debe
conservar los UUID para evitar duplicados.

El ácido ursodesoxicólico faltaba en el export OCL de medicamentos del paquete y
en `minsa-drugs.csv`. Se incorpora como concepto `Drug` con tipo `N/A` y una
presentación ordenable de 250 mg en tableta; la forma farmacéutica reutiliza el
concepto existente `Tableta` (`bd1e9059-62b4-4967-a804-a63eda4f8657`). La
identidad y presentación proceden del [Petitorio Farmacológico de
EsSalud](https://ietsi.essalud.gob.pe/petitorio-farmacologico-essalud/), entrada
`010450038`, consultado el 12 de septiembre de 2026. Ese código pertenece a
EsSalud: no se le asigna un código MINSA ni se modifica el export OCL. El
registro describe una presentación, no existencias, indicación, pauta ni
autorización de dispensación. El buscador del frontend espera un medicamento
activo con concepto `Drug`, concentración y forma farmacéutica; no acepta texto libre.

### Procedencia y mantenimiento de medicamentos

`minsa-drugs.csv` conserva 494 identidades procedentes del archivo local
`peruHCE-drugs.csv` de noviembre de 2025: 493 activas y una retirada. Su cambio
de nombre en marzo de 2026 no incorporó otro catálogo. `clinical-drugs.csv`
añade una presentación activa documentada arriba. No se ha identificado el
archivo oficial original que justificaría todas las filas ni el petitorio
institucional aprobado de Santa Clotilde; el nombre del CSV no acredita vigencia
del PNUME ni autorización de uso hospitalario.

Los códigos `00143` y `00145`, por ejemplo, corresponden a SISMED en
[documentos oficiales de DIGEMID](https://www.digemid.minsa.gob.pe/Archivos/MedicamentosFarmacia/SanMiguel-Diciembre.pdf).
La identidad debe contrastarse por presentación:
aciclovir de 200 y 400 mg comparte concepto en OCL, pero tiene dos `Drug` y códigos
SISMED distintos. `extras.COD_MED` del concepto no identifica ambas presentaciones.

| Fuente | Actualización y límite |
| --- | --- |
| [Catalogación SISMED](https://www.digemid.minsa.gob.pe/catalogacionSismed/assets/documentos/Manual_Usuario_MRV.pdf) | El manual documenta Excel, paquetes ZIP y comunicados de códigos inactivos/equivalentes. Conservar el archivo recibido, fecha, versión y SHA-256; el acceso público devolvió 403 en esta revisión. No quedó verificado un feed automatizable. |
| [PNUME y sus anexos](https://repositorio-digemid.minsa.gob.pe/items/ea629572-1ea9-47e6-95d7-dd2e529db307) | Contrastar la base y las listas complementarias publicadas con el petitorio institucional aprobado. SISMED, pertenencia al PNUME y autorización institucional son datos diferentes. |
| [Registro sanitario y fichas DIGEMID](https://www.digemid.minsa.gob.pe/webDigemid/registro-sanitario/productos-farmaceuticos/) | Son consultas documentales oficiales. No se ha verificado un contrato de API o descarga integral que permita sincronizarlas con este paquete. |
| OCL `SIHSALUS/medicamentos` | Usar versiones publicadas y exports oficiales. La consulta autenticada de solo lectura del 19 de octubre de 2026 confirmó `2026-06-30` como última release publicada; HEAD no es una release aprobada. |
| [RxNorm/NLM](https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxcuiHistoryStatus.html) | Comprobar estado de los identificadores existentes y registrar la versión NLM consultada. Un identificador activo no acredita equivalencia clínica exacta ni cobertura de todas las presentaciones. |
| ViDAL Integrated | No hay conector ni acceso verificado en el código revisado. Su mantenimiento requiere confirmar acceso, cobertura para Perú y condiciones del proveedor. |

#### Revisión reproducible de RxNorm

```sh
python3 .github/scripts/check_rxnorm_mappings.py > /tmp/rxnorm-review.json
```

El comando descubre los mappings activos de medicamentos en los ZIP publicados
del paquete y consulta por GET los identificadores RxNorm correspondientes.
Comprueba la versión NLM antes y después para detectar un cambio durante la
lectura. Devuelve `0` (`CURRENT`) si todos siguen activos, `1` (`REVIEW`) si algún
identificador necesita revisión y `2` (`ERROR`) si no pudo completar la
comprobación. Un fallo de red, una respuesta incompleta o un inventario vacío
impiden el resultado `CURRENT`. No cambia mappings, importa datos ni publica
versiones.

Este comando nuevo cubre la consulta de vigencia upstream que no realizan el
validador estático, el separador de exports o el migrador inicial de OCL. Sus
pruebas usan respuestas sintéticas; el build del paquete sigue siendo reproducible
sin NLM. El [workflow de revisión](../.github/workflows/review-rxnorm-mappings.yml)
permite ejecución manual y semanal, los lunes a las 12:00 UTC (07:00 en Lima),
con un informe conservado 30 días. Sólo queda activo al integrar el workflow en
la rama predeterminada. Este control no comprueba la vigencia de SISMED, PNUME,
fichas o petitorio institucional.

La [evidencia técnica del 19 de octubre de 2026](audits/2026-10-19-medication-maintenance.json)
registra la versión NLM `05-Oct-2026`, API `3.1.356`, y los cuatro identificadores
activos comprobados. Son ingredientes o combinaciones (`IN`/`MIN`), no
presentaciones clínicas (`SCD`). Conserva pendientes las decisiones de Farmacia.
Este control tampoco evalúa interacciones: NLM
[retiró esa API el 2 de enero de 2024](https://lhncbc.nlm.nih.gov/RxNav/information/FAQs.html).

#### Incorporación de cambios

1. Obtener la descarga oficial y el petitorio aprobado, con sus versiones y hash.
2. Comparar las presentaciones y clasificar altas, cambios, ausencias o fusiones;
   cada decisión conserva los UUID históricos y requiere revisión del dominio.
   Una ausencia o una fusión no autoriza retirar ni sustituir datos automáticamente.
3. Revisar concentración, composición, forma y vía antes de aprobar equivalencias.
   [Initializer admite](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/readme/drugs.md)
   `DrugReferenceMap` e ingredientes mediante los encabezados nativos del CSV
   existente. [Al recargar reconstruye los mappings](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/api/src/main/java/org/openmrs/module/initializer/api/drugs/MappingsDrugLineProcessor.java#L34): conservar el
   conjunto completo aprobado por `Drug` en su fuente declarativa, sin overlays
   ni modificaciones sólo por REST que una recarga pueda borrar.
4. Incorporar la versión OCL publicada con `split_ocl_export.py` y los CSV
   correspondientes, ejecutar los validadores y ensayos existentes y presentar
   el diff en un PR. El migrador inicial de terminología no es un actualizador
   recurrente de fuentes ya pobladas.

Farmacia debe revisar también el alcance del catálogo seleccionable: permanece
activa una entrada denominada «VACUNA ANTIRRABICA DE USO VETERINARIO». Esta revisión
no la retira ni reasigna sus referencias; su presencia necesita una decisión
explícita del responsable del catálogo para atención humana (código SISMED
`30602`, UUID `931d8199-6316-4624-b940-e77022c30602`).

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

## Relación madre-hijo y sala de hospitalización

`configuration/relationshiptypes/relationshiptypes.csv` define la relación
Madre→Hijo (`e6be4def-dbc8-462a-8714-53da66903cb8`). El mapeo
`emr.motherChildRelationshipType` de
`configuration/metadatatermmappings/metadatatermmappings-core-sihsalus.csv`
permite que EmrApi resuelva ese tipo para
`GET /emrapi/maternal/mothersAndChildren`; debe apuntar al mismo UUID. Los
registros guardados llevan a la madre en `personA` y al hijo en `personB`. La
configuración frontend `motherChildRelationshipTypeUuid` también debe coincidir
para que el flujo de parto y la sala materna compartan el mismo vínculo.

## Antecedentes obstétricos

`OBST-001-ANTECEDENTES` `1.0.1` permite declarar explícitamente **Ninguna** en
antecedentes familiares y personales. Reutiliza el concepto activo `sihsalus:521`
(`dbb7efe1-12d9-58b0-8de2-c218f626ff48`), ya asociado como respuesta a ambas
preguntas en el catálogo. El validador declarativo del motor impide combinarlo
con enfermedades. Ambos antecedentes siguen siendo obligatorios; no se
preselecciona una respuesta ni se interpreta un campo vacío como ausencia.

Vaginales, cesáreas, nacidos vivos, nacidos muertos y peso del RN pueden
registrarse aunque el contador de partos esté vacío o sea cero. Conservan sus
conceptos, límites y carácter opcional. Esto permite registrar un parto
pretérmino sin exigir un parto a término previo.

La corrección no resuelve la ambigüedad del concepto `sihsalus:915`
(`8795c05b-f286-4d70-a1e6-69172e676f05`): su nombre preferido en español indica
partos a término, mientras otras denominaciones y mapeos remiten a paridad.
Se conserva la etiqueta **Partos** y no se sustituye por `sihsalus:818`, cuya
definición tampoco acredita un contador equivalente. La
[revisión clínica documentada](audits/2026-09-23-forms-clinical-review.md)
requiere decisión del responsable clínico y de terminología antes de redefinir
estos conceptos, añadir un contador o reinterpretar observaciones históricas.

La versión usa `AmpathFormsLoader` de Initializer; no sobrescribe el esquema
histórico `1.0.0` ni migra sus encuentros u observaciones.

## Responsable de puerperio inmediato

`OBST-006-PUERPERIO INMEDIATO` `1.0.2` concentra proveedor, ubicación y rol en
una página **Responsable**. Conserva el primer proveedor (`resposable`), que
gobierna el envío nativo, junto con `lugarAtencion` y `rolDelResponsable`.
Retira del nuevo esquema el segundo control `responsableAtencion`: ambos eran
metadata del mismo encuentro, sin concepto ni observación independiente, y se
rehidrataban del mismo proveedor guardado. No se renombra el ID histórico
`resposable` ni se modifica la captura clínica de puerperio.

La versión anterior `1.0.1` conserva su esquema y encuentros mediante el mismo
loader. No se migran proveedores, roles, ubicaciones ni observaciones.

## Sujeto de la epicrisis obstétrica

`HOSP-010-EPICRISIS OBSTÉTRICO-POSTPARTO` `1.0.2` conserva la epicrisis de la
madre y retira de la captura nueva el grupo **Recién Nacido**: género, peso,
Apgar, observaciones, condición de alta y responsable de neonatología. Todos
eran observaciones del RN dentro del encuentro materno. El grupo no cambia el
sujeto del encuentro; su peso reutilizaba `5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`,
el concepto general de peso, y podía atribuir una medida del niño a la madre.

Un control Markdown nativo, sin concepto ni observación, orienta a registrar la
evaluación y medidas en la historia propia del recién nacido desde **Hijos
vinculados**. El profesional elige al hijo correcto mediante el vínculo nativo;
el formulario no infiere un niño, duplica datos ni cambia el paciente activo.
El motor del frontend registra `markdown`, transforma su tipo a `control` y
renderiza `value`; el validador del paquete reconoce ese renderer nativo sin
valor clínico. El esquema `1.0.1` y sus encuentros se conservan mediante el
loader versionado. No se trasladan ni corrigen datos históricos; cualquier
revisión de atribución previa requiere un procedimiento clínico separado.

La revisión acotada de `HOSP-007` y `OBST-005` encontró grupos Neonato que
registran el equipo/responsable de atención del parto, no peso ni Apgar del RN.
Esos campos de resumen requieren su propia revisión clínica y no se eliminan
por equivalencia con la biometría. El `pesoMadreKg` de `OBST-005` permanece como
medida materna. `HOSP-011` no contiene un grupo de biometría de recién nacido.
No se introducen filtros en lectores para ocultar observaciones mal atribuidas.

## Contrato clínico de CRED

Los formularios CRED precargan el profesional vinculado a la sesión mediante el
adaptador del motor de formularios. El rol se selecciona explícitamente en la
lista visible: `Enfermería Responsable` para enfermería o `Médico Responsable`
para medicina. No se infiere la profesión desde permisos, nombres o el orden del
catálogo. `Enfermera de Triaje` conserva su alcance de triaje y los encuentros
históricos conservan su rol. El cambio de profesional sigue sujeto a la
autorización del backend; el rol del encuentro no concede privilegios.


`(CRED) Detalles de Nacimiento` incorpora una observación opcional de fecha y
hora de alta del recién nacido. Reutiliza `Fecha de alta` de OCL, UUID
`e911fe60-6d45-40c7-8d65-1ab93b3c77f4`, datatype `Datetime`. Su contexto es el
formulario de nacimiento del paciente, no el alta de la madre ni una
hospitalización posterior. El lugar del parto conserva su única captura en
`(CRED) Embarazo y Parto`. Se conserva la identidad nombre/versión `1.2`, el tipo
de encuentro perinatal y todos los campos anteriores; la adición no modifica
observaciones históricas. El frontend consulta este alta para el primer control
cuando el paciente tiene menos de 29 días: un parto institucional exige alta
válida y un mínimo exacto de 48 horas, y una lectura incompleta o fallida no
habilita el control. El segundo control incluye el día 14 y conserva siete días
mínimos desde el control anterior. La reanudación del mismo control conserva su
número.

La corrección de los reportes #389 y #390 mantiene la identidad del formulario
`(CRED) Detalles de Nacimiento` `1.2`. El alta no puede preceder al día de
nacimiento ni estar en el futuro; se permite el mismo día sin inferir una hora
de nacimiento que el dato demográfico no contiene. Si se introduce un alta y
no se dispone de una fecha de nacimiento válida, pide revisar la demografía.

El tiempo de hospitalización solo se edita con «Sí». Al cambiar a «No» se
conserva el valor introducido, pero se bloquea el guardado contradictorio y se
pide volver a «Sí» para corregirlo o borrarlo. No se eliminan observaciones por
ocultación ni se sustituye una respuesta ausente por cero. La regla se aplica
también al editar; no modifica registros históricos automáticamente.

**Talla al nacer (#391):** el candidato institucional `sihsalus/2026-10-16-1`
declara `extras.allow_decimal: true` para el concepto `382`
(`bf82beb1-d3b8-400e-8160-90869cad8136`). Conserva tipo numérico, unidad `cm`,
nombres y mappings. El formulario mantiene sus pasos de `0.1`, sin redondear
la medición. La corrección canónica y su snapshot están preparados; **la
publicación OCL y la aplicación en ambientes siguen pendientes**.

La [transición institucional](audits/2026-10-16-ocl-institutional-transition.md)
coordina los 34 exports con el host de la suscripción. Conserva las exclusiones
históricas de barrios y verifica las identidades en las 18 fuentes. Los ZIP se
generan desde exports oficiales con el splitter existente; no se editan registros
a mano ni se duplican conceptos en CSV/SQL.

El token institucional solo autentica en ese servidor. El secret de GitHub
no cambia `OMRS_OCL_TOKEN` en DEV/QLTY. La importación local de los ZIP por
Initializer no descarga el catálogo ni usa ese token; una futura importación
remota requiere verificar la credencial del entorno mediante una aprobación
operativa separada. La tarea no modifica credenciales ni controles del backend.
La aceptación requiere verificar `allowDecimal: true` y guardar/reabrir una
talla sintética de `30.1 cm` tras la actualización autorizada de content.

`CRED-001` `1.2.1` conserva la hemoglobina medida y la clasificación confirmada
por el profesional; incluye 500 m en la advertencia de ajuste por altitud y
admite captura hasta 5500 m, según la tabla 1 de la
[RM 429-2024/MINSA](https://bvs.minsa.gob.pe/local/fi-admin/RM-429-2024-minsa.pdf).
No calcula ni persiste hemoglobina ajustada. La selección de rangos de
hemoglobina por edad a la fecha de la muestra pertenece al
[contrato de laboratorio](contracts/laboratory-reporting.md).

Las curvas escolares del frontend usan las tablas OMS 2007 para ambos sexos
entre 61 y 228 meses; no se persisten puntajes z ni clasificaciones. EDI
(`CRED-009`) es una transcripción resumida de cinco ejes, Huanca (`CRED-026`)
guarda áreas y detalles y M-CHAT (`CRED-010`) conserva puntaje y resumen;
ninguno captura ítems individuales. Distribuir el cuestionario
[M-CHAT-R/F](https://mchatscreen.com/wp-content/uploads/2015/09/M-CHAT-R_F_NoShade_Aug2018.pdf)
en software requiere permiso de sus autores.

### Terminología a preparar en la fuente canónica

El inventario de `configuration/ocl/*concepts*.zip` no contiene conceptos
específicos para estos resultados. No sustituirlos por el concepto de Hb medida,
un resultado nutricional genérico repetido ni un UUID inventado en el formulario.

| Dato | Tipo / unidad | Semántica y revisión requerida |
| --- | --- | --- |
| Corrección de hemoglobina por altitud | Numeric, g/dL | Cantidad restada; conservar altitud aplicable, método/tabla y versión. |
| Hemoglobina ajustada por altitud | Numeric, g/dL | Resultado separado de la medición original y ligado a ella. |
| Puntaje z de P/E, T/E, P/T, IMC/E y PC/E | Un Numeric por indicador, sin unidad | Identificador propio por indicador; conservar sexo, edad al medir, referencia y mediciones fuente. |
| Clasificación de cada indicador | Un Coded por indicador | Respuestas compatibles con edad/referencia; no reutilizar indiscriminadamente la clasificación global. |
| Notificación del nacimiento extrainstitucional | Datetime | Fecha de conocimiento del nacimiento, diferente de fecha de nacimiento y de atención. |
| Ítems EDI | Coded por ítem | Mantener código oficial, grupo de edad, eje, observación/pregunta y respuestas completas. |
| Hitos Huanca | Coded por hito | Mantener pauta, área y método de constatación de la adaptación aprobada. |
| Ítems y seguimiento M-CHAT-R/F | Coded por ítem y decisión de seguimiento | Conservar orden, versión, respuestas iniciales, segunda etapa y resultado final diferenciado. |

Antes de asignar UUIDs, el mantenedor de OCL debe buscar equivalencias en HEAD,
reutilizar las existentes y publicar una versión/export oficial con los Q-AND-A.
La lógica clínica y los resultados derivados pertenecen al backend responsable;
no se añade una segunda regla en SQL, un script de carga ni un cálculo AMPATH
para suplir su ausencia. La
[NTS 238](https://cdn.www.gob.pe/uploads/document/file/9598727/7857089-norma-cred-12-03-26.pdf)
(numeral 6.4 para controles; anexo 10 para desarrollo) identifica EDI, segunda
edición 2021 de CeNSIA, y la adaptación de Huanca 2023.

## Sujeto del tamizaje de salud mental CRED

`CRED-011-SALUD MENTAL NIÑO Y CUIDADOR` `1.3.1` conserva el nombre y UUID
JSON para continuar su historia versionada; la captura nueva corresponde al
niño del encuentro. Retira las opciones PHQ-9 y AUDIT-C, que el propio esquema
anterior indicaba aplicar al cuidador, y la detección de violencia en la
madre/cuidadora con su campo `resultadoViolencia`. Estas observaciones se
guardaban bajo el paciente activo, sin un sujeto adulto independiente.

Un control Markdown nativo orienta a registrar los instrumentos y resultados
del cuidador en su propia historia clínica. La ayuda de instrumento y
observaciones deja de solicitar resultados del adulto. No selecciona ni abre
una historia automáticamente, no copia puntajes y no infiere quién es el
cuidador.

PPSC/PSC-17 conserva su opción, conceptos, rango de puntaje, resultados y edad
del niño. El plan sigue siendo obligatorio para resultados positivos o sospecha
diagnóstica. El cálculo y la visibilidad dejan de referenciar el campo de
violencia retirado; el puntaje sigue obligatorio para la opción infantil
restante. Esta corrección de sujeto no valida la selección clínica de PPSC o
PSC-17, no añade reglas de edad ni sustituye sus instrumentos oficiales.

El loader nativo conserva el esquema `1.3.0` y sus encuentros. No migra ni
reatribuye resultados históricos del cuidador; su revisión requiere un
procedimiento clínico separado.

## Alcance clínico documentado

El inventario siguiente orienta la revisión de formularios para categoría II-1 /
II-2. Antes de implementar cambios, comprobar el contrato del dominio, los
módulos del distro y la norma vigente en fuentes oficiales.

### Formularios y metadata incluidos

| Área | Contenido y límites |
| --- | --- |
| Cartera y agenda | Servicios y enrutamiento de la [cartera HSC](contracts/hsc-care-routing.md), referidos a NTS 249; especialidades profesionales y categorías locales declaradas en CSV nativos, con fuentes oficiales y alcance CRED diferenciado. |
| Consulta externa y salud mental | `CE-*` y `PSIC-001` a `PSIC-004`. Los diagnósticos se registran mediante Visit Notes. |
| Signos vitales y emergencia | Metadata separada para el chart, triaje y atención posterior; el [contrato de encuentros](contracts/chart-vitals-encounter-contract.md) requiere captura embebida en el frontend. No hay un JSON AMPATH adicional. |
| Obstetricia y neonatal | `OBST-*`, partograma, recién nacido y puerperio. |
| Hospitalización | `HOSP-001`, `HOSP-004`, `HOSP-008`, `HOSP-009`, `HOSP-012` y `FormularioEpicrisisMédica`. |
| Referencia | `CE-REF-*` y [catálogo de transporte](contracts/referral-transport-terminology.md). |
| CRED | `CRED-*`, incluidos Huanca adaptado (`CRED-026`) y habilidades/conductas (`CRED-027`); véase el [contrato clínico de CRED](#contrato-clínico-de-cred). |
| Odontología | `ODONT-*`; el odontograma es un componente separado. |
| Inmunizaciones | `INMU-001` e `INMU-002`; la [auditoría NTS 246](audits/2026-06-17-inmunizaciones-nts-246.md) registra brechas de vacunas y productos. |
| Laboratorio | Formularios de resultados y rangos con los límites del [contrato de laboratorio](contracts/laboratory-reporting.md). |

### Referencias documentadas

- [NTS 021-MINSA/DGSP-V.03: categorías de establecimientos](https://spij.minjus.gob.pe/Graficos/Peru/2011/Julio/16/RM-546-2011-MINSA.pdf).
- [NTS 139-MINSA/2018/DGAIN: gestión de historia clínica](https://spij.minjus.gob.pe/Graficos/Peru/2018/Marzo/15/RM-214-2018-MINSA.pdf).
- [NTS 238-MINSA/DGIESP-2025: crecimiento y desarrollo del niño](https://www.gob.pe/institucion/minsa/informes-publicaciones/7857089-norma-tecnica-de-salud-para-el-control-de-crecimiento-y-desarrollo-del-nino-nts-n-238-minsa-dgiesp-2025).
- [NTS 246-MINSA/DGIESP-2026: esquema nacional de inmunizaciones](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa).
- [NTS 249-MINSA/DGAIN-2026: cartera de servicios de salud](https://www.gob.pe/institucion/minsa/normas-legales/8389687-625-2026-minsa).
- [Guía de Vigilancia del Neurodesarrollo de Huanca Payehuanca](https://repositorio.essalud.gob.pe/handle/20.500.12959/5846).
