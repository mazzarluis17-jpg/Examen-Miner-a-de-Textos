"""Contratos de H9: esquemas exactos y rechazo de cambios silenciosos."""
from pathlib import Path

import pandas as pd
import pytest

from mtx.entrega import RAIZ, tablas, tex
from mtx.validacion_entrega import ESQUEMAS, validar_csv


@pytest.mark.parametrize("nombre", ESQUEMAS)
def test_seis_csv_oficiales(nombre):
    """Los originales versionados conservan contrato y unicidad."""
    assert not validar_csv(RAIZ / nombre, nombre).empty


def test_rechaza_relevancia_fuera_del_dominio(tmp_path):
    ruta = tmp_path / "juicios.csv"
    ruta.write_text("query_id,doc_id,passage_id,relevante\nQ1,1,1_0,2\n")
    with pytest.raises(ValueError, match="Etiqueta"):
        validar_csv(ruta, "juicios_relevancia.csv")


def test_rechaza_columnas_reordenadas(tmp_path):
    ruta = tmp_path / "gold.csv"
    ruta.write_text("tipo,passage_id,texto,inicio,fin\nORG,1_0,x,0,1\n")
    with pytest.raises(ValueError, match="Columnas"):
        validar_csv(ruta, "gold_entidades.csv")


def test_rechaza_duplicados(tmp_path):
    ruta = tmp_path / "gold.csv"
    ruta.write_text("passage_id,tipo,texto,inicio,fin\n1_0,ORG,x,0,1\n1_0,ORG,x,0,1\n")
    with pytest.raises(ValueError, match="duplicada"):
        validar_csv(ruta, "gold_entidades.csv")


def test_metricas_del_reporte_usan_promedios_oficiales():
    ir, _ = tablas()
    oficial = pd.read_csv(RAIZ / "salida/resultados_ir.csv")
    esperado = oficial[oficial.query_id == "PROMEDIO (MAP = AP)"].set_index("modelo")
    pd.testing.assert_frame_equal(ir, esperado[["P@5", "P@10", "AP"]])


def test_escape_tex_conserva_tildes_y_protege_sintaxis():
    assert tex("A&B_é 15%") == r"A\&B\_é 15\%"
    assert Path(RAIZ).is_dir()


def test_rechaza_tipo_resumen_como_entidad(tmp_path):
    ruta = tmp_path / "gold.csv"
    ruta.write_text("passage_id,tipo,texto,inicio,fin\n1_0,TODOS,x,0,1\n")
    with pytest.raises(ValueError, match="Tipo desconocido"):
        validar_csv(ruta, "gold_entidades.csv")
