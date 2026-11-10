"""Minería preparatoria o extracción del ámbito H4, sin anotaciones humanas."""

import argparse
from dataclasses import asdict, fields

import pandas as pd

from mtx import config
from mtx.ambito_ie import cargar_ambito
from mtx.reglas import Entidad, extraer_auxiliares, extraer_con_auditoria, minar_siglas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--minar", action="store_true", help="Solo candidatos del corpus, sin aceptar"
    )
    args = parser.parse_args()
    config.DIR_SALIDA.mkdir(exist_ok=True)
    if args.minar:
        pasajes = pd.read_parquet(config.PASAJES_PARQUET)
        stoplist = (config.DIR_CONFIG / "stopwords_es.txt").read_text().split()
        filas = minar_siglas(pasajes.to_dict("records"), stoplist)
        pd.DataFrame(filas, columns=["sigla", "nombre_propuesto", "frecuencia", "ejemplo"]).to_csv(
            config.DIR_SALIDA / "06_siglas_candidatas.csv", index=False
        )
        return
    ranking, pasajes = cargar_ambito(config.RAIZ)
    entidades, auxiliares, colisiones = [], [], []
    for fila in pasajes.itertuples():
        extraidas, choques = extraer_con_auditoria(fila.texto, int(fila.inicio_cuerpo))
        for q in ranking.loc[ranking.passage_id.eq(fila.passage_id), "query_id"]:
            entidades.extend(
                dict(query_id=q, doc_id=fila.doc_id, passage_id=fila.passage_id, **asdict(e))
                for e in extraidas
            )
            auxiliares.extend(
                dict(query_id=q, passage_id=fila.passage_id, **a)
                for a in extraer_auxiliares(fila.texto)
            )
        for choque in choques:
            colisiones.append(
                dict(
                    passage_id=fila.passage_id,
                    **{f"{lado}_{k}": v for lado, e in choque.items() for k, v in e.items()},
                )
            )
    pd.DataFrame(
        entidades,
        columns=[
            "query_id",
            "doc_id",
            "passage_id",
            "tipo",
            "texto",
            "inicio",
            "fin",
            "metodo",
            "fuente",
            "en_marca",
        ],
    ).to_csv(config.DIR_SALIDA / "06_entidades_reglas.csv", index=False)
    pd.DataFrame(
        auxiliares,
        columns=[
            "query_id",
            "passage_id",
            "texto",
            "inicio",
            "fin",
            "tipo_aux",
            "valor_num",
            "unidad",
            "estado_normalizacion",
            "regla_id",
        ],
    ).to_csv(config.DIR_SALIDA / "cantidades_auxiliares.csv", index=False)
    columnas = ["passage_id"] + [
        f"{lado}_{k}"
        for lado in ["ganadora", "suprimida"]
        for k in [campo.name for campo in fields(Entidad)]
    ]
    pd.DataFrame(colisiones, columns=columnas).to_csv(
        config.DIR_SALIDA / "06_colisiones_reglas.csv", index=False
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc))
