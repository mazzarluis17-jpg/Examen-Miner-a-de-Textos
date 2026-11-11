"""Valoración humana rápida de Q1–Q10, sin calificaciones ni opiniones sugeridas."""

import json
import subprocess

import streamlit as st

from mtx.app import valoraciones as v


def mostrar(raiz):
    st.header("Valoraciones humanas de respuestas · H8")
    st.caption(
        "Una consulta a la vez. Revisa las citas y escribe 2–3 líneas: ¿es creíble?, ¿qué falta?, ¿qué está mal?"
    )
    if st.button("Recargar valoraciones desde disco"):
        for k in list(st.session_state):
            if k.startswith("val_"):
                del st.session_state[k]
        st.rerun()
    try:
        if "val_ctx" not in st.session_state:
            st.session_state.val_ctx = v.cargar_contexto(raiz)
        ctx = st.session_state.val_ctx
        v.comprobar_fuentes(ctx)
        if "val_estado" not in st.session_state:
            st.session_state.val_estado = v.leer(ctx)
        estado = st.session_state.val_estado
        hechas = v.completadas(ctx, estado)
        consultas = ctx["consultas"].set_index("query_id")
        opciones = ctx["consultas"].query_id.tolist()
        pendientes = [q for q in opciones if q not in hechas]
        st.write(f"Valoraciones vigentes: {len(hechas)}/10")
        st.progress(len(hechas) / 10)
        if "val_siguiente" in st.session_state:
            st.session_state.val_query = st.session_state.pop("val_siguiente")
        if "val_query" not in st.session_state:
            st.session_state.val_query = pendientes[0] if pendientes else opciones[0]
        q = st.selectbox(
            "Consulta a valorar",
            opciones,
            key="val_query",
            format_func=lambda x: f"{x} · {'guardada' if x in hechas else 'pendiente'}",
        )
        st.subheader(consultas.loc[q, "pregunta_extraccion"])
        st.markdown(ctx["tablas"][q])
        with st.expander("Evidencia completa y offsets"):
            filas = ctx["respuestas"][ctx["respuestas"].query_id.eq(q)]
            con_evidencia = filas[filas.passage_id.ne("")].reset_index(drop=True)
            if len(con_evidencia):
                indice = st.selectbox(
                    "Cita a consultar",
                    range(len(con_evidencia)),
                    format_func=lambda i: (
                        f"{con_evidencia.iloc[i].campo_respuesta} · {con_evidencia.iloc[i].valor} · {con_evidencia.iloc[i].estado} · {con_evidencia.iloc[i].passage_id}"
                    ),
                )
                f = con_evidencia.iloc[indice]
                st.caption(
                    f"Documento {f.doc_id} · {f.fecha_documento} · {f.interlocutor} · pasaje {f.passage_id} [{f.evidencia_inicio}:{f.evidencia_fin}]"
                )
                st.code(f.cita, language=None)
            else:
                st.info("Sin evidencia en el top-10; no completar con conocimiento externo.")
        st.caption("Huella de la tabla valorada: " + ctx["hashes"][q])
        entrada = estado["valoraciones"].get(q, {})
        if entrada.get("valoracion") and entrada.get("tabla_sha256") != ctx["hashes"][q]:
            st.warning(
                "La tabla cambió: tu texto anterior se conserva, pero requiere revisión personal."
            )
        texto = st.text_area(
            "Valoración personal (2–3 líneas)",
            value=entrada.get("valoracion", ""),
            key=f"val_texto_{q}_{estado['revision']}",
            height=130,
            help="Escribe con tus palabras la credibilidad, lo que falta y los errores. No hay una nota numérica exigida.",
        )
        st.caption(
            "Pulsa Guardar antes de salir o cambiar de consulta. Se conservan respaldos y revisión."
        )
        if st.button("Guardar valoración y continuar", type="primary"):
            nuevo = v.guardar(ctx, estado, q, texto)
            st.session_state.val_estado = nuevo
            faltan = [x for x in opciones if x not in v.completadas(ctx, nuevo)]
            if not faltan:
                v.finalizar(ctx, nuevo)
                st.session_state.pop("val_ctx", None)
            st.session_state.val_siguiente = faltan[0] if faltan else q
            st.rerun()
        if len(hechas) == 10:
            ruta = raiz / "salida/10_cierre_h8.json"
            sello = json.loads(ruta.read_text()) if ruta.exists() else {}
            if (
                sello.get("sha256_valoraciones") == estado["sha256"]
                and sello.get("revision") == estado["revision"]
                and sello.get("tablas") == ctx["hashes"]
            ):
                st.success(
                    "H8 validado: 10/10 valoraciones humanas guardadas e incorporadas a las tablas. H9 no iniciado."
                )
            elif st.button("Validar las diez valoraciones y completar H8"):
                v.finalizar(ctx, estado)
                st.session_state.pop("val_ctx", None)
                st.rerun()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        st.error(str(exc))
