# ADR-0001: Registrar las decisiones de arquitectura en Git

- **Estado:** aceptada
- **Fecha:** 2026-10-22
- **Servicios afectados:** todos

## Contexto

Las decisiones se tomaban en reuniones de Zoom y en PRs largos, sin registro del "por qué". Esto causaba repetición de debates y pérdida de contexto cuando alguien salía del equipo.

## Opciones consideradas

1. Mantener las decisiones en Slack y Zoom: se pierden, como ya ocurrió.
2. Wiki externa (Confluence): se vuelve obsoleta porque no está acoplada al código.
3. ADRs en el mismo repositorio, revisados por PR: versionados y auditables.

## Decisión

Adoptar la opción 3. Cada decisión relevante se escribe como ADR en `docs/adr/` y se aprueba mediante Pull Request.

## Consecuencias

Hay un costo de escritura por cada decisión. A cambio, el razonamiento queda disponible para futuros ingenieros y auditorías.
