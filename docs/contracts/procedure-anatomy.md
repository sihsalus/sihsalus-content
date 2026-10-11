# Sitios anatómicos para procedimientos

## Fuente y alcance

El selector institucional utiliza el conjunto OpenMRS
`25b4e8e6-0781-5c04-bc76-888402f3f505` (`PROCEDURE-BODY-SITES`).
Su fuente de verdad es OCL `SIHSALUS/anatomia-procedimientos`, release
`2026-10-11-01`. Contiene 133 sitios anatómicos humanos: 120 conceptos nuevos
y 13 conceptos existentes reutilizados, unidos mediante `CONCEPT-SET` y con
una equivalencia `SAME-AS` por sitio.

Los códigos proceden de [HL7 v2-0550 Body Parts, THO 7.4.0](https://terminology.hl7.org/7.4.0/CodeSystem-v2-0550.html),
CodeSystem `4.0.0`, canonical `http://terminology.hl7.org/CodeSystem/v2-0550`.
El JSON oficial tiene SHA-256
`56cdf48e0548a337400ce58fcd11d11152f6594e6dadad143b02c4d56149d68b`.
HL7 publica este recurso bajo [CC0](https://terminology.hl7.org/license.html).
La selección y los nombres españoles son una adaptación SIHSALUS; no se
presentan como traducción oficial HL7 ni homologación de MINSA. La búsqueda
realizada no identificó un catálogo peruano público de anatomía general
aplicable a este selector. Los catálogos de procedimientos CPMS y las tablas
de lesiones ocupacionales tienen otro alcance.

La tabla original contiene 442 códigos. Se seleccionan 133 sitios y se
excluyen líquidos, muestras, células, dispositivos, enfermedades, referencias
ambiguas y términos fuera del alcance inicial. Se incluyen regiones externas,
huesos y articulaciones, sitios de cabeza y cuello, órganos toracoabdominales,
urogenitales y obstétricos, deltoides y vasto lateral. El conjunto no pretende
ser exhaustivo: no hay código genérico de piel en esta distribución y no se
inventa uno. No incorpora lateralidad ni reglas sobre dónde efectuar una
intervención. La idoneidad y cobertura clínica quedan pendientes de revisión.

## Identidades e historia

Se reutilizan los conceptos existentes de pezón, tórax, labio, paladar duro,
paladar blando, laringe, hueso maxilar, orofaringe, ovario, endometrio, placenta,
esófago y lengua. Los mappings del nuevo catálogo apuntan a sus URLs
históricas en `SIHSALUS/sihsalus`; no se vuelven a exportar esos conceptos
desde otra fuente. Sus nombres, clases, tipos de dato y respuestas permanecen
intactos. Tórax conserva `Anatomy/Coded`; esófago sigue siendo respuesta de
la pregunta histórica de permeabilidad.

Las preguntas de examen abdominal, cuello, cadera y clavícula no equivalen
al sitio anatómico aislado. Sus conceptos nuevos usan el nombre español
completo con «(sitio anatómico)» y el nombre común como sinónimo. No se
reasignan registros previos, ni se convierten tejidos específicos en órganos
completos. El páncreas histórico con index-term `301305` no recibe una
equivalencia sin aclarar su procedencia.

El selector configura `bodySiteConceptSourceType: "Concept set"` y
`bodySiteConceptUuid` con el UUID indicado. Usa el parámetro REST nativo
`q` junto a `memberOf`: en la versión instalada, `name` más `searchType=fuzzy`
con `memberOf` ignora el término buscado. Las selecciones históricas se
rehidratan desde el procedimiento guardado; no se migran ni se filtran al leer.
La configuración frontend coordinada es [PR #1206](https://github.com/sihsalus/sihsalus-frontend/pull/1206).
Importar y verificar primero el contenido en OpenMRS; crear el catálogo en
OCL por sí solo no lo instala en QLTY.

## Distribución y mantenimiento

La release oficial se divide con `.github/scripts/split_ocl_export.py` en
los slots `17_` (121 conceptos, incluido el conjunto) y `67_` (266 mappings).
El ZIP oficial tiene SHA-256
`d90f27a60fb95e797b18986155370cee6fe8ffa80c235f2b612ff6c195078dbc`;
su JSON canónico recombinado tiene SHA-256
`beca354daa202a249fb1b08140cfd2d0fe1b2e6bb18f3fdb780080e8f646962a`.
El validador fija el hash JSON recombinado y verifica español, códigos,
pertenencia, equivalencias, UUIDs únicos e identidades históricas. Estos exports
son la única definición operativa; no hay CSV paralelo ni migración SQL.
La propiedad histórica `openconceptlab.subscriptionUrl` permanece intacta:
su namespace es necesario para resolver los conceptos importados existentes.

La versión upstream `4.0.0` y el hash de su distribución se conservan en la
metadata OCL. En OCL `2.3.209-28fabfa2`, el importador masivo omite
`to_source_version`; la API de creación individual sí lo conserva. Por eso
ese campo opcional puede estar vacío, pero nunca contradecir `4.0.0` en esta
release; `extras.upstream_version` es obligatorio en todas las equivalencias.
OpenMRS OCL `3.2.0-sihsalus.1` importa el código y la fuente `v2-0550`, pero
no traslada esa versión al `ConceptReferenceTerm`. No se afirma haber validado
la exportación FHIR del procedimiento.

Para actualizar el catálogo, editar su fuente OCL, conservar las identidades,
publicar otra release y sustituir juntos los dos ZIP mediante el splitter.
Contrastar el export oficial contra los cambios de autoría antes de aceptarlo:
un import masivo con `SUCCESS` no prueba que se hayan conservado todos los
campos. Usar payloads completos al actualizar mappings; esta versión de OCL
puede borrar el destino si un PATCH sólo incluye `extras`.

## Verificación

Ejecutar el validador OCL, sus regresiones y la verificación completa del
[paquete](../development.md). El ensayo nativo de Initializer comprueba en
instalación nueva, actualización y reinicio:

- Los 133 miembros exactos, sus nombres preferidos españoles, clases y datatypes.
- Los 133 códigos HL7 y sus mappings persistidos.
- Búsqueda nativa por abdomen, deltoides y esófago; ceftriaxona debe devolver cero.
- Estabilidad de identidades de base de datos y mappings al reiniciar.

Estas pruebas verifican carga y consulta de terminología. No acreditan
aceptación clínica, guardado integral de procedimientos ni despliegue.
