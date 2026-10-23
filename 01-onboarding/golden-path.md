---
tipo: guia
id: GUI-003
titulo: Golden Path de onboarding
estado: vigente
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [todos]
etiquetas: [onboarding, golden-path]
relacionados: ["[[MOC-Onboarding]]", "[[runbook-notificaciones]]"]
---

# Golden Path de onboarding

**Meta:** que un ingeniero nuevo despliegue un cambio en producción en su segunda semana. Hoy el proceso tarda 6 semanas; el estándar de la industria es 2.

## Semana 1: entorno y contexto

- [ ] Acceso a GitHub, Jira, Slack y PagerDuty.
- [ ] Clonar el repositorio y abrirlo en Obsidian.
- [ ] Leer [[MOC-Arquitectura]] y los ADR aceptados.
- [ ] Levantar el entorno local según el servicio asignado en [[MOC-Servicios]].

## Semana 2: primer cambio real

- [ ] Resolver una tarea etiquetada como `good-first-issue`.
- [ ] Hacer un PR que actualice el runbook si el cambio toca el código del servicio.
- [ ] Seguir [[runbook-notificaciones]] en staging.
- [ ] Leer el post-mortem en [[MOC-Incidentes]].

## Preguntas

Cada servicio indica su responsable en su documento de servicio. Las preguntas que se repiten deben convertirse en una entrada de esta guía.
