"""Protecciones del compilador académico de H9, sin TeX ni red en las pruebas."""
import pandas as pd
import plotly.graph_objects as go
import pytest

from mtx import reporte
from mtx.entrega import RAIZ


def test_conserva_formula_y_escapa_texto():
    assert reporte.literal('Precisión & $k_1=1.5$') == r'Precisión \& $k_1=1.5$'


def test_revision_larga_conserva_caracteres():
    revision = '2c463bb3d5bf58742b4d842917da1211c44d2e18'
    resultado = reporte.tex(revision)
    assert r'\allowbreak{}' in resultado
    assert resultado.replace(r'\allowbreak{}', '') == revision


@pytest.mark.parametrize('contenido', ['```python\nprint(1)\n```', 'Código `x = 1`'])
def test_rechaza_codigo_en_reporte(contenido):
    with pytest.raises(ValueError, match='código'):
        reporte.convertir_md(contenido, {})


def test_rechaza_formula_incompleta():
    with pytest.raises(ValueError, match='sin cierre'):
        reporte.convertir_md('$$\nx+1', {})


def test_conversion_no_reemplaza_parrafo_aprobado():
    texto = '## Resultados\n\nPárrafo aprobado por el alumno.\n\n<!-- tabla: ir -->'
    resultado = reporte.convertir_md(texto, {'ir': 'TABLA DERIVADA'})
    assert 'Párrafo aprobado por el alumno.' in resultado
    assert 'TABLA DERIVADA' in resultado
    assert '[VALIDAR' not in resultado


def test_figura_usa_todas_las_consultas_y_ap_oficial(monkeypatch):
    capturadas = []
    monkeypatch.setattr(go.Figure, 'write_image', lambda self, *_: capturadas.append(self))
    reporte.generar_figura()
    figura = capturadas[0]
    assert len(figura.data) == 4
    assert list(figura.data[0].x) == [f'Q{i}' for i in range(1, 11)]
    assert figura.data[0].y[0] == .9091
    datos = pd.read_csv(RAIZ / 'salida/05_ir_por_consulta.csv').set_index('query_id')
    assert list(figura.data[0].y) == list(datos.loc[list(figura.data[0].x), 'AP__bm25_con_filtro'])


def test_readme_preserva_prosa_fuera_de_marcadores():
    fuente = "Texto aprobado\n<!-- resultados:inicio -->viejo<!-- resultados:fin -->\nUso de IA aprobado"
    resultado = reporte.insertar_resultados(fuente, "tabla nueva")
    assert resultado == ("Texto aprobado\n<!-- resultados:inicio -->\ntabla nueva\n"
                         "<!-- resultados:fin -->\nUso de IA aprobado")


def test_readme_rechaza_marcadores_ambiguos():
    with pytest.raises(ValueError, match="Marcadores"):
        reporte.insertar_resultados("README sin marcadores", "No sobrescribir")
