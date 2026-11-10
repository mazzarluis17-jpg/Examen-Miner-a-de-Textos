"""Alcance auditable previo a D15: presencia léxica, nunca decisiones de entidad."""
import json
import re
from pathlib import Path

import pandas as pd

from mtx import adaptadores_kit as kit
from mtx.ambito_ie import cargar_ambito


def analizar(candidatos, pasajes, entradas):
    """Propone coincidencias adicionales en cuerpos; audita también las marcas."""
    textos = []
    for f in pasajes.itertuples():
        cubiertos = []
        for nombre, sigla in entradas:
            flags = 0 if sigla and len(nombre) <= 5 else re.IGNORECASE
            cubiertos.extend((m.start(), m.end()) for m in re.finditer(
                r"(?<!\w)" + re.escape(nombre) + r"(?!\w)", f.texto, flags))
        textos.append((f, cubiertos))
    filas, ocurrencias = [], []
    for candidato in candidatos.itertuples(index=False):
        observadas = {}
        formas = [(candidato.sigla, 0)]
        if candidato.nombre_propuesto:
            formas.append((candidato.nombre_propuesto, re.IGNORECASE))
        for f, cubiertos in textos:
            for forma, flags in formas:
                for m in re.finditer(r"(?<!\w)" + re.escape(forma) + r"(?!\w)", f.texto, flags):
                    clave = (f.passage_id, m.start(), m.end())
                    observadas[clave] = {
                        "sigla": candidato.sigla, "passage_id": f.passage_id,
                        "doc_id": f.doc_id, "inicio": m.start(), "fin": m.end(),
                        "en_marca": m.end() <= f.inicio_cuerpo,
                        "cubierta": any(a <= m.start() and m.end() <= b for a, b in cubiertos),
                        "contexto": f.texto[max(0, m.start()-60):m.end()+60],
                    }
        obs = list(observadas.values())
        nuevas = [o for o in obs if not o["cubierta"]]
        cuerpo = [o for o in nuevas if not o["en_marca"]]
        motivo = ("propuesto_revision" if cuerpo else "adicionales_solo_en_marca" if nuevas else
                  "coincidencias_ya_cubiertas" if obs else "sin_coincidencias_en_ambito")
        filas.append({**candidato._asdict(), "estado_alcance": motivo,
                      "ocurrencias_ambito": len(obs), "ocurrencias_adicionales": len(nuevas),
                      "adicionales_cuerpo": len(cuerpo),
                      "adicionales_marca": len(nuevas)-len(cuerpo),
                      "pasajes_adicionales": len({o["passage_id"] for o in nuevas}),
                      "documentos_adicionales": len({o["doc_id"] for o in nuevas}),
                      "ejemplo_ambito": cuerpo[0]["contexto"] if cuerpo else ""})
        ocurrencias.extend(obs)
    auditoria = pd.DataFrame(filas)
    seleccion = auditoria[auditoria.estado_alcance.eq("propuesto_revision")].sort_values(
        ["adicionales_cuerpo", "pasajes_adicionales", "ocurrencias_adicionales", "sigla"],
        ascending=[False, False, False, True], kind="stable").reset_index(drop=True)
    cols = ["sigla", "passage_id", "doc_id", "inicio", "fin", "en_marca", "cubierta", "contexto"]
    return seleccion, auditoria, pd.DataFrame(ocurrencias, columns=cols)


def preparar(raiz: Path):
    """Solo genera propuestas y métricas, conservando el archivo original de minería."""
    if (raiz / "config/gazetteer_revision.json").exists():
        raise ValueError("Existe revisión humana: no cambiar el alcance sin reconciliación explícita")
    _, pasajes = cargar_ambito(raiz)
    candidatos = pd.read_csv(raiz / "salida/06_siglas_candidatas.csv", keep_default_na=False)
    rutas = ["kit/gazetteer_dependencias.csv", "config/gazetteer_prescrito.csv", "config/gazetteer_loc.csv"]
    entradas = []
    for ruta in rutas:
        for f in pd.read_csv(raiz/ruta, keep_default_na=False).to_dict("records"):
            for campo in ("nombre", "variantes", "siglas"):
                entradas.extend((s.strip(), campo == "siglas") for s in f.get(campo, "").split("|") if s.strip())
    seleccion, auditoria, obs = analizar(candidatos, pasajes, entradas)
    for nombre, tabla in [("06_revision_alcance.csv", seleccion),
                           ("06_revision_auditoria.csv", auditoria), ("06_revision_ocurrencias.csv", obs)]:
        tabla.to_csv(raiz/"salida"/nombre, index=False, lineterminator="\n")
    fuentes = rutas + ["salida/06_siglas_candidatas.csv", "data/mejor_modelo.json",
                       "salida/ranking.csv", "data/pasajes.parquet"]
    informe = {
        "estado": "propuesta_pendiente_aprobacion", "politica": "Revisar todos los candidatos con alguna coincidencia literal adicional EN EL CUERPO (sigla o nombre minado), no contenida en un alias del gazetteer base/prescrito/LOC, dentro del ámbito IR ganador. Coincidencias exclusivas de marca quedan auditadas fuera del alcance. Sin umbral de frecuencia ni clasificación automática.",
        "medida": "Cobertura léxica potencial; no mide entidades correctas, recall ni F1. Incluye marcas y cuerpo.",
        "pasajes_ambito": len(pasajes), "originales": len(candidatos), "propuestos": len(seleccion),
        "siglas_propuestas": seleccion.sigla.tolist(),
        "excluidos_por_motivo": auditoria.loc[auditoria.estado_alcance.ne("propuesto_revision"),
                                               "estado_alcance"].value_counts().to_dict(),
        "ocurrencias_total": len(obs), "ocurrencias_ya_cubiertas": int(obs.cubierta.sum()),
        "ocurrencias_adicionales_propuestas": int((~obs.cubierta & obs.sigla.isin(seleccion.sigla)).sum()),
        "ocurrencias_adicionales_fuera_revision": int((~obs.cubierta & ~obs.sigla.isin(seleccion.sigla)).sum()),
        "adicionales_cuerpo_total": int((~obs.cubierta & ~obs.en_marca).sum()),
        "adicionales_cuerpo_fuera_revision": int((~obs.cubierta & ~obs.en_marca & ~obs.sigla.isin(seleccion.sigla)).sum()),
        "adicionales_marca_total": int((~obs.cubierta & obs.en_marca).sum()),
        "pasajes_con_coincidencias": obs.passage_id.nunique(),
        "pasajes_con_coincidencias_adicionales": obs.loc[~obs.cubierta, "passage_id"].nunique(),
        "pasajes_cuerpo_adicional": obs.loc[~obs.cubierta & ~obs.en_marca, "passage_id"].nunique(),
        "rechazados_humanos": 0,
        "fuentes": {p: kit.sha256_archivo(raiz/p) for p in fuentes},
        "sha256_subconjunto": kit.sha256_archivo(raiz/"salida/06_revision_alcance.csv"),
        "sha256_auditoria": kit.sha256_archivo(raiz/"salida/06_revision_auditoria.csv"),
        "sha256_ocurrencias": kit.sha256_archivo(raiz/"salida/06_revision_ocurrencias.csv"),
    }
    (raiz/"salida/06_revision_alcance.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2)+'\n')
    return informe
