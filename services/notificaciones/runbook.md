# Runbook: servicio de notificaciones

**Última verificación:** 2026-10-22 (pendiente de validar en staging)

## Diagnóstico rápido

1. Revisar el estado del servicio en el panel de monitoreo.
2. Revisar la profundidad de la cola de mensajes.
3. Si la cola no responde, NO reiniciar ni restaurar sin revisar la sección "Restauración de la cola".

## Restauración de la cola

Pendiente de documentar con el equipo. No aplicar soluciones de tickets antiguos sin verificar la versión del sistema.

## Rollback de despliegue

1. Identificar la última versión estable con la etiqueta de release.
2. Desplegar esa versión con el pipeline de rollback.
3. Verificar que la cola procesa mensajes.

## Escalamiento

Si el incidente supera 30 minutos, escalar a [[responsable-notificaciones]] mediante PagerDuty.
