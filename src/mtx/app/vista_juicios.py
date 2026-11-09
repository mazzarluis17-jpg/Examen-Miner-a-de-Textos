"""Vista ciega al recuperador para decisiones humanas de relevancia."""
import streamlit as st

from mtx.app import componentes as c


def mostrar(ctx: c.Contexto, estado: c.Estado) -> None:
    """Presenta solo contenido y metadatos permitidos; no sugiere respuestas."""
    criterio = ctx.raiz / "config/criterios_relevancia.md"
    with st.expander("Criterios de relevancia", expanded=not c.criterio_aprobado(ctx)):
        st.markdown(criterio.read_text() if criterio.exists() else "Falta definir el criterio.")
    if not c.criterio_aprobado(ctx):
        st.warning("Anotación bloqueada: falta aprobación explícita del criterio y su hash.")
        return
    consulta_id = st.sidebar.selectbox("Consulta", ctx.consultas.query_id.tolist())
    consulta = ctx.consultas.set_index("query_id").loc[consulta_id]
    # Proyección explícita: la vista no accede a procedencia, rangos ni puntajes.
    tabla = ctx.tabla.loc[ctx.tabla.query_id.eq(consulta_id),
                         ["query_id", "passage_id", "doc_id", "fecha", "texto"]].reset_index(drop=True)
    clave = "posicion_" + consulta_id
    if clave not in st.session_state:
        st.session_state[clave] = c.primer_pendiente(tabla, estado.juicios)
    posicion = min(st.session_state[clave], len(tabla) - 1)
    fila = tabla.iloc[posicion]
    terminados = estado.juicios.relevante.isin(["0", "1"])
    locales = estado.juicios.query_id.eq(consulta_id) & terminados
    st.sidebar.write(f"Consulta: {int(locales.sum())}/{len(tabla)}")
    st.sidebar.write(f"Global: {int(terminados.sum())}/{len(ctx.tabla)}")
    st.sidebar.progress(float(terminados.sum() / len(ctx.tabla)))
    st.header(consulta.consulta)
    st.write(consulta.pregunta_extraccion)
    st.info("El juicio es temático: la fecha y el modelo recuperador no cuentan.")
    meta = ctx.pasajes.set_index("passage_id").loc[fila.passage_id]
    st.caption(f"Pasaje {posicion + 1}/{len(tabla)} · {fila.passage_id} · doc_id {fila.doc_id}")
    st.write(f"Título: {meta.titulo}")
    st.write(f"Interlocutor: {meta.interlocutor}")
    st.write(f"Fecha: {fila.fecha or 'desconocida'}")
    st.markdown(c.resaltar(fila.texto, consulta.consulta), unsafe_allow_html=True)
    anterior = estado.juicios.loc[estado.juicios.query_id.eq(consulta_id) &
                                 estado.juicios.passage_id.eq(fila.passage_id), "relevante"]
    valor_actual = anterior.iloc[0] if len(anterior) else ""
    st.caption("Respuesta guardada: " + ({"0": "No relevante", "1": "Relevante"}.get(
        valor_actual, "Sin juzgar")))

    def accion(valor, desplazamiento):
        try:
            actualizado = c.guardar_accion(ctx, estado, consulta_id, fila.passage_id, valor)
            st.session_state["estado_juicios"] = actualizado
            st.session_state[clave] = (posicion + desplazamiento) % len(tabla)
            st.rerun()
        except c.ErrorAnotacion as exc:
            st.error(str(exc))
        except OSError:
            st.error("No se pudo guardar. El respaldo conserva la revisión previa; recarga.")

    botones = st.columns(4)
    if botones[0].button("Relevante (1)"):
        accion("1", 1)
    if botones[1].button("No relevante (0)"):
        accion("0", 1)
    if botones[2].button("Omitir por ahora"):
        accion(None if valor_actual else "", 1)
    if botones[3].button("Anterior", disabled=posicion == 0):
        accion(None, -1)
    if st.sidebar.button("Guardar"):
        accion(None, 0)


