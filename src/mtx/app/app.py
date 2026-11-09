"""Entrada Streamlit: registra vistas; no ejecuta inferencia ni descarga datos."""
from pathlib import Path

import streamlit as st

from mtx import config
from mtx.app import componentes, vista_estado, vista_juicios


@st.cache_resource(show_spinner="Verificando insumos locales…")
def contexto(raiz: str, firma: tuple):
    return componentes.cargar_contexto(Path(raiz))


def main():
    st.set_page_config(page_title="Anotación humana · Minería de Textos", layout="wide")
    st.title("Anotación humana de relevancia")
    if st.sidebar.button("Recargar desde disco"):
        st.session_state.clear()
        contexto.clear()
        st.rerun()
    try:
        rutas = [config.RAIZ / "data/pasajes.parquet", config.RAIZ / "kit/data/discursos.parquet"]
        for directorio in ("config", "salida", "src/mtx"):
            rutas.extend(p for p in (config.RAIZ / directorio).glob("*") if p.is_file())
        rutas.extend([config.RAIZ / "ranking.csv", config.RAIZ / "data/consultas.csv",
                      config.RAIZ / "data/corpus_meta.json"])
        firma = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size)
                      for p in sorted(rutas) if p.exists())
        ctx = contexto(str(config.RAIZ), firma)
        componentes.comprobar_vigencia(ctx)
        if "estado_juicios" not in st.session_state:
            st.session_state["estado_juicios"] = componentes.leer_estado(ctx)
        estado = st.session_state["estado_juicios"]
        componentes.validar_parcial(estado.juicios, ctx)
    except (componentes.ErrorAnotacion, OSError, ValueError) as exc:
        st.error(f"Estado obsoleto o error: {exc}. Se conservan las anotaciones.")
        st.stop()
    estado_tab, juicios_tab, gold_tab, gazetteer_tab = st.tabs(
        ["Estado", "Juicios", "Gold", "Gazetteer"])
    with estado_tab:
        vista_estado.mostrar(ctx, estado)
    with juicios_tab:
        vista_juicios.mostrar(ctx, estado)
    with gold_tab:
        st.info("Pendiente H5/H6. No se cargan ni muestran predicciones.")
    with gazetteer_tab:
        st.info("Pendiente H5. No hay escritura de gazetteer en esta etapa.")


if __name__ == "__main__":
    main()
