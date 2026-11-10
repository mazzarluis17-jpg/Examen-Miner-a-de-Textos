"""Inferencia solo en ámbito H4; caché perezosa, sin leer gold ni juicios."""

import argparse
import json
import time

import pandas as pd

from mtx import config
from mtx.ambito_ie import cargar_ambito
from mtx.ner_modelo import cargar_pipeline, procesar_pasaje

COLUMNAS = ["query_id", "doc_id", "passage_id", "tipo", "texto", "inicio", "fin", "metodo"]
UNIONES = [
    "passage_id",
    "tipo",
    "inicio_1",
    "fin_1",
    "inicio_2",
    "fin_2",
    "inicio_union",
    "fin_union",
    "texto_union",
    "confianza_1",
    "confianza_2",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", default="beto")
    parser.add_argument("--forzar", action="store_true")
    parser.add_argument("--cache-pesos", default=None)
    parser.add_argument("--solo-local", action="store_true")
    args = parser.parse_args()
    ranking, pasajes = cargar_ambito(config.RAIZ)
    parametros = next(
        (p for p in config.cargar_yaml("ner.yaml")["modelos"] if p["slug"] == args.modelo), None
    )
    if parametros is None:
        raise ValueError("Modelo no configurado")
    predictor = None

    def proveedor():
        nonlocal predictor
        if predictor is None:
            predictor = cargar_pipeline(parametros, args.cache_pesos, args.solo_local)
        return predictor

    entidades, uniones, crudas = [], [], []
    inicio = time.perf_counter()
    aciertos, descartadas = 0, 0
    for fila in pasajes.itertuples():
        procesadas, registro, datos, acierto = procesar_pasaje(
            fila.texto,
            fila.passage_id,
            parametros,
            config.DIR_DATA / "cache_ner",
            proveedor,
            args.forzar,
        )
        aciertos += int(acierto)
        descartadas += datos["descartadas"]
        uniones.extend(registro)
        for q in ranking.loc[ranking.passage_id.eq(fila.passage_id), "query_id"]:
            for destino, lista in [(entidades, procesadas), (crudas, datos["crudas"])]:
                destino.extend(
                    dict(
                        query_id=q,
                        doc_id=fila.doc_id,
                        passage_id=fila.passage_id,
                        metodo="modelo",
                        **e,
                    )
                    for e in lista
                )
    config.DIR_SALIDA.mkdir(exist_ok=True)
    for nombre, filas in [
        (f"entidades_{args.modelo}", entidades),
        (f"07_crudas_{args.modelo}", crudas),
    ]:
        pd.DataFrame(filas, columns=COLUMNAS).to_csv(
            config.DIR_SALIDA / f"{nombre}.csv", index=False
        )
    pd.DataFrame(uniones, columns=UNIONES).to_csv(
        config.DIR_SALIDA / "07_uniones_spans.csv", index=False
    )
    informe = {
        "modelo": parametros,
        "pasajes": len(pasajes),
        "cacheados": aciertos,
        "inferidos": len(pasajes) - aciertos,
        "descartadas_misc_oth": descartadas,
        "segundos": time.perf_counter() - inicio,
    }
    (config.DIR_SALIDA / "07_ejecucion_ner.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc))
