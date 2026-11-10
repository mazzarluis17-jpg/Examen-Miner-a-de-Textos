"""Guardas de D15: no crea aprobaciones ni decide por el alumno."""

import hashlib
import json
import subprocess

from mtx.app.gazetteer import congelado, fuentes
from mtx.config import cargar_yaml


def verificar_congelacion(raiz):
    """Comprueba aprobaciones humanas vinculadas a contenido y P06, sin leer gold."""

    def sha(ruta):
        return hashlib.sha256((raiz / ruta).read_bytes()).hexdigest()

    try:
        criterio = json.loads((raiz / "config/criterios_anotacion_aprobacion.json").read_text())
        gaz = json.loads((raiz / "config/gazetteer_aprobacion.json").read_text())
        ner = json.loads((raiz / "data/modelo_ner.json").read_text())
        verificacion = json.loads((raiz / "salida/07_verificacion_ner.json").read_text())
    except FileNotFoundError as exc:
        raise ValueError(
            "Pendiente humano/técnico antes de congelar: " + str(exc.filename)
        ) from exc
    if (
        not criterio.get("aprobado_por")
        or not criterio.get("fecha")
        or criterio.get("sha256_criterio") != sha("config/criterios_anotacion.md")
    ):
        raise ValueError("Criterios de anotación sin aprobación vigente del alumno")
    if (
        not gaz.get("aprobado_por")
        or not gaz.get("fecha")
        or gaz.get("fuentes") != fuentes(raiz)
        or gaz.get("sha256_extendido") != sha("config/gazetteer_extendido.csv")
    ):
        raise ValueError("Gazetteer sin revisión humana vigente")
    p = cargar_yaml("ner.yaml", raiz / "config")["modelos"][0]
    if (
        ner.get("revision") != p["revision"]
        or ner.get("modelo") != p["repo_id"]
        or verificacion["revision"] != p["revision"]
    ):
        raise ValueError("NER provisional incompatible con verificación técnica")
    cambios = subprocess.run(
        ["git", "status", "--porcelain"], cwd=raiz, capture_output=True, text=True, check=True
    ).stdout
    if cambios:
        raise ValueError("Hay cambios sin commit: registrar antes de congelar")

    if congelado(raiz):
        resultado = subprocess.run(
            [
                "git",
                "diff",
                "--exit-code",
                "reglas-congeladas",
                "--",
                "src/mtx/reglas.py",
                "src/mtx/normalizacion.py",
                "src/mtx/ner_modelo.py",
                "config",
                "data/modelo_ner.json",
            ],
            cwd=raiz,
            capture_output=True,
            check=False,
        )
        if resultado.returncode:
            raise ValueError("Reglas o configuración distintas de reglas-congeladas")
