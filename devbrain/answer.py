"""Respuesta a preguntas sobre la bóveda.

Orden de decisión (lo que el código puede resolver solo, no pasa por el modelo):
1. Búsqueda híbrida (vectores + palabras exactas) -> documentos candidatos.
2. Si la pregunta pide un procedimiento, se copian los pasos del documento
   (listas numeradas, subsecciones "### 1. ..." o tablas con columna N.º).
3. Si la pregunta nombra una sección o subsección de un documento candidato
   ("plazos", "causales", "quién lo diligencia", "audiencia", "puntos de control"...),
   se copia esa sección tal cual.
4. Si preguntan qué formato usar, se arma la respuesta desde el documento del formato.
5. En otro caso, el modelo responde con las secciones más relevantes y reglas estrictas.
   Si no encuentra el dato, se dice y se muestra lo más relacionado.
Las fuentes, avisos de estado y fichas de formato siempre las arma el código.
"""
import math
import re
import unicodedata
from urllib.parse import quote

from . import config, llm, store, vault

SISTEMA = (
    "Eres DevBrain, el asistente de DevCore. Respondes en español usando ÚNICAMENTE las "
    "secciones de documentación que se te entregan.\n"
    "Reglas:\n"
    "1. Responde la pregunta en 2 a 4 frases cortas, de corrido, sin repetir ideas.\n"
    "2. Si la respuesta es una lista o una tabla en el documento, cópiala completa y en el "
    "mismo orden. No agregues elementos, pasos, campos ni requisitos que no estén escritos.\n"
    "3. No uses conocimiento general sobre el tema: solo lo que dicen las secciones.\n"
    "4. No hables de los metadatos (responsable, estado, servicios) salvo que la pregunta los pida.\n"
    "5. Si el dato que se pregunta (un número, un plazo, un nombre) no está escrito en las "
    "secciones, responde exactamente: 'No encontré documentación que responda esto.'\n"
    "6. Si una sección dice 'pendiente' o 'por completar', dilo explícitamente.\n"
    "7. No pongas citas entre paréntesis después de cada frase: las fuentes se agregan aparte. "
    "Puedes nombrar el código del documento (por ejemplo ADR-0001) una sola vez."
)

NO_ENCONTRE = "no encontré documentación"
ESCALAR = "Si es una caída activa, escala al responsable del servicio por PagerDuty."
ESTADOS_NO_VIGENTES = {"borrador", "propuesta", "pendiente", "reemplazada"}

# Palabras sin contenido para comparar la pregunta con los encabezados.
VACIAS = {
    "para", "como", "cual", "cuales", "cuando", "donde", "este", "esta", "estos", "estas",
    "sobre", "tiene", "tengo", "debo", "puedo", "quiero", "necesito", "hacer", "hago",
    "sirve", "servicio", "pasa", "paso", "segun", "desde", "hasta", "entre", "otro", "otra",
    "algun", "alguna", "todo", "todos", "toda", "todas", "cosa", "favor", "dime", "explica",
    "documento", "devbrain", "porque", "debe", "deben", "puede", "pueden", "hace", "hacen",
    "realiza", "realizar", "realizo", "funciona", "manera", "forma",
}
# Sinónimos: si la pregunta usa la raíz de la izquierda, también cuenta la de la derecha.
SINONIMOS = {
    "antic": "plazo", "demor": "plazo", "tiemp": "plazo", "venci": "plazo", "termi": "plazo",
    "fecha": "plazo",
    "pasos": "etapa", "etapa": "pasos", "activ": "pasos", "desar": "pasos",
    "firma": "dilig", "llena": "dilig", "radic": "entre",
    "datos": "infor", "campo": "infor", "requi": "infor", "conti": "infor",
    "desca": "archi", "bajar": "desca",
    "rever": "rollb", "devol": "rollb", "plant": "forma", "formu": "forma",
    "motiv": "causa", "razon": "causa",
    "respo": "quien", "encar": "quien", "funci": "quien", "papel": "quien", "rol": "quien",
    "defin": "termi", "signi": "termi", "conce": "termi",
    "norma": "norma", "leyes": "norma", "decre": "norma",
    "preve": "punto", "verif": "punto",
}
FRASES_PLAZO = re.compile(r"(hasta cuando|cuanto tiempo|en que tiempo|"
                          r"con cuanta anticipacion|que termino|dentro de cuanto)")
