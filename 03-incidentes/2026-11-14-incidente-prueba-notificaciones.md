---
tipo: postmortem
id: PM-2026-11-14-prueba-notificaciones
titulo: "Incidente prueba notificaciones (2026-11-14)"
estado: borrador
fecha_creacion: 2026-11-18
ultima_revision: 2026-11-18
responsable: por definir
servicios: []
etiquetas: [incidente, generado-por-devbrain]
relacionados: ["[[MOC-Incidentes]]", "[[indice-errores-recurrentes]]"]
---

# Post-mortem: Incidente prueba notificaciones (2026-11-14)

- **Canal:** #inc-prueba-notificaciones
- **Primer mensaje:** 2026-11-14 11:42
- **Último mensaje:** 2026-11-18 21:18
- **Duración de la conversación:** 105.6 horas (aproximación del MTTR; confirmar con el monitoreo)

> Borrador generado automáticamente por DevBrain a partir del canal. Revisar contra el historial antes de aprobar el Pull Request.

## Resumen
El servicio de notificaciones no estaba enviando correos y había 50.000 mensajes pendientes en la cola. El problema se resolvió haciendo rollback a la versión anterior con el pipeline.

## Línea de tiempo
- 21:14: Alerta: notificaciones no está enviando correos
- 21:15: Revisé la cola, tiene 50.000 mensajes pendientes
- 21:16: Hice rollback a la versión anterior con el pipeline
- 21:17: La cola volvió a procesar, servicio restaurado
- 21:18: Acción: documentar la restauración de la cola en el runbook
- 21:18: @DevBrain postmortem

## Causa raíz
Sin confirmar: no se mencionó la causa raíz del problema en el canal.

## Qué funcionó y qué no
Qué funcionó: el rollback a la versión anterior con el pipeline.
Qué no funcionó: no se mencionó nada que no funcionara.

## Acciones correctivas
| Acción | Responsable | Fecha límite |
|--------|-------------|--------------|
| Documentar la restauración de la cola en el runbook | Sebastian Rayo Cuesta | por definir |

## Conocimiento a registrar
No registrado en el canal.
