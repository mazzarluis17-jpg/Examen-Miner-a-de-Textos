"""Contratos de ámbito, muestreo y revisión; fixtures humanos solo en tmp_path."""

import json
import subprocess

import pandas as pd
import pytest

from mtx.ambito_ie import cargar_ambito
from mtx.app import gazetteer as g
from mtx.app.componentes import ErrorAnotacion
from mtx.congelacion import verificar_congelacion
from mtx.muestreo import sortear_muestra


def test_sin_h4_bloquea_sin_leer_juicios(tmp_path):
    with pytest.raises(ValueError, match="H4"):
        cargar_ambito(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_sin_aprobacion_no_congela(tmp_path):
    with pytest.raises(ValueError, match="Pendiente humano"):
        verificar_congelacion(tmp_path)


def test_t09_colisiones_y_caso_imposible():
    filas = []
    for q in range(10):
        for i in range(10):
            filas.append({"query_id": f"Q{q}", "passage_id": f"{q + i}_0", "rango": i + 1})
    ranking = pd.DataFrame(filas)
    pasajes = pd.DataFrame(
        [{"passage_id": f"{i}_0", "doc_id": i, "texto": f"Sintético {i}"} for i in range(30)]
    )
    # Solo 19 IDs para 20 plazas: no se duplica silenciosamente.
    with pytest.raises(ValueError, match="imposible"):
        sortear_muestra(ranking, pasajes)
    ranking = pd.concat(
        [ranking, pd.DataFrame([{"query_id": "Q9", "passage_id": "25_0", "rango": 10}])]
    )
    muestra = sortear_muestra(ranking, pasajes)
    assert len(muestra) == 20 and muestra.passage_id.nunique() == 20
    assert muestra.groupby("query_id").size().eq(2).all()
    pd.testing.assert_frame_equal(muestra, sortear_muestra(ranking, pasajes))


@pytest.fixture
def revision(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for d in ["config", "salida", "kit"]:
        (tmp_path / d).mkdir()
    (tmp_path / "salida/06_siglas_candidatas.csv").write_text(
        "sigla,nombre_propuesto,frecuencia,ejemplo\nABC,Organización Ficticia,2,Ejemplo sintético\n"
    )
    for ruta in [
        "kit/gazetteer_dependencias.csv",
        "config/gazetteer_prescrito.csv",
        "config/gazetteer_loc.csv",
    ]:
        (tmp_path / ruta).write_text("nombre,siglas,tipo\n")
    return tmp_path


def test_revision_dos_sesiones_respaldo_cierre_y_congelacion(revision):
    r = revision
    estado = g.cargar(r)
    huellas = g.fuentes(r)
    with pytest.raises(ErrorAnotacion):
        g.guardar(r, estado, huellas, "ABC", "aceptar")
    nuevo = g.guardar(r, estado, huellas, "ABC", "aceptar", "Organización Ficticia", "ORG")
    with pytest.raises(ErrorAnotacion, match="otra pestaña"):
        g.guardar(r, estado, huellas, "ABC", "descartar")
    nuevo = g.guardar(r, nuevo, huellas, "ABC", "descartar")
    assert (r / "config/historial_gazetteer/1_gazetteer_extendido.csv").exists()
    g.cerrar_revision(r, nuevo, huellas, "Persona sintética")
    aprobado = json.loads((r / "config/gazetteer_aprobacion.json").read_text())
    assert aprobado["sha256_extendido"] == g.digest(
        (r / "config/gazetteer_extendido.csv").read_bytes()
    )
    (r / "salida/06_siglas_candidatas.csv").write_text("cambiado")
    with pytest.raises(ErrorAnotacion, match="obsoletos"):
        g.guardar(r, nuevo, huellas, "ABC", "descartar")


def test_interrupcion_no_sobrescribe_y_bloquea(revision, monkeypatch):
    r = revision
    estado = g.cargar(r)
    huellas = g.fuentes(r)
    nuevo = g.guardar(r, estado, huellas, "ABC", "descartar")
    ruta = r / "config/gazetteer_extendido.csv"
    antes = ruta.read_bytes()
    original = g.atomico

    def interrumpir(destino, datos):
        if destino == ruta:
            raise OSError("interrupción sintética")
        original(destino, datos)

    monkeypatch.setattr(g, "atomico", interrumpir)
    with pytest.raises(OSError):
        g.guardar(r, nuevo, huellas, "ABC", "aceptar", "Otra Organización", "ORG")
    assert ruta.read_bytes() == antes
    with pytest.raises(ErrorAnotacion, match="interrumpido"):
        g.guardar(r, g.cargar(r), huellas, "ABC", "descartar")


def test_congelado_bloquea_escritura(revision, monkeypatch):
    monkeypatch.setattr(g, "congelado", lambda raiz: True)
    with pytest.raises(ErrorAnotacion, match="congeladas"):
        g.guardar(revision, g.cargar(revision), g.fuentes(revision), "ABC", "descartar")


def test_muestra_app_no_sobrescribe_ni_anota(tmp_path, monkeypatch):
    from mtx.app import preparacion_gold as m

    (tmp_path / "config").mkdir()
    (tmp_path / "config/protocolo.txt").write_text("saludo sintético")
    ranking = pd.DataFrame(
        [
            {"query_id": f"Q{q}", "passage_id": f"{q}_{i}", "rango": i + 1}
            for q in range(10)
            for i in range(10)
        ]
    )
    pasajes = pd.DataFrame(
        [
            {"passage_id": f"{q}_{i}", "doc_id": q, "texto": "Texto sintético"}
            for q in range(10)
            for i in range(10)
        ]
    )
    monkeypatch.setattr(m, "congelado", lambda raiz: True)
    monkeypatch.setattr(m, "verificar_congelacion", lambda raiz: None)
    monkeypatch.setattr(m, "cargar_ambito", lambda raiz: (ranking, pasajes))
    muestra = m.preparar_muestra(tmp_path)
    assert len(muestra) == 20
    pd.testing.assert_frame_equal(muestra, m.preparar_muestra(tmp_path))
    assert not (tmp_path / "anotaciones/gold_entidades.csv").exists()
    destino = tmp_path / "anotaciones/muestra_gold.csv"
    destino.write_text("Muestra anterior sintética")
    with pytest.raises(ErrorAnotacion, match="conservar"):
        m.preparar_muestra(tmp_path)
    assert destino.read_text() == "Muestra anterior sintética"


def test_vista_gazetteer_sintetica_sin_juicios(revision):
    from streamlit.testing.v1 import AppTest

    codigo = (
        "from pathlib import Path\n"
        "from mtx.app.vista_gazetteer import mostrar\n"
        f"mostrar(Path({str(revision)!r}))\n"
    )
    app = AppTest.from_string(codigo).run()
    assert not app.exception
    app.text_input[0].set_value("Organización Sintética")
    app.selectbox[1].select("ORG")
    app.button[0].click().run()
    assert not app.exception
    estado = g.cargar(revision)
    assert estado["decisiones"]["ABC"]["accion"] == "aceptar"
    assert not (revision / "anotaciones").exists()
