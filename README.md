# DevCore — Segundo Cerebro de ingeniería

Repositorio de conocimiento vivo del equipo. Es la fuente de verdad de la documentación de ingeniería y se abre como vault de Obsidian.

## Estructura

- `docs/onboarding/`: Golden Path y guía de inicio para nuevos ingenieros.
- `docs/adr/`: Decisiones de arquitectura (una por archivo, formato MADR).
- `docs/incidents/`: Post-mortems y el índice de errores recurrentes.
- `services/<servicio>/`: README, runbook y mapa de dependencias de cada servicio.
- `templates/`: Plantillas para Obsidian (ADR, post-mortem, runbook).

## Reglas del equipo

1. Toda decisión técnica relevante lleva un ADR, aprobado mediante Pull Request.
2. Todo incidente en producción cierra con un post-mortem en `docs/incidents/`.
3. Si un PR cambia `services/<servicio>/src/`, también debe actualizar `services/<servicio>/runbook.md`. El CI lo valida.
4. El conocimiento no se queda en Slack ni en Zoom: si se decidió algo, se registra aquí.

## Cómo usarlo en Obsidian

1. Clona el repositorio: `git clone <url-del-repo>`.
2. En Obsidian, elige "Open folder as vault" y selecciona la carpeta clonada.
3. Usa los enlaces `[[nombre]]` para conectar servicios, ADRs e incidentes. El grafo mostrará las relaciones.
4. Los archivos de configuración personal de `.obsidian/` no se suben al repositorio (ver `.gitignore`).