# Una sola palabra en común basta si es de este tipo (nombra la sección por su función).
FUERTES = {"plazo", "causa", "pasos", "etapa", "rollb", "dilig", "infor", "forma", "punto",
           "diagn", "escal", "decis", "termi", "norma", "conse", "regla", "difer", "requi",
           "audie", "recur", "objet", "alcan", "flujo", "regis", "linea", "respo"}
# Encabezados que nunca se devuelven solos.
GENERICOS = re.compile(r"^(introduccion|ficha.*|como se suele preguntar|preguntas frecuentes|"
                       r"archivo original|descarga|control de cambios)$")
# Encabezados de secciones de pasos que no son "el procedimiento" en sí.
NO_ES_PROCEDIMIENTO = re.compile(r"(puntos? de control|flujograma|control de cambios|"
                                 r"preguntas|terminos|normativ|documentos)")

PIDE_LISTADO = re.compile(r"\b(qu[eé] (formatos|documentos|procedimientos|adr|runbooks)|lista|"
                          r"listado|cu[aá]les (formatos|documentos|procedimientos))\b", re.I)
PIDE_FORMATO = re.compile(r"\b(formato|formulario|planilla|plantilla|acta)\b", re.I)
# Pregunta explícita por cuál formato usar: va antes que las secciones.
CUAL_FORMATO = re.compile(r"(qu[eé]|cu[aá]l) (formato|formulario|planilla|acta)|"
                          r"(formato|formulario) (uso|lleno|diligencio|necesito|debo|hay que)", re.I)
PIDE_PROCEDIMIENTO = re.compile(
    r"\b(pasos|etapas|actividades|rollback|revertir|desplegar|despliegue|restaurar|reiniciar|"
    r"diagnosticar|como se (hace|realiza|desarrolla|tramita|liquida|ejecuta|lleva)|"
    r"como (hago|hacer|realizo|tramito|liquido|se debe)|procedimiento (para|de|del)|"
    r"que (debo|hay que|tengo que) hacer|en que consiste el procedimiento)\b")
PASO = re.compile(r"^\s*\d+\.\s+\S")
MARGEN = 0.06        # fragmentos cuyo puntaje está cerca del mejor
MARGEN_DOC = 0.06    # otro documento entra al contexto si está cerca del mejor
MAX_CONTEXTO = 5000
MAX_UNIDAD = 2200    # máximo por sección enviada al modelo
MAX_LITERAL = 3500   # máximo de una sección copiada a Slack


# ---------------------------------------------------------------- utilidades de texto

def _normal(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _palabras(texto):
    return {p for p in re.split(r"[^a-z0-9]+", _normal(texto)) if len(p) > 3}


def _raices(texto, quitar=(), sinonimos=True):
    """Raíces de 5 letras (plazo/plazos -> plazo), sin palabras vacías, con sinónimos.
    `quitar`: palabras completas que no cuentan (por ejemplo las del título del documento)."""
    quitar = set(quitar)
    raices = set()
    if sinonimos and FRASES_PLAZO.search(_normal(texto)):
        raices.add("plazo")
    for p in re.split(r"[^a-z0-9]+", _normal(texto)):
        if len(p) < 3 or p in VACIAS or p in quitar or p.isdigit():
            continue
        if len(p) == 3 and p != "rol":
            continue
        r = p[:5]
        raices.add(r)
        if sinonimos and r in SINONIMOS:
            raices.add(SINONIMOS[r])
    return raices


def _sin_numero(encabezado):
    return re.sub(r"^\s*\d+[.)]\s*", "", encabezado).strip()


def enlace_github(ruta):
    return f"https://github.com/{config.GITHUB_REPO}/blob/{config.GIT_BRANCH}/{quote(ruta)}"


def _leer(ruta):
    try:
        texto = (config.VAULT_PATH / ruta).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}, ""
    meta, cuerpo = vault.parse_frontmatter(texto)
    return meta, cuerpo.strip()


def cuerpo_de(ruta):
    return _leer(ruta)[1]


