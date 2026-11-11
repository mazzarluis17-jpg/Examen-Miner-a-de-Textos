# Progreso — Sistema de recuperación y extracción de información sobre discursos presidenciales

## Completado

- (2026-11-10) H6 cerrado personalmente por Luis y verificado por hashes:
  veinte pasajes revisados, 138 entidades, revisión 20; `1133_87` sin entidades.
  Persistencia y cierre oficiales versionados en `ae00990`, sin Excel auxiliar.
  Respaldo externo H7 verificado. Infraestructura H7 de fusión D12, enriquecimiento
  auxiliar separado y evaluación oficial/complementaria preparada; pruebas
  sintéticas nuevas aprobadas. Reglas ejecutadas con configuración congelada.
  Inferencia BETO detenida por span de puntuación que queda vacío tras recorte;
  no se filtra silenciosamente ni se modifica el posproceso congelado.

- (2026-11-10) H5 cerrado: commit `d4ca0a7`, etiqueta oficial
  `reglas-congeladas`. Pruebas generales 294 passed/9 deselected, objetivo
  congelación 92 passed/1 deselected y Ruff limpio. Muestra H6 preparada con
  función oficial de la app: veinte IDs únicos, dos por consulta, semilla 42,
  reproducible byte a byte, hashes vigentes y sin sustituciones objetivas.
  AppTest Gold muestra 0/20 sin errores; no existen entidades, estados ni cierre
  gold. Evidencia técnica: `salida/08_preparacion_h6.json`. Los 302 archivos
  protegidos mantienen sus hashes; no se consultaron predicciones ni hubo push.

- (2026-11-10) Cierre formal humano de Gazetteer verificado: once descartes,
  cero ampliaciones, 76 entradas base conservadas. Aprobaciones IE y alcance
  vigentes; 21 fuentes H4 intactas. Respaldo externo verificado de 302 archivos;
  versionado autorizado de persistencia humana sin cambiar contenidos.

- (2026-11-10) Verificada revisión Gazetteer revisión 11: once descartes humanos,
  ninguna ampliación, fuentes y exportación compatibles; 76 entradas originales
  conservadas. Falta el botón de cierre humano: no existe
  `config/gazetteer_aprobacion.json`. No se congela ni se crea muestra H6 hasta
  ese cierre explícito en la app, conforme al contrato de persistencia.

- (2026-11-10) Luis aprobó explícitamente el alcance de once candidatos y los
  criterios IE sin modificaciones. Constancias y hashes registrados en decisiones;
  Gazetteer habilitado y comprobado sin pulsar botones de decisión. Cero candidatos
  aceptados/rechazados por el asistente; fuera de alcance permanecen no revisados.
  No se ejecuta congelación ni se crea muestra o gold.

- Preparación prioritaria H5/H6 (2026-11-10): propuesta de alcance de once candidatos
  con coincidencias adicionales en cuerpos del ámbito ganador; originales 1,505
  intactos y exclusiones auditadas, sin convertirlas en rechazos humanos. Alcance
  bloqueado hasta aprobación por hash. Criterios IE completos y protocolo preparados
  como propuesta, sin constancias de aprobación. Captura Gold ciega y validador
  implementados: búsqueda con desambiguación, tokens, corrección/borrado, cierre
  vacío, reanudación, guardas D15, persistencia y cierre global. Sin muestra ni gold
  reales, sin congelación. Ver `docs/h5_revision_acotada.md`, `docs/h6_anotacion.md`
  y `salida/06_preparacion_h6_pruebas.json` para evidencia y pruebas.

