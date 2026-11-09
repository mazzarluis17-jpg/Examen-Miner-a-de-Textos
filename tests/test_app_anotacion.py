"""T15 · Persistencia, aislamiento, modo ciego y Streamlit con fixtures sintéticos."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from mtx import config, corpus, pool
from mtx.app import componentes as c


@pytest.fixture
def ctx(tmp_path):
    """Solo crea insumos y aprobación ficticios bajo tmp_path, nunca en el repo."""
    (tmp_path / "config").mkdir()
    (tmp_path / "salida").mkdir()
    criterio = tmp_path / "config/criterios_relevancia.md"
    criterio.write_text("Criterio del fixture sintético")
    digest = c.sha256(criterio.read_bytes())
    (tmp_path / "config/criterios_relevancia_aprobacion.json").write_text(json.dumps({
        "sha256_criterio": digest, "aprobado_por": "persona ficticia", "fecha": "2000-01-01"}))
    (tmp_path / "salida/04_pool_meta.json").write_text(json.dumps({"fuentes": {
        "config/criterios_relevancia.md": digest}}))
    textos = ["😀 <script> & tren de prueba " + "contenido completo " * 40, "Texto de prueba final"]
    pasajes = pd.DataFrame([{
        "passage_id": f"{i}_0", "doc_id": i, "texto": t, "texto_sha256": corpus.sha256_texto(t),
        "titulo": "Título ficticio", "interlocutor": "PERSONA DE PRUEBA"}
        for i, t in enumerate(textos)])
    (tmp_path / "data").mkdir()
    pasajes.to_parquet(tmp_path / "data/pasajes.parquet", index=False)
    filas = []
    for q in ("Q1", "Q2"):
        for fila in pasajes.itertuples():
            filas.append({"query_id": q, "passage_id": fila.passage_id,
                          "doc_id": fila.doc_id, "fecha": "2020-01-01", "texto": fila.texto,
                          "texto_sha256": fila.texto_sha256, "variantes": "SECRETO_VARIANTE",
                          "mejor_rango_tfidf": 919, "mejor_rango_bm25": 818})
    tabla = pd.DataFrame(filas)
    consultas = pd.DataFrame([{"query_id": q, "consulta": "tren de prueba",
                               "pregunta_extraccion": "Pregunta ficticia"} for q in ("Q1", "Q2")])
    huellas = c.huellas_actuales(tmp_path, ["data/pasajes.parquet", "config/criterios_relevancia.md",
        "config/criterios_relevancia_aprobacion.json", "salida/04_pool_meta.json"])
    return c.Contexto(tmp_path, tabla, consultas, pasajes, huellas)


def test_arranque_no_crea_archivos_y_bloquea_sin_aprobacion(ctx):
    (ctx.raiz / "config/criterios_relevancia_aprobacion.json").unlink()
    estado = c.leer_estado(ctx)
    assert estado.juicios.empty
    assert not (ctx.raiz / "anotaciones").exists()
    with pytest.raises(c.ErrorAnotacion):
        c.guardar_accion(ctx, estado, "Q1", "0_0", "1")
    assert not (ctx.raiz / "anotaciones").exists()


def test_t15_guardado_reanudacion_omitir_y_asociacion_independiente(ctx):
    estado = c.leer_estado(ctx)
    estado = c.guardar_accion(ctx, estado, "Q1", "0_0", "1")
    estado = c.guardar_accion(ctx, estado, "Q1", "1_0", "")
    recargado = c.leer_estado(ctx)
    assert recargado.revision == 2
    assert recargado.juicios.relevante.tolist() == ["1", ""]
    assert c.primer_pendiente(ctx.tabla, recargado.juicios) == 1
    assert not recargado.juicios.query_id.eq("Q2").any()
    assert (ctx.raiz / "anotaciones/juicios_relevancia.csv").read_text().startswith(
        "query_id,doc_id,passage_id,relevante\n")
    assert c.cobertura(ctx, estado)[0]


def test_t15_dos_pestanas_no_pierden_respuestas(ctx):
    primera = c.leer_estado(ctx)
    segunda = c.leer_estado(ctx)
    c.guardar_accion(ctx, primera, "Q1", "0_0", "0")
    ruta = ctx.raiz / "anotaciones/juicios_relevancia.csv"
    antes = ruta.read_bytes()
    with pytest.raises(c.ErrorAnotacion, match="otra pestaña"):
        c.guardar_accion(ctx, segunda, "Q1", "1_0", "1")
    assert ruta.read_bytes() == antes


def test_t15_interrupcion_antes_del_reemplazo_csv(ctx, monkeypatch):
    estado = c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "0_0", "1")
    ruta = ctx.raiz / "anotaciones/juicios_relevancia.csv"
    antes = ruta.read_bytes()
    reemplazar = c.os.replace

    def interrumpir(origen, destino):
        if Path(destino) == ruta:
            raise OSError("interrupción simulada")
        reemplazar(origen, destino)

    monkeypatch.setattr(c.os, "replace", interrumpir)
    with pytest.raises(OSError):
        c.guardar_accion(ctx, estado, "Q1", "1_0", "0")
    assert ruta.read_bytes() == antes
    assert c.leer_estado(ctx).revision == estado.revision
    assert any(p.read_bytes() == antes for p in
               (ctx.raiz / "anotaciones/historial_juicios").glob("*.csv"))
    monkeypatch.setattr(c.os, "replace", reemplazar)
    assert c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "1_0", "0").revision == 2


def test_t15_insumo_cambiado_conserva_juicios(ctx):
    estado = c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "0_0", "1")
    ruta = ctx.raiz / "anotaciones/juicios_relevancia.csv"
    antes = ruta.read_bytes()
    (ctx.raiz / "config/criterios_relevancia.md").write_text("Cambió el criterio")
    with pytest.raises(c.ErrorAnotacion, match="obsoletos"):
        c.guardar_accion(ctx, estado, "Q1", "1_0", "0")
    assert ruta.read_bytes() == antes


def test_t15_texto_cambiado_en_parquet_invalida_sin_borrar(ctx):
    estado = c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "0_0", "1")
    ruta = ctx.raiz / "anotaciones/juicios_relevancia.csv"
    antes = ruta.read_bytes()
    cambiados = ctx.pasajes.copy()
    cambiados.loc[0, "texto"] = "Texto cambiado después del juicio sintético"
    cambiados.to_parquet(ctx.raiz / "data/pasajes.parquet", index=False)
    with pytest.raises(c.ErrorAnotacion, match="obsoletos"):
        c.guardar_accion(ctx, estado, "Q1", "1_0", "0")
    ctx.huellas = c.huellas_actuales(ctx.raiz, ctx.huellas)
    with pytest.raises(c.ErrorAnotacion, match="obsoletos"):
        c.leer_estado(ctx)
    assert ruta.read_bytes() == antes


@pytest.mark.parametrize("valor", ["2", "probable", "nan"])
def test_rechaza_etiquetas_invalidas(ctx, valor):
    with pytest.raises(c.ErrorAnotacion):
        c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "0_0", valor)


def test_ids_ajenos_y_omitir_no_borra(ctx):
    estado = c.guardar_accion(ctx, c.leer_estado(ctx), "Q1", "0_0", "0")
    with pytest.raises(c.ErrorAnotacion, match="ajeno"):
        c.guardar_accion(ctx, estado, "Q1", "999_0", "1")
    with pytest.raises(c.ErrorAnotacion, match="no borra"):
        c.guardar_accion(ctx, estado, "Q1", "0_0", "")
    assert c.leer_estado(ctx).juicios.relevante.tolist() == ["0"]


@pytest.mark.parametrize("problema", ["duplicado", "doc_id", "relevante", "columnas"])
def test_no_modifica_archivos_existentes_invalidos(ctx, problema):
    directorio = ctx.raiz / "anotaciones"
    directorio.mkdir()
    j = pd.DataFrame([["Q1", "0", "0_0", "1"]], columns=pool.COLUMNAS_JUICIOS)
    if problema == "duplicado":
        j = pd.concat([j, j])
    elif problema == "doc_id":
        j.loc[0, "doc_id"] = "99"
    elif problema == "relevante":
        j.loc[0, "relevante"] = "2"
    else:
        j = j.drop(columns="doc_id")
    ruta = directorio / "juicios_relevancia.csv"
    j.to_csv(ruta, index=False)
    antes = ruta.read_bytes()
    with pytest.raises(c.ErrorAnotacion):
        c.leer_estado(ctx)
    assert ruta.read_bytes() == antes


def test_html_escapado_y_offsets_unicode():
    texto = "😀 <script> & tren tren"
    salida = c.resaltar(texto, "tren")
    assert "&lt;script&gt;" in salida and "&amp;" in salida
    assert "<script>" not in salida
    assert salida.count("<mark>tren</mark>") == 2
    assert "😀" in salida


def app_sintetica(ctx, monkeypatch):
    monkeypatch.setattr(config, "RAIZ", ctx.raiz)
    monkeypatch.setattr(c, "cargar_contexto", lambda raiz: ctx)
    entrada = Path(__file__).resolve().parents[1] / "src/mtx/app/app.py"
    return AppTest.from_file(entrada, default_timeout=30).run()


def boton(app, label):
    return next(b for b in app.button if b.label == label)


def contenido_visible(app):
    return "\n".join(x.value for tipo in (app.markdown, app.caption, app.info, app.warning)
                     for x in tipo)


def test_streamlit_bloqueado_y_modo_ciego(ctx, monkeypatch):
    (ctx.raiz / "config/criterios_relevancia_aprobacion.json").unlink()
    ctx.huellas = c.huellas_actuales(ctx.raiz, ctx.huellas)
    (ctx.raiz / "salida/entidades.csv").write_text("PREDICCION_SECRETA")
    app = app_sintetica(ctx, monkeypatch)
    assert not app.exception
    assert any("bloqueada" in x.value for x in app.warning)
    assert not any(b.label == "Relevante (1)" for b in app.button)
    assert "PREDICCION_SECRETA" not in contenido_visible(app)
    assert not (ctx.raiz / "anotaciones").exists()


def test_streamlit_navegacion_persistencia_y_ocultacion(ctx, monkeypatch):
    app = app_sintetica(ctx, monkeypatch)
    assert not app.exception
    assert "SECRETO_VARIANTE" not in contenido_visible(app)
    assert "919" not in contenido_visible(app) and "818" not in contenido_visible(app)
    assert any(x.value == c.resaltar(ctx.tabla.iloc[0].texto, "tren de prueba")
               for x in app.markdown)
    boton(app, "Relevante (1)").click().run()
    assert not app.exception
    boton(app, "Anterior").click().run()
    assert not app.exception
    assert any("Respuesta guardada: Relevante" in x.value for x in app.caption)
    boton(app, "Omitir por ahora").click().run()
    boton(app, "No relevante (0)").click().run()
    assert c.leer_estado(ctx).juicios.relevante.tolist() == ["1", "0"]
    boton(app, "Recargar desde disco").click().run()
    assert not app.exception


@pytest.mark.lento
@pytest.mark.skipif(not config.PASAJES_PARQUET.exists(), reason="requiere pasajes recuperados")
def test_streamlit_real_arranca_bloqueado_sin_anotaciones():
    """Lee insumos reales; nunca pulsa botones de juicio ni escribe etiquetas."""
    if (config.RAIZ / "config/criterios_relevancia_aprobacion.json").exists():
        pytest.skip("La sesión humana ya tiene criterio aprobado")
    ruta = config.RAIZ / "anotaciones/juicios_relevancia.csv"
    previo = ruta.read_bytes() if ruta.exists() else None
    entrada = Path(__file__).resolve().parents[1] / "src/mtx/app/app.py"
    app = AppTest.from_file(entrada, default_timeout=60).run()
    assert not app.exception and not app.error
    assert any("bloqueada" in x.value for x in app.warning)
    assert (ruta.read_bytes() if ruta.exists() else None) == previo