def meta_de(ruta):
    return _leer(ruta)[0]


def _sin_codigo(texto):
    """Quita los bloques ``` para que un flujograma no cuente como lista de pasos."""
    return re.sub(r"(?s)```.*?```", "", texto)


def bloques_de(cuerpo):
    """Secciones '##' y subsecciones '###' del documento.

    Cada bloque: nivel, encabezado, padre, contenido (con subsecciones), propio (sin ellas)
    e hijos (encabezados de sus subsecciones). El texto antes del primer '##' es 'Introducción'.
    """
    partes = re.split(r"(?m)^(#{2,3})\s+(.+?)\s*$", cuerpo)
    bloques = []
    intro = re.sub(r"(?m)^#\s+.*$", "", partes[0]).strip()
    if intro:
        bloques.append({"nivel": 2, "encabezado": "Introducción", "padre": None,
                        "contenido": intro, "propio": intro, "hijos": []})
    padre = None
    for i in range(1, len(partes) - 2, 3):
        nivel, encabezado, texto = len(partes[i]), partes[i + 1].strip(), partes[i + 2].strip()
        if nivel == 2:
            padre = {"nivel": 2, "encabezado": encabezado, "padre": None,
                     "contenido": texto, "propio": texto, "hijos": []}
            bloques.append(padre)
        else:
            hijo = {"nivel": 3, "encabezado": encabezado,
                    "padre": padre["encabezado"] if padre else None,
                    "contenido": texto, "propio": texto, "hijos": []}
            bloques.append(hijo)
            if padre:
                padre["hijos"].append(encabezado)
                padre["contenido"] += f"\n\n### {encabezado}\n{texto}"
    return bloques


def seccion(cuerpo, *patrones):
    for b in bloques_de(cuerpo):
        for patron in patrones:
            if re.fullmatch(patron, _normal(b["encabezado"])) and b["contenido"]:
                return b["contenido"]
    return None


def es_generico(encabezado):
    return bool(GENERICOS.match(_normal(_sin_numero(encabezado)).strip()))


def _tabla(texto):
    """Primera tabla Markdown del texto como (encabezados, filas)."""
    filas = [l.strip() for l in texto.splitlines() if l.strip().startswith("|")]
    filas = [f for f in filas if not re.match(r"^\|?\s*:?-{3,}", f)]
    if len(filas) < 2:
        return None
    celdas = [[c.strip() for c in f.strip("|").split("|")] for f in filas]
    return celdas[0], celdas[1:]


def pasos_de(bloque):
    """Lista de pasos de un bloque, o None si no describe pasos."""
    propio = _sin_codigo(bloque["propio"])
    # 1. Subsecciones numeradas: "### 1. Ingresar a la plataforma"
    numerados = [h for h in bloque["hijos"] if re.match(r"^\s*\d+[.)]\s", h)]
    if len(numerados) >= 2:
        return [_sin_numero(h) for h in numerados]
    # 2. Tabla con columna N.º / Paso / Actividad
    tabla = _tabla(propio)
    if tabla:
        encabezados, filas = tabla
        norm = [_normal(e) for e in encabezados]
        if norm and re.match(r"^(n\.?º?|no\.?|n°|#|paso|item)$", norm[0].replace(" ", "")) \
                and all(f and re.match(r"^\d+$", f[0]) for f in filas if f):
            col_act = next((i for i, e in enumerate(norm) if "actividad" in e), 1)
            col_resp = next((i for i, e in enumerate(norm) if "responsable" in e), None)
            pasos = []
            for f in filas:
                if len(f) <= col_act:
                    continue
                paso = f[col_act]
                if col_resp is not None and len(f) > col_resp and f[col_resp]:
                    paso += f" — _{f[col_resp]}_"
                pasos.append(paso)
            return pasos or None
    # 3. Lista numerada "1. ..."
    lineas = [l for l in propio.splitlines() if PASO.match(l)]
    if len(lineas) >= 2:
        return None  # se muestra el texto tal cual (conserva sublíneas)
    return None


def tiene_lista_numerada(bloque):
    return sum(1 for l in _sin_codigo(bloque["propio"]).splitlines() if PASO.match(l)) >= 2