- Integración H5 (2026-11-10): merge real de `desarrollo-h5` (`e164ca6`) sobre
  `desarrollo-luis` (`c69581c`), conservando los commits y el worktree de origen.
  Único conflicto Git: este registro de progreso; se combinan H4 cerrado, H5
  técnico y notas locales legítimas de H3. Documentación local recuperada desde
  copia externa verificada. Los 254 archivos protegidos mantienen sus hashes;
  no hay cambios ni altas de archivos humanos. Pruebas rápidas: 276 passed,
  9 deselected; offsets reales de reglas: 1 passed; Ruff limpio. App integrada
  arranca sin errores y conserva respuestas, sin pulsar acciones humanas. Evidencia:
  `salida/06_integracion_h5.json`. No se repitieron evaluaciones reales H3/H4 ni
  se inició H6, se ejecutó inferencia o se aprobó ningún criterio nuevo.

- H4 (2026-11-10): Luis confirmó visualmente H3 y autorizó evaluar los rankings
  congelados. Evaluador oficial: ganador global `bm25_con_filtro`, MAP 0.6150
  frente a 0.3998 de TF-IDF con filtro, sin desempate. Sin pasajes no juzgados.
  Vista temporal separada, tablas/auditorías para H8, cien asociaciones del ganador
  (99 IDs únicos), manifiestos y tres figuras PNG generados. Fuentes y métricas:
  `salida/05_validacion_h4.json`, `docs/h4_evaluacion_ir.md`. Suite: 183 passed,
  1 skipped; Ruff limpio. Juicios revisión 197 e insumos históricos intactos.

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

- (2026-11-10) H3: incorporados los 176 juicios humanos de Luis realizados en Excel,
  por transferencia expresamente autorizada y con precedencia ratificada del CSV
  ante los cinco conflictos. Conservados 17, actualizados 5, añadidos 154;
  revisión final 197. Persistencia oficial con respaldos: 113 relevantes,
  63 no relevantes y cero pendientes. Validación nativa sin errores ni avisos;
  AppTest reconoce 176/176, todas las consultas completas y reapertura correcta.
  Pruebas de pool y app: 29 passed, 1 skipped (criterio real ya aprobado).
  Procedencia real documentada en el historial; no se atribuye a captura íntegra
  directa en Streamlit. Sin commits, push, cambios de interfaz ni ejecución de H4.

- (2026-11-09, 17:19 CDMX) Luis aprobó explícitamente el criterio sin cambios.
  Constancia por SHA-256 y decisión registradas; pool real verificado sin cambios.
  Aplicación habilitada para comenzar captura humana; no hay juicios generados.

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

1. Resolver con Luis el bloqueo del posproceso congelado documentado en
   `salida/07_bloqueo_ner.json`; no modificar D15 ni publicar métricas parciales.
2. Tras decisión explícita, completar inferencia H7, fusión y evaluación oficial,
   complementaria de veinte IDs, auditorías y figuras. No reajustar usando Gold.
3. Después H8–H9 según PRD, conservando ganador H4 e insumos congelados.
4. Revisar `salida/02_vocabulario_top.csv` para la discusión de la stoplist.

## Decisiones

Ver `docs/decisiones.md`. Las no obvias: el corpus real tiene otro formato de marcas que el PRD (parser propio); acotaciones por lista y no por mayúsculas (se conservan siglas como `(IMSS)`); candidatas de fecha fuera de rango se descartan; el 65 % de las intervenciones de reporteros queda bajo 40 palabras y el reporte debe discutirlo (costo de D02); plotly en lugar de matplotlib por indicación del profesor.

## Bloqueos

- H3 confirmado por Luis y H4 cerrado; no son bloqueos pendientes de la rama H5.
- H6 cerrado y validado. H7 bloqueado: en `1812_0` BETO emite LOC
  `[945:946]` con texto de una comilla; `posprocesar()` congelado aborta tras
  recortarla. Se solicita autorización para una versión separada auditada;
  no se modifica el congelado ni se evalúa una extracción incompleta.
- Entrega individual en GitHub según decisión documentada en H5. Publicación y
  acceso del profesor pendientes; no se cambia el remote ni se hace push aquí.
- Índice, tokens y TF-IDF no se han reconstruido en Debian; no se requieren para
  integrar las reglas y NER ni para conservar los resultados de H4.
- Stopwords resueltas con copia versionada; figuras H4 ya exportadas con Chrome local.
