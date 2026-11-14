"""Generación de post-mortems a partir del historial de un canal de incidente."""
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, llm

SECCIONES = ["Resumen", "Línea de tiempo", "Causa raíz", "Qué funcionó y qué no",
             "Acciones correctivas", "Conocimiento a registrar"]
SIN_DATO = "No registrado en el canal."

SISTEMA = (
    "Redactas post-mortems de incidentes para DevCore a partir de la conversación de Slack "
    "que se te entrega. Reglas estrictas:\n"
    "1. Usa solo hechos que aparecen en la conversación. No inventes horas, causas, cifras, "
    "personas ni comandos.\n"
    f"2. Si un dato no aparece, escribe '{SIN_DATO}'.\n"
    "3. La línea de tiempo usa las horas exactas de los mensajes, en formato '- HH:MM: suceso'.\n"
    "4. Si la causa raíz no se confirmó en el canal, escribe 'Sin confirmar:' seguido de las "
    "hipótesis mencionadas.\n"
    "5. Acciones correctivas: tabla Markdown con columnas Acción | Responsable | Fecha límite. "
    "Solo acciones que alguien propuso en el canal; si no se nombró responsable, escribe 'por definir'.\n"
    "6. Responde SOLO con estas secciones, cada una con encabezado '## ' exacto y en este orden: "
    + ", ".join(SECCIONES) + ". Sin título, sin introducción y sin bloque YAML."
)


def slug(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-") or "incidente"


def leer_historial(client, canal):
    mensajes, cursor = [], None
    while True:
        r = client.conversations_history(channel=canal, limit=200, cursor=cursor)
        mensajes.extend(r["messages"])
        cursor = r.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    utiles = [m for m in mensajes
              if m.get("type") == "message" and m.get("text")
              and m.get("subtype") not in {"channel_join", "channel_leave", "channel_purpose",
                                           "channel_topic", "bot_message"}
              and not m.get("bot_id")]
    return sorted(utiles, key=lambda m: float(m["ts"]))


def transcripcion(client, mensajes):
    zona = ZoneInfo(config.TIMEZONE)
    nombres = {}

    def nombre(uid):
        if uid not in nombres:
            try:
                u = client.users_info(user=uid)["user"]
                nombres[uid] = u.get("real_name") or u.get("name") or uid
            except Exception:
                nombres[uid] = uid
        return nombres[uid]

    lineas = []
    for m in mensajes:
        hora = datetime.fromtimestamp(float(m["ts"]), zona).strftime("%Y-%m-%d %H:%M")
        texto = re.sub(r"<@(\w+)>", lambda x: "@" + nombre(x.group(1)), m["text"])
        lineas.append(f"[{hora}] {nombre(m.get('user', '?'))}: {texto}")
    completo = "\n".join(lineas)
    if len(completo) > config.MAX_TRANSCRIPT_CHARS:
        completo = ("[Conversación recortada: solo se incluyen los últimos mensajes]\n"
                    + completo[-config.MAX_TRANSCRIPT_CHARS:])
    return completo


def asegurar_secciones(cuerpo):
    """Garantiza las secciones de la plantilla aunque el modelo omita alguna."""
    cuerpo = cuerpo.strip()
    cuerpo = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", cuerpo).strip()
    cuerpo = re.sub(r"(?s)\A---\n.*?\n---\n", "", cuerpo).strip()
    for seccion in SECCIONES:
        if not re.search(rf"(?mi)^##\s+{re.escape(seccion)}\s*$", cuerpo):
            cuerpo += f"\n\n## {seccion}\n\n{SIN_DATO}"
    return cuerpo


def construir(canal_nombre, transcripcion_texto, inicio, fin):
    base = slug(re.sub(rf"^{re.escape(config.INCIDENT_PREFIX)}", "", canal_nombre))
    fecha = inicio.strftime("%Y-%m-%d")
    nombre_archivo = f"{fecha}-incidente-{base}.md"
    titulo = f"Incidente {base.replace('-', ' ')} ({fecha})"
    duracion = fin - inicio
    horas = round(duracion.total_seconds() / 3600, 1)

    cuerpo = asegurar_secciones(llm.chat(
        SISTEMA, f"Canal: #{canal_nombre}\n\nConversación:\n{transcripcion_texto}",
        num_ctx=config.POSTMORTEM_CTX))

    hoy = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y-%m-%d")
    documento = f"""---
tipo: postmortem
id: PM-{fecha}-{base}
titulo: "{titulo}"
estado: borrador
fecha_creacion: {hoy}
ultima_revision: {hoy}
responsable: por definir
servicios: []
etiquetas: [incidente, generado-por-devbrain]
relacionados: ["[[MOC-Incidentes]]", "[[indice-errores-recurrentes]]"]
---

# Post-mortem: {titulo}

- **Canal:** #{canal_nombre}
- **Primer mensaje:** {inicio.strftime('%Y-%m-%d %H:%M')}
- **Último mensaje:** {fin.strftime('%Y-%m-%d %H:%M')}
- **Duración de la conversación:** {horas} horas (aproximación del MTTR; confirmar con el monitoreo)

> Borrador generado automáticamente por DevBrain a partir del canal. Revisar contra el historial antes de aprobar el Pull Request.

{cuerpo}
"""
    return f"{config.INCIDENTS_DIR}/{nombre_archivo}", titulo, documento


def generar(client, canal):
    info = client.conversations_info(channel=canal)["channel"]
    mensajes = leer_historial(client, canal)
    if not mensajes:
        raise ValueError("El canal no tiene mensajes para generar el post-mortem.")
    zona = ZoneInfo(config.TIMEZONE)
    inicio = datetime.fromtimestamp(float(mensajes[0]["ts"]), zona)
    fin = datetime.fromtimestamp(float(mensajes[-1]["ts"]), zona)
    return construir(info["name"], transcripcion(client, mensajes), inicio, fin)
