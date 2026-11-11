"""Fusión exacta y enriquecimiento auxiliar del extractor congelado, sin ajustes."""

import json
import subprocess

import pandas as pd

from mtx import config
from mtx.adaptadores_kit import sha256_archivo
from mtx.enriquecimiento import enriquecer
from mtx.evaluacion import escribir_conservando
from mtx.evaluacion_ie import validar_entidades, verificar_cierre
from mtx.fusion import fusionar
from mtx.ner_posproceso_v2 import VERSION, posprocesar_auditado


def main():
    raiz = config.RAIZ
    ctx, _ = verificar_cierre(raiz)
    reglas = pd.read_csv(raiz / "salida/06_entidades_reglas.csv", keep_default_na=False)
    modelo = json.loads((raiz / "data/modelo_ner.json").read_text())
    parametros = next(p for p in config.cargar_yaml("ner.yaml")["modelos"]
                      if p["repo_id"] == modelo["modelo"] and p["revision"] == modelo["revision"])
    pred = pd.read_csv(raiz / f"salida/entidades_{parametros['slug']}.csv", keep_default_na=False)
    oficial, unica, publica, solapes = fusionar(reglas, pred, ctx["ranking"], ctx["pasajes"])
    validar_entidades(oficial, ctx["pasajes"])
    equivalencias = {}
    for f in pd.read_csv(raiz / "config/gazetteer_extendido.csv", keep_default_na=False).itertuples():
        for alias in [f.nombre, f.siglas, *f.variantes.split("|")]:
            if alias:
                equivalencias[alias.casefold()] = f.nombre
    puntajes = {}
    for f in ctx["pasajes"].itertuples():
        ruta = raiz / "data/cache_ner" / (
            f"{parametros['slug']}@{parametros['revision'][:12]}") / f"{f.passage_id}.json"
        datos = json.loads(ruta.read_text())
        if datos["texto_sha256"] != sha256_archivo_texto(f.texto):
            raise ValueError("Caché distinta del texto canónico")
        procesadas, _, _ = posprocesar_auditado(f.texto, datos["crudas"], f.passage_id)
        for e in procesadas:
            puntajes[(f.passage_id, e["tipo"], e["inicio"], e["fin"])] = e["confianza"]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip()
    # Versión derivada de código y reglas: estable al añadir commits solo de datos/docs.
    import hashlib
    fuentes_version = ["src/mtx/fusion.py", "src/mtx/enriquecimiento.py",
                       "src/mtx/ner_posproceso_v2.py", "src/mtx/ner_modelo.py",
                       "src/mtx/reglas.py", "config/ner.yaml"]
    version = hashlib.sha256(json.dumps({p: sha256_archivo(raiz/p) for p in
                                       fuentes_version}, sort_keys=True).encode()).hexdigest()
    enriquecidas = enriquecer(publica, ctx["pasajes"], modelo["modelo"], modelo["revision"],
                             version, equivalencias, puntajes)
    for nombre, tabla in [("entidades.csv", oficial), ("salida/entidades.csv", oficial),
            ("salida/entidades_unicas.csv", unica),
            ("salida/entidades_enriquecidas.csv", enriquecidas),
            ("salida/08_solapes_parciales.csv", solapes)]:
        escribir_conservando(raiz / nombre, tabla.to_csv(index=False, lineterminator="\n").encode())
    entradas = ["salida/06_entidades_reglas.csv", f"salida/entidades_{parametros['slug']}.csv",
                "data/modelo_ner.json", "config/ner.yaml", "src/mtx/fusion.py",
                "src/mtx/enriquecimiento.py", "scripts/08_extraer.py",
                "src/mtx/ner_posproceso_v2.py", "scripts/07c_ner_auditado.py"]
    manifiesto = {"esquema": 1, "productor": "scripts/08_extraer.py", "commit": commit,
        "modelo": modelo, "version_posproceso": VERSION, "posterior_D15": True, "entradas": {p: sha256_archivo(raiz/p) for p in entradas},
        "pasajes": ctx["pasajes"].passage_id.nunique(), "entidades": len(oficial),
        "entidades_unicas": len(unica), "discrepancias": len(solapes)}
    (raiz/"salida/08_manifiesto_extraccion.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2)+"\n")


def sha256_archivo_texto(texto):
    import hashlib
    return hashlib.sha256(texto.encode()).hexdigest()


if __name__ == "__main__":
    main()
