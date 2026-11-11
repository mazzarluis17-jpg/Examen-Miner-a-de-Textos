"""Opiniones solo de fixtures sintéticas: reanudación, concurrencia y cierre técnico."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from mtx.app import valoraciones as v
from mtx.app.componentes import ErrorAnotacion, sha256
from mtx.respuestas import COLUMNAS, hash_tabla


@pytest.fixture
def ctx(tmp_path):
    for d in ["anotaciones", "data", "salida/tablas_respuesta"]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    consultas = pd.DataFrame(
        [
            {
                "query_id": f"Q{i}",
                "consulta": f"Consulta {i}",
                "pregunta_extraccion": f"Pregunta {i}",
            }
            for i in range(1, 11)
        ]
    )
    consultas.to_csv(tmp_path / "data/consultas.csv", index=False)
    filas = []
    hashes = {}
    salidas = {}
    for q in consultas.query_id:
        texto = f"# {q}\n\nTabla sintética sin entidades.\n\nvaloracion:\n[VALIDAR] pendiente del alumno\n"
        ruta = f"salida/tablas_respuesta/{q}.md"
        (tmp_path / ruta).write_text(texto)
        hashes[q] = hash_tabla(texto)
        salidas[ruta] = sha256(texto.encode())
        f = dict.fromkeys(COLUMNAS, "")
        f.update(query_id=q, campo_respuesta="campo", estado="no_encontrado")
        filas.append(f)
    pd.DataFrame(filas, columns=COLUMNAS).to_csv(tmp_path / "salida/respuestas.csv", index=False)
    salidas["salida/respuestas.csv"] = sha256((tmp_path / "salida/respuestas.csv").read_bytes())
    (tmp_path / "salida/10_hashes_tablas.json").write_text(json.dumps(hashes))
    fuentes = {"data/consultas.csv": sha256((tmp_path / "data/consultas.csv").read_bytes())}
    archivos = {}
    for clave, nombre in [("Evaluación", "gold_entidades.csv"), ("estados", "estado_gold.csv")]:
        (tmp_path / "anotaciones" / nombre).write_text("Fixture técnica\n")
        archivos[clave] = sha256((tmp_path / "anotaciones" / nombre).read_bytes())
    control = {"revision": 1, "archivos": archivos, "fuentes": fuentes}
    (tmp_path / "anotaciones/gold_revision.json").write_text(json.dumps(control))
    (tmp_path / "anotaciones/cierre_gold.json").write_text(
        json.dumps({**control, "fecha": "2020-01-01", "anotado_por": "Fixture"})
    )
    (tmp_path / "salida/10_manifiesto_respuestas.json").write_text(
        json.dumps({"entradas": fuentes, "salidas": salidas})
    )
    return v.cargar_contexto(tmp_path)


def opinion(q):
    return f"Texto humano simulado {q}, exclusivo de fixture.\nSegunda línea ficticia."


def test_abrir_no_crea_valoraciones_y_guardar_reanuda(ctx):
    estado = v.leer(ctx)
    assert estado["revision"] == 0 and v.completadas(ctx, estado) == []
    assert not (ctx["raiz"] / "anotaciones/valoraciones.yaml").exists()
    nuevo = v.guardar(ctx, estado, "Q1", opinion("Q1"))
    assert v.leer(ctx) == nuevo and nuevo["revision"] == 1
    assert v.completadas(ctx, nuevo) == ["Q1"]
    assert nuevo["valoraciones"]["Q1"]["valoracion"] == opinion("Q1")


def test_respaldos_y_dos_pestanas_sin_sobrescritura(ctx):
    inicial = v.leer(ctx)
    primera = v.guardar(ctx, inicial, "Q1", opinion("Q1"))
    with pytest.raises(ErrorAnotacion, match="otra pestaña"):
        v.guardar(ctx, inicial, "Q2", opinion("Q2"))
    archivo = (ctx["raiz"] / "anotaciones/valoraciones.yaml").read_bytes()
    segunda = v.guardar(ctx, primera, "Q2", opinion("Q2"))
    assert segunda["revision"] == 2
    assert (
        ctx["raiz"] / "anotaciones/historial_valoraciones/1_valoraciones.yaml"
    ).read_bytes() == archivo


@pytest.mark.parametrize("texto", ["", "  ", "[VALIDAR] pendiente del alumno"])
def test_no_inventa_opinion_ni_guarda_plantilla(ctx, texto):
    with pytest.raises(ErrorAnotacion):
        v.guardar(ctx, v.leer(ctx), "Q1", texto)
    assert not (ctx["raiz"] / "anotaciones/valoraciones.yaml").exists()


def test_fuentes_cambiadas_bloquean_guardado(ctx):
    estado = v.leer(ctx)
    (ctx["raiz"] / "salida/respuestas.csv").write_text("Cambio no permitido")
    with pytest.raises(ErrorAnotacion, match="cambiaron"):
        v.guardar(ctx, estado, "Q1", opinion("Q1"))


def test_interrupcion_detectada_y_respaldo_conservado(ctx, monkeypatch):
    estado = v.guardar(ctx, v.leer(ctx), "Q1", opinion("Q1"))
    original = (ctx["raiz"] / "anotaciones/valoraciones.yaml").read_bytes()
    atomico = v.atomico

    def interrumpir(ruta, datos):
        if ruta.name == "valoraciones.yaml":
            raise OSError("Interrupción sintética")
        atomico(ruta, datos)

    monkeypatch.setattr(v, "atomico", interrumpir)
    with pytest.raises(OSError):
        v.guardar(ctx, estado, "Q2", opinion("Q2"))
    assert (ctx["raiz"] / "anotaciones/valoraciones.yaml").read_bytes() == original
    assert (
        ctx["raiz"] / "anotaciones/historial_valoraciones/1_valoraciones.yaml"
    ).read_bytes() == original
    with pytest.raises(ErrorAnotacion, match="interrumpido"):
        v.leer(ctx)


def test_yamls_duplicados_o_editados_no_se_sobrescriben(ctx):
    ruta = ctx["raiz"] / "anotaciones/valoraciones.yaml"
    ruta.write_text("Q1: {}\nQ1: {}\n")
    with pytest.raises(ErrorAnotacion, match="duplicadas"):
        v.leer(ctx)


def test_cierre_solo_con_diez_y_comando_estricto(ctx, monkeypatch):
    inicial = v.leer(ctx)
    with pytest.raises(ErrorAnotacion, match="pendiente"):
        v.finalizar(ctx, inicial)
    estado = inicial
    for q in ctx["hashes"]:
        estado = v.guardar(ctx, estado, q, opinion(q))
    assert len(v.completadas(ctx, estado)) == 10
    llamadas = []

    def ejecutar(args, **kwargs):
        llamadas.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="", args=args)

    monkeypatch.setattr(v.subprocess, "run", ejecutar)
    antes = (ctx["raiz"] / "anotaciones/valoraciones.yaml").read_bytes()
    sello = v.finalizar(ctx, estado)
    assert llamadas[0][-1] == "--exigir-valoraciones" and sello["consultas_valoradas"] == 10
    assert (ctx["raiz"] / "anotaciones/valoraciones.yaml").read_bytes() == antes
    assert not (ctx["raiz"] / "reporte").exists()


def test_ui_guardar_avanza_y_reanuda_sin_opiniones_precargadas(ctx):
    codigo = (
        "from pathlib import Path\nfrom mtx.app.vista_valoraciones import mostrar\nmostrar(Path("
        + repr(str(ctx["raiz"]))
        + "))"
    )
    at = AppTest.from_string(codigo).run()
    assert not at.exception and not at.error
    assert at.text_area[0].value == ""
    at.text_area[0].set_value(opinion("Q1"))
    next(b for b in at.button if b.label == "Guardar valoración y continuar").click().run()
    assert not at.exception and not at.error
    assert next(s for s in at.selectbox if s.label == "Consulta a valorar").value == "Q2"
    assert at.text_area[0].value == ""
    otra = AppTest.from_string(codigo).run()
    assert next(s for s in otra.selectbox if s.label == "Consulta a valorar").value == "Q2"
    assert v.completadas(ctx, v.leer(ctx)) == ["Q1"]


def test_hash_de_tabla_obsoleto_conserva_opinion(ctx):
    estado = v.guardar(ctx, v.leer(ctx), "Q1", opinion("Q1"))
    actualizado = {**ctx, "hashes": {**ctx["hashes"], "Q1": "otro hash"}}
    assert v.completadas(actualizado, estado) == []
    assert estado["valoraciones"]["Q1"]["valoracion"] == opinion("Q1")


def test_sin_cierre_gold_no_carga_evidencia(ctx):
    (ctx["raiz"] / "anotaciones/cierre_gold.json").unlink()
    with pytest.raises(ErrorAnotacion, match="cierre Gold"):
        v.cargar_contexto(ctx["raiz"])


def test_ui_decima_valoracion_ejecuta_cierre_estricto(ctx, monkeypatch):
    llamadas = []

    def ejecutar(args, **kwargs):
        llamadas.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="", args=args)

    monkeypatch.setattr(v.subprocess, "run", ejecutar)
    codigo = (
        "from pathlib import Path\nfrom mtx.app.vista_valoraciones import mostrar\nmostrar(Path("
        + repr(str(ctx["raiz"]))
        + "))"
    )
    at = AppTest.from_string(codigo).run()
    for i in range(1, 11):
        assert at.text_area[0].value == ""
        at.text_area[0].set_value(opinion(f"Q{i}"))
        next(b for b in at.button if b.label == "Guardar valoración y continuar").click().run()
        assert not at.exception and not at.error
    assert len(llamadas) == 1 and llamadas[0][-1] == "--exigir-valoraciones"
    assert len(v.completadas(ctx, v.leer(ctx))) == 10
    assert any("H8 validado" in s.value for s in at.success)


def test_manifiestos_no_pueden_sustituir_hash_del_cierre(ctx):
    ruta = ctx["raiz"] / "salida/10_manifiesto_respuestas.json"
    m = json.loads(ruta.read_text())
    m["entradas"]["data/consultas.csv"] = "hash diferente"
    ruta.write_text(json.dumps(m))
    with pytest.raises(ErrorAnotacion, match="incompatibles"):
        v.cargar_contexto(ctx["raiz"])
