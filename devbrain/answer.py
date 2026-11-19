"""Respuesta a preguntas: búsqueda semántica + respuesta estricta + fuentes con enlace."""
import re
import unicodedata
from urllib.parse import quote

from . import config, llm, store

SISTEMA = (
    "Eres DevBrain, el asistente de guardia de DevCore. Respondes en español usando "
    "ÚNICAMENTE los fragmentos de documentación que se te entregan.\n"
    "Reglas:\n"
    "1. Si la pregunta pide un procedimiento (rollback, despliegue, diagnóstico), copia TODOS "
    "los pasos tal como aparecen, numerados y en el mismo orden. No omitas ni agregues pasos.\n"
    "2. No inventes nombres de servicios, comandos, versiones ni causas.\n"
    "3. Si una sección dice 'pendiente' o 'por completar', dilo explícitamente.\n"
    "4. Si los fragmentos no responden la pregunta, responde exactamente: "
    "'No encontré documentación que responda esto.'\n"
    "5. Sé breve: es de madrugada y alguien está resolviendo una caída."
)

ESTADOS_NO_VIGENTES = {"borrador", "propuesta", "pendiente", "reemplazada"}

# Palabras que indican que la pregunta pide un procedimiento.
PROCEDIMIENTO = {"rollback", "revertir", "despliegue", "desplegar", "deploy", "restaurar",
                 "restauracion", "diagnostico", "diagnosticar", "pasos", "procedimiento",
                 "escalar", "escalamiento", "reiniciar", "recuperar"}
# Un fragmento entra a la respuesta solo si su puntaje está cerca del mejor.
MARGEN = 0.06
PASO = re.compile(r"^\s*\d+\.\s+\S")


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
    if not puntuados:
        return []
    # Descarta fragmentos muy por debajo del mejor: evitan fuentes que no tienen que ver.
    mejor = puntuados[0][0]
    return [(s, f) for s, f in puntuados[:config.TOP_K] if s >= mejor - MARGEN]


def pasos_literales(pregunta, candidatos):
    """Si la pregunta pide un procedimiento y una sección tiene pasos numerados,
    devuelve ese fragmento: los pasos se copian tal cual, sin pasar por el modelo."""
    claves = _palabras(pregunta)
    if not claves & PROCEDIMIENTO:
        return None
    opciones = []
    for score, f in candidatos:
        lineas = [l for l in f["texto"].splitlines() if PASO.match(l)]
        if not lineas:
            continue
        en_seccion = len(claves & _palabras(f["seccion"]))
        opciones.append((en_seccion, score, f, lineas))
    if not opciones:
        return None
    opciones.sort(key=lambda x: (x[0], x[1]), reverse=True)
    en_seccion, _, f, lineas = opciones[0]
    return (f, lineas) if en_seccion > 0 else None


def fuentes_y_avisos(fragmentos):
    """Las fuentes y advertencias las arma el código, no el modelo: así siempre son verificables."""
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
    return fuentes, avisos


def armar(texto, fragmentos):
    fuentes, avisos = fuentes_y_avisos(fragmentos)
    partes = [texto]
    if avisos:
        partes.append("\n".join(avisos))
    partes.append("*Fuentes:*\n" + "\n".join(fuentes))
    return "\n\n".join(partes)


def responder(pregunta):
    """Devuelve el mensaje listo para Slack (formato mrkdwn)."""
    candidatos = recuperar(pregunta)
    if not candidatos:
        return ("No encontré documentación que responda esto en la bóveda.\n"
                "Si es una caída activa, escala al responsable del servicio por PagerDuty.")

    literal = pasos_literales(pregunta, candidatos)
    if literal:
        f, lineas = literal
        texto = (f"*{f['seccion']}* según _{f['titulo']}_:\n"
                 + "\n".join(l.strip() for l in lineas))
        return armar(texto, [f])

    fragmentos = [f for _, f in candidatos]
    contexto = "\n\n---\n\n".join(
        f"[{f['doc_id'] or 'sin id'} | {f['ruta']} | estado: {f['estado'] or 'sin estado'}]\n{f['texto']}"
        for f in fragmentos)
    texto = llm.chat(SISTEMA, f"Fragmentos:\n\n{contexto}\n\nPregunta: {pregunta}")
    if "no encontré documentación" in texto.lower():
        return (texto + "\nSi es una caída activa, escala al responsable del servicio por PagerDuty.")
    return armar(texto, fragmentos)
