# Instrucciones para sihsalus-content

Este repositorio distribuye metadata backend para OpenMRS. Leer el [README](README.md)
y el [contrato del dominio afectado](docs/README.md#contratos-por-dominio) antes de
cambiar contenido. La mantenibilidad
y la reducción de parches son criterios de aceptación, junto con la corrección
funcional y las pruebas.

## Reutilización y responsabilidad

- Preferir los formatos declarativos y mecanismos soportados por la versión de
  Initializer y los módulos que consume el distro. Verificar sus capacidades en
  el código o documentación de esa versión; un comentario histórico no demuestra
  que una limitación siga vigente.
- Reutilizar conceptos, UUIDs, formularios y contratos existentes. Mantener una
  sola fuente de verdad para cada catálogo, identidad o política de permisos.
  No mantener copias operativas de la misma regla en CSV, SQL, JSON y scripts.
- Resolver una capacidad ausente o un defecto en el componente existente que
  tiene esa responsabilidad, con una corrección reutilizable y contribución al
  proyecto de origen cuando corresponda. Crear otro módulo o framework también
  necesita justificación; mover el parche de archivo no elimina su causa.
- El content declara metadata. La lógica de negocio, las transacciones clínicas,
  la autorización efectiva y el esquema interno de cada módulo corresponden al
  backend responsable. La presentación y composición visual corresponden al
  frontend y deben reutilizar sus componentes y patrones compartidos.

## Liquibase y compatibilidad histórica

- Usar Liquibase para migraciones puntuales y versionadas cuya necesidad esté
  demostrada. No ampliarlo como un segundo loader, un sincronizador recurrente de
  CSV o un motor de reconciliación de tablas internas de otros módulos.
- Evitar SQL dinámico, reglas de permisos duplicadas y cambios al esquema del
  core para compensar problemas de configuración, identidad u orden de carga.
  Corregir primero la causa en el loader o módulo responsable.
- Si una transición puntual requiere una excepción, documentar en el PR la
  limitación verificada, las alternativas evaluadas, el alcance mínimo, el issue
  de seguimiento, el responsable de mantenimiento y la condición de retirada o
  sustitución. Una excepción existente no autoriza a ampliarla por analogía.
- Antes de simplificar o retirar una migración, determinar qué versiones y
  ambientes la ejecutaron y qué rutas de actualización siguen soportadas.
  Preservar los changesets publicados/aplicados, sus identidades y checksums;
  cualquier cambio de esa historia requiere una estrategia explícita y probada.
- Conservar UUIDs, referencias y datos históricos. Probar instalación nueva y
  actualización desde una versión soportada cuando cambie una migración o su
  carga. No borrar checksums, forzar recargas ni marcar una migración ejecutada
  para ocultar errores o estados incompatibles.
- El Liquibase y los scripts heredados son deuda a evaluar, no ejemplos que
  deban reproducirse. Su retirada debe preservar la compatibilidad necesaria;
  conservar historia aplicada no justifica añadir nuevos parches al mismo lugar.

## Scripts y automatización

- Reutilizar las herramientas y entradas de ejecución existentes. Un script
  nuevo debe tener un propósito acotado y explicar qué necesidad no cubren.
- Mantener los scripts como una capa pequeña de automatización. Evitar lógica
  clínica o de permisos, SQL operativo embebido, duplicación de validadores,
  frameworks de despliegue propios y cadenas de wrappers difíciles de seguir.
- Si aumenta la complejidad, revisar el diseño y extraer solo responsabilidades
  reutilizables que lo simplifiquen. Dividir un script grande en muchos archivos
  o añadir más pruebas no sustituye esa revisión.
- Definir entradas, salidas y fallos claros. Proteger secretos y datos clínicos;
  las comprobaciones automatizadas deben usar datos sintéticos y limpiar sus
  propios recursos cuando corresponda.

## Validación y revisión

- Usar los comandos del [workflow existente](.github/workflows/main.yml) y las
  pruebas del dominio afectado. Añadir regresiones para cambios de comportamiento;
  comprobar efectos y contratos, no solo que el código contiene cierto texto.
- Para cambios solo de documentación, revisar el diff, los enlaces y la
  consistencia de las instrucciones. No crear scripts o tests nuevos para
  validar esta política ni subir la versión del paquete por esa razón.
- En el PR, identificar el componente responsable, qué se reutiliza, qué deuda
  se elimina o por qué una excepción es inevitable, y la evidencia pertinente.
  Aplicar este criterio también a propuestas en curso antes de ampliarlas.
- Un CI correcto no acredita por sí solo mantenibilidad, aceptación clínica o
  despliegue. Distinguir esas evidencias y dejar visibles las pendientes.
