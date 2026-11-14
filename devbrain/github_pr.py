"""Crea una rama, sube el post-mortem, lo enlaza en el MOC y abre el Pull Request."""
import base64
import re
from urllib.parse import quote

import requests

from . import config

API = "https://api.github.com"


def _h():
    return {"Authorization": f"Bearer {config.requerido('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _req(metodo, ruta, **kw):
    r = requests.request(metodo, f"{API}/repos/{config.GITHUB_REPO}{ruta}", headers=_h(), timeout=30, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"GitHub {metodo} {ruta}: {r.status_code} {r.text[:300]}")
    return r.json()


def insertar_en_moc(moc, enlace):
    """Agrega '- [[enlace]]' al final de la lista bajo '## Post-mortems'."""
    if f"[[{enlace}]]" in moc:
        return moc
    linea = f"- [[{enlace}]]: borrador generado por DevBrain, pendiente de revisión."
    lineas = moc.split("\n")
    for i, l in enumerate(lineas):
        if re.match(r"^##\s+Post-mortems\s*$", l, re.I):
            j = i + 1
            while j < len(lineas) and (not lineas[j].strip() or lineas[j].startswith("- ")):
                j += 1
            while j > i + 1 and not lineas[j - 1].strip():
                j -= 1
            lineas.insert(j, linea)
            return "\n".join(lineas)
    return moc.rstrip("\n") + f"\n\n## Post-mortems\n\n{linea}\n"


def abrir_pr(ruta, titulo, contenido, canal):
    base = config.GIT_BRANCH
    sha_base = _req("GET", f"/git/ref/heads/{base}")["object"]["sha"]
    rama = f"postmortem/{ruta.rsplit('/', 1)[-1][:-3]}"
    for intento in range(1, 6):
        try:
            _req("POST", "/git/refs", json={"ref": f"refs/heads/{rama}", "sha": sha_base})
            break
        except RuntimeError as e:
            if "Reference already exists" not in str(e) or intento == 5:
                raise
            rama = f"{rama.rsplit('-v', 1)[0]}-v{intento + 1}"

    _req("PUT", f"/contents/{quote(ruta)}", json={
        "message": f"Post-mortem: {titulo}",
        "content": base64.b64encode(contenido.encode("utf-8")).decode(),
        "branch": rama})

    try:
        moc = _req("GET", f"/contents/{quote(config.INCIDENTS_MOC)}", params={"ref": rama})
        texto = base64.b64decode(moc["content"]).decode("utf-8")
        nuevo = insertar_en_moc(texto, ruta.rsplit("/", 1)[-1][:-3])
        if nuevo != texto:
            _req("PUT", f"/contents/{quote(config.INCIDENTS_MOC)}", json={
                "message": "Enlazar post-mortem en MOC-Incidentes",
                "content": base64.b64encode(nuevo.encode("utf-8")).decode(),
                "branch": rama, "sha": moc["sha"]})
    except RuntimeError:
        pass  # Si el MOC no existe, el PR sigue siendo válido; el revisor lo enlaza a mano.

    pr = _req("POST", "/pulls", json={
        "title": f"Post-mortem: {titulo}",
        "head": rama, "base": base,
        "body": (f"Borrador generado por DevBrain desde #{canal}.\n\n"
                 "Antes de aprobar:\n"
                 "- [ ] Comparar la línea de tiempo con el historial del canal\n"
                 "- [ ] Confirmar la causa raíz\n"
                 "- [ ] Asignar responsables y fechas a las acciones correctivas\n"
                 "- [ ] Completar `servicios` en los metadatos\n"
                 "- [ ] Cambiar `estado` a `vigente`")})
    return pr["html_url"]
