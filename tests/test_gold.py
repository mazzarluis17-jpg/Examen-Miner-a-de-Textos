"""T10/T15 · Gold humano sobre fixtures sintéticos, sin etiquetas del corpus real."""
import html
import re
import subprocess

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from mtx import gold
from mtx.app import vista_gold


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    (tmp_path/"anotaciones").mkdir()
    (tmp_path/"config").mkdir()
    (tmp_path/"config/criterios_anotacion.md").write_text("Criterio ficticio de prueba")
    textos, muestras, ranking = [], [], []
    for i in range(20):
        texto = "😀 PERSONA: <Banco> Banco $100 pesos."
        pid, q = f"{i}_0", f"Q{i//2+1}"
        textos.append({"passage_id":pid, "doc_id":i, "texto":texto, "inicio_cuerpo":11})
        muestras.append([q,pid,str(i),gold.sha(texto.encode()),"42","1"])
        ranking.append({"query_id":q,"passage_id":pid})
    muestra = pd.DataFrame(muestras, columns=gold.MUESTRA)
    muestra.to_csv(tmp_path/"anotaciones/muestra_gold.csv", index=False)
    monkeypatch.setattr(gold,"verificar_d15",lambda raiz:None)
    return {"raiz":tmp_path,"muestras":{"Evaluación":muestra},"pasajes":pd.DataFrame(textos),
            "ranking":pd.DataFrame(ranking),"fuentes":{"config/criterios_anotacion.md":
                gold.sha((tmp_path/"config/criterios_anotacion.md").read_bytes())}}


def entidad(ctx, a=12, b=17, tipo="ORG"):
    texto=ctx["pasajes"].iloc[0].texto
    return pd.DataFrame([["0_0",tipo,texto[a:b],str(a),str(b)]],columns=gold.COLUMNAS)


def test_busqueda_ambigua_tokens_unicode_y_html():
    texto="😀 <Banco> Banco $100, pesos."
    assert gold.ocurrencias(texto,"Banco")==[(3,8),(10,15)]
    assert gold.ocurrencias(texto,"")==[]
    a,b=gold.span_tokens(texto,3,3)
    assert texto[a:b]=="$100"
    with pytest.raises(ValueError):
        gold.span_tokens(texto,3,1)
    entidades=pd.DataFrame([["0_0","ORG","Banco","3","8"]],columns=gold.COLUMNAS)
    salida=gold.renderizar(texto,entidades,2)
    assert "&lt;" in salida and "&gt;" in salida
    assert html.unescape(re.sub(r"<[^>]+>","",salida))==texto


def test_spans_duplicados_tipos_offsets_y_solapes(ctx):
    textos=ctx["pasajes"].set_index("passage_id").texto.to_dict()
    buena=entidad(ctx)
    assert not gold.validar_spans(buena,textos)
    assert gold.validar_spans(pd.concat([buena,buena]),textos)
    assert gold.validar_spans(entidad(ctx,tipo="MISC"),textos)
    mala=buena.copy();mala.loc[0,"inicio"]="0"
    assert gold.validar_spans(mala,textos)
    anidada=pd.concat([entidad(ctx,12,18),entidad(ctx,13,17)],ignore_index=True)
    assert gold.validar_spans(anidada,textos)
    parcial=pd.concat([entidad(ctx,12,18),entidad(ctx,16,21)],ignore_index=True)
    assert not gold.validar_spans(parcial,textos)


def test_persistencia_edicion_borrado_y_reanudacion(ctx):
    inicial=gold.leer(ctx)
    assert not (ctx["raiz"]/"anotaciones/gold_entidades.csv").exists()
    nuevo=gold.guardar(ctx,inicial,"Evaluación","0_0",entidad(ctx))
    assert len(gold.leer(ctx)["tablas"]["Evaluación"])==1
    corregida=entidad(ctx,tipo="LOC")
    nuevo=gold.guardar(ctx,nuevo,"Evaluación","0_0",corregida)
    assert gold.leer(ctx)["tablas"]["Evaluación"].tipo.tolist()==["LOC"]
    nuevo=gold.guardar(ctx,nuevo,"Evaluación","0_0",pd.DataFrame(columns=gold.COLUMNAS),True)
    assert gold.leer(ctx)["tablas"]["Evaluación"].empty
    assert nuevo["tablas"]["estados"].estado.tolist()==["cerrado"]
    assert list((ctx["raiz"]/"anotaciones/historial_gold").glob("*"))


def test_dos_sesiones_y_fuentes_cambiadas(ctx):
    a,b=gold.leer(ctx),gold.leer(ctx)
    a=gold.guardar(ctx,a,"Evaluación","0_0",entidad(ctx))
    with pytest.raises(ValueError,match="otra pestaña"):
        gold.guardar(ctx,b,"Evaluación","0_0",entidad(ctx))
    ruta=ctx["raiz"]/"anotaciones/gold_entidades.csv";antes=ruta.read_bytes()
    (ctx["raiz"]/"config/criterios_anotacion.md").write_text("Cambio")
    with pytest.raises(ValueError,match="obsoleto"):
        gold.guardar(ctx,a,"Evaluación","0_0",entidad(ctx))
    assert ruta.read_bytes()==antes


