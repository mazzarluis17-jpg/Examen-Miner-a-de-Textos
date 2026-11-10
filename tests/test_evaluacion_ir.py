"""H4 · Contratos oficiales, D08, ventana complementaria y conservación de referencias."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from mtx import adaptadores_kit as kit
from mtx import evaluacion as e
from mtx import pool


@pytest.fixture
def oficial(tmp_path):
    """Relevancias artificiales solo sobre IDs ficticios en un directorio temporal."""
    j = pd.DataFrame([['Q1', 0, '0_0', 1], ['Q1', 1, '1_0', 0], ['Q1', 2, '2_0', 1]],
                     columns=pool.COLUMNAS_JUICIOS)
    r = pd.DataFrame([{'query_id': 'Q1', 'modelo': m, 'rango': i + 1, 'passage_id': f'{i}_0'}
                      for m in pool.VARIANTES for i in range(3)])
    jp, rp = tmp_path / 'j.csv', tmp_path / 'r.csv'
    j.to_csv(jp, index=False)
    r.to_csv(rp, index=False)
    registro = tmp_path / 'ejecucion.json'
    ruta = kit.ejecutar_evaluador('ir', jp, rp, tmp_path, registro=registro)
    return pd.read_csv(ruta), j, r, json.loads(registro.read_text())


def test_metricas_oficiales_y_registro_real(oficial):
    resultado, _, _, registro = oficial
    e.validar_resultados(resultado, ['Q1'])
    assert len(resultado) == 8
    filas = resultado[resultado.query_id.eq('Q1')]
    assert filas['P@5'].eq(0.4).all()
    assert filas['P@10'].eq(0.2).all()
    assert filas.AP.eq(0.8333).all()
    assert filas.no_juzgados.eq(0).all()
    assert registro['codigo_salida'] == 0 and 'PROMEDIO' in registro['stdout']
    assert len(registro['sha256_referencia']) == 64


@pytest.mark.parametrize('ma,mb,ganador,cercano', [
    (0.6, 0.4, 'tfidf_con_filtro', False),
    (0.4, 0.6, 'bm25_con_filtro', False),
    (0.5, 0.5, 'bm25_con_filtro', True),
    (0.504, 0.5, 'tfidf_con_filtro', True),
])
def test_d08_ignora_variantes_sin_filtro_y_desempata(ma, mb, ganador, cercano):
    filas = pd.DataFrame([
        {'query_id': e.PROMEDIO, 'modelo': m, 'AP': valor}
        for m, valor in [('tfidf_con_filtro', ma), ('bm25_con_filtro', mb),
                         ('tfidf_sin_filtro', 0.99), ('bm25_sin_filtro', 1.0)]])
    resultado = e.elegir_modelo(filas, 'ranking_hash', 'juicios_hash')
    assert resultado['modelo'] == ganador
    assert resultado['diferencia_menor_0.01'] == cercano
    assert resultado['empate_exacto'] == (ma == mb)
    assert resultado['sha256_juicios'] == 'juicios_hash'


def test_vista_ventana_preserva_original_y_cuenta_fecha_desconocida():
    juicios = pd.DataFrame([['Q1', i, f'{i}_0', r] for i, r in enumerate([1, 1, 1, 0])],
                           columns=pool.COLUMNAS_JUICIOS)
    tabla = pd.DataFrame({'query_id': ['Q1'] * 4, 'passage_id': [f'{i}_0' for i in range(4)],
                          'fecha': ['2020-01-01', '2010-01-01', '', '2020-01-01'],
                          'en_ventana': [True, False, False, True]})
    antes = juicios.copy(deep=True)
    vista, soporte = e.vista_ventana(juicios, tabla)
    assert vista.relevante_ventana.tolist() == [1, 0, 0, 0]
    pd.testing.assert_frame_equal(juicios, antes)
    assert soporte.iloc[0].to_dict() == {'query_id': 'Q1', 'relevantes_tematicos': 3,
        'relevantes_en_ventana': 1, 'relevantes_fuera_ventana': 1, 'relevantes_fecha_desconocida': 1}


@pytest.mark.parametrize('problema', ['duplicado', 'faltante', 'no_juzgado', 'nan', 'fuera_rango'])
def test_rechaza_salida_invalida(oficial, problema):
    r = oficial[0].copy()
    if problema == 'duplicado':
        r = pd.concat([r, r.iloc[:1]])
    elif problema == 'faltante':
        r = r.iloc[1:]
    elif problema == 'no_juzgado':
        r.loc[0, 'no_juzgados'] = 1
    elif problema == 'nan':
        r.loc[0, 'AP'] = float('nan')
    else:
        r.loc[0, 'P@10'] = 1.1
    with pytest.raises(ValueError):
        e.validar_resultados(r, ['Q1'])


def test_resultado_distinto_no_sobrescribe(tmp_path):
    ruta = tmp_path / 'resultado.csv'
    e.escribir_conservando(ruta, b'referencia\n')
    e.escribir_conservando(ruta, b'referencia\n')
    with pytest.raises(ValueError):
        e.escribir_conservando(ruta, b'otra cifra\n')
    assert ruta.read_bytes() == b'referencia\n'


def test_tablas_ancho_y_vistas_separadas(oficial):
    r, _, ranking, _ = oficial
    etiquetas = pd.DataFrame([{'query_id': 'Q1', 'longitud': 'corta'}])
    ancho, ganadores, comparacion = e.tablas_comparativas(r, r.copy(), etiquetas, ranking)
    assert ancho.loc[0, 'juzgados__tfidf_con_filtro'] == 3
    assert ancho.loc[0, 'no_juzgados__bm25_con_filtro'] == 0
    assert ganadores.loc[0, 'ganador_AP'] == 'bm25_con_filtro'
    assert bool(ganadores.loc[0, 'empate_exacto'])
    assert set(comparacion.criterio) == {'oficial_tematico', 'complementaria_ventana'}


def test_no_exporta_juicios_incompletos(tmp_path, monkeypatch):
    monkeypatch.setattr(e.c, 'cargar_contexto', lambda _: object())
    monkeypatch.setattr(e.c, 'leer_estado', lambda _: object())
    monkeypatch.setattr(e.c, 'criterio_aprobado', lambda _: True)
    monkeypatch.setattr(e.c, 'cobertura', lambda *_: (['Falta un juicio'], []))
    with pytest.raises(ValueError, match='incompletos'):
        e.ejecutar_ir(tmp_path)
    assert not (tmp_path / 'juicios_relevancia.csv').exists()
