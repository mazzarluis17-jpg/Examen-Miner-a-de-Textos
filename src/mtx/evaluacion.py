"""Evaluación IR oficial, vista temporal complementaria y auditorías (H4, D08)."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import yaml

from . import adaptadores_kit as kit
from . import pool, preproceso
from .app import componentes as c

PROMEDIO = "PROMEDIO (MAP = AP)"
COLUMNAS_IR = ["query_id", "modelo", "P@5", "P@10", "AP", "relevantes_recuperados",
               "relevantes_en_pool", "no_juzgados"]


def escribir_conservando(ruta: Path, contenido: bytes) -> None:
    """Publica un artefacto nuevo o idéntico; nunca pisa una cifra anterior distinta."""
    if ruta.exists():
        if ruta.read_bytes() != contenido:
            raise ValueError(f"Existe un resultado diferente en {ruta}; conservar y revisar versión")
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    c.atomico(ruta, contenido)


def csv_bytes(tabla: pd.DataFrame) -> bytes:
    return tabla.to_csv(index=False, lineterminator="\n").encode("utf-8")


def validar_resultados(tabla: pd.DataFrame, consultas: list[str]) -> None:
    """Exige salida íntegra del kit, métricas finitas y ningún recuperado sin juicio."""
    if list(tabla.columns) != COLUMNAS_IR:
        raise ValueError("Columnas de resultados IR incompatibles con el kit")
    esperadas = {(q, m) for q in [*consultas, PROMEDIO] for m in pool.VARIANTES}
    if (tabla.duplicated(["query_id", "modelo"]).any() or
            set(map(tuple, tabla[["query_id", "modelo"]].values)) != esperadas):
        raise ValueError("Resultados IR incompletos o duplicados")
    metricas = tabla[["P@5", "P@10", "AP"]].to_numpy(dtype=float)
    if not np.isfinite(metricas).all() or not ((metricas >= 0) & (metricas <= 1)).all():
        raise ValueError("Métricas IR fuera de rango")
    if not tabla.loc[tabla.query_id.ne(PROMEDIO), "no_juzgados"].eq(0).all():
        raise ValueError("El ranking contiene pasajes sin juicio")


def elegir_modelo(tabla: pd.DataFrame, hash_ranking: str, hash_juicios: str) -> dict:
    """D08: MAP oficial con filtro, empate exacto a BM25; no usar vista temporal."""
    resumen = tabla[tabla.query_id.eq(PROMEDIO)].set_index("modelo")
    if resumen.index.duplicated().any():
        raise ValueError("Promedios duplicados")
    a, b = "tfidf_con_filtro", "bm25_con_filtro"
    ma, mb = float(resumen.loc[a, "AP"]), float(resumen.loc[b, "AP"])
    if not np.isfinite([ma, mb]).all():
        raise ValueError("MAP inválido")
    ganador, alternativa = (a, b) if ma > mb else (b, a)
    return {"modelo": ganador, "MAP": float(resumen.loc[ganador, "AP"]),
            "alternativa": alternativa, "MAP_alternativa": float(resumen.loc[alternativa, "AP"]),
            "diferencia_menor_0.01": bool(abs(ma - mb) < 0.01),
            "empate_exacto": ma == mb, "criterio": "mayor MAP oficial con filtro; empate a BM25",
            "sha256_ranking": hash_ranking, "sha256_juicios": hash_juicios}


def vista_ventana(juicios: pd.DataFrame, tabla_pool: pd.DataFrame):
    """Deriva relevancia temporal sin alterar el juicio temático original."""
    vista = juicios.merge(tabla_pool[["query_id", "passage_id", "fecha", "en_ventana"]],
                          on=["query_id", "passage_id"], validate="one_to_one")
    vista["relevante_ventana"] = (vista.relevante.eq(1) & vista.en_ventana).astype(int)
    filas = []
    for q, g in vista.groupby("query_id", sort=False):
        fechas = pd.to_datetime(g.fecha, errors="coerce")
        rel = g.relevante.eq(1)
        filas.append({"query_id": q, "relevantes_tematicos": int(rel.sum()),
                      "relevantes_en_ventana": int((rel & g.en_ventana).sum()),
                      "relevantes_fuera_ventana": int((rel & ~g.en_ventana & fechas.notna()).sum()),
                      "relevantes_fecha_desconocida": int((rel & fechas.isna()).sum())})
    return vista, pd.DataFrame(filas)


def etiquetas_consultas(consultas: pd.DataFrame, pasajes: pd.DataFrame, grupos: list) -> pd.DataFrame:
    """Auditoría descriptiva; DF alto >=10% del corpus y nombres/siglas por heurística."""
    tokens = {q.query_id: preproceso.tokenizar(q.consulta) for q in consultas.itertuples()}
    buscados = {t for ts in tokens.values() for t in ts}
    df: Counter = Counter()
    for fila in pasajes.itertuples():
        df.update(buscados.intersection(preproceso.tokenizar_pasaje(fila.texto, fila.inicio_cuerpo)))
    mediana = float(np.median([len(ts) for ts in tokens.values()]))
    filas = []
    for q in consultas.itertuples():
        ts = tokens[q.query_id]
        sinonimos = [" ↔ ".join(g) for g in grupos if any(s.casefold() in q.consulta.casefold()
                                                        for s in g)]
        filas.append({"query_id": q.query_id, "tokens": "|".join(ts), "longitud_tokens": len(ts),
                      "mediana_longitud": mediana, "longitud": "larga" if len(ts) > mediana else "corta",
                      "n_terminos_df_alto": sum(df[t] / len(pasajes) >= 0.1 for t in set(ts)),
                      "umbral_df_alto": 0.1,
                      "siglas_heuristica": bool(re.search(r"\b[A-ZÁÉÍÓÚÑ]{2,}\b", q.consulta)),
                      "nombre_propio_heuristica": bool(re.search(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+", q.consulta)),
                      "sinonimos_conocidos": "|".join(sinonimos),
                      "df_terminos": json.dumps({t: df[t] for t in sorted(set(ts))}, ensure_ascii=False)})
    return pd.DataFrame(filas)


def tablas_comparativas(oficial: pd.DataFrame, temporal: pd.DataFrame,
                       etiquetas: pd.DataFrame, ranking: pd.DataFrame):
    """Tablas anchas y diferencias separadas por criterio; solo lectura de rankings."""
    detalle = oficial[oficial.query_id.ne(PROMEDIO)].copy()
    conteos = ranking.groupby(["query_id", "modelo"]).size()
    detalle["juzgados"] = [int(conteos.loc[q, m] - n)
                           for q, m, n in detalle[["query_id", "modelo", "no_juzgados"]].values]
    valores = ["P@5", "P@10", "AP", "relevantes_recuperados", "relevantes_en_pool",
               "juzgados", "no_juzgados"]
    ancho = detalle.pivot(index="query_id", columns="modelo", values=valores)
    ancho.columns = [f"{metrica}__{modelo}" for metrica, modelo in ancho.columns]
    ancho = ancho.reindex(etiquetas.query_id).reset_index()
    ap = detalle.pivot(index="query_id", columns="modelo", values="AP")
    ganadores = etiquetas.copy()
    ganadores["AP_tfidf_con_filtro"] = ganadores.query_id.map(ap["tfidf_con_filtro"])
    ganadores["AP_bm25_con_filtro"] = ganadores.query_id.map(ap["bm25_con_filtro"])
    ganadores["diferencia_bm25_menos_tfidf"] = (ganadores.AP_bm25_con_filtro -
                                               ganadores.AP_tfidf_con_filtro).round(4)
    ganadores["ganador_AP"] = np.where(ganadores.diferencia_bm25_menos_tfidf.lt(0),
                                       "tfidf_con_filtro", "bm25_con_filtro")
    ganadores["empate_exacto"] = ganadores.diferencia_bm25_menos_tfidf.eq(0)
    comparaciones = []
    for criterio, resultados in (("oficial_tematico", oficial), ("complementaria_ventana", temporal)):
        for q, grupo in resultados.groupby("query_id", sort=False):
            indice = grupo.set_index("modelo")
            for modelo in ("tfidf", "bm25"):
                fila = {"criterio": criterio, "query_id": q, "modelo": modelo}
                for metrica in ("P@5", "P@10", "AP"):
                    con, sin = (float(indice.loc[f"{modelo}_{v}", metrica])
                                for v in ("con_filtro", "sin_filtro"))
                    fila.update({f"{metrica}_con_filtro": con, f"{metrica}_sin_filtro": sin,
                                 f"{metrica}_delta_con_menos_sin": round(con - sin, 4)})
                comparaciones.append(fila)
    return ancho, ganadores, pd.DataFrame(comparaciones)


def figuras_ir(oficial: pd.DataFrame, temporal: pd.DataFrame, destino: Path) -> list[Path]:
    """Tres PNG Plotly/Kaleido; no descarga Chrome ni usa la red."""
    import plotly.express as px
    promedios = oficial[oficial.query_id.eq(PROMEDIO)]
    detalles = oficial[oficial.query_id.ne(PROMEDIO)]
    vistas = pd.concat([promedios.assign(criterio="Oficial temática"),
                        temporal[temporal.query_id.eq(PROMEDIO)].assign(criterio="Complementaria temporal")])
    paleta = ["#24557a", "#358580", "#be8534", "#885d92"]
    figuras = {
        "ir_map_por_modelo": px.bar(promedios, x="modelo", y="AP", color="modelo",
                                    title="MAP oficial por variante", color_discrete_sequence=paleta),
        "ir_ap_por_consulta": px.bar(detalles, x="query_id", y="AP", color="modelo",
                                    barmode="group", title="AP oficial por consulta",
                                    color_discrete_sequence=paleta),
        "ir_con_vs_sin_filtro": px.bar(vistas, x="modelo", y="AP", color="criterio",
                                      barmode="group", title="MAP: criterio temático y temporal",
                                      color_discrete_sequence=paleta),
    }
    destino.mkdir(parents=True, exist_ok=True)
    rutas = []
    for nombre, figura in figuras.items():
        figura.update_layout(template="plotly_white", font_family="Arial", width=1100, height=550,
                             colorway=["#24557a", "#358580", "#be8534", "#885d92"])
        figura.update_yaxes(range=[0, 1], title="MAP" if "consulta" not in nombre else "AP")
        html = destino / f"{nombre}.html"
        figura.write_html(html, include_plotlyjs=True)
        png = destino / f"{nombre}.png"
        figura.write_image(png, scale=2)
        rutas.extend([html, png])
    return rutas


def ejecutar_ir(raiz: Path) -> dict:
    """Orquesta H4 con contexto congelado, evaluador oficial y exportaciones íntegras."""
    ctx = c.cargar_contexto(raiz)
    estado = c.leer_estado(ctx)
    if not c.criterio_aprobado(ctx):
        raise ValueError("Falta aprobación vigente del criterio de relevancia")
    errores, avisos = c.cobertura(ctx, estado)
    if errores:
        raise ValueError("Juicios incompletos o inválidos: " + "; ".join(errores))
    ruta_juicios = raiz / "anotaciones/juicios_relevancia.csv"
    control = raiz / "anotaciones/juicios_relevancia_estado.json"
    congelados = {**ctx.huellas, "anotaciones/juicios_relevancia.csv": estado.sha256,
                  "anotaciones/juicios_relevancia_estado.json": kit.sha256_archivo(control)}
    fuente = ruta_juicios.read_bytes()
    juicios = pd.read_csv(ruta_juicios, dtype={"passage_id": str})
    ranking = pd.read_csv(raiz / "ranking.csv", dtype={"passage_id": str})
    vista, soporte = vista_ventana(juicios, ctx.tabla)
    sinonimos = yaml.safe_load((raiz / "config/sinonimos_consultas.yaml").read_text())["grupos"]
    etiquetas = etiquetas_consultas(ctx.consultas, ctx.pasajes, sinonimos)
    with TemporaryDirectory(prefix="mtx-h4-") as temporal:
        tmp = Path(temporal)
        # Entradas fijadas para los subprocesos; nunca se cambian las fuentes humanas.
        (tmp / "juicios.csv").write_bytes(fuente)
        (tmp / "ranking.csv").write_bytes((raiz / "ranking.csv").read_bytes())
        referencias = vista[pool.COLUMNAS_JUICIOS].copy()
        referencias["relevante"] = vista.relevante_ventana
        (tmp / "juicios_ventana.csv").write_bytes(csv_bytes(referencias))
        salida_oficial = kit.ejecutar_evaluador("ir", tmp / "juicios.csv", tmp / "ranking.csv",
                                              tmp, registro=tmp / "ejecucion_oficial.json")
        contenido_oficial = salida_oficial.read_bytes()
        oficial = pd.read_csv(salida_oficial)
        salida_temporal = kit.ejecutar_evaluador("ir", tmp / "juicios_ventana.csv", tmp / "ranking.csv",
                                               tmp, registro=tmp / "ejecucion_ventana.json")
        contenido_temporal = salida_temporal.read_bytes()
        temporal_df = pd.read_csv(salida_temporal)
        for resultado in (oficial, temporal_df):
            validar_resultados(resultado, list(ctx.consultas.query_id))
        ganador = elegir_modelo(oficial, congelados["ranking.csv"], estado.sha256)
        ancho, ganadores, comparaciones = tablas_comparativas(oficial, temporal_df, etiquetas, ranking)
        seleccionados = ranking[ranking.modelo.eq(ganador["modelo"])].merge(
            ctx.pasajes[["passage_id", "titulo", "interlocutor", "texto", "texto_sha256",
                         "inicio_cuerpo", "es_reportero"]], on="passage_id", validate="many_to_one")
        auditoria_h8 = ctx.consultas.copy()
        soporte_ganador = seleccionados.groupby("query_id").agg(
            pasajes=("passage_id", "size"), discursos_distintos=("doc_id", "nunique"),
            pasajes_reporteros=("es_reportero", "sum"))
        auditoria_h8 = auditoria_h8.merge(soporte_ganador, on="query_id", validate="one_to_one")
        auditoria_h8["modelo_global"] = ganador["modelo"]
        auditoria_h8["MAP_global_oficial"] = ganador["MAP"]
        auditoria_h8["estado_extraccion_y_respuesta"] = "pendiente H5–H8; sin inferir relaciones"
        productos = {
            "juicios_relevancia.csv": fuente, "resultados_ir.csv": contenido_oficial,
            "salida/resultados_ir.csv": contenido_oficial,
            "salida/05_juicios_con_ventana.csv": csv_bytes(vista),
            "salida/05_juicios_ventana_evaluador.csv": csv_bytes(referencias),
            "salida/05_resultados_ir_ventana.csv": contenido_temporal,
            "salida/05_soporte_ventana.csv": csv_bytes(soporte),
            "salida/05_ir_por_consulta.csv": csv_bytes(ancho),
            "salida/05_ir_ganador_por_consulta.csv": csv_bytes(ganadores),
            "salida/05_etiquetas_consultas.csv": csv_bytes(etiquetas),
            "salida/05_comparacion_filtros.csv": csv_bytes(comparaciones),
            "salida/05_pasajes_ganador.csv": csv_bytes(seleccionados),
            "salida/05_auditoria_h8.csv": csv_bytes(auditoria_h8),
            "data/mejor_modelo.json": (json.dumps(ganador, ensure_ascii=False, indent=2) + "\n").encode(),
        }
        for nombre in ("oficial", "ventana"):
            # Se conserva la salida estándar real del subproceso, no una reconstrucción.
            registro = json.loads((tmp / f"ejecucion_{nombre}.json").read_text())
            registro["criterio"] = "oficial_tematico" if nombre == "oficial" else "complementaria_ventana"
            (raiz / "salida").mkdir(exist_ok=True)
            c.atomico(raiz / f"salida/05_ejecucion_{nombre}.json",
                      (json.dumps(registro, ensure_ascii=False, indent=2) + "\n").encode())
        if c.huellas_actuales(raiz, congelados) != congelados:
            raise ValueError("Un insumo congelado cambió durante la evaluación; no publicar resultados")
        for ruta, contenido in productos.items():
            escribir_conservando(raiz / ruta, contenido)
    figuras = figuras_ir(oficial, temporal_df, raiz / "reporte/figuras")
    if c.huellas_actuales(raiz, congelados) != congelados:
        raise ValueError("Cambió un insumo durante la generación de figuras")
    registro = {
        "esquema": 1, "productor": "scripts/05_evaluar_ir.py", "revision_juicios": estado.revision,
        "horizonte": "AP sobre top-10; denominador: relevantes del pool; MAP oficial del kit",
        "procedencia_juicios": "Juicios personales de Luis en Excel, transferencia autorizada; H3 confirmado visualmente",
        "entradas": congelados,
        "auditoria": {"df_alto": "df/N >= 0.10", "longitud_larga": "tokens > mediana",
                      "nombres_y_siglas": "heurísticas descriptivas, sin modificar consultas ni rankings",
                      "sha256_sinonimos": kit.sha256_archivo(raiz / "config/sinonimos_consultas.yaml")},
        "salidas": {ruta: kit.sha256_archivo(raiz / ruta) for ruta in productos},
        "figuras": [str(p.relative_to(raiz)) for p in figuras], "avisos": avisos,
        "alerta_map_bajo": ganador["MAP"] < 0.15,
        "seleccion_global": ganador,
        "codigo_sha256": {r: kit.sha256_archivo(raiz / r) for r in (
            "src/mtx/evaluacion.py", "src/mtx/adaptadores_kit.py", "scripts/05_evaluar_ir.py")},
    }
    c.atomico(raiz / "salida/05_manifiesto_ir.json",
              (json.dumps(registro, ensure_ascii=False, indent=2) + "\n").encode())
    manifiesto_global = raiz / "salida/manifiesto_ejecucion.json"
    global_actual = json.loads(manifiesto_global.read_text()) if manifiesto_global.exists() else {
        "esquema": 1, "alcance": "Registro incremental; etapas IE y entrega pendientes", "etapas": {}}
    global_actual.setdefault("etapas", {})["H4"] = registro
    c.atomico(manifiesto_global,
              (json.dumps(global_actual, ensure_ascii=False, indent=2) + "\n").encode())
    return ganador
