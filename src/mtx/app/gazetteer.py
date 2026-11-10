"""Persistencia de decisiones humanas de gazetteer, aislada de los juicios H3."""

import csv
import fcntl
import hashlib
import io
import json
import subprocess
from datetime import UTC, datetime

from mtx.app.componentes import ErrorAnotacion, atomico

COLUMNAS = ["nombre", "variantes", "siglas", "tipo", "etiqueta", "origen", "evidencia"]


def digest(datos):
    return hashlib.sha256(datos).hexdigest()


def congelado(raiz):
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "refs/tags/reglas-congeladas"],
            cwd=raiz,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def cargar(raiz):
    ruta = raiz / "config/gazetteer_revision.json"
    return json.loads(ruta.read_text()) if ruta.exists() else {"revision": 0, "decisiones": {}}


def fuentes(raiz):
    rutas = [
        "salida/06_siglas_candidatas.csv",
        "kit/gazetteer_dependencias.csv",
        "config/gazetteer_prescrito.csv",
        "config/gazetteer_loc.csv",
    ]
    propuesta = raiz / "salida/06_revision_alcance.json"
    if propuesta.exists():
        candidatos_revision(raiz)  # bloquea si falta aprobación explícita o hay hashes obsoletos
        datos = json.loads(propuesta.read_text())
        rutas.extend(["salida/06_revision_alcance.json", "salida/06_revision_alcance.csv",
                      "salida/06_revision_auditoria.csv", "salida/06_revision_ocurrencias.csv",
                      "config/alcance_gazetteer_aprobacion.json", *datos["fuentes"]])
    return {p: digest((raiz / p).read_bytes()) for p in sorted(set(rutas))}


def candidatos_revision(raiz):
    """Alcance aprobado; las exclusiones técnicas nunca se convierten en rechazos."""
    propuesta = raiz / "salida/06_revision_alcance.json"
    if not propuesta.exists():
        return list(csv.DictReader((raiz / "salida/06_siglas_candidatas.csv").open()))
    try:
        datos = json.loads(propuesta.read_text())
        aprobado = json.loads((raiz / "config/alcance_gazetteer_aprobacion.json").read_text())
        if (not aprobado.get("aprobado_por") or not aprobado.get("fecha") or
                aprobado.get("sha256_propuesta") != digest(propuesta.read_bytes())):
            raise ErrorAnotacion("Alcance sin aprobación vigente")
        for ruta, clave in [("06_revision_alcance.csv", "sha256_subconjunto"),
                            ("06_revision_auditoria.csv", "sha256_auditoria"),
                            ("06_revision_ocurrencias.csv", "sha256_ocurrencias")]:
            if digest((raiz/"salida"/ruta).read_bytes()) != datos[clave]:
                raise ErrorAnotacion("Alcance obsoleto: conservar revisión")
        if any(digest((raiz/p).read_bytes()) != h for p, h in datos["fuentes"].items()):
            raise ErrorAnotacion("Fuentes del alcance obsoletas")
        return list(csv.DictReader((raiz / "salida/06_revision_alcance.csv").open()))
    except FileNotFoundError as exc:
        raise ErrorAnotacion("Pendiente aprobación explícita del alcance de revisión") from exc


def exportar(decisiones):
    archivo = io.StringIO(newline="")
    w = csv.DictWriter(archivo, fieldnames=COLUMNAS, lineterminator="\n")
    w.writeheader()
    for sigla, d in sorted(decisiones.items()):
        if d["accion"] == "descartar":
            continue
        w.writerow(
            {
                "nombre": d["nombre"],
                "variantes": d["variantes"],
                "siglas": sigla,
                "tipo": "organizacion" if d["etiqueta"] == "ORG" else "lugar",
                "etiqueta": d["etiqueta"],
                "origen": "minado",
                "evidencia": d["evidencia"],
            }
        )
    return archivo.getvalue().encode()