# ---------------------------------------------------------------- búsqueda

VACIAS_BM25 = {"que", "los", "las", "del", "para", "con", "por", "una", "uno", "como", "cual",
               "cuales", "cuando", "donde", "quien", "este", "esta", "hay", "son", "fue", "ser",
               "muy", "pero", "mas", "sus", "les", "nos", "mis", "tus", "the", "and",
               "sobre", "entre", "hasta", "desde", "puedo", "debo", "tengo", "quiero", "necesito",
               "debe", "hace", "hacer", "cada", "sea", "est", "esa", "ese"}
PENALIZA_TIPO = {"moc": 0.12}


def _terminos(texto):
    return [t for t in re.split(r"[^a-z0-9]+", _normal(texto))
            if len(t) >= 3 and t not in VACIAS_BM25]


def _bm25(consulta, documentos_tokens):
    """BM25 clásico sobre los fragmentos. Devuelve un puntaje por fragmento."""
    n = len(documentos_tokens)
    if not n:
        return []
    largo_medio = sum(len(d) for d in documentos_tokens) / n or 1
    df = {}
    for d in documentos_tokens:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    puntajes = []
    for d in documentos_tokens:
        frec = {}
        for t in d:
            frec[t] = frec.get(t, 0) + 1
        total = 0.0
        for t in set(consulta):
            if t not in frec:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            tf = frec[t]
            total += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * len(d) / largo_medio))
        puntajes.append(total)
    return puntajes


def recuperar(pregunta):
    """Fragmentos candidatos ordenados por puntaje: [(puntaje, fragmento)].

    Búsqueda híbrida: similitud de vectores + BM25 por palabras (atrapa siglas y códigos
    como CDP, TVEC, FUID o GAD-FT-003 que el modelo de embeddings no distingue bien).
    """
    vector = llm.embed([pregunta], "consulta")[0]
    todos = store.buscar(vector, 5000)
    if not todos:
        return []
    consulta = _terminos(pregunta)
    lexico = _bm25(consulta, [_terminos(f["texto"]) for _, f in todos])
    tope_lexico = max(lexico) if lexico and max(lexico) > 0 else 1.0
    puntuados = []
    for (score, frag), lex in zip(todos, lexico):
        relativo = lex / tope_lexico
        if score < config.MIN_SCORE and relativo < 0.6:
            continue
        total = score + 0.30 * relativo - PENALIZA_TIPO.get(frag.get("tipo"), 0)
        puntuados.append((total, frag))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return puntuados[:config.TOP_K * 4]


def documentos(candidatos):
    """[(puntaje, fragmento representativo)] uno por documento, de mejor a peor."""
    mejor = {}
    for score, f in candidatos:
        if f["ruta"] not in mejor or score > mejor[f["ruta"]][0]:
            mejor[f["ruta"]] = (score, f)
    return sorted(mejor.values(), key=lambda x: x[0], reverse=True)


# ---------------------------------------------------------------- respuestas sin modelo

def _claves_seccion(pregunta, f):
    """Raíces de la pregunta sin las palabras del título del documento (identifican el
    documento, no la sección)."""
    return _raices(pregunta, quitar=_palabras(f"{f['titulo']} {f['doc_id']}"))


