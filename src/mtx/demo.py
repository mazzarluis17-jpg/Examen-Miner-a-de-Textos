"""Demostración sin red sobre consultas y artefactos congelados."""
from __future__ import annotations

import time
from functools import lru_cache

import pandas as pd
from rich.console import Console
from rich.table import Table

from mtx.entrega import RAIZ


@lru_cache(maxsize=1)
def cargar():
    """Carga únicamente los resultados existentes, sin inferencia."""
    return {
        "consultas": pd.read_csv(RAIZ / "data/consultas.csv", keep_default_na=False),
        "ranking": pd.read_csv(RAIZ / "salida/03_ranking_detalle.csv"),
        "entidades": pd.read_csv(RAIZ / "entidades.csv"),
        "respuestas": pd.read_csv(RAIZ / "salida/respuestas.csv", keep_default_na=False),
    }


def mostrar(q="Q3", consola=None):
    """Muestra consulta → top-10 → pasajes → entidades → respuesta y citas."""
    consola = consola or Console()
    inicio = time.perf_counter()
    datos = cargar()
    consulta = datos["consultas"].loc[lambda d: d.query_id == q]
    if len(consulta) != 1:
        raise ValueError(f"Consulta oficial desconocida: {q}")
    fila = consulta.iloc[0]
    consola.rule(f"{q}: {fila.consulta}")
    consola.print(f"Ventana inclusiva: {fila.desde} a {fila.hasta}")
    consola.print(fila.pregunta_extraccion)
    ranking = datos["ranking"].loc[lambda d: d.query_id == q]
    tabla = Table(title="Top-10 con filtro: TF-IDF y BM25")
    for col in ("Rango", "TF-IDF: ID / fecha / posición / puntaje / fragmento",
                "BM25: ID / fecha / posición / puntaje / fragmento"):
        tabla.add_column(col)
    for rango in range(1, 11):
        celdas = []
        for modelo in ("tfidf_con_filtro", "bm25_con_filtro"):
            r = ranking.loc[(ranking.modelo == modelo) & (ranking.rango == rango)].iloc[0]
            celdas.append(f"{r.passage_id} / {r.fecha} / {r.posicion} / {r.puntaje:.6f}\n"
                          + r.texto[:100])
        tabla.add_row(str(rango), *celdas)
    consola.print(tabla)
    for r in ranking.loc[lambda d: d.modelo == "bm25_con_filtro"].itertuples():
        consola.rule(f"Pasaje {r.passage_id}, {r.fecha}")
        consola.print(r.texto, markup=False)
        entidades = datos["entidades"].loc[
            (datos["entidades"].query_id == q) & (datos["entidades"].passage_id == r.passage_id)]
        for e in entidades.itertuples():
            consola.print(f"{e.tipo} [{e.inicio}:{e.fin}] {e.texto} ({e.metodo})", markup=False)
    consola.rule("Tabla de respuesta: cada fila conserva su estado de evidencia")
    for r in datos["respuestas"].loc[lambda d: d.query_id == q].itertuples():
        consola.print(f"{r.campo_respuesta}: {r.valor} | {r.estado}", markup=False)
        consola.print(f"{r.passage_id} [{r.evidencia_inicio}:{r.evidencia_fin}] {r.cita}",
                      markup=False)
    duracion = time.perf_counter() - inicio
    consola.print(f"Latencia total: {duracion:.3f} s; sin red ni inferencia.")
    return duracion