def guardar(raiz, estado, huellas, sigla, accion, nombre="", etiqueta="", variantes=""):
    """Cada acción humana: cerrojo, revisión, respaldo y publicación atómica."""
    if accion not in {"aceptar", "descartar"}:
        raise ErrorAnotacion("Acción de revisión inválida")
    if accion == "aceptar" and (not nombre.strip() or etiqueta not in {"ORG", "LOC"}):
        raise ErrorAnotacion("Indica nombre y etiqueta ORG/LOC")
    config = raiz / "config"
    with (config / ".gazetteer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if congelado(raiz):
            raise ErrorAnotacion("Reglas congeladas: escritura bloqueada")
        actual = cargar(raiz)
        if actual != estado:
            raise ErrorAnotacion("Editado desde otra pestaña: recarga antes de guardar")
        if fuentes(raiz) != huellas or (actual.get("fuentes") and actual["fuentes"] != huellas):
            raise ErrorAnotacion("Candidatos o gazetteers obsoletos: conservar revisión anterior")
        ruta = config / "gazetteer_extendido.csv"
        if actual.get("sha256_exportacion") and (
            not ruta.exists() or digest(ruta.read_bytes()) != actual["sha256_exportacion"]
        ):
            raise ErrorAnotacion("Exportación modificada o guardado interrumpido: revisar respaldo")
        candidatos = candidatos_revision(raiz)
        candidato = next((c for c in candidatos if c["sigla"] == sigla), None)
        if candidato is None:
            raise ErrorAnotacion("Sigla fuera de candidatos")
        decisiones = dict(actual["decisiones"])
        decisiones[sigla] = {
            "accion": accion,
            "nombre": nombre.strip(),
            "etiqueta": etiqueta,
            "variantes": variantes,
            "evidencia": candidato.get("ejemplo_ambito") or candidato["ejemplo"],
        }
        contenido = exportar(decisiones)
        nuevo = {
            "revision": actual["revision"] + 1,
            "decisiones": decisiones,
            "fuentes": huellas,
            "sha256_exportacion": digest(contenido),
        }
        historial = config / "historial_gazetteer"
        historial.mkdir(exist_ok=True)
        for p in [ruta, config / "gazetteer_revision.json"]:
            if p.exists():
                atomico(historial / f"{actual['revision']}_{p.name}", p.read_bytes())
        # Diario antes del CSV: interrupciones bloquean, sin sobrescritura silenciosa.
        atomico(
            config / "gazetteer_revision.json",
            (json.dumps(nuevo, ensure_ascii=False, indent=2) + "\n").encode(),
        )
        atomico(ruta, contenido)
        return nuevo


def cerrar_revision(raiz, estado, huellas, persona):
    """Solo invocada por el botón explícito del alumno tras revisar cada candidato."""
    with (raiz / "config/.gazetteer.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (
            congelado(raiz)
            or cargar(raiz) != estado
            or fuentes(raiz) != huellas
            or estado.get("fuentes") != huellas
        ):
            raise ErrorAnotacion("Estado cambiado o congelado: recarga")
        candidatos = candidatos_revision(raiz)
        if {c["sigla"] for c in candidatos} != set(estado["decisiones"]) or not persona.strip():
            raise ErrorAnotacion("Faltan candidatos por revisar o nombre del revisor")
        ruta = raiz / "config/gazetteer_extendido.csv"
        if digest(ruta.read_bytes()) != estado["sha256_exportacion"]:
            raise ErrorAnotacion("Exportación incompatible")
        aprobacion = {
            "aprobado_por": persona.strip(),
            "fecha": datetime.now(UTC).isoformat(),
            "fuentes": huellas,
            "sha256_extendido": digest(ruta.read_bytes()),
            "candidatos_revisados": len(estado["decisiones"]),
            "fuera_alcance_no_rechazados": len(list(csv.DictReader(
                (raiz / "salida/06_siglas_candidatas.csv").open()))) - len(candidatos),
        }
        atomico(
            raiz / "config/gazetteer_aprobacion.json",
            (json.dumps(aprobacion, ensure_ascii=False, indent=2) + "\n").encode(),
        )
