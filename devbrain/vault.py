"""Lectura de la bóveda: separa metadatos YAML y divide cada nota por secciones."""
import re
import uuid
from pathlib import Path

EXCLUIDAS = {".obsidian", ".github", ".git", ".trash", "adjuntos", "05-plantillas",
             "devbrain", "scripts", "src", ".venv", "venv", "node_modules", "site-packages"}
MAX_CHUNK = 1500


def _limpiar(valor):
    valor = valor.strip().replace("\\[", "[").replace("\\]", "]")
    while len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1].strip()
    return valor


def parse_frontmatter(texto):
    """Lee el bloque YAML simple del inicio. Acepta listas en línea [a, b], en bloque (- a)
    y valores que continúan en la línea siguiente. Devuelve (metadatos, cuerpo normalizado)."""
    texto = texto.replace("\r\n", "\n").lstrip("\ufeff")
    meta = {}
    if not texto.startswith("---\n"):
        return meta, normalizar(texto)
    fin = texto.find("\n---", 4)
    if fin == -1:
        return meta, normalizar(texto)
    clave_lista = clave_escalar = None
    for linea in texto[4:fin].splitlines():
        if not linea.strip():
            continue
        item = re.match(r"^\s*-\s+(.*)$", linea)
        if item and clave_lista:
            if isinstance(meta.get(clave_lista), list):
                meta[clave_lista].append(_limpiar(item.group(1)))
            continue
        if linea.startswith((" ", "\t")):
            if clave_escalar and isinstance(meta.get(clave_escalar), str):
                meta[clave_escalar] = f"{meta[clave_escalar]} {_limpiar(linea)}".strip()
            continue
        if ":" not in linea:
            continue
        clave, valor = linea.split(":", 1)
        clave, valor = clave.strip(), valor.strip()
        clave_lista = clave_escalar = None
        if not valor:
            clave_lista = clave
            meta[clave] = []
        elif valor.startswith("[") and valor.endswith("]"):
            meta[clave] = [_limpiar(v) for v in valor[1:-1].split(",") if v.strip()]
        else:
            meta[clave] = _limpiar(valor)
            clave_escalar = clave
    return meta, normalizar(texto[fin + 4:].lstrip("\n"))


BORDE = re.compile(r"^\s*-{20,}\s*$")
COLUMNAS = re.compile(r"^\s*-{3,}(\s+-{3,})+\s*$")


def _tabla_pandoc(lineas):
    """Convierte una tabla de pandoc (multilínea o simple) en una tabla Markdown con barras."""
    sep = next(i for i, l in enumerate(lineas) if COLUMNAS.match(l))
    cols = [(m.start(), m.end()) for m in re.finditer(r"-+", lineas[sep])]
    inicios = [c[0] for c in cols] + [None]

    def celdas(bloque):
        valores = []
        for k in range(len(cols)):
            a, b = inicios[k], inicios[k + 1]
            partes = [(l[a:b] if b else l[a:]).strip() for l in bloque]
            valores.append(" ".join(p for p in partes if p).replace("|", "/"))
        return valores

    encabezado = celdas([l for l in lineas[:sep] if l.strip() and not BORDE.match(l)])
    cuerpo = [l for l in lineas[sep + 1:] if not BORDE.match(l)]
    multilinea = any(BORDE.match(l) for l in lineas[:sep])
    filas, bloque = [], []
    for l in cuerpo + [""]:
        if l.strip() and multilinea:
            bloque.append(l)
            continue
        if l.strip():
            filas.append(celdas([l]))
            continue
        if bloque:
            filas.append(celdas(bloque))
            bloque = []
    salida = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(cols)]
    salida += ["| " + " | ".join(f) + " |" for f in filas if any(f)]
    return salida


def normalizar(cuerpo):
    """Limpia lo que dejan las conversiones desde Word/PDF: tablas de pandoc y [[ ]] escapados."""
    cuerpo = cuerpo.replace("\\[", "[").replace("\\]", "]")
    lineas = cuerpo.split("\n")
    salida, i = [], 0
    while i < len(lineas):
        linea = lineas[i]
        inicio_tabla = None
        if BORDE.match(linea) and any(COLUMNAS.match(l) for l in lineas[i + 1:i + 8]):
            inicio_tabla = i
        elif (linea.strip() and i + 1 < len(lineas) and COLUMNAS.match(lineas[i + 1])
              and not linea.strip().startswith("|")):
            inicio_tabla = i
        if inicio_tabla is None:
            salida.append(linea)
            i += 1
            continue
        j = i + 1
        multilinea = BORDE.match(linea)
        sep_visto = False
        while j < len(lineas):
            if COLUMNAS.match(lineas[j]):
                sep_visto = True
            elif multilinea and sep_visto and BORDE.match(lineas[j]):
                j += 1
                break
            elif not multilinea and sep_visto and not lineas[j].strip():
                break
            j += 1
        try:
            salida.extend(_tabla_pandoc(lineas[i:j]))
        except (StopIteration, IndexError):
            salida.extend(lineas[i:j])
        i = j
    return "\n".join(salida)


def _partir(texto, limite=MAX_CHUNK):
    if len(texto) <= limite:
        return [texto]
    partes, actual = [], ""
    for parrafo in texto.split("\n\n"):
        if actual and len(actual) + len(parrafo) + 2 > limite:
            partes.append(actual)
            actual = parrafo
        else:
            actual = f"{actual}\n\n{parrafo}" if actual else parrafo
    if actual:
        partes.append(actual)
    return partes


def leer_documentos(vault: Path):
    docs = []
    for ruta in sorted(vault.rglob("*.md")):
        rel = ruta.relative_to(vault)
        if any(p in EXCLUIDAS or p.startswith(".") for p in rel.parts):
            continue
        meta, cuerpo = parse_frontmatter(ruta.read_text(encoding="utf-8", errors="ignore"))
        docs.append({"ruta": rel.as_posix(), "meta": meta, "cuerpo": cuerpo})
    return docs


def fragmentar(doc):
    """Un fragmento por sección '## '. Cada fragmento conserva título, id, estado y ruta."""
    meta = doc["meta"]
    titulo = meta.get("titulo") or Path(doc["ruta"]).stem
    secciones = re.split(r"(?m)^(?=###? )", doc["cuerpo"])
    fragmentos = []
    for i, seccion in enumerate(s for s in secciones if s.strip()):
        encabezado = seccion.splitlines()[0].lstrip("#").strip() if seccion.startswith("#") and not seccion.startswith("# ") else "Introducción"
        for j, parte in enumerate(_partir(seccion.strip())):
            fragmentos.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc['ruta']}#{i}.{j}")),
                "ruta": doc["ruta"],
                "doc_id": meta.get("id", ""),
                "titulo": titulo,
                "tipo": meta.get("tipo", ""),
                "estado": meta.get("estado", ""),
                "seccion": encabezado,
                "texto": f"{titulo} — {encabezado}\n\n{parte}",
            })
    return fragmentos
