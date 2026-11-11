# Guía de defensa técnica

Borrador para estudio y revisión humana; no acredita un ensayo.

## src/mtx/__init__.py

Sistema de recuperación y extracción de información sobre discursos presidenciales.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: .

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/adaptadores_kit.py

Único punto de contacto con el kit del profesor (`kit/`).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: cargar_modulo_corpus, ejecutar_evaluador, sha256_archivo, hashes_registrados, verificar_hashes.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/alcance_gazetteer.py

Alcance auditable previo a D15: presencia léxica, nunca decisiones de entidad.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: analizar, preparar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/ambito_ie.py

Frontera H4→H5: ningún ganador o pasaje se elige por conveniencia.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: cargar_ambito.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/__init__.py

Aplicación local de captura humana; no carga modelos ni usa la red.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: .

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/app.py

Entrada Streamlit: registra vistas; no ejecuta inferencia ni descarga datos.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: contexto, main.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/componentes.py

Contratos, resaltado y persistencia compartidos por las vistas de anotación.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: ErrorAnotacion, Contexto, Estado, sha256, huellas_actuales, cargar_contexto, comprobar_vigencia, criterio_aprobado, validar_parcial, _rutas, _leer, leer_estado, atomico, guardar_accion, primer_pendiente, resaltar, gold_cerrado, cobertura.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/gazetteer.py

Persistencia de decisiones humanas de gazetteer, aislada de los juicios H3.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: digest, congelado, cargar, fuentes, candidatos_revision, exportar, guardar, cerrar_revision.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/preparacion_gold.py

Solo preparación de manifiesto H5, sin entidades ni anotación H6.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: preparar_muestra, mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/valoraciones.py

Persistencia de opiniones humanas H8: hashes, revisiones, cerrojo y respaldos.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: YAMLHumano, _mapa, cargar_contexto, comprobar_fuentes, _leer, leer, completadas, _respaldar, guardar, finalizar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/vista_estado.py

Estado de H3 sin exponer la procedencia de recuperación ni predicciones.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/vista_gazetteer.py

Revisión humana explícita; nunca lee juicios, gold ni predicciones.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/vista_gold.py

Captura gold ciega: únicamente texto y anotaciones humanas existentes.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: contexto, mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/vista_juicios.py

Vista ciega al recuperador para decisiones humanas de relevancia.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/app/vista_valoraciones.py

Valoración humana rápida de Q1–Q10, sin calificaciones ni opiniones sugeridas.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/config.py

Rutas del repositorio, constantes y carga de `config/*.yaml`.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: cargar_yaml.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/congelacion.py

Guardas de D15: no crea aprobaciones ni decide por el alumno.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: verificar_congelacion.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/consultas.py

`data/consultas.csv` = filas del kit tal cual + Q9 + Q10 (PRD §3.2, §5.2).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: construir, cargar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/corpus.py

Carga, limpieza auditada y segmentación del corpus (PRD §6.1, D02 a D05).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: sin_acentos, normalizar_para_hash, sha256_texto, _kit_corpus, cargar, commit_dataset, huella_corpus, _compilar, _recortar_a_ultima_oracion, _marcar_en_linea, _parentesis_balanceados, limpiar_texto, partir_canonico, _fecha_valida, candidata_titulo, candidata_url, reparar_fecha, _shingles, detectar_duplicados, limpiar_ruido, es_reportero, segmentar_con_descartes, segmentar, hash_pasajes, _clave_id, estadisticas_corpus, escribir_json.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/demo.py

Demostración sin red sobre consultas y artefactos congelados.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: cargar, mostrar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/descubrimiento.py

Descubrimiento guiado de Q9 y Q10 (PRD §5.2). Calcula señal; el alumno elige.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: cuerpo_normalizado, analizar_candidato, _ejemplos, a_markdown.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/enriquecimiento.py

Representaciones auxiliares H7; no modifica el normalizador congelado ni spans.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: numero_decimal, monto_auxiliar, fecha_auxiliar, enriquecer.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/entrega.py

Artefactos de H9 derivados exclusivamente de resultados existentes.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: sha, tablas, tex, tabla_tex, reporte.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/evaluacion.py

Evaluación IR oficial, vista temporal complementaria y auditorías (H4, D08).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: escribir_conservando, csv_bytes, validar_resultados, elegir_modelo, vista_ventana, etiquetas_consultas, tablas_comparativas, figuras_ir, ejecutar_ir.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/evaluacion_ie.py

