"""Métrica independiente del kit, pasaje vacío y categorías reales sintéticas."""

import pandas as pd
import pytest

from mtx.adaptadores_kit import ejecutar_evaluador
from mtx.evaluacion_ie import analizar_errores, detalle_ie, validar_entidades
from mtx.fusion import COLUMNAS


def test_detalle_contra_kit_y_complementaria_vacia(tmp_path):
    ref=pd.DataFrame([['1_0','ORG','Banco',0,5]],
                     columns=['passage_id','tipo','texto','inicio','fin'])
    pred=pd.DataFrame([['Q1',1,'1_0','ORG','Banco',0,5,'ambos'],
                       ['Q3',1,'1_0','ORG','Banco',0,5,'ambos'],
                       ['Q2',2,'2_0','PER','Ana',0,3,'modelo']],columns=COLUMNAS)
    rg=tmp_path/'g.csv';rp=tmp_path/'p.csv';ref.to_csv(rg,index=False);pred.to_csv(rp,index=False)
    oficial=pd.read_csv(ejecutar_evaluador('ie',rg,rp,tmp_path/'eval'))
    detalle=detalle_ie(ref,pred,{'1_0'})
    for f in oficial.itertuples():
        row=detalle[detalle.metodo.eq(f.metodo)&detalle.tipo.eq(f.tipo)].iloc[0]
        assert row.TP==f.tp and row.FP==f.predichas-f.tp and row.FN==f.gold-f.tp
    c=detalle_ie(ref,pred,{'1_0','2_0'})
    assert c.loc[c.metodo.eq('combinado')&c.tipo.eq('TODOS'),'FP'].iloc[0]==1
    assert c.loc[c.metodo.eq('modelo')&c.tipo.eq('FECHA'),'cobertura'].iloc[0]=='sin cobertura'
    assert c.loc[c.tipo.eq('FECHA'),'F1'].isna().all()


def test_categorias_fn_fp_y_no_exclusivas():
    ref=pd.DataFrame([['1_0','ORG','Banco Azul',0,10],['1_0','ORG','SAT',11,14]],
                     columns=['passage_id','tipo','texto','inicio','fin'])
    pred=pd.DataFrame([['Q1',1,'1_0','ORG','Banco',0,5,'modelo'],
                       ['Q1',1,'1_0','ORG','Azul',6,10,'modelo'],
                       ['Q1',1,'1_0','LOC','Roma',15,19,'regla']],columns=COLUMNAS)
    pasajes=pd.DataFrame([{'passage_id': '1_0','texto': 'Banco Azul SAT Roma','inicio_cuerpo': 14}])
    e=analizar_errores(ref,pred,pasajes,{'1_0'})
    assert {'frontera','entidad_partida','en_marca','sigla_no_reconocida','omision','espuria'}<=set(e.categoria)


def test_contrato_rechaza_offset_o_metodo():
    p=pd.DataFrame([{'passage_id': '1_0','texto': 'Ana'}])
    tabla=pd.DataFrame([['Q1',1,'1_0','PER','Ana',0,3,'modelo']],columns=COLUMNAS)
    validar_entidades(tabla,p)
    tabla.loc[0,'metodo']='desconocido'
    with pytest.raises(ValueError):validar_entidades(tabla,p)
