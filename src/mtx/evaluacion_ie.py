"""Evaluación IE oficial, complemento de veinte IDs y auditoría de errores."""

import json

import pandas as pd

from mtx import gold
from mtx.fusion import CLAVE, COLUMNAS

TIPOS = ["PER", "ORG", "LOC", "FECHA", "MONTO", "TODOS"]
METODOS = ["regla", "modelo", "combinado"]
ERRORES = ["passage_id", "tipo", "texto_gold", "texto_pred", "inicio", "fin",
           "metodo", "categoria", "fuente", "contexto"]


def verificar_cierre(raiz):
    """No basta existencia del sello: exige fuentes, hashes, revisión y exportación."""
    ctx = gold.cargar_contexto(raiz)
    estado = gold.leer(ctx)
    sello = json.loads((raiz / "anotaciones/cierre_gold.json").read_text())
    if (not sello.get("anotado_por") or not sello.get("fecha") or
            sello.get("revision") != estado["revision"] or
            sello.get("fuentes") != ctx["fuentes"] or
            sello.get("archivos") != estado["archivos"]):
        raise ValueError("Cierre Gold inválido u obsoleto; predicciones bloqueadas")
    errores = gold.validar_gold(ctx["muestras"]["Evaluación"], estado["tablas"]["Evaluación"],
        estado["tablas"]["estados"], ctx["pasajes"], ctx["ranking"])
    if errores:
        raise ValueError("; ".join(errores))
    if (raiz / "gold_entidades.csv").read_bytes() != (
            raiz / "anotaciones/gold_entidades.csv").read_bytes():
        raise ValueError("Exportación oficial Gold distinta de la persistencia")
    return ctx, estado


def validar_entidades(pred, pasajes):
    """Contrato D16 y claves públicas, permitiendo solapes entre fuentes D12."""
    if list(pred.columns) != COLUMNAS or pred.duplicated(["query_id", *CLAVE]).any():
        raise ValueError("Columnas o claves de entidades inválidas")
    textos = pasajes.set_index("passage_id").texto.to_dict()
    for f in pred.itertuples():
        if (f.tipo not in TIPOS[:-1] or f.metodo not in {"regla", "modelo", "ambos"} or
                f.passage_id not in textos or not 0 <= f.inicio < f.fin <= len(
                    textos[f.passage_id]) or textos[f.passage_id][f.inicio:f.fin] != f.texto):
            raise ValueError("Tipo, método o offsets de entidades inválidos")


def vista_metodo(pred, metodo):
    if metodo == "combinado":
        return pred.drop_duplicates(CLAVE)
    return pred[pred.metodo.isin([metodo, "ambos"])].drop_duplicates(CLAVE)


def sin_union_interpalabra(crudas, pasajes):
    """Ablación informativa: mismo recorte/v2 y unión intrapalabra, sin unir palabras."""
    from mtx.ner_posproceso_v2 import posprocesar_auditado

    textos = pasajes.set_index("passage_id").texto.to_dict()
    filas = []
    for (_, pid), grupo in crudas.groupby(["query_id", "passage_id"], sort=True):
        procesadas = []
        for entidad in grupo.sort_values(["inicio", "fin"]).to_dict("records"):
            recortadas, _, _ = posprocesar_auditado(textos[pid], [entidad], pid)
            if not recortadas:
                continue
            e = recortadas[0]
            if (procesadas and procesadas[-1]["tipo"] == e["tipo"] and
                    procesadas[-1]["fin"] == e["inicio"]):
                previa = procesadas[-1]
                previa["fin"] = e["fin"]
                previa["texto"] = textos[pid][previa["inicio"]:e["fin"]]
            else:
                procesadas.append(e)
        filas.extend(procesadas)
    return pd.DataFrame(filas, columns=COLUMNAS)


