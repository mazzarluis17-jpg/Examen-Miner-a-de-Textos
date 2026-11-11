"""T08/T13: unión exacta, discrepancias conservadas y asociaciones sin duplicar."""

import pandas as pd

from mtx.fusion import COLUMNAS, fusionar


def test_fusion_exacta_solapes_y_pasaje_compartido():
    pasajes = pd.DataFrame([{"passage_id": "1_0", "doc_id": 1, "texto": "Banco Azul México"}])
    ranking = pd.DataFrame([{"query_id": q, "passage_id": "1_0", "doc_id": 1} for q in ["Q1","Q3"]])
    reglas = pd.DataFrame([
        ["Q1",1,"1_0","ORG","Banco Azul",0,10,"regla"],
        ["Q3",1,"1_0","ORG","Banco Azul",0,10,"regla"],
        ["Q1",1,"1_0","LOC","México",11,17,"regla"]], columns=COLUMNAS)
    modelo = pd.DataFrame([
        ["Q1",1,"1_0","ORG","Banco Azul",0,10,"modelo"],
        ["Q1",1,"1_0","ORG","Azul",6,10,"modelo"],
        ["Q1",1,"1_0","ORG","México",11,17,"modelo"]], columns=COLUMNAS)
    oficial, unica, _, solapes = fusionar(reglas, modelo, ranking, pasajes)
    assert len(unica)==4 and len(oficial)==8
    assert list(oficial.columns)==COLUMNAS
    assert set(unica.metodo)=={"regla","modelo","ambos"}
    assert set(solapes.clase)=={"solape_parcial","tipo_distinto"}
    assert len(solapes)==2
    segunda = fusionar(reglas,modelo,ranking,pasajes)[0]
    assert oficial.to_csv(index=False)==segunda.to_csv(index=False)


def test_fusion_vacia_conserva_esquema():
    tabla=pd.DataFrame(columns=COLUMNAS)
    ranking=pd.DataFrame(columns=["query_id","passage_id","doc_id"])
    pasajes=pd.DataFrame(columns=["passage_id","doc_id","texto"])
    assert list(fusionar(tabla,tabla,ranking,pasajes)[0].columns)==COLUMNAS
