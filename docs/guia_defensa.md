# Guía de defensa técnica

Borrador de estudio: no certifica comprensión, aprobación ni ensayo del alumno.

## src/mtx/__init__.py

Sistema de recuperación y extracción de información sobre discursos presidenciales.

API que debe explicarse: importación del paquete.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/adaptadores_kit.py

Único punto de contacto con el kit del profesor (`kit/`).

API que debe explicarse: cargar_modulo_corpus, ejecutar_evaluador, sha256_archivo, hashes_registrados, verificar_hashes.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/alcance_gazetteer.py

Alcance auditable previo a D15: presencia léxica, nunca decisiones de entidad.

API que debe explicarse: analizar, preparar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_alcance_gazetteer.py::test_presencia_cuerpo_marca_cubiertos_y_ausentes`. La entrada está en sus fixtures y la salida esperada se verifica mediante `seleccion.sigla.tolist()==["DEF"]`. Ver [test_alcance_gazetteer.py](../tests/test_alcance_gazetteer.py#L11).

## src/mtx/ambito_ie.py

Frontera H4→H5: ningún ganador o pasaje se elige por conveniencia.

API que debe explicarse: cargar_ambito.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/app/__init__.py

Aplicación local de captura humana; no carga modelos ni usa la red.

API que debe explicarse: importación del paquete.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/app/app.py

Entrada Streamlit: registra vistas; no ejecuta inferencia ni descarga datos.

API que debe explicarse: contexto, main.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_app_anotacion.py::test_arranque_no_crea_archivos_y_bloquea_sin_aprobacion`. La entrada está en sus fixtures y la salida esperada se verifica mediante `estado.juicios.empty`. Ver [test_app_anotacion.py](../tests/test_app_anotacion.py#L49).

## src/mtx/app/componentes.py

Contratos, resaltado y persistencia compartidos por las vistas de anotación.

API que debe explicarse: ErrorAnotacion, Contexto, Estado, sha256, huellas_actuales, cargar_contexto, comprobar_vigencia, criterio_aprobado, validar_parcial, _rutas, _leer, leer_estado, atomico, guardar_accion, primer_pendiente, resaltar, gold_cerrado, cobertura.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/app/gazetteer.py

Persistencia de decisiones humanas de gazetteer, aislada de los juicios H3.

API que debe explicarse: digest, congelado, cargar, fuentes, candidatos_revision, exportar, guardar, cerrar_revision.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_alcance_gazetteer.py::test_presencia_cuerpo_marca_cubiertos_y_ausentes`. La entrada está en sus fixtures y la salida esperada se verifica mediante `seleccion.sigla.tolist()==["DEF"]`. Ver [test_alcance_gazetteer.py](../tests/test_alcance_gazetteer.py#L11).

## src/mtx/app/preparacion_gold.py

Solo preparación de manifiesto H5, sin entidades ni anotación H6.

API que debe explicarse: preparar_muestra, mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_gold.py::test_busqueda_ambigua_tokens_unicode_y_html`. La entrada está en sus fixtures y la salida esperada se verifica mediante `gold.ocurrencias(texto,"Banco")==[(3,8),(10,15)]`. Ver [test_gold.py](../tests/test_gold.py#L39).

## src/mtx/app/valoraciones.py

Persistencia de opiniones humanas H8: hashes, revisiones, cerrojo y respaldos.

API que debe explicarse: YAMLHumano, _mapa, cargar_contexto, comprobar_fuentes, _leer, leer, completadas, _respaldar, guardar, finalizar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_valoraciones_app.py::test_abrir_no_crea_valoraciones_y_guardar_reanuda`. La entrada está en sus fixtures y la salida esperada se verifica mediante `estado["revision"] == 0 and v.completadas(ctx, estado) == []`. Ver [test_valoraciones_app.py](../tests/test_valoraciones_app.py#L65).

## src/mtx/app/vista_estado.py

Estado de H3 sin exponer la procedencia de recuperación ni predicciones.

API que debe explicarse: mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/app/vista_gazetteer.py

Revisión humana explícita; nunca lee juicios, gold ni predicciones.

API que debe explicarse: mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_alcance_gazetteer.py::test_presencia_cuerpo_marca_cubiertos_y_ausentes`. La entrada está en sus fixtures y la salida esperada se verifica mediante `seleccion.sigla.tolist()==["DEF"]`. Ver [test_alcance_gazetteer.py](../tests/test_alcance_gazetteer.py#L11).

## src/mtx/app/vista_gold.py

Captura gold ciega: únicamente texto y anotaciones humanas existentes.

API que debe explicarse: contexto, mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_gold.py::test_busqueda_ambigua_tokens_unicode_y_html`. La entrada está en sus fixtures y la salida esperada se verifica mediante `gold.ocurrencias(texto,"Banco")==[(3,8),(10,15)]`. Ver [test_gold.py](../tests/test_gold.py#L39).

## src/mtx/app/vista_juicios.py

Vista ciega al recuperador para decisiones humanas de relevancia.

API que debe explicarse: mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/app/vista_valoraciones.py

Valoración humana rápida de Q1–Q10, sin calificaciones ni opiniones sugeridas.

API que debe explicarse: mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_valoraciones_app.py::test_abrir_no_crea_valoraciones_y_guardar_reanuda`. La entrada está en sus fixtures y la salida esperada se verifica mediante `estado["revision"] == 0 and v.completadas(ctx, estado) == []`. Ver [test_valoraciones_app.py](../tests/test_valoraciones_app.py#L65).

## src/mtx/config.py

Rutas del repositorio, constantes y carga de `config/*.yaml`.

API que debe explicarse: cargar_yaml.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/congelacion.py

Guardas de D15: no crea aprobaciones ni decide por el alumno.

API que debe explicarse: verificar_congelacion.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_congelacion_politicas_h8.py::test_config_nueva_compatible_sin_debilitar_archivos_congelados`. La entrada está en sus fixtures y la salida esperada se verifica mediante `test_config_nueva_compatible_sin_debilitar_archivos_congelados`. Ver [test_congelacion_politicas_h8.py](../tests/test_congelacion_politicas_h8.py#L14).

## src/mtx/consultas.py

`data/consultas.csv` = filas del kit tal cual + Q9 + Q10 (PRD §3.2, §5.2).

API que debe explicarse: construir, cargar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_consultas.py::test_q1_a_q8_quedan_literales_y_q9_q10_se_agregan_al_final`. La entrada está en sus fixtures y la salida esperada se verifica mediante `list(todas.columns) == consultas.COLUMNAS`. Ver [test_consultas.py](../tests/test_consultas.py#L17).

## src/mtx/corpus.py

Carga, limpieza auditada y segmentación del corpus (PRD §6.1, D02 a D05).

API que debe explicarse: sin_acentos, normalizar_para_hash, sha256_texto, _kit_corpus, cargar, commit_dataset, huella_corpus, _compilar, _recortar_a_ultima_oracion, _marcar_en_linea, _parentesis_balanceados, limpiar_texto, partir_canonico, _fecha_valida, candidata_titulo, candidata_url, reparar_fecha, _shingles, detectar_duplicados, limpiar_ruido, es_reportero, segmentar_con_descartes, segmentar, hash_pasajes, _clave_id, estadisticas_corpus, escribir_json.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_corpus.py::test_marca_tilde_se_canoniza_a_una_linea_por_intervencion`. La entrada está en sus fixtures y la salida esperada se verifica mediante `limpio(t, rx) == ("\nPRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR: Buenos días."
                             "\nPREGUNTA: Gracias, presidente.")`. Ver [test_corpus.py](../tests/test_corpus.py#L27).

## src/mtx/demo.py

Demostración sin red sobre consultas y artefactos congelados.

API que debe explicarse: cargar, mostrar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/descubrimiento.py

Descubrimiento guiado de Q9 y Q10 (PRD §5.2). Calcula señal; el alumno elige.

API que debe explicarse: cuerpo_normalizado, analizar_candidato, _ejemplos, a_markdown.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_descubrimiento.py::test_conteos_en_corpus_y_en_ventana`. La entrada está en sus fixtures y la salida esperada se verifica mediante `(r["pasajes_total"], r["pasajes_ventana"]) == (2, 1)`. Ver [test_descubrimiento.py](../tests/test_descubrimiento.py#L27).

## src/mtx/enriquecimiento.py

Representaciones auxiliares H7; no modifica el normalizador congelado ni spans.

API que debe explicarse: numero_decimal, monto_auxiliar, fecha_auxiliar, enriquecer.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_enriquecimiento.py::test_montos_decimal`. La entrada está en sus fixtures y la salida esperada se verifica mediante `monto_auxiliar(texto)['valor_num']==valor`. Ver [test_enriquecimiento.py](../tests/test_enriquecimiento.py#L17).

## src/mtx/entrega.py

Artefactos de H9 derivados exclusivamente de resultados existentes.

API que debe explicarse: sha, tablas, tex, tabla_tex, reporte.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/evaluacion.py

Evaluación IR oficial, vista temporal complementaria y auditorías (H4, D08).

API que debe explicarse: escribir_conservando, csv_bytes, validar_resultados, elegir_modelo, vista_ventana, etiquetas_consultas, tablas_comparativas, figuras_ir, ejecutar_ir.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_evaluacion_ie.py::test_detalle_contra_kit_y_complementaria_vacia`. La entrada está en sus fixtures y la salida esperada se verifica mediante `c.loc[c.metodo.eq('combinado')&c.tipo.eq('TODOS'),'FP'].iloc[0]==1`. Ver [test_evaluacion_ie.py](../tests/test_evaluacion_ie.py#L16).

## src/mtx/evaluacion_ie.py

Evaluación IE oficial, complemento de veinte IDs y auditoría de errores.

API que debe explicarse: verificar_cierre, validar_entidades, vista_metodo, sin_union_interpalabra, detalle_ie, analizar_errores.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_evaluacion_ie.py::test_detalle_contra_kit_y_complementaria_vacia`. La entrada está en sus fixtures y la salida esperada se verifica mediante `c.loc[c.metodo.eq('combinado')&c.tipo.eq('TODOS'),'FP'].iloc[0]==1`. Ver [test_evaluacion_ie.py](../tests/test_evaluacion_ie.py#L16).

## src/mtx/fusion.py

Fusión D12 por clave exacta, sin consultar anotaciones humanas.

API que debe explicarse: fusionar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_fusion.py::test_fusion_exacta_solapes_y_pasaje_compartido`. La entrada está en sus fixtures y la salida esperada se verifica mediante `len(unica)==4 and len(oficial)==8`. Ver [test_fusion.py](../tests/test_fusion.py#L8).

## src/mtx/gold.py

Contratos y edición humana del gold ciego; sin dependencias de extractores.

API que debe explicarse: sha, verificar_d15, validar_spans, validar_gold, cargar_contexto, comprobar_fuentes, archivos_gold, _leer, leer, guardar, cerrar_gold, ocurrencias, tokens, span_tokens, renderizar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_gold.py::test_busqueda_ambigua_tokens_unicode_y_html`. La entrada está en sus fixtures y la salida esperada se verifica mediante `gold.ocurrencias(texto,"Banco")==[(3,8),(10,15)]`. Ver [test_gold.py](../tests/test_gold.py#L39).

## src/mtx/indice.py

Índice invertido construido a mano (PRD §6.3).

API que debe explicarse: identidad, Indice, construir, matriz_conteos, guardar, cargar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_indice.py::test_conteos_conocidos`. La entrada está en sus fixtures y la salida esperada se verifica mediante `ind.N == len(CUERPOS)`. Ver [test_indice.py](../tests/test_indice.py#L37).

## src/mtx/muestreo.py

Preparación H5: emparejamiento global reproducible, sin anotar entidades.

API que debe explicarse: sortear_muestra.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/ner_modelo.py

NER CPU: ventanas completas, caché cruda y posproceso independiente (D18).

API que debe explicarse: clave_cache, cargar_pipeline, fragmentar, validar_span, inferir_crudo, posprocesar, procesar_pasaje.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/ner_posproceso_v2.py

Corrección autorizada posterior a D15; la versión congelada queda intacta.

API que debe explicarse: posprocesar_auditado, procesar_pasaje_auditado.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/normalizacion.py

Normalización prudente: nunca altera spans ni inventa fechas relativas.

API que debe explicarse: normalizar_numero, normalizar_fecha, normalizar_monto.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## src/mtx/pool.py

Pool reproducible de cuatro variantes y validación de juicios (D06, D07).

API que debe explicarse: construir, serializar, guardar, validar_juicios.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_pool.py::test_t07_union_procedencia_y_rangos`. La entrada está en sus fixtures y la salida esperada se verifica mediante `len(tabla) == 10 and avisos`. Ver [test_pool.py](../tests/test_pool.py#L30).

## src/mtx/preproceso.py

Preprocesamiento para IR (PRD §6.2, D03).

API que debe explicarse: stoplist, hash_stoplist, configuracion_efectiva, _raiz, tokenizar_sin_stem, tokenizar, tokenizar_pasaje.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_preproceso.py::test_terminos_clave_de_las_consultas_sobreviven`. La entrada está en sus fixtures y la salida esperada se verifica mediante `clave in sin_stem`. Ver [test_preproceso.py](../tests/test_preproceso.py#L16).

## src/mtx/ranking.py

Ranking TF-IDF (coseno) y BM25 propio con filtro de fecha (PRD §6.4, U9, U10).

API que debe explicarse: BM25, ajustar_tfidf, Tfidf, guardar_tfidf, cargar_tfidf, validar_ventana, mascara_fecha, top_k, Buscador, variantes_oficiales.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_ranking.py::test_bm25_a_mano`. La entrada está en sus fixtures y la salida esperada se verifica mediante `test_bm25_a_mano`. Ver [test_ranking.py](../tests/test_ranking.py#L45).

## src/mtx/reglas.py

Extracción determinista sobre caracteres canónicos (PRD §6.7).

API que debe explicarse: Entidad, cargar_gazetteers, resolver_colisiones, extraer_con_auditoria, extraer_reglas, extraer_auxiliares, minar_siglas.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_reglas.py::test_positivos_exactos`. La entrada está en sus fixtures y la salida esperada se verifica mediante `[e.texto for e in entidades] == [span]`. Ver [test_reglas.py](../tests/test_reglas.py#L53).

## src/mtx/respuestas.py

H8: respuestas conservadoras con evidencia literal, sin reextraer entidades.

API que debe explicarse: normalizar, decimal_estable, oraciones, contexto, cargar_listas, validar_politica, seleccionar, preparar_candidatos, tokens_globales, fase_evento, evento, oracion_del_span, ancla_local, limites_inequivocos, relacion_directa, generar_respuestas, validar_respuestas, hash_tabla, validar_valoraciones, escapar, renderizar_tablas.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Ejemplo ejecutable: `uv run --no-sync pytest -q tests/test_respuestas.py::test_t14_reportero_no_atribuido_y_coocurrencia_ambigua`. La entrada está en sus fixtures y la salida esperada se verifica mediante `r.estado.eq("ambiguo").all()`. Ver [test_respuestas.py](../tests/test_respuestas.py#L128).

## src/mtx/validacion_entrega.py

Contratos de entrega de H9. Valida sin escribir datos humanos ni resultados históricos.

API que debe explicarse: validar_csv, verificar.

Entradas y salidas: consultar las firmas y docstrings; distinguir valores retornados de archivos persistidos.

Invariante transversal: conservar IDs y texto original; las anotaciones humanas no se generan por inferencia.

Entrada/salida de integración: ejecutar la demo Q3 y comprobar IDs, tipos y citas contra los CSV raíz; los módulos de composición no se evalúan aisladamente.

## Fórmulas y ejemplos numéricos de estudio

Estos ejemplos son sintéticos, no métricas de la colección.

- BM25: idf(t)=ln(1+(N-df+0.5)/(df+0.5)); k1=1.5, b=0.75.
  Para N=10, df=1: idf=ln(1+9.5/1.5). El término crece menos que linealmente con tf.
- TF-IDF: (1+ln(tf))*(ln((1+N)/(1+df))+1), seguido de normalización L2.
- Coseno: producto punto entre vectores normalizados; vectores iguales dan 1.
- P@k: relevantes/k. Dos relevantes entre cinco producen P@5=0.4.
- AP@10: suma P@r*rel(r), dividida entre relevantes del pool, incluidos los no recuperados.
- MAP: promedio de AP de las diez consultas, no promedio de puntajes BM25.
- IE: P=TP/(TP+FP), R=TP/(TP+FN), F1=2PR/(P+R).
  TP exige mismo pasaje, tipo, inicio y fin; texto parcial o tipo distinto no coincide.

## Casos reales que deben revisarse

Los postings de huachicol están en salida/02_postings.md; las diferencias por
consulta, en salida/05_ir_ganador_por_consulta.csv. La entidad partida de
1458_12, SEDENA en 326_25 y la discrepancia ORG/LOC de 228_7 están documentadas
en salida/09_auditoria_ie.json. No son propuestas de corrección del Gold.

La demo obligatoria se ejecuta con `make demo Q=Q3`. Consulte laminas/guion.md
para preguntas, tiempo presupuestado y registro pendiente del ensayo humano.
