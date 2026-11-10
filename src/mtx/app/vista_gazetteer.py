"""Revisión humana explícita; nunca lee juicios, gold ni predicciones."""

import pandas as pd
import streamlit as st

from mtx.app import gazetteer as g
from mtx.app.componentes import ErrorAnotacion


def mostrar(raiz):
    st.header("Gazetteer: revisión humana de candidatos")
    if g.congelado(raiz):
        st.info("Reglas congeladas: revisión de solo lectura.")
        return
    ruta = raiz / "salida/06_siglas_candidatas.csv"
    if not ruta.exists():
        st.info("Pendiente técnico: ejecutar make minar-siglas.")
        return
    try:
        estado = g.cargar(raiz)
        huellas = g.fuentes(raiz)
        tabla = pd.read_csv(ruta, keep_default_na=False)
        base = pd.read_csv(raiz / "kit/gazetteer_dependencias.csv")
        with st.expander("Base del profesor (solo lectura)"):
            st.dataframe(base)
        decisiones = estado["decisiones"]
        rechazadas = sum(d["accion"] == "descartar" for d in decisiones.values())
        st.write(
            f"Base: {len(base)} · nuevas: {len(decisiones) - rechazadas} · rechazadas: {rechazadas} · pendientes: {len(tabla) - len(decisiones)}"
        )
        if tabla.empty:
            st.info("No hay candidatos.")
            return
        pendientes = [s for s in tabla.sigla if s not in decisiones]
        sigla = st.selectbox(
            "Candidato",
            list(tabla.sigla),
            index=list(tabla.sigla).index(pendientes[0]) if pendientes else 0,
        )
        fila = tabla.set_index("sigla").loc[sigla]
        st.text(fila.ejemplo)
        st.caption("Nombre minado (propuesta sin aceptar): " + fila.nombre_propuesto)
        with st.form("revision_" + sigla):
            nombre = st.text_input(
                "Nombre corregido", value=decisiones.get(sigla, {}).get("nombre", "")
            )
            variantes = st.text_input("Variantes separadas por |")
            etiqueta = st.selectbox("Tipo elegido por el alumno", ["ORG", "LOC"], index=None)
            aceptar = st.form_submit_button("Aceptar / corregir")
            descartar = st.form_submit_button("Descartar")
        if aceptar or descartar:
            g.guardar(
                raiz,
                estado,
                huellas,
                sigla,
                "aceptar" if aceptar else "descartar",
                nombre,
                etiqueta,
                variantes,
            )
            st.rerun()
        persona = st.text_input("Nombre del revisor para cierre")
        confirmar = st.checkbox(
            "He revisado todos los candidatos y apruebo los gazetteers prescritos y extendido"
        )
        if st.button("Cerrar revisión humana", disabled=not confirmar):
            g.cerrar_revision(raiz, estado, huellas, persona)
            st.success("Aprobación guardada con hashes. Registrar decisión en docs/decisiones.md.")
    except (OSError, ValueError, ErrorAnotacion) as exc:
        st.error(str(exc))
