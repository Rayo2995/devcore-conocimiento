"""Respuesta a preguntas: búsqueda semántica + respuesta estricta + fuentes con enlace."""
import re
import unicodedata
from urllib.parse import quote

from . import config, llm, store

SISTEMA = (
    "Eres DevBrain, el asistente de guardia de DevCore. Respondes en español usando "
    "ÚNICAMENTE los fragmentos de documentación que se te entregan.\n"
    "Reglas:\n"
    "1. Si la pregunta pide un procedimiento (rollback, despliegue, diagnóstico), copia los "
    "pasos tal como aparecen, numerados y en el mismo orden. No agregues pasos ni comandos.\n"
    "2. No inventes nombres de servicios, comandos, versiones ni causas.\n"
    "3. Si una sección dice 'pendiente' o 'por completar', dilo explícitamente.\n"
    "4. Si los fragmentos no responden la pregunta, responde exactamente: "
    "'No encontré documentación que responda esto.'\n"
    "5. Sé breve: es de madrugada y alguien está resolviendo una caída."
)

ESTADOS_NO_VIGENTES = {"borrador", "propuesta", "pendiente", "reemplazada"}


def _palabras(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return {p for p in re.split(r"[^a-z0-9]+", texto) if len(p) > 3}


def enlace_github(ruta):
    return f"https://github.com/{config.GITHUB_REPO}/blob/{config.GIT_BRANCH}/{quote(ruta)}"


def recuperar(pregunta):
    vector = llm.embed([pregunta], "consulta")[0]
    candidatos = store.buscar(vector, config.TOP_K * 3)
    claves = _palabras(pregunta)
    puntuados = []
    for score, frag in candidatos:
        if score < config.MIN_SCORE:
            continue
        # Pequeño refuerzo léxico: ayuda al modelo de embeddings con términos técnicos.
        en_texto = len(claves & _palabras(frag["texto"]))
        en_titulo = len(claves & _palabras(f"{frag['titulo']} {frag['seccion']}"))
        puntuados.append((score + 0.03 * en_texto + 0.08 * en_titulo, frag))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in puntuados[:config.TOP_K]]


def responder(pregunta):
    """Devuelve el mensaje listo para Slack (formato mrkdwn)."""
    fragmentos = recuperar(pregunta)
    if not fragmentos:
        return ("No encontré documentación que responda esto en la bóveda.\n"
                "Si es una caída activa, escala al responsable del servicio por PagerDuty.")

    contexto = "\n\n---\n\n".join(
        f"[{f['doc_id'] or 'sin id'} | {f['ruta']} | estado: {f['estado'] or 'sin estado'}]\n{f['texto']}"
        for f in fragmentos)
    texto = llm.chat(SISTEMA, f"Fragmentos:\n\n{contexto}\n\nPregunta: {pregunta}")
    if "no encontré documentación" in texto.lower():
        return (texto + "\nSi es una caída activa, escala al responsable del servicio por PagerDuty.")

    # Las fuentes y advertencias las arma el código, no el modelo: así siempre son verificables.
    vistos, fuentes, avisos = set(), [], []
    for f in fragmentos:
        if f["ruta"] in vistos:
            continue
        vistos.add(f["ruta"])
        etiqueta = f"{f['doc_id']} · {f['titulo']}" if f["doc_id"] else f["titulo"]
        fuentes.append(f"• <{enlace_github(f['ruta'])}|{etiqueta}> (estado: {f['estado'] or 'sin estado'})")
        if str(f["estado"]).lower() in ESTADOS_NO_VIGENTES:
            avisos.append(f"⚠️ *{f['titulo']}* está en estado *{f['estado']}*: "
                          "valida con el responsable antes de ejecutar pasos en producción.")

    partes = [texto]
    if avisos:
        partes.append("\n".join(avisos))
    partes.append("*Fuentes:*\n" + "\n".join(fuentes))
    return "\n\n".join(partes)
