"""Captura gold ciega: únicamente texto y anotaciones humanas existentes."""
import pandas as pd
import streamlit as st

from mtx import gold
from mtx.app import preparacion_gold


@st.cache_resource(show_spinner="Verificando muestra y congelación…")
def contexto(raiz, firma):
    return gold.cargar_contexto(raiz)


def mostrar(raiz):
    st.header("Gold: anotación humana ciega")
    if not (raiz/"anotaciones/muestra_gold.csv").exists():
        st.info("Falta muestra ciega: aprobar H5 y congelar antes de anotar.")
        preparacion_gold.mostrar(raiz)
        return
    if st.button("Recargar gold desde disco"):
        st.session_state.pop("gold_estado", None)
        contexto.clear()
        st.rerun()
    try:
        archivos = [*list((raiz/"config").glob("*")), raiz/"anotaciones/muestra_gold.csv",
                    raiz/"anotaciones/muestra_seleccion.csv", raiz/"data/pasajes.parquet",
                    raiz/"data/mejor_modelo.json", raiz/"data/modelo_ner.json", raiz/"salida/ranking.csv"]
        firma = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size)
                      for p in sorted(archivos) if p.is_file())
        ctx = contexto(raiz, firma)
        gold.comprobar_fuentes(ctx)
        if "gold_estado" not in st.session_state:
            st.session_state["gold_estado"] = gold.leer(ctx)
        estado = st.session_state["gold_estado"]
        opciones = ["Selección","Evaluación"] if "Selección" in ctx["muestras"] else ["Evaluación"]
        conjunto = st.selectbox("Conjunto gold", opciones)
        muestra = ctx["muestras"][conjunto]
        estados = estado["tablas"]["estados"]
        cerrados = set(estados.loc[estados.estado.eq("cerrado"), "passage_id"])
        if (conjunto == "Evaluación" and "Selección" in ctx["muestras"] and
                not set(ctx["muestras"]["Selección"].passage_id) <= cerrados):
            st.info("Completar primero el conjunto de selección disjunto.")
            return
        pendientes = [p for p in muestra.passage_id if p not in cerrados]
        st.write(f"Pasajes revisados: {len(cerrados & set(muestra.passage_id))}/{len(muestra)}")
        progreso = muestra[["query_id","passage_id"]].copy()
        progreso["revisado"] = progreso.passage_id.isin(cerrados)
        st.sidebar.caption("Progreso gold por consulta")
        st.sidebar.dataframe(progreso.groupby("query_id",sort=False).agg(
            revisados=("revisado","sum"),total=("passage_id","size")))
        pid = st.selectbox("Pasaje gold", muestra.passage_id.tolist(),
                           index=muestra.passage_id.tolist().index(pendientes[0]) if pendientes else 0)
        fila = ctx["pasajes"].set_index("passage_id").loc[pid]
        entidades = estado["tablas"][conjunto]
        actuales = entidades[entidades.passage_id.eq(pid)].reset_index(drop=True)
        st.caption("Texto completo; la marca gris también se anota. No se cargan predicciones.")
        st.markdown(gold.renderizar(fila.texto, actuales, int(fila.inicio_cuerpo)), unsafe_allow_html=True)
        st.markdown((raiz/"config/criterios_anotacion.md").read_text())
        st.write("Entidades anotadas por tipo:", entidades.tipo.value_counts().to_dict())
        cerrado_global = (raiz/"anotaciones/cierre_gold.json").exists()
        cerrado_pasaje = pid in cerrados

        def persistir(nuevas, cerrar=False):
            st.session_state["gold_estado"] = gold.guardar(ctx, estado, conjunto, pid, nuevas, cerrar)
            st.rerun()

        if cerrado_global:
            st.success("Gold cerrado: consulta de solo lectura. No se muestran predicciones aquí.")
        elif cerrado_pasaje:
            st.success("Pasaje revisado completo; válido también con cero entidades.")
            if st.button("Reabrir pasaje para corregir"):
                persistir(actuales)
        else:
            modo = st.radio("Selección de span", ["Buscar texto exacto", "Seleccionar tokens"])
            span = None
            if modo == "Buscar texto exacto":
                buscado = st.text_input("Texto exacto a anotar", key="buscar_"+pid)
                opciones = gold.ocurrencias(fila.texto, buscado)
                eleccion = st.selectbox("Aparición (elige explícitamente)", opciones, index=None,
                    format_func=lambda ab: f"[{ab[0]}:{ab[1]}] "+fila.texto[max(0,ab[0]-40):ab[1]+40])
                span = eleccion
            else:
                ts = gold.tokens(fila.texto)
                primero = st.selectbox("Primer token", range(len(ts)), index=None,
                                        format_func=lambda i: f"{i}: {ts[i][2]}")
                ultimo = st.selectbox("Último token", range(len(ts)), index=None,
                                       format_func=lambda i: f"{i}: {ts[i][2]}")
                recortar = st.checkbox("Recortar puntuación final (conservar $)", value=True)
                if primero is not None and ultimo is not None:
                    span = gold.span_tokens(fila.texto, primero, ultimo, recortar)
            tipo = st.selectbox("Tipo elegido por el alumno", gold.TIPOS, index=None)
            if st.button("Agregar entidad", disabled=span is None or tipo is None):
                a, b = span
                nueva = pd.DataFrame([[pid,tipo,fila.texto[a:b],str(a),str(b)]], columns=gold.COLUMNAS)
                persistir(pd.concat([actuales,nueva],ignore_index=True))
            if len(actuales):
                editor = actuales[["tipo","inicio","fin"]].copy()
                editor["inicio"] = editor.inicio.astype(int)
                editor["fin"] = editor.fin.astype(int)
                editor["Eliminar"] = False
                editado = st.data_editor(editor, hide_index=True, key="editar_"+pid,
                    column_config={"tipo": st.column_config.SelectboxColumn(options=gold.TIPOS)})
                if st.button("Guardar correcciones / eliminaciones"):
                    nuevas = []
                    for f in editado.itertuples(index=False):
                        if not f.Eliminar:
                            a,b = int(f.inicio),int(f.fin)
                            nuevas.append([pid,f.tipo,fila.texto[a:b],str(a),str(b)])
                    persistir(pd.DataFrame(nuevas,columns=gold.COLUMNAS))
            if st.button("Pasaje revisado completo (puede tener cero entidades)"):
                persistir(actuales, True)
        if not actuales.empty:
            st.dataframe(actuales, hide_index=True)
        if not cerrado_global:
            persona = st.text_input("Nombre del anotador para cierre gold")
            confirmar = st.checkbox("Revisé todos los pasajes completos sin consultar predicciones")
            if st.button("Cerrar gold de evaluación", disabled=not confirmar):
                gold.cerrar_gold(ctx, estado, persona)
                st.rerun()
    except (ValueError, OSError, KeyError) as exc:
        st.error(str(exc))
