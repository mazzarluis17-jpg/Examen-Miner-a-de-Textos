# Progreso — Sistema de recuperación y extracción de información sobre discursos presidenciales

## Completado

- H5 técnico (2026-11-09, rama/worktree `desarrollo-h5`): reglas de cinco tipos,
  auxiliares y normalización prudente; gazetteers prescritos separados de revisión
  humana; candidatos minados sin aceptar. NER principal con revisión fija verificado
  en CPU mediante frases sintéticas; fragmentación, caché cruda perezosa y posproceso
  auditado probados offline. App de revisión Gazetteer con persistencia protegida,
  guardas de congelación y preparación del manifiesto desde la app. Muestreo global
  probado sin generar muestra real. Contratos y límites en `docs/h5_infraestructura.md`.
  Verificación: 262 pruebas rápidas aprobadas y 101 de H5 incluida integración
  con 200 pasajes reales; Ruff limpio. Evidencia en `salida/06_pruebas_h5.json`.
  No se accedió a juicios, gold ni selección; no se ejecutó extracción final sin H4.

- H3 técnico (2026-11-09): aplicación Streamlit en `src/mtx/app/`, vistas Estado y
  Juicios, texto completo con resaltado por offsets y ocultación de procedencia.
  Persistencia atómica, respaldos, diario de revisión y exclusión mutua con detección
  de dos sesiones; validación parcial y de cobertura, IDs y huellas vigentes.
  Propuesta de criterio preparada por autorización del alumno, sin aprobación.
  App bloqueada hasta aprobación explícita ligada al hash. Suite completa:
  170 passed (18 pruebas de app, incluida integración real sin escribir juicios);
  ruff y diff-check limpios. Evidencia en `salida/04_pruebas_h3.json`.

- Continuación individual (2026-11-09, rama `desarrollo-luis`): H1 recuperado desde
  la revisión autorizada en `/tmp`, con Parquet del corpus idéntico al histórico,
  127,739 pasajes y hash de contenido histórico idéntico. Verificadas las 400 filas
  del ranking y sus fragmentos/metadatos. Corpus y pasajes en rutas de trabajo
  ignoradas; referencias originales intactas. Ver `docs/recuperacion_h1.md`.
- H2 técnico (2026-11-09): `pool.py`, `04_pool.py`, T07/T08 y manifiesto de fuentes.
  Pool de 176 pares reproducible byte por byte en dos ejecuciones; avisos Q5/Q7/Q8
  por tamaño inferior al esperado, sin alterar la unión de cuatro variantes.
  Suite completa, incluidas las lentas: 152 passed; ruff limpio. No hay juicios ni gold.

- Arnés (`/harnesser`): CLAUDE.md, AGENTS.md, 17 skills, `docs/harness/`.
- H0 cerrado (2026-11-04): entorno `uv` (Python 3.11, torch CPU, plotly y kaleido), `Makefile`, kit copiado a `kit/` con hashes, `src/mtx/adaptadores_kit.py`, 42 pruebas de contrato, `docs/contratos_kit.md`, `docs/decisiones.md`. Alumno: Daniel Gonzalez. Plazo: entrega y presentación el 11 de noviembre de 2026, presentación a las 20:00 (CDMX). Repo de entrega: este GitLab.
- H1 (2026-11-04): `src/mtx/corpus.py` (limpieza, canonización de marcas, fechas, duplicados, segmentación), `config/limpieza.yaml`, `scripts/01_corpus_y_pasajes.py`, `make corpus` verde: 127,739 pasajes, 5 discursos excluidos, 10 fechas reparadas. Descubrimiento de Q9 y Q10 (`make explorar`, `salida/00_candidatos_q9q10.md`). `data/consultas.csv` con Q9 y Q10 en borrador (`make consultas`). 79 pruebas rápidas verdes.

- H2 en curso (2026-11-08): `preproceso.py`, `indice.py` y `ranking.py` probados. `tests/test_indice.py` (T03, 10 pruebas, contra `CountVectorizer`) y `tests/test_ranking.py` (T04 a T06, 29 pruebas: fórmulas a mano, subclase de `rank_bm25` con 1e-6, ventana de fechas, 0/3/10 candidatos, desempate numérico, marca sin efecto). `scripts/02_indice.py` corrió (`make indice`, 42 s): N = 127,739, vocabulario 35,891, avgdl 72.2, 7.24 M postings, df idéntico al de `CountVectorizer`. Memoria medida: pico de 1.3 GB (el índice como dict no necesita varios GB aquí); `indice.pkl` 43.5 MB. Salidas: `data/{tokens.parquet,indice.pkl,indice_meta.json,tfidf.pkl,tfidf_X.npz}` (las pesadas, ignoradas por git) y `salida/02_{postings.md,vocabulario_top.csv,tokens_consultas.md,memoria.json}`. 133 pruebas rápidas verdes, ruff limpio.

