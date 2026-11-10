"""Revisión humana explícita; nunca lee juicios, gold ni predicciones."""

import json

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
        propuesta = raiz / "salida/06_revision_alcance.json"
        if propuesta.exists():
            datos = json.loads(propuesta.read_text())
            st.info(f"Alcance propuesto: {datos['propuestos']}/{datos['originales']}. "
                    "Los restantes quedan fuera de revisión, no rechazados.")
            try:
                g.candidatos_revision(raiz)
            except ErrorAnotacion as exc:
                st.warning(str(exc))
                st.dataframe(pd.read_csv(raiz / "salida/06_revision_alcance.csv")[[
                    "sigla", "pasajes_adicionales", "ocurrencias_adicionales"]])
                return
        estado = g.cargar(raiz)
        huellas = g.fuentes(raiz)
        tabla = pd.DataFrame(g.candidatos_revision(raiz))
        base = pd.read_csv(raiz / "kit/gazetteer_dependencias.csv")
        with st.expander("Base del profesor (solo lectura)"):
            st.dataframe(base)
        with st.expander("Gazetteers prescritos del PRD (solo lectura)"):
            for nombre in ("gazetteer_prescrito.csv", "gazetteer_loc.csv"):
                st.caption(nombre)
                st.dataframe(pd.read_csv(raiz / "config" / nombre, keep_default_na=False))
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
        st.text(fila.get("ejemplo_ambito") or fila.ejemplo)
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
            "He revisado todos los candidatos del alcance aprobado y apruebo los gazetteers prescritos y extendido"
        )
        if st.button("Cerrar revisión humana", disabled=not confirmar):
            g.cerrar_revision(raiz, estado, huellas, persona)
            st.success("Aprobación guardada con hashes. Registrar decisión en docs/decisiones.md.")
    except (OSError, ValueError, ErrorAnotacion) as exc:
        st.error(str(exc))