Evaluación IE oficial, complemento de veinte IDs y auditoría de errores.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: verificar_cierre, validar_entidades, vista_metodo, sin_union_interpalabra, detalle_ie, analizar_errores.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/fusion.py

Fusión D12 por clave exacta, sin consultar anotaciones humanas.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: fusionar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/gold.py

Contratos y edición humana del gold ciego; sin dependencias de extractores.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: sha, verificar_d15, validar_spans, validar_gold, cargar_contexto, comprobar_fuentes, archivos_gold, _leer, leer, guardar, cerrar_gold, ocurrencias, tokens, span_tokens, renderizar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/indice.py

Índice invertido construido a mano (PRD §6.3).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: identidad, Indice, construir, matriz_conteos, guardar, cargar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/muestreo.py

Preparación H5: emparejamiento global reproducible, sin anotar entidades.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: sortear_muestra.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/ner_modelo.py

NER CPU: ventanas completas, caché cruda y posproceso independiente (D18).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: clave_cache, cargar_pipeline, fragmentar, validar_span, inferir_crudo, posprocesar, procesar_pasaje.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/ner_posproceso_v2.py

Corrección autorizada posterior a D15; la versión congelada queda intacta.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: posprocesar_auditado, procesar_pasaje_auditado.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/normalizacion.py

Normalización prudente: nunca altera spans ni inventa fechas relativas.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: normalizar_numero, normalizar_fecha, normalizar_monto.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/pool.py

Pool reproducible de cuatro variantes y validación de juicios (D06, D07).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: construir, serializar, guardar, validar_juicios.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/preproceso.py

Preprocesamiento para IR (PRD §6.2, D03).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: stoplist, hash_stoplist, configuracion_efectiva, _raiz, tokenizar_sin_stem, tokenizar, tokenizar_pasaje.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/ranking.py

Ranking TF-IDF (coseno) y BM25 propio con filtro de fecha (PRD §6.4, U9, U10).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: BM25, ajustar_tfidf, Tfidf, guardar_tfidf, cargar_tfidf, validar_ventana, mascara_fecha, top_k, Buscador, variantes_oficiales.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/reglas.py

Extracción determinista sobre caracteres canónicos (PRD §6.7).

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: Entidad, cargar_gazetteers, resolver_colisiones, extraer_con_auditoria, extraer_reglas, extraer_auxiliares, minar_siglas.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/respuestas.py

H8: respuestas conservadoras con evidencia literal, sin reextraer entidades.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: normalizar, decimal_estable, oraciones, contexto, cargar_listas, validar_politica, seleccionar, preparar_candidatos, tokens_globales, fase_evento, evento, oracion_del_span, ancla_local, limites_inequivocos, relacion_directa, generar_respuestas, validar_respuestas, hash_tabla, validar_valoraciones, escapar, renderizar_tablas.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## src/mtx/validacion_entrega.py

Contratos de entrega de H9. Valida sin escribir datos humanos ni resultados históricos.

Entradas: argumentos explícitos y rutas descritas en sus docstrings.

Salidas: valores o artefactos definidos por esas funciones; comprobar contratos en tests/.

Funciones/clases: validar_csv, verificar.

Ejemplo de estudio: localizar una prueba de este módulo en tests/ y explicar sus entradas sintéticas y sus aserciones.

Integridad: nunca interpretar un ejemplo sintético como anotación humana ni resultado real.

## Fórmulas que deben explicarse

BM25: idf(t)=ln(1+(N-df+0.5)/(df+0.5)); k1=1.5, b=0.75.
Su saturación divide tf*(k1+1) entre tf+k1*(1-b+b*longitud/avgdl).
TF-IDF: (1+ln(tf))*(ln((1+N)/(1+df))+1), con normalización L2.
Coseno: producto punto de vectores normalizados.
AP@10: suma P@r*rel(r), dividida entre relevantes del pool de la consulta.
MAP: promedio de AP de las diez consultas. P@k: relevantes/k.
IE: P=TP/(TP+FP), R=TP/(TP+FN), F1=2PR/(P+R), coincidencia de span exacto.

Las métricas oficiales y complementarias se distinguen en salida/. Véanse
laminas/guion.md para preguntas y docs/decisiones.md para decisiones congeladas.