def seccion_literal(pregunta, docs, candidatos=()):
    """Si la pregunta nombra una sección de uno de los mejores documentos, la devuelve.

    Cada palabra en común pesa según lo rara que es entre los encabezados ("regreso" pesa
    más que "diligenciarlo", que está en todos los formatos). Devuelve (documento, [bloques]).
    """
    if not docs:
        return None
    tope = docs[0][0]
    pide_listado = bool(PIDE_LISTADO.search(pregunta))
    elegidos = []
    for orden, (score, f) in enumerate(docs[:4]):
        if score < tope - 0.10:
            break
        if f.get("tipo") == "moc" and not pide_listado:
            continue
        elegidos.append((orden, f, [b for b in bloques_de(cuerpo_de(f["ruta"]))
                                    if not es_generico(b["encabezado"]) and b["contenido"]]))
    todas = [_raices(_sin_numero(b["encabezado"])) for _, _, bs in elegidos for b in bs]
    if not todas:
        return None
    df = {}
    for raices in todas:
        for r in raices:
            df[r] = df.get(r, 0) + 1
    peso = lambda r: 1 + math.log(len(todas) / df.get(r, 1))
    marcadas = {(fr["ruta"], fr["seccion"]) for _, fr in candidatos}

    opciones = []
    for orden, f, bloques in elegidos:
        claves = _claves_seccion(pregunta, f)
        for b in bloques:
            raices_enc = _raices(_sin_numero(b["encabezado"]))
            comunes = claves & raices_enc
            if not comunes:
                continue
            fuerte = bool(comunes & FUERTES)
            total = sum(peso(r) for r in comunes) + (1.5 if fuerte else 0)
            if len(comunes) == 1 and not fuerte and total < 2.5:
                continue  # coincidencia débil (por ejemplo solo "quién"): mejor el modelo
            total += 0.5 if (f["ruta"], b["encabezado"]) in marcadas else 0
            total += 0.3 * (b["nivel"] == 3) - 0.4 * orden
            opciones.append((total, len(comunes), f, b))
    if not opciones:
        return None
    opciones.sort(key=lambda x: x[:2], reverse=True)
    mejor, n, f, b = opciones[0]
    # Subsecciones hermanas que empatan (por ejemplo "Citación a audiencia" y "Desarrollo de
    # la audiencia") se muestran juntas.
    juntas = [b]
    for total, n2, f2, b2 in opciones[1:]:
        if (f2["ruta"] == f["ruta"] and b2["nivel"] == 3 and b["nivel"] == 3
                and b2["padre"] == b["padre"] and mejor - total < 0.35 and len(juntas) < 3):
            juntas.append(b2)
    return f, juntas


def pasos_literales(pregunta, docs):
    """Pregunta por un procedimiento -> pasos del documento."""
    if not PIDE_PROCEDIMIENTO.search(_normal(pregunta)):
        return None
    opciones = []
    for orden, (score, f) in enumerate(docs[:4]):
        if f.get("tipo") == "moc":
            continue
        claves = _claves_seccion(pregunta, f)
        for b in bloques_de(cuerpo_de(f["ruta"])):
            if NO_ES_PROCEDIMIENTO.search(_normal(b["encabezado"])):
                continue
            if not (pasos_de(b) or tiene_lista_numerada(b)):
                continue
            comunes = claves & _raices(_sin_numero(b["encabezado"]))
            estructurado = pasos_de(b) is not None
            opciones.append((len(comunes) + (2 if estructurado else 0), -orden, b["nivel"] == 2, f, b))
    if not opciones:
        return None
    opciones.sort(key=lambda x: x[:3], reverse=True)
    n, orden, _, f, b = opciones[0]
    n -= 2 if pasos_de(b) is not None else 0
    # Sin coincidencia en el encabezado, solo vale si es el documento principal.
    if n == 0 and orden != 0:
        return None
    return f, b