def test_interrupcion_preserva_gold_y_bloquea(ctx,monkeypatch):
    a=gold.guardar(ctx,gold.leer(ctx),"Evaluación","0_0",entidad(ctx))
    ruta=ctx["raiz"]/"anotaciones/gold_entidades.csv";antes=ruta.read_bytes()
    original=gold.atomico
    def interrumpir(p,datos):
        if p==ruta:
            raise OSError("Interrupción simulada")
        original(p,datos)
    monkeypatch.setattr(gold,"atomico",interrumpir)
    with pytest.raises(OSError):
        gold.guardar(ctx,a,"Evaluación","0_0",entidad(ctx,tipo="LOC"))
    assert ruta.read_bytes()==antes
    with pytest.raises(ValueError,match="interrumpido"):
        gold.leer(ctx)


def test_t10_cierre_veinte_pasajes_sin_entidades(ctx):
    a=gold.leer(ctx)
    with pytest.raises(ValueError):
        gold.cerrar_gold(ctx,a,"Persona ficticia")
    for pid in ctx["muestras"]["Evaluación"].passage_id:
        a=gold.guardar(ctx,a,"Evaluación",pid,pd.DataFrame(columns=gold.COLUMNAS),True)
    assert not gold.validar_gold(ctx["muestras"]["Evaluación"],a["tablas"]["Evaluación"],
                                a["tablas"]["estados"],ctx["pasajes"],ctx["ranking"])
    gold.cerrar_gold(ctx,a,"Persona ficticia")
    assert (ctx["raiz"]/"anotaciones/cierre_gold.json").exists()
    assert pd.read_csv(ctx["raiz"]/"gold_entidades.csv").empty
    with pytest.raises(ValueError,match="cerrado"):
        gold.guardar(ctx,a,"Evaluación","0_0",entidad(ctx))


@pytest.mark.parametrize("problema",["id","hash","semilla","consulta","incompleto"])
def test_muestra_invalida(ctx,problema):
    m=ctx["muestras"]["Evaluación"].copy()
    if problema=="id":m.loc[0,"passage_id"]="999_0"
    elif problema=="hash":m.loc[0,"texto_sha256"]="incorrecto"
    elif problema=="semilla":m.loc[0,"semilla"]="43"
    elif problema=="consulta":m.loc[0,"query_id"]="Q99"
    else:m=m.iloc[:-1]
    assert gold.validar_gold(m,pd.DataFrame(columns=gold.COLUMNAS),pd.DataFrame(columns=gold.ESTADOS),
                            ctx["pasajes"],ctx["ranking"])


def test_guardia_real_sin_congelacion_no_crea_gold(tmp_path):
    subprocess.run(["git","init","-q",str(tmp_path)],check=True)
    with pytest.raises(ValueError,match="D15"):
        gold.cargar_contexto(tmp_path)
    assert not (tmp_path/"anotaciones").exists()


def test_etiqueta_precede_primer_commit_gold(tmp_path):
    def git(*args):
        return subprocess.run(["git","-c","user.name=Prueba","-c","user.email=prueba@example.invalid",
                               *args],cwd=tmp_path,check=True,capture_output=True)
    git("init","-q")
    (tmp_path/"base.txt").write_text("Fixture sin datos reales")
    git("add","base.txt");git("commit","-qm","base")
    git("tag","reglas-congeladas")
    (tmp_path/"anotaciones").mkdir()
    (tmp_path/"anotaciones/gold_entidades.csv").write_text("passage_id,tipo,texto,inicio,fin\n")
    git("add","anotaciones/gold_entidades.csv");git("commit","-qm","fixture gold vacío")
    gold.verificar_d15(tmp_path)
    git("tag","-f","reglas-congeladas")
    with pytest.raises(ValueError,match="preceder"):
        gold.verificar_d15(tmp_path)


def test_ui_ciega_no_precarga_y_agrega_solo_tras_click(ctx,monkeypatch):
    (ctx["raiz"]/"salida").mkdir()
    (ctx["raiz"]/"salida/entidades_beto.csv").write_text("PREDICCION_OCULTA")
    monkeypatch.setattr(gold,"cargar_contexto",lambda _:ctx)
    vista_gold.contexto.clear()
    codigo="from pathlib import Path\nfrom mtx.app.vista_gold import mostrar\nmostrar(Path("+repr(str(ctx["raiz"]))+"))"
    app=AppTest.from_string(codigo,default_timeout=30).run()
    assert not app.exception and not app.error
    assert not (ctx["raiz"]/"anotaciones/gold_entidades.csv").exists()
    assert "PREDICCION_OCULTA" not in '\n'.join(m.value for m in app.markdown)
    assert gold.leer(ctx)["tablas"]["Evaluación"].empty
    next(x for x in app.text_input if x.label=="Texto exacto a anotar").set_value("Banco").run()
    next(x for x in app.selectbox if x.label.startswith("Aparición")).select((12,17)).run()
    next(x for x in app.selectbox if x.label=="Tipo elegido por el alumno").select("ORG").run()
    next(x for x in app.button if x.label=="Agregar entidad").click().run()
    assert not app.exception and not app.error
    assert gold.leer(ctx)["tablas"]["Evaluación"].texto.tolist()==["Banco"]