- H2 cerrado salvo juicios (2026-11-08): Q9 y Q10 aprobadas por Daniel (registrado en `docs/decisiones.md`); también confirmó acceso del profesor al repo de GitLab. `scripts/03_ranking.py` (`make ranking`) genera `ranking.csv` (400 filas, copia idéntica en la raíz) y `salida/03_{ranking_detalle,solape_modelos,excluidos_por_filtro}.csv`. `tests/test_ranking_real.py` (lento, 7 pruebas) cubre los criterios bloqueantes: 400 filas y claves únicas, top-10 con filtro dentro de la ventana, Q3 con refinería o Pemex, Q1 con Tren Maya, Q6 con huachicol, TF-IDF distinto de BM25 y `kit/evaluar.py ir` con juicios sintéticos. 140 pruebas verdes (con las lentas). Ningún ranking idéntico entre TF-IDF y BM25; ninguna fila sin señal léxica. Observación para el reporte: la ventana de Q6 (2018-12 a 2019-06) deja solo 11,120 pasajes elegibles y el top-10 sin filtro casi no coincide con el filtrado (1 de 10 en TF-IDF, 0 en BM25).

## Pendiente

- Integrar los commits de `desarrollo-h5` en `desarrollo-luis`, conservando sus
  aprobaciones y cambios posteriores. La rama H5 no hizo merge ni push.
- Tras H4, revisar candidatos íntegros en Gazetteer y cerrar aprobación humana;
  escribir/fijar criterios de anotación y su constancia por hash. Después congelar,
  preparar muestra desde la app y ejecutar extracción del ámbito. No hay etiqueta
  `reglas-congeladas`, revisión de siglas ni criterios de anotación aprobados aquí.
- H6: completar app de anotación Gold, sustitución y cierre; H7: fusión/evaluación.
  Segundo NER/selección (P1) no iniciado mientras hay P0 pendientes.

1. H3 humano: revisar y aprobar o corregir la propuesta completa de
   `config/criterios_relevancia.md` `[VALIDAR]`. Tras aprobación explícita registrar
   decisión y constancia SHA-256 según `docs/pruebas_app.md`; ejecutar `make pool`
   y recargar la app. El alumno captura los juicios; la cobertura total habilita H4.
   No hay aprobación ni archivos de juicios reales al cierre de esta sesión.
2. Revisar `salida/02_vocabulario_top.csv` para la discusión de la stoplist.
3. Luego H4 a H9 (PRD §12.2).

## Decisiones

Ver `docs/decisiones.md`. Las no obvias: el corpus real tiene otro formato de marcas que el PRD (parser propio); acotaciones por lista y no por mayúsculas (se conservan siglas como `(IMSS)`); candidatas de fecha fuera de rango se descartan; el 65 % de las intervenciones de reporteros queda bajo 40 palabras y el reporte debe discutirlo (costo de D02); plotly en lugar de matplotlib por indicación del profesor.

## Bloqueos

- H5 no puede cerrarse oficialmente sin H4, revisión humana de gazetteer, criterios
  de anotación aprobados y congelación. P06 técnico está documentado y el principal
  es provisional; no hay F1 ni decisión humana simulados.
- Entrega individual de Luis requiere GitHub según instrucción actual; resolver
  publicación y acceso al integrar, sin alterar remote histórico de esta rama.

- H3 humano pendiente del usuario actual: aprobación del criterio y captura de juicios;
  bloquea H4. Se conserva la procedencia histórica del trabajo previo de Daniel.
- Stopwords resueltas: `config/stopwords_es.txt` existe y el preprocesador usa la copia versionada.
- Índice, tokens y TF-IDF no se han reconstruido en Debian; no son necesarios para
  construir el pool desde los rankings históricos y pasajes verificados.
- Kaleido necesita el Chrome que instala `plotly_get_chrome` (`make setup` lo hace); los Chromium de snap fallan.