def detalle_ie(referencia, pred, ids):
    """Conjuntos como el kit; ids explícitos permiten medir pasajes gold vacíos."""
    ref = referencia[referencia.passage_id.isin(ids)].drop_duplicates(CLAVE)
    pred = pred[pred.passage_id.isin(ids)]
    filas = []
    for metodo in METODOS:
        vista = vista_metodo(pred, metodo)
        for tipo in TIPOS:
            g = ref if tipo == "TODOS" else ref[ref.tipo.eq(tipo)]
            p = vista if tipo == "TODOS" else vista[vista.tipo.eq(tipo)]
            gs = set(g[CLAVE].itertuples(index=False, name=None))
            ps = set(p[CLAVE].itertuples(index=False, name=None))
            tp, fp, fn = len(gs & ps), len(ps - gs), len(gs - ps)
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1 = 2 * tp / (2*tp + fp + fn) if 2*tp + fp + fn else 0.0
            filas.append({"metodo": metodo, "tipo": tipo, "P": precision if gs else None,
                "R": recall if gs else None, "F1": f1 if gs else None, "TP": tp, "FP": fp, "FN": fn,
                "soporte": len(gs), "estado": "evaluado" if gs else "no aplicable",
                "cobertura": "sin cobertura" if metodo == "modelo" and tipo in
                {"FECHA", "MONTO"} else "cubierto", "pasajes": len(set(ids))})
    return pd.DataFrame(filas)


def analizar_errores(referencia, pred, pasajes, ids, obras=()):
    """Clasifica cada FP/FN, sin alterar Gold ni predicciones; etiquetas no exclusivas."""
    textos = pasajes.set_index("passage_id")
    salida = []
    obras = {t.casefold() for t in obras}
    for metodo in METODOS:
        vista = vista_metodo(pred, metodo)
        for pid in sorted(ids):
            g = referencia[referencia.passage_id.eq(pid)].drop_duplicates(CLAVE)
            p = vista[vista.passage_id.eq(pid)]
            gs = set(g[CLAVE].itertuples(index=False, name=None))
            ps = set(p[CLAVE].itertuples(index=False, name=None))
            for lado, tabla, otras, buenas in [("FN", g, p, ps), ("FP", p, g, gs)]:
                for e in tabla.to_dict("records"):
                    if tuple(e[c] for c in CLAVE) in buenas:
                        continue
                    solapadas = otras[(otras.inicio < e["fin"]) & (otras.fin > e["inicio"])]
                    exactas = solapadas[solapadas.inicio.eq(e["inicio"]) &
                                        solapadas.fin.eq(e["fin"])]
                    mismo_tipo = solapadas[solapadas.tipo.eq(e["tipo"])]
                    categorias = []
                    if not exactas.empty:
                        categorias.append("tipo")
                        if e["texto"].casefold() in obras:
                            categorias.append("obra_LOC_vs_ORG")
                    if not mismo_tipo.empty:
                        categorias.append("frontera")
                        dentro = mismo_tipo[(mismo_tipo.inicio >= e["inicio"]) &
                                             (mismo_tipo.fin <= e["fin"])]
                        if lado == "FN" and len(dentro) >= 2:
                            categorias.append("entidad_partida")
                        if lado == "FN" and e["tipo"] == "MONTO" and any(
                                f.inicio == e["inicio"] and f.fin < e["fin"]
                                for f in mismo_tipo.itertuples()):
                            categorias.append("monto_sin_unidad")
                    if e["fin"] <= textos.loc[pid, "inicio_cuerpo"]:
                        categorias.append("en_marca")
                    if solapadas.empty:
                        categorias.append("omision" if lado == "FN" else "espuria")
                    cubre = otras[(otras.inicio <= e["inicio"]) & (otras.fin >= e["fin"])]
                    if (lado == "FN" and 2 <= len(e["texto"]) <= 7 and
                            e["texto"].isalpha() and e["texto"].isupper() and cubre.empty):
                        categorias.append("sigla_no_reconocida")
                    if not categorias:
                        categorias.append("solape_tipo_distinto")
                    fuente = e.get("fuentes", e.get("metodo", "sin_prediccion"))
                    contexto = textos.loc[pid, "texto"][max(0, e["inicio"]-50):e["fin"]+50]
                    for categoria in categorias:
                        salida.append([pid, e["tipo"], e["texto"] if lado == "FN" else
                            " | ".join(solapadas.texto), e["texto"] if lado == "FP" else
                            " | ".join(solapadas.texto), e["inicio"], e["fin"], metodo,
                            categoria, fuente, contexto])
    return pd.DataFrame(salida, columns=ERRORES)
