"""T07/T08 · Unión, asociaciones por consulta y protección de juicios con fixtures."""
from __future__ import annotations

import pandas as pd
import pytest

from mtx import corpus, pool


@pytest.fixture
def entradas():
    pasajes = pd.DataFrame([
        {"passage_id": f"{i}_0", "doc_id": i, "posicion": 0,
         "fecha": pd.Timestamp("2020-01-01") if i != 4 else pd.NaT,
         "texto": f"Texto sintético {i}",
         "texto_sha256": corpus.sha256_texto(f"Texto sintético {i}")}
        for i in range(5)])
    consultas = pd.DataFrame([{"query_id": q, "desde": "2019-01-01", "hasta": "2021-01-01"}
                              for q in ("Q1", "Q2")])
    filas = []
    for q in consultas.query_id:
        for modelo, ids in zip(pool.VARIANTES, ([0, 1], [1, 2], [2, 3], [3, 4]), strict=True):
            for rango, i in enumerate(ids, 1):
                filas.append({"query_id": q, "modelo": modelo, "rango": rango,
                              "passage_id": f"{i}_0", "doc_id": i, "posicion": 0,
                              "fecha": pasajes.loc[i, "fecha"]})
    return pd.DataFrame(filas), pasajes, consultas


def test_t07_union_procedencia_y_rangos(entradas):
    tabla, avisos = pool.construir(*entradas)
    assert len(tabla) == 10 and avisos
    assert list(tabla.columns) == pool.COLUMNAS
    assert not tabla.duplicated(["query_id", "passage_id"]).any()
    assert set(tabla[tabla.query_id == "Q1"].passage_id) == {f"{i}_0" for i in range(5)}
    fila = tabla[(tabla.query_id == "Q1") & (tabla.passage_id == "1_0")].iloc[0]
    assert fila.variantes == "tfidf_con_filtro|bm25_con_filtro"
    assert fila.mejor_rango_tfidf == 2 and fila.mejor_rango_bm25 == 1
    assert not tabla[tabla.passage_id == "4_0"].en_ventana.any()


def test_orden_reproducible_independiente_del_ranking(entradas):
    r, p, q = entradas
    a, _ = pool.construir(r, p, q)
    b, _ = pool.construir(r.sample(frac=1, random_state=7), p, q)
    assert pool.serializar(a) == pool.serializar(b)


def test_t08_pasaje_compartido_no_comparte_juicio(entradas):
    tabla, _ = pool.construir(*entradas)
    juicios = tabla[pool.COLUMNAS_JUICIOS[:-1]].copy()
    # Etiquetas artificiales exclusivamente sobre el fixture sintético en memoria.
    juicios["relevante"] = juicios.query_id.eq("Q1").astype(int)
    errores, avisos = pool.validar_juicios(juicios, tabla, entradas[1])
    assert not errores and len(avisos) == 1
    assert juicios[juicios.passage_id == "0_0"].relevante.tolist() == [1, 0]
    errores, _ = pool.validar_juicios(juicios.iloc[:-1], tabla, entradas[1])
    assert any("Cobertura" in e for e in errores)


@pytest.mark.parametrize("cambio", ["duplicado", "relevancia", "doc_id", "texto"])
def test_validacion_rechaza_juicios_invalidos(entradas, cambio):
    tabla, _ = pool.construir(*entradas)
    juicios = tabla[pool.COLUMNAS_JUICIOS[:-1]].assign(relevante=0)
    pasajes = entradas[1].copy()
    if cambio == "duplicado":
        juicios = pd.concat([juicios, juicios.iloc[:1]])
    elif cambio == "relevancia":
        juicios.loc[0, "relevante"] = 2
    elif cambio == "doc_id":
        juicios.loc[0, "doc_id"] = 999
    else:
        pasajes.loc[0, "texto"] = "Cambio artificial"
    assert pool.validar_juicios(juicios, tabla, pasajes)[0]


def test_no_sobrescribe_pool_con_juicios(entradas, tmp_path):
    tabla, _ = pool.construir(*entradas)
    ruta, juicios = tmp_path / "pool.csv", tmp_path / "juicios.csv"
    assert pool.guardar(tabla, ruta, juicios)
    antes = ruta.read_bytes()
    assert not pool.guardar(tabla, ruta, juicios)
    juicios.write_text("archivo centinela, sin etiquetas\n")
    tabla.loc[0, "texto"] = "Cambio"
    with pytest.raises(ValueError, match="modificados="):
        pool.guardar(tabla, ruta, juicios)
    assert ruta.read_bytes() == antes


@pytest.mark.parametrize("cambio", ["ausente", "hash", "fecha", "rango"])
def test_pool_rechaza_fuentes_incompatibles(entradas, cambio):
    r, p, q = (x.copy() for x in entradas)
    if cambio == "ausente":
        p = p.iloc[1:]
    elif cambio == "hash":
        p.loc[0, "texto_sha256"] = "incorrecto"
    elif cambio == "fecha":
        r.loc[0, "fecha"] = pd.Timestamp("1990-01-01")
    else:
        r.loc[0, "rango"] = 9
    with pytest.raises(ValueError):
        pool.construir(r, p, q)
