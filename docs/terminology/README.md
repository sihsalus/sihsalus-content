# Curación pendiente de inmunizaciones

El [borrador JSONL](2026-10-19-immunization-curation.draft.jsonl) contiene dos
conceptos propuestos y dos Q-AND-A de `sihsalus:4121`, en el formato del
importador masivo nativo de OCL. Es una propuesta revisable: no es un export
oficial, no está en `configuration/`, no se empaqueta ni se importa automáticamente.
No hay una segunda definición operativa del catálogo.

## Evidencia

Se consultó todo el bundle y HEAD institucional mediante HTTPS autenticado de
solo lectura el 19 de octubre de 2026. Las consultas `hexavalente` y
`meningococo` en `inmunizaciones` y `medicamentos` devolvieron cero conceptos
(hash SHA-256 de cada respuesta JSON vacía:
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`).
No se modificó HEAD ni se publicaron versiones. Los procedimientos CPMS de
administración no son productos y no se usan como equivalencias.

La [NTS 246 / RM 561-2026](https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa)
y la [comunicación MINSA](https://www.gob.pe/institucion/minsa/noticias/1406009-minsa-fortalece-la-salud-publica-con-la-aprobacion-del-nuevo-esquema-nacional-de-inmunizaciones-uno-de-los-mas-completos-de-la-region)
incorporan hexavalente y meningococo para niños con VIH. Los anexos 1–2 de la
norma regulan la transición de pentavalente/IPV; el primer refuerzo cambia en
2027. Incorporar el producto no vuelve universal su pauta ni completa esa
transición automáticamente.

## Revisión y cierre

1. El responsable clínico y de terminología revisa nombre, formulación,
   serogrupos, clase, UUIDs propuestos y sus equivalencias en HEAD actualizado.
   La definición meningocócica queda deliberadamente sin serogrupos atribuidos:
   **no importar hasta completar esa decisión**.
2. Con autorización expresa, importar primero conceptos y luego mappings en las
   fuentes existentes. Reconciliar códigos, UUIDs y Q-AND-A mediante el mecanismo
   nativo; no crear otra fuente o un CSV operativo paralelo.
3. Publicar versiones OCL aprobadas y descargar sus exports oficiales. Dividirlos
   con el script existente `split_ocl_export.py`, preservando las exclusiones
   históricas del source principal y todos los UUIDs anteriores.
4. Actualizar el bundle y sus validaciones en este PR antes de considerarlo listo
   para merge. Incorporar los productos al selector existente y verificar
   persistencia, lectura histórica y poblaciones/transición en DEV/QLTY con
   datos sintéticos. No sustituir vacunas ni reasignar dosis ya administradas.

Los pendientes tienen responsables: terminología para equivalencias y publicación;
responsable de inmunizaciones para formulación, poblaciones y fases; backend y
frontend para la aceptación integrada. El borrador se retira cuando el bundle
contenga los exports oficiales aceptados. No requiere SQL ni migración de datos.
