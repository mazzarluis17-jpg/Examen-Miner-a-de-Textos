"""Regresión de spans vacíos, preservación de v1 y ninguna mutación cruda."""

from copy import deepcopy

import pytest

from mtx.ner_modelo import posprocesar
from mtx.ner_posproceso_v2 import VERSION, posprocesar_auditado, procesar_pasaje_auditado


def entidad(texto, a, b, tipo="LOC"):
    return {"tipo": tipo, "texto": texto[a:b], "inicio": a, "fin": b, "confianza": .5, "cortada": False}


@pytest.mark.parametrize("texto", ["'", '"', "...", "   ", "¿?!", " “ ” "])
def test_recorte_vacio_auditado_sin_cambiar_congelado(texto):
    raw=[entidad(texto,0,len(texto))]
    antes=deepcopy(raw)
    with pytest.raises(ValueError, match="Span vacío"):
        posprocesar(texto,raw)
    procesadas,uniones,descartes=posprocesar_auditado(texto,raw,'1_0')
    assert procesadas==uniones==[] and len(descartes)==1
    assert descartes[0]['texto_original']==texto
    assert descartes[0]['version_posproceso']==VERSION
    assert raw==antes


def test_entidades_restantes_identicas_y_simbolo_monetario():
    texto=" 'Ana' Pérez $5"
    raw=[entidad(texto,1,6,'PER'),entidad(texto,7,12,'PER'),entidad(texto,13,15,'ORG')]
    esperado=posprocesar(texto,raw,'1_0')
    result=posprocesar_auditado(texto,raw,'1_0')
    assert result[:2]==esperado and result[2]==[]
    assert result[0][-1]['texto']=='$5'


def test_offsets_invalidos_no_se_ocultan():
    with pytest.raises(ValueError):
        posprocesar_auditado('Ana',[entidad('Ana',1,1)])


def test_cache_original_intacta_y_proveedor_no_invocado(tmp_path,monkeypatch):
    import json

    import mtx.ner_posproceso_v2 as v2

    parametros={'slug':'beto','revision':'a'*40}
    monkeypatch.setattr(v2,'clave_cache',lambda *args:'clave')
    ruta=tmp_path/('beto@'+'a'*12)/'1_0.json'
    ruta.parent.mkdir()
    contenido=json.dumps({'clave':'clave','crudas':[entidad("'",0,1)]}).encode()
    ruta.write_bytes(contenido)

    def falla(*args):
        raise ValueError('Span vacío después del recorte')

    monkeypatch.setattr(v2,'procesar_pasaje',falla)
    result=procesar_pasaje_auditado("'",'1_0',parametros,tmp_path,None)
    assert result[3] is True and len(result[4])==1 and ruta.read_bytes()==contenido
