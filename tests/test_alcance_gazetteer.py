"""Cobertura objetiva, aprobación de alcance y separación de rechazos humanos."""
import json

import pandas as pd
import pytest

from mtx.alcance_gazetteer import analizar
from mtx.app import gazetteer as g


def test_presencia_cuerpo_marca_cubiertos_y_ausentes():
    candidatos=pd.DataFrame([
        ["ABC","",1,"Base"],["DEF","",1,"Nuevo"],
        ["MARCA","",1,"Prefijo"],["XYZ","",1,"Ausente"]],
        columns=["sigla","nombre_propuesto","frecuencia","ejemplo"])
    pasajes=pd.DataFrame([{"passage_id":"0_0","doc_id":0,"texto":"MARCA: ABC DEF","inicio_cuerpo":7}])
    seleccion,auditoria,obs=analizar(candidatos,pasajes,[("ABC",True)])
    assert seleccion.sigla.tolist()==["DEF"]
    assert len(auditoria)==4 and len(obs)==3
    motivos=auditoria.set_index("sigla").estado_alcance.to_dict()
    assert motivos=={"ABC":"coincidencias_ya_cubiertas","DEF":"propuesto_revision",
                     "MARCA":"adicionales_solo_en_marca","XYZ":"sin_coincidencias_en_ambito"}
    assert "descartar" not in str(auditoria.to_dict())


@pytest.fixture
def alcance(tmp_path):
    for d in ["config","salida","kit"]:(tmp_path/d).mkdir()
    raw="sigla,nombre_propuesto,frecuencia,ejemplo\nABC,,1,Original\nDEF,,2,Evidencia\n"
    (tmp_path/"salida/06_siglas_candidatas.csv").write_text(raw)
    (tmp_path/"salida/06_revision_alcance.csv").write_text(
        "sigla,nombre_propuesto,frecuencia,ejemplo\nDEF,,2,Evidencia\n")
    for n in ["06_revision_auditoria.csv","06_revision_ocurrencias.csv"]:
        (tmp_path/"salida"/n).write_text("auditoria ficticia\n")
    for n in ["kit/gazetteer_dependencias.csv","config/gazetteer_prescrito.csv","config/gazetteer_loc.csv"]:
        (tmp_path/n).write_text("nombre,siglas,tipo\n")
    datos={"fuentes":{"salida/06_siglas_candidatas.csv":g.digest(raw.encode())}}
    for archivo,campo in [("06_revision_alcance.csv","sha256_subconjunto"),
                          ("06_revision_auditoria.csv","sha256_auditoria"),
                          ("06_revision_ocurrencias.csv","sha256_ocurrencias")]:
        datos[campo]=g.digest((tmp_path/"salida"/archivo).read_bytes())
    (tmp_path/"salida/06_revision_alcance.json").write_text(json.dumps(datos))
    return tmp_path


def aprobar_fixture(r):
    (r/"config/alcance_gazetteer_aprobacion.json").write_text(json.dumps({
        "aprobado_por":"Persona ficticia","fecha":"2000-01-01",
        "sha256_propuesta":g.digest((r/"salida/06_revision_alcance.json").read_bytes())}))


def test_alcance_pendiente_bloquea_sin_decisiones(alcance):
    with pytest.raises(ValueError,match="aprobación"):
        g.candidatos_revision(alcance)
    assert not (alcance/"config/gazetteer_revision.json").exists()


def test_cierre_solo_subconjunto_y_excluidos_no_rechazados(alcance,monkeypatch):
    monkeypatch.setattr(g,"congelado",lambda _:False)
    aprobar_fixture(alcance)
    assert [x["sigla"] for x in g.candidatos_revision(alcance)]==["DEF"]
    huellas=g.fuentes(alcance)
    estado=g.guardar(alcance,g.cargar(alcance),huellas,"DEF","descartar")
    g.cerrar_revision(alcance,estado,huellas,"Persona ficticia")
    assert set(g.cargar(alcance)["decisiones"])=={"DEF"}
    assert "ABC" not in g.cargar(alcance)["decisiones"]
    assert (alcance/"config/gazetteer_aprobacion.json").exists()


def test_aprobacion_hash_y_fuentes_obsoletas(alcance):
    aprobar_fixture(alcance)
    (alcance/"salida/06_siglas_candidatas.csv").write_text("cambiado")
    with pytest.raises(ValueError,match="obsoletas"):
        g.candidatos_revision(alcance)
