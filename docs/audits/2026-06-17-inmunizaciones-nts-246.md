# Auditoría de inmunizaciones contra NTS 246-MINSA/DGIESP-2026

> [Registro histórico](README.md): evidencia y estados correspondientes a la fecha de la revisión.

Fecha de auditoría: 2026-06-17

## Alcance

Este documento registra la brecha normativa de los formularios y conceptos de inmunizaciones. Triaje queda fuera de alcance por decisión explícita del equipo.

## Norma vigente revisada

La fuente vigente para el esquema peruano de inmunizaciones es la **NTS N. 246-MINSA/DGIESP-2026, Norma Técnica de Salud que establece el Esquema Nacional de Inmunizaciones**, aprobada mediante **Resolución Ministerial N. 561-2026-MINSA** el **13 de junio de 2026**.

Fuentes oficiales:

- Resolución Ministerial N. 561-2026-MINSA: https://www.gob.pe/institucion/minsa/normas-legales/8265031-561-2026-minsa
- Nota oficial MINSA sobre la nueva NTS: https://www.gob.pe/institucion/minsa/noticias/1406009-minsa-fortalece-la-salud-publica-con-la-aprobacion-del-nuevo-esquema-nacional-de-inmunizaciones-uno-de-los-mas-completos-de-la-region

La página oficial de la resolución publica tres PDFs: la resolución y la NTS en dos partes. Los anexos de la NTS están publicados como PDF escaneado; `pdftotext` no extrajo texto usable. Antes de codificar reglas por edad/dosis debe hacerse OCR o revisión manual de los cuadros oficiales.

## Hallazgos normativos seguros

La nota oficial MINSA confirma estos cambios de alto impacto:

- La NTS 246 reemplaza el uso operativo de la NTS 196-MINSA/DGIESP-2022 y sus modificatorias como fuente principal del esquema actual.
- El esquema incorpora vacuna hexavalente.
- El esquema incorpora estrategia contra Virus Respiratorio Sincitial (VRS): vacunación de gestantes y anticuerpo monoclonal de larga duración para recién nacidos y lactantes menores de seis meses.
- El esquema incorpora nuevas medidas de protección para personas con VIH.
- El esquema fortalece vacunación contra Virus del Papiloma Humano (VPH).
- El esquema incluye vacuna contra meningococo para niños con VIH.
- El esquema reincorpora vacuna contra sarampión y rubéola (SR) para grupos de riesgo.

## Estado actual en SIHSALUS

Formulario principal:

- `configuration/backend_configuration/ampathforms/INMU-001-REGISTRO DE VACUNACIÓN.json`
  - Usa el set `f9840000-0000-4000-8000-000000000984` para seleccionar `Vacuna administrada`.
  - No codifica calendario ni reglas por edad; actúa como contrato de persistencia para vacuna, dosis, lote, estado y próxima dosis.

Formulario ESAVI:

- `configuration/backend_configuration/ampathforms/INMU-002-REPORTE ESAVI.json`
  - Captura vacuna relacionada como texto, lote, severidad, descripción y plan/notificación.

Export OCL actual revisado:

- `configuration/backend_configuration/ocl/12_SIHSALUS_inmunizaciones_v2026-06-16-openmrs-current.zip`
- Contiene 22 conceptos de clase `Drug`.

Conceptos presentes relevantes:

| Tema NTS 246 | Estado en OCL actual | Nota |
|---|---|---|
| VRS vacuna | Parcial | Existe `Vacuna contra Virus Sincitial Respiratorio` (`inmunizaciones:5341`). |
| VRS anticuerpo monoclonal | No en `inmunizaciones` | Existe procedimiento CPMS `90378` como anticuerpo monoclonal VRS, pero no un concepto canónico de inmunización/producto administrable en `inmunizaciones`. |
| Hexavalente | No encontrado | No aparece en `inmunizaciones`, `medicamentos` ni como concepto de vacuna en el set actual. |
| Meningococo para niños con VIH | Parcial | CPMS contiene procedimientos meningococo (`90733`, `90734`, `90644`), pero no concepto en `inmunizaciones`. |
| VPH | Parcial | Existen VPH bivalente y tetravalente (`inmunizaciones:1206`, `inmunizaciones:1205`) y medicamentos MINSA relacionados. Falta confirmar formulación vigente de NTS 246. |
| SR grupos de riesgo | Presente | Existe `Vacuna SR (sarampión, rubéola)` (`inmunizaciones:5332`) y medicamentos MINSA relacionados. Falta confirmar reglas de grupo de riesgo. |

## Brechas de implementación

1. Re-exportar o actualizar la fuente OCL `SIHSALUS/inmunizaciones` contra NTS 246.
2. Agregar conceptos faltantes para:
   - Vacuna hexavalente.
   - Vacuna meningocócica aplicable al esquema vigente.
   - Anticuerpo monoclonal VRS como producto administrable o concepto diferenciado, según decisión clínica/terminológica.
3. Revisar si VRS debe modelarse como `Drug`, `Medical supply` o concepto de inmunización no vacuna; no asumir que todo lo administrado en `INMU-001` es vacuna.
4. Confirmar si `INMU-001` debe renombrar `Vacuna administrada` a un término más amplio, por ejemplo `Producto de inmunización administrado`, si la NTS incluye anticuerpo monoclonal.
5. Confirmar reglas por edad, gestación, condición VIH y grupos de riesgo desde los cuadros oficiales antes de crear lógica de calendario.
6. Evaluar si `INMU-002` debe guardar `Vacuna relacionada` como concepto codificado en lugar de texto libre, para ESAVI interoperable.

## Siguiente cambio recomendado

No modificar calendario en formulario hasta extraer los cuadros completos de la NTS 246. El siguiente PR debería:

1. Curar OCL `inmunizaciones` con los conceptos faltantes.
2. Re-exportar el ZIP de `inmunizaciones`.
3. Actualizar `INMU-001` solo si el modelo debe admitir productos no vacuna.
4. Agregar una validación CI que verifique que el set usado por `INMU-001` contiene los conceptos mínimos de NTS 246.