def _recortar(texto, limite=MAX_LITERAL):
    if len(texto) <= limite:
        return texto, False
    corte = texto.rfind("\n\n", 0, limite)
    return texto[: corte if corte > limite // 2 else limite].rstrip(), True


def mostrar_bloque(f, b):
    """Una sección del documento, lista para Slack."""
    nombre = f"{f['doc_id'] + ' · ' if f['doc_id'] else ''}{f['titulo']}"
    titulo = _sin_numero(b["encabezado"])
    if b["padre"] and not es_generico(b["padre"]):
        titulo = f"{_sin_numero(b['padre'])} › {titulo}"
    pasos = pasos_de(b)
    if pasos:
        intro = _sin_codigo(b["propio"])
        intro = "\n".join(l for l in intro.splitlines()
                          if l.strip() and not l.strip().startswith("|")).strip()
        lista = "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, 1))
        texto = f"*{titulo}* según _{nombre}_:\n"
        if intro and len(intro) < 600:
            texto += f"{intro}\n\n"
        texto += lista
        if b["hijos"]:
            texto += "\n\n_Pregúntame por un paso concreto para ver su detalle._"
        return texto
    contenido, recortado = _recortar(b["contenido"])
    texto = f"*{titulo}* según _{nombre}_:\n{contenido}"
    if recortado:
        texto += f"\n\n_(Continúa en el documento: <{enlace_github(f['ruta'])}|abrir {f['doc_id'] or 'documento'}>.)_"
    return texto


def ficha_formato(f, cuerpo, omitir=None):
    """Datos clave de un formato, copiados del documento. `omitir`: sección ya mostrada."""
    omitir = _normal(_sin_numero(omitir or ""))
    lineas = []
    quien = seccion(cuerpo, r"(\d+\.\s*)?quien lo diligencia.*")
    plazo = seccion(cuerpo, r"(\d+\.\s*)?plazos?.*")
    if not plazo:
        m = re.search(r"[^.\n]*(?:d[ií]as? h[aá]bil(?:es)?|mismo d[ií]a|anticipaci[oó]n)[^.\n]*\.",
                      cuerpo, re.I)
        plazo = m.group(0).strip() if m else None
    descarga = seccion(cuerpo, r"descarga", r"archivo original")
    if quien and not omitir.startswith("quien"):
        lineas.append(f"*Quién lo diligencia:* {_recortar(' '.join(quien.split()), 700)[0]}")
    if plazo and not omitir.startswith("plazo"):
        lineas.append(f"*Plazo:* {_recortar(' '.join(plazo.split()), 500)[0]}")
    if descarga:
        enlace = re.search(r"\]\(([^)]+)\)", descarga)
        if enlace and not enlace.group(1).startswith("http"):
            ruta_archivo = f"{f['ruta'].rsplit('/', 1)[0]}/{enlace.group(1)}"
            nombre = enlace.group(1).rsplit("/", 1)[-1]
            lineas.append(f"*Descarga:* <{enlace_github(ruta_archivo)}|{nombre}>")
        else:
            lineas.append(f"*Archivo:* {_recortar(' '.join(descarga.split()), 300)[0]}")
    return "\n".join(lineas)


def respuesta_formato(f, inicio="Para esto se usa el"):
    cuerpo = cuerpo_de(f["ruta"])
    tipo = "procedimiento" if f.get("tipo") == "procedimiento" else "formato"
    texto = f"{inicio} {tipo} *{f['doc_id']} · {f['titulo']}*."
    para_que = seccion(cuerpo, r"para que sirve", r"(\d+\.\s*)?objetivo")
    if para_que:
        texto += f"\n\n{_recortar(' '.join(para_que.split()), 800)[0]}"
    ficha = ficha_formato(f, cuerpo)
    if ficha:
        texto += f"\n\n{ficha}"
    return texto


# ---------------------------------------------------------------- armado final

FILA_SEP = re.compile(r"^\s*\|?\s*:?-{3,}")


# Líneas que empiezan un bloque propio: listas, títulos, tablas, código y etiquetas en
# negrita como "*Plazo:*" (las fichas de formato), que no deben unirse a la línea anterior.
INICIO_BLOQUE = re.compile(r"^\s*([-*+•]\s|\d+[.)]\s|#|\||>|```|\*\*.*\*\*\s*$|\*[^*\s][^*]*:\*|_)")


def _desenvolver(texto):
    """Une las líneas cortadas a 72 columnas por la conversión desde Word/PDF."""
    salida, en_codigo = [], False
    for linea in texto.splitlines():
        if linea.strip().startswith("```"):
            en_codigo = not en_codigo
            salida.append(linea)
            continue
        previa = salida[-1] if salida else ""
        continua = (not en_codigo and linea.strip() and previa.strip()
                    and not INICIO_BLOQUE.match(linea) and not previa.strip().startswith(("|", "```", "#"))
                    and not re.match(r"^\s*\*\*.*\*\*\s*$", previa)
                    and not previa.rstrip().endswith((":", "_:")))
        if continua:
            salida[-1] = previa.rstrip() + " " + linea.strip()
        else:
            salida.append(linea)
    texto = "\n".join(salida)
    return re.sub(r"(?m)^(\s*)[-*+]\s{2,}", r"\1- ", texto)


def a_slack(texto):
    """Markdown de Obsidian -> formato de Slack: tablas a viñetas, [[enlaces]] y **negritas**."""
    texto = _desenvolver(texto)
    salida, encabezados = [], None
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if FILA_SEP.match(linea):
            continue
        es_fila = linea.strip().startswith("|") and linea.strip().endswith("|")
        if not es_fila:
            encabezados = None
            salida.append(linea)
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        siguiente = lineas[i + 1] if i + 1 < len(lineas) else ""
        if FILA_SEP.match(siguiente):
            encabezados = celdas  # fila de encabezado de la tabla
            continue
        if len(celdas) <= 2 or not encabezados:
            salida.append("• " + " — ".join(c for c in celdas if c))
        else:
            resto = "; ".join(f"{encabezados[k]}: {c}" for k, c in enumerate(celdas[1:], 1)
                              if c and k < len(encabezados))
            salida.append(f"• *{celdas[0]}* — {resto}")
    texto = "\n".join(salida)
    texto = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", texto)
    texto = re.sub(r"\[\[([^\]]+)\]\]", r"`\1`", texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"*\1*", texto)
    texto = re.sub(r"(?m)^#{1,6}\s+(.+)$", r"*\1*", texto)
    return texto


def armar(texto, fragmentos):
    """Agrega avisos de estado y fuentes con enlace. Lo arma el código, no el modelo."""
    texto = a_slack(texto)
    vistos, fuentes, avisos = set(), [], []
    for f in fragmentos:
        if f["ruta"] in vistos:
            continue
        vistos.add(f["ruta"])
        etiqueta = f"{f['doc_id']} · {f['titulo']}" if f["doc_id"] else f["titulo"]
        fuentes.append(f"• <{enlace_github(f['ruta'])}|{etiqueta}> (estado: {f['estado'] or 'sin estado'})")
        if str(f["estado"]).lower() in ESTADOS_NO_VIGENTES:
            avisos.append(f"⚠️ *{f['titulo']}* está en estado *{f['estado']}*: "
                          "valídalo con el responsable antes de usarlo.")
        etiquetas = meta_de(f["ruta"]).get("etiquetas") or []
        if "prueba" in _normal(f["titulo"]) or "prueba" in [_normal(str(e)) for e in etiquetas]:
            avisos.append(f"⚠️ *{f['titulo']}* es un documento de prueba o ficticio.")
    partes = [texto]
    if avisos:
        partes.append("\n".join(avisos))
    partes.append("*Fuentes:*\n" + "\n".join(fuentes))
    return "\n\n".join(partes)


def contexto_para_modelo(pregunta, candidatos, docs):
    """Secciones de los mejores documentos, las más relevantes primero, sin pasar el límite."""
    tope = docs[0][0]
    elegidos = [f for s, f in docs if s >= tope - MARGEN_DOC][:2]
    claves = _palabras(pregunta)
    bloques, usado = [], 0
    for f in elegidos:
        unidades = []
        for b in bloques_de(cuerpo_de(f["ruta"]) or f["texto"]):
            if es_generico(b["encabezado"]) and b["encabezado"] != "Introducción":
                continue
            texto = b["propio"] if b["nivel"] == 2 else b["contenido"]
            if texto.strip():
                unidades.append((b["encabezado"], texto[:MAX_UNIDAD]))
        # Secciones que la búsqueda marcó para este documento, en orden de puntaje.
        marcadas = [fr["seccion"] for _, fr in candidatos if fr["ruta"] == f["ruta"]]

        def prioridad(item):
            e, c = item
            rango = marcadas.index(e) if e in marcadas else len(marcadas) + 1
            return (rango, -len(claves & _palabras(f"{e} {c}")))

        partes = []
        for e, c in sorted(unidades, key=prioridad):
            pedazo = f"## {e}\n{c}"
            if usado + len(pedazo) > MAX_CONTEXTO and partes:
                break
            partes.append(pedazo)
            usado += len(pedazo)
        meta = meta_de(f["ruta"])
        sin_valor = {"", "por definir", "pendiente", "n/a", "na"}
        datos = ([f"responsable: {meta['responsable']}"]
                 if str(meta.get("responsable", "")).strip().lower() not in sin_valor else [])
        if meta.get("servicios"):
            serv = meta["servicios"]
            datos.append(f"servicios: {', '.join(serv) if isinstance(serv, list) else serv}")
        encabezado = (f"[{f['doc_id'] or 'sin id'} | {f['titulo']} | tipo: {f.get('tipo') or 'nota'} | "
                      f"estado: {f['estado'] or 'sin estado'}{' | ' + ' | '.join(datos) if datos else ''}]")
        bloques.append(encabezado + "\n" + "\n\n".join(partes))
        if usado >= MAX_CONTEXTO:
            break
    return "\n\n=====\n\n".join(bloques), elegidos


def limpiar_citas(texto):
    """Quita citas "(ADR-0001)" repetidas al final de las frases y une frases sueltas."""
    cita = r"\s*\((?:[A-Z]{2,4}-[A-Z0-9-]+(?:,\s*)?)+[^)]{0,80}\)"
    if len(re.findall(cita, texto)) > 1:
        texto = re.sub(cita + r"(?=\s*[.\n]|\s*$)", "", texto)
    # Párrafos de una sola frase -> un solo párrafo (las listas y tablas se respetan).
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    if len(bloques) > 1 and all("\n" not in b and not re.match(r"^([-*•|]|\d+[.)])", b)
                                for b in bloques):
        texto = " ".join(bloques)
    return re.sub(r"\s+\.", ".", texto).strip()


def responder(pregunta):
    """Devuelve el mensaje listo para Slack (formato mrkdwn)."""
    candidatos = recuperar(pregunta)
    if not candidatos:
        return f"No encontré documentación que responda esto en la bóveda.\n{ESCALAR}"
    mejor = candidatos[0][0]
    candidatos = [(s, f) for s, f in candidatos if s >= mejor - MARGEN * 2]
    docs = documentos(candidatos)
    principal = docs[0][1]
    es_formato = principal.get("tipo") in {"formato", "procedimiento"}

    # 0. "¿Qué formato lleno?": la respuesta sale entera del formato.
    if principal.get("tipo") == "formato" and CUAL_FORMATO.search(pregunta):
        return armar(respuesta_formato(principal), [principal])

    # 1. Procedimientos (runbooks, etapas, pasos de un procedimiento).
    literal = pasos_literales(pregunta, docs)
    # 2. Una sección o subsección concreta nombrada en la pregunta.
    if not literal:
        literal = seccion_literal(pregunta, docs, candidatos)
    if literal:
        f, bloques = literal[0], (literal[1] if isinstance(literal[1], list) else [literal[1]])
        texto = "\n\n".join(mostrar_bloque(f, b) for b in bloques)
        if f.get("tipo") == "formato":
            extra = ficha_formato(f, cuerpo_de(f["ruta"]), omitir=bloques[0]["encabezado"])
            if extra:
                texto += f"\n\n*{f['doc_id']} · {f['titulo']}*\n{extra}"
        return armar(texto, [f])

    # 3. "¿Qué formato uso?": respuesta completa desde el documento del formato.
    if principal.get("tipo") == "formato" and PIDE_FORMATO.search(pregunta):
        return armar(respuesta_formato(principal), [principal])

    # 4. El modelo, con secciones completas y reglas estrictas.
    contexto, elegidos = contexto_para_modelo(pregunta, candidatos, docs)
    texto = llm.chat(SISTEMA, f"Secciones de documentación:\n\n{contexto}\n\nPregunta: {pregunta}",
                     num_ctx=max(config.CHAT_CTX, 6144))
    texto = re.sub(r"^\s*\[[^\]\n]*\|[^\]\n]*\]\s*", "", texto).strip()  # encabezado interno copiado
    texto = limpiar_citas(texto)

    if NO_ENCONTRE in texto.lower():
        if es_formato:
            return armar("No encontré ese dato exacto en la documentación.\n\n"
                         + respuesta_formato(principal, "Lo más relacionado es el"), [principal])
        return f"No encontré documentación que responda esto.\n{ESCALAR}"

    if principal.get("tipo") == "formato":
        ficha = ficha_formato(principal, cuerpo_de(principal["ruta"]))
        if ficha:
            texto += f"\n\n*{principal['doc_id']} · {principal['titulo']}*\n{ficha}"
    return armar(texto, elegidos)
