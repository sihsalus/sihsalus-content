## Problema y resultado

Explica el problema, el comportamiento resultante y el issue relacionado, si existe.

## Mantenibilidad

- Componente responsable y mecanismo existente que se reutiliza:
- Fuente de verdad de la metadata o reglas afectadas:
- Deuda eliminada o excepción inevitable (indicar «no aplica» cuando corresponda):

Si se introduce una excepción, documentar la limitación verificada, alternativas,
alcance mínimo, issue de seguimiento, responsable y condición de retirada o
sustitución, según [AGENTS.md](https://github.com/sihsalus/sihsalus-content/blob/main/AGENTS.md).

## Validación y compatibilidad

- Comprobaciones ejecutadas y resultado; indicar las pendientes y su causa.
- Si cambia una migración o su carga: versiones de origen soportadas, preservación
  del historial/checksums y evidencia de instalación nueva y actualización.
- Impacto operativo y recuperación, cuando corresponda.

Usar las comprobaciones de la [guía de desarrollo](https://github.com/sihsalus/sihsalus-content/blob/main/docs/development.md)
y del dominio afectado. Para cambios solo de documentación, basta revisar diff,
enlaces y consistencia; no se requieren pruebas nuevas ni subir la versión.

No adjuntar secretos ni datos clínicos. La evidencia de CI, aceptación clínica y
despliegue debe distinguirse explícitamente.
