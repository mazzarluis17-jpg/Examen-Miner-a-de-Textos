"""Representaciones auxiliares sintéticas; no dependen del Gold real."""

import pandas as pd
import pytest

from mtx.enriquecimiento import enriquecer, fecha_auxiliar, monto_auxiliar
from mtx.fusion import COLUMNAS


@pytest.mark.parametrize('texto,valor',[
    ('500 pesos','500'),('1,200 pesos','1200'),('6 mil 300 pesos','6300'),
    ('mil 200 pesos','1200'),('un millón de pesos','1000000'),
    ('dos mil millones de pesos','2000000000'),('1.5 billones de pesos','1500000000000.0'),
    ('$1,200 millones','1200000000'),('$ 5 mil','5000'),('5 mil pesos','5000'),
    ('2 mil 500 millones de pesos','2500000000'),('100 millones de dólares','100000000'),
    ('20 mil millones de pesos','20000000000'),('3.5 pesos','3.5'),('1.200 pesos','')])
def test_montos_decimal(texto,valor):
    assert monto_auxiliar(texto)['valor_num']==valor


def test_monto_moneda_rango_y_billones_ambiguos():
    assert monto_auxiliar('$5')['moneda']==''
    assert monto_auxiliar('varios millones')['valor_num']==''
    assert monto_auxiliar('un billón de pesos','equivale a mil millones')['valor_num']==''
    r=monto_auxiliar('entre 2 y 3 mil millones de pesos')
    assert r['valor_min']=='2000000000' and r['valor_max']=='3000000000'


@pytest.mark.parametrize('texto,iso',[
    ('15 de enero de 2021','2021-01-15'),('diciembre de 2021','2021-12'),
    ('2019','2019'),('29 de febrero de 2020','2020-02-29'),
    ('29 de febrero de 2021',''),('31 de febrero de 2020',''),
    ('1/1/19',''),('próximo 15 de enero',''),('15 de enero',''),
    ('15/12/2023','2023-12-15')])
def test_fechas_sin_dia_inventado(texto,iso):
    assert fecha_auxiliar(texto)['fecha_iso']==iso


def test_intervalos_ancla_y_no_mezcla():
    assert fecha_auxiliar('del 1 al 15 de marzo de 2020')['fecha_fin']=='2020-03-15'
    assert fecha_auxiliar('del 15 al 1 de marzo de 2020')['estado_fecha']=='invalida'
    assert fecha_auxiliar('15 de enero','2021-03-01')['fecha_iso']=='2021-01-15'
    pub=pd.DataFrame([['Q1',1,'1_0','MONTO','$5',0,2,'regla','regex_monto']],
                     columns=COLUMNAS+['fuentes'])
    pasajes=pd.DataFrame([{'passage_id': '1_0','texto': '$5','fecha': '2020-01-01','inicio_cuerpo': 0}])
    en=enriquecer(pub,pasajes,'modelo','rev','version')
    pd.testing.assert_frame_equal(en[COLUMNAS],pub[COLUMNAS])
