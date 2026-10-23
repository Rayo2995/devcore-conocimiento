# DevCore: Segundo Cerebro de ingeniería

Repositorio de conocimiento vivo del equipo. Es la fuente de verdad de la documentación de ingeniería y se abre como vault de Obsidian.

Punto de entrada: [00-MOC-DevCore.md](00-moc/00-MOC-DevCore.md)

## Estructura de carpetas

```
devcore-conocimiento/
├── 00-moc/              Mapas de contenido y convenciones
├── 01-onboarding/       Golden Path y guía de inicio
├── 02-arquitectura/     Decisiones de arquitectura (ADR)
├── 03-incidentes/       Post-mortems e índice de errores recurrentes
├── 04-servicios/        Un subdirectorio por servicio: documento, runbook y src/
├── 05-plantillas/       Plantillas de Obsidian (ADR, post-mortem, runbook, MOC)
├── adjuntos/            Imágenes y diagramas
├── .obsidian/           Configuración compartida del vault
└── .github/workflows/   Validación automática en CI
```

## Metadatos

Todo documento empieza con un bloque YAML con `tipo`, `id`, `titulo`, `estado`, `fecha_creacion`, `ultima_revision`, `responsable`, `servicios`, `etiquetas` y `relacionados`. Los detalles están en [convenciones.md](00-moc/convenciones.md).

## Reglas del equipo

1. Toda decisión técnica relevante lleva un ADR aprobado por Pull Request.
2. Todo incidente en producción cierra con un post-mortem en `03-incidentes/`.
3. Si un PR cambia `04-servicios/<servicio>/src/`, también debe actualizar `runbook-<servicio>.md`. El CI lo valida.
4. Todo documento nuevo se enlaza desde su MOC en el mismo PR.
5. El conocimiento no se queda en Slack ni en Zoom: si se decidió algo, se registra aquí.

## Cómo usarlo en Obsidian

1. Clona el repositorio.
2. En Obsidian, elige "Open folder as vault" y selecciona la carpeta.
3. Empieza por [[00-MOC-DevCore]].

La configuración compartida está en `.obsidian/`. Los archivos de sesión personal (`workspace*.json`) no se suben (ver `.gitignore`).
