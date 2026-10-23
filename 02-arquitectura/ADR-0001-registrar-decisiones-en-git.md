---
tipo: adr
id: ADR-0001
titulo: Registrar las decisiones de arquitectura en Git
estado: aceptada
fecha_creacion: 2026-10-22
ultima_revision: 2026-10-22
responsable: por definir
servicios: [todos]
etiquetas: [arquitectura, documentacion]
relacionados: ["[[MOC-Arquitectura]]", "[[ADR-0002-runbooks-en-el-repositorio]]"]
---

# ADR-0001: Registrar las decisiones de arquitectura en Git

## Contexto

Las decisiones se tomaban en reuniones de Zoom y en PRs largos, sin registro del "por qué". Cuando alguien salía del equipo, el razonamiento se perdía.

## Opciones consideradas

1. Mantener las decisiones en Slack y Zoom: se pierden.
2. Wiki externa (Confluence): se desactualiza porque no está acoplada al código.
3. ADR en el mismo repositorio, aprobados por Pull Request: versionados y auditables.

## Decisión

Se adopta la opción 3. Cada decisión relevante se escribe como ADR en `02-arquitectura/` y se aprueba mediante Pull Request.

## Consecuencias

Escribir cada decisión tiene un costo. A cambio, el razonamiento queda disponible para futuros ingenieros y auditorías.
