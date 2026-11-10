"""Frontera H4→H5: ningún ganador o pasaje se elige por conveniencia."""

import json

import pandas as pd


def cargar_ambito(raiz):
    """Lee exclusivamente ganador, ranking y pasajes; nunca juicios humanos."""
    ruta = raiz / "data/mejor_modelo.json"
    if not ruta.exists():
        raise ValueError(
            "Pendiente H4: falta data/mejor_modelo.json. Completar H3 y make evaluar-ir."
        )
    decision = json.loads(ruta.read_text())
    modelo = decision.get("modelo")
    if modelo not in {"tfidf_con_filtro", "bm25_con_filtro"}:
        raise ValueError("Ganador IR inválido: se exige modelo *_con_filtro (D08)")
    ranking = pd.read_csv(raiz / "salida/ranking.csv")
    filas = ranking[ranking.modelo.eq(modelo)].copy()
    if filas.empty or not filas["variante"].eq("con_filtro").all():
        raise ValueError("Ámbito IE vacío o no filtrado")
    if not filas["rango"].between(1, 10).all() or filas.passage_id.nunique() > 100:
        raise ValueError("Ámbito IE fuera del top-10")
    pasajes = pd.read_parquet(raiz / "data/pasajes.parquet")
    if pasajes.passage_id.duplicated().any():
        raise ValueError("Pasajes duplicados")
    textos = pasajes.set_index("passage_id")
    if not set(filas.passage_id) <= set(textos.index):
        raise ValueError("Pasaje recuperado ausente")
    return filas, textos.loc[sorted(set(filas.passage_id))].reset_index()
