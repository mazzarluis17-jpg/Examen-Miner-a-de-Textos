"""Estado de H3 sin exponer la procedencia de recuperación ni predicciones."""
import streamlit as st

from mtx.app import componentes as c


def mostrar(ctx: c.Contexto, estado: c.Estado) -> None:
    st.header("Estado del proyecto")
    errores, avisos = c.cobertura(ctx, estado)
    st.write("Pool: válido (unión e insumos verificados).")
    st.write("Criterio: " + ("válido" if c.criterio_aprobado(ctx) else "pendiente humano"))
    cerrados = int(estado.juicios.relevante.isin(["0", "1"]).sum())
    st.write(f"Juicios: {'pendiente humano' if errores else 'válido'} · "
             f"{cerrados}/{len(ctx.tabla)} · revisión {estado.revision}")
    if errores:
        st.info("Completa los pendientes en Juicios. La cobertura total se exige antes de evaluar IR.")
    for aviso in avisos:
        st.warning(aviso)
    st.write("Gold y selección: pendiente técnico (H5/H6).")
    st.write("Gazetteer extendido: pendiente técnico (H5).")
    st.write("NER y evaluación: pendiente técnico (H4–H7).")
    st.caption("Esta aplicación H3 no lee entidades, caché NER ni predicciones.")
