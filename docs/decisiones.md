# Decisiones del proyecto

## Fase 0 (2026-11-04)

- SO: Linux x86_64 (Ubuntu, kernel 6.8)  Python: 3.12.3 del sistema; el proyecto usa 3.11.18 vía `uv` (`.python-version`)  uv: 0.11.14  pandoc: 3.1.3  TeX: XeTeX (TeX Live 2023), disponible para `make reporte`.
- Acceso a Hugging Face: la API del dataset `carevies/discursos_AMLO` responde 200 (2026-11-04). La descarga completa del corpus se prueba en H1.
- Repo: remoto en GitLab (`git@gitlab.com:oscar.acosta.mac/text-mining-ir-er.git`); el PRD habla de GitHub y del nombre `examen1-mineria-textos`. El alumno confirmó el 2026-11-04 que se entrega en este repo de GitLab. Pendiente verificar que el profesor tenga acceso (el enunciado habla de GitHub).
- Alumno: Daniel Gonzalez (portada y láminas). Falta confirmar si requiere apellido completo adicional.
- Plazo vigente: **entrega el 11 de noviembre de 2026** (nuevo plazo informado por el alumno el 2026-11-04; hora de entrega no indicada). **Presentación el 11 de noviembre de 2026 a las 20:00 (CDMX)**, según el alumno. El enunciado original fijaba entrega el 28 de octubre a las 20:00 y presentación el 4 de noviembre.
- Q9: tema elegido por el alumno el 2026-11-04: Banco del Bienestar. Redacción en `config/consultas_q9q10.yaml`, **borrador pendiente de `[VALIDAR]`** (ventana 2019-01-01 a 2023-12-31 y pregunta tomadas de los candidatos del PRD).
- Q10: tema elegido por el alumno el 2026-11-04: Tren Interoceánico. Misma situación (ventana 2020-01-01 a 2024-06-30).
- Horas disponibles: pendiente.
- Utilerías: mensaje en `docs/mensaje_profesor_utilerias.md`, enviado por el alumno (fecha exacta no registrada, antes del 2026-11-04). Respuesta del profesor (relatada por el alumno): todo está bien excepto `matplotlib`; usar `plotly` o `cufflinks`.
- Estado previo: ninguno. Repo con arnés y PRD; sin commit entregado ni artefactos en `salida/` o `anotaciones/`.
- Kit del profesor: copiado en `kit/` (cuatro archivos más `README.md`), sin modificar; hashes en `docs/contratos_kit.md`.

## Contratos del kit (2026-11-04): ver docs/contratos_kit.md; diferencias con el PRD: `metodo` desconocido cuenta en `combinado`; el pasaje gold sin entidades no se evalúa y no penaliza falsos positivos; `evaluar.py` escribe en el directorio actual; `cargar_corpus` conserva columnas extra; juicios duplicados inflan el denominador de AP; ranking vacío revienta el evaluador. Q1 a Q8 coinciden literalmente con el PRD §5.1; el gazetteer tiene 76 entradas y 10 tipos.

## Decisiones posteriores

- (2026-11-09) H3 técnico: se implementan las vistas Estado/Juicios y componentes
  compartidos conforme a D19. Gold y Gazetteer muestran su estado pendiente; no
  leen predicciones ni escriben datos. Se prepara el criterio por autorización
  explícita del usuario, con estado pendiente; no se declara aprobado ni se inicia
  ninguna anotación. Tras aprobación humana se registrará el hash final en
  `config/criterios_relevancia_aprobacion.json` (`sha256_criterio`, `aprobado_por`,
  `fecha`) y en esta bitácora; el manifiesto del pool debe contener ese mismo hash.
- (2026-11-09) Persistencia de juicios: mantener las cuatro columnas exactas del CSV;
  revisión y huellas en `anotaciones/juicios_relevancia_estado.json`, respaldos en
  `anotaciones/historial_juicios/`. Diario preparado antes del reemplazo del CSV
  permite distinguir una interrupción del guardado completado. `flock` y comparación
  de revisión/hash evitan carreras; cambios de insumos o CSV externo bloquean sin
  sobrescribir. Solo se ignora el cerrojo local `.juicios.lock`; datos y revisiones
  permanecen versionables. Omitir conserva decisiones existentes y deja vacío un
  pendiente. La alternativa CLI y las funciones H5/H6 no se consideran implementadas.

- (2026-11-09) Continuación individual en `desarrollo-luis` desde `0e52244`.
  Recuperación H1 autorizada por el usuario: corpus y pasajes reconstruidos en `/tmp`
  y copiados a las rutas ignoradas solo tras coincidir con las huellas históricas.
  Se conservan intactos `corpus_meta.json`, `indice_meta.json`, las salidas históricas
  y los rankings. Evidencia: `salida/01_recuperacion_validacion.json` y
  `docs/recuperacion_h1.md`.
- (2026-11-09) Pool técnico autorizado antes de los criterios humanos: se implementan
  D06, T07 y T08 y manifiesto de fuentes en `salida/04_pool_meta.json`. La anotación
  permanece bloqueada hasta que el alumno escriba y apruebe los criterios; después
  se actualiza el manifiesto antes del primer juicio. Q5, Q7 y Q8 generan avisos por
  tamaño inferior al intervalo esperado; se mantiene la unión exacta sin recortar
  variantes. No se producen juicios ni gold. La identidad histórica de Daniel se
  conserva; falta confirmar los datos completos de Luis para la entrega individual.

- (2026-11-04) Entorno: `pyproject.toml` con `requires-python >=3.11,<3.13`, build `hatchling` con layout `src/mtx`, torch CPU desde el índice de PyTorch en Linux y Windows. `uv.lock` versionado.
- (2026-11-04) `make setup` no falla si NLTK no descarga las stopwords (NLTK bloquea su carpeta por validación de rutas); se usará `config/stopwords_es.txt` como respaldo versionado, según PRD §9.
- (2026-11-04) Gráficas con `plotly` exportadas a PNG con `kaleido`, en lugar de `matplotlib`, por indicación del profesor. `cufflinks` no se usa: es un envoltorio sin mantenimiento sobre plotly. Kaleido necesita Chrome; `make setup` ejecuta `plotly_get_chrome` (los Chromium del sistema, de snap, fallan). PRD §2.2, §6.6 y §11.1 y tres skills se actualizaron para reflejarlo.
- (2026-11-04) `evaluar.py` se invoca siempre desde `adaptadores_kit.ejecutar_evaluador()` con `cwd` en el directorio de destino, porque el kit escribe `resultados_*.csv` en el directorio actual.
- (2026-11-04) Limitación a declarar en el reporte: la métrica IE oficial no penaliza falsos positivos en pasajes gold sin entidades (comportamiento del kit); la evaluación complementaria sobre los 20 IDs lo cubre.
- (2026-11-04) **El corpus real no tiene el formato que suponía el PRD §6.1.** Verificado sobre los 2,294 discursos: las marcas son `~~~ETIQUETA texto` (sin dos puntos, con espacios duros) para tres etiquetas (`PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR`, `INTERLOCUTORA`, `PREGUNTA`) y `NOMBRE, CARGO: texto` en línea para los demás; solo 12 textos traen saltos de línea. `RE_INTERLOCUTOR` del kit reconoce marcas en 0 de 2,294 discursos y admite etiquetas de máximo 81 caracteres. Decisión: `limpiar_ruido()` canoniza las marcas a una intervención por línea y `partir_canonico()` las separa; `ventanas()` del kit se reutiliza. Efecto sobre D02 a D05: ninguno de fondo, el pasaje sigue siendo `f"{quien}: {trozo}"` con `inicio_cuerpo`.
- (2026-11-04) Acotaciones (D05): no se borra todo paréntesis en mayúsculas como proponía el PRD, porque eliminaría siglas legítimas como `(IMSS)`, `(PROFECO)` o `(SEDENA)` (127, 81 y 50 casos). Se borran solo los paréntesis que coinciden por completo con la lista de `config/limpieza.yaml` (video, audio, inaudible, falla de transmisión, himno, etc.). Eliminadas: 7,338 acotaciones, 0.12 % de los caracteres. No existen separadores ni encabezados fijos en el cuerpo; sí un lema anual ("2022: Año de ...") en 60 discursos, que se elimina.
- (2026-11-04) Reparación de fechas: una candidata de título o URL fuera de [2018-12-01, 2024-09-30] se descarta antes de compararla. Sin esa guarda, títulos con año mal escrito (`03.03.30`, `17.12.16`, `11.10.09`, `26.04.18`) habrían reemplazado fechas originales correctas. Diez discursos corregidos con el título (año equivocado en `fecha`, por ejemplo 2020-05-15 → 2022-05-15); detalle en `salida/01_fechas_reparadas.csv`. Ninguna fecha NaT.
- (2026-11-04) Duplicados: 5 discursos excluidos (4 exactos y 1 casi duplicado, Jaccard 0.9864), listados en `salida/01_duplicados.csv`; reversibles desde `config/limpieza.yaml`.
- (2026-11-04) Resultado de la segmentación base (D02): 127,739 pasajes, 15.5 % de reporteros. El 64.94 % de las intervenciones de reporteros queda bajo `min_tokens=40` y se descarta. Supera el 10 % del PRD §6.1.4: **el reporte debe discutirlo como costo de D02.** La base se mantiene (D02), sin cambios, y todavía no hay juicios.
- (2026-11-04) `data/consultas.csv` generado con el kit literal más Q9 y Q10 en borrador. No se generan rankings hasta que el alumno apruebe o corrija la redacción de Q9 y Q10.
- (2026-11-08) **Q9 y Q10 aprobadas por el alumno** sin cambios: Q9 "operación y apertura de sucursales del Banco del Bienestar" (2019-01-01 a 2023-12-31); Q10 "construcción y operación del Tren Interoceánico del Istmo de Tehuantepec" (2020-01-01 a 2024-06-30); preguntas de extracción como en `config/consultas_q9q10.yaml`. Se levanta el bloqueo de rankings. El mismo día el alumno confirmó que el profesor tiene acceso al repo de GitLab.
- (2026-11-08) H2: `indice.py` y `ranking.py` probados (T03 a T06). Memoria del índice a mano medida: pico de 1.3 GB, `indice.pkl` 43.5 MB (`salida/02_memoria.json`). `rank_bm25` difiere del BM25 propio en todos los términos (no solo df > N/2) porque su idf es `ln(x)` y el propio `ln(1+x)`; la prueba usa una subclase con el idf propio.

- (2026-11-09) H5 técnico aislado en `desarrollo-h5`, worktree separado desde
  `4cd65f1`, por autorización de Luis. Se implementan componentes independientes
  de juicios y H4; la extracción final exige `data/mejor_modelo.json` con campo
  `modelo` igual a una variante con filtro. No se consultan juicios H3, gold ni
  selección; no se modifican kit, rankings, pool, criterios ni metadatos históricos.
- (2026-11-09) Gazetteers: las entradas expresamente enumeradas en PRD §6.7.4/D14
  se guardan en `config/gazetteer_prescrito.csv`; los lugares de §6.7.5 en
  `config/gazetteer_loc.csv`. Se distingue así contenido prescrito de revisión
  humana de candidatos; `config/gazetteer_extendido.csv` solo lo produce el alumno
  con la app. No hay candidatos aceptados automáticamente. La minería cuenta
  ocurrencias en cuerpos de pasajes con ventanas; no son frecuencias por discurso.
- (2026-11-09) Normalización prudente: años de dos dígitos sin regla de siglo
  permanecen sin resolver; fechas relativas e intervalos se detectan sin inventar
  ISO; día imposible tiene estado `fecha_invalida`. `1.200` es ambiguo; billón
  español equivale a 10**12; `$` sin denominación conserva valor pero no presupone
  MXN. Los spans permanecen intactos. Reglas no cubren números completamente en
  palabras, como `quince` o `trescientos cincuenta`, según PRD §6.7.
- (2026-11-09) P06: se verifica el principal prescrito
  `mrm8488/bert-spanish-cased-finetuned-ner`, revisión
  `b11721d41d9e948da32fcdabeeef4fb0f3ebcdf7`, con pesos fuera del repo en `/tmp`.
  Se informó modelo, tamaño aproximado y motivo antes de descargar. Cabeza de
  clasificación de tokens y mapa BIO reales; tokenizador rápido, offsets y CPU
  comprobados con frases sintéticas. `salida/07_verificacion_ner.json` conserva
  medición y resultados. `data/modelo_ner.json` es provisional con criterio
  técnico D09, F1 nulos y sin selección humana simulada. No se compara segundo
  NER (P1) mientras hay P0 pendientes; no se cambia el entorno ni dependencias.
- (2026-11-09) Fragmentación NER: ventanas de subtokens de capacidad real menos
  especiales, solapamiento explícito, verificación de cobertura y retokenización.
  Se rechaza un fragmento que exceda capacidad; nunca se trunca silenciosamente.
  Caché cruda con clave versionada y carga perezosa; posproceso separado, con
  uniones auditadas. MISC/OTH se cuentan. No se produce caché real sin ganador H4.
- (2026-11-09) App H5: accesos independientes de Gazetteer y preparación Gold sin
  cargar juicios. Persistencia de revisión con cerrojo, revisión, respaldos y diario
  previo a publicación. Una interrupción entre diario/CSV bloquea para revisión
  explícita; conserva decisiones y respaldos. `make congelar` ahora exige hashes
  de aprobaciones humanas de criterios y gazetteer y P06, además de pruebas.
  No se crea etiqueta ni aprobación en esta sesión. Muestreo global reproducible
  probado con fixtures; la app solo podrá escribir el manifiesto real tras H4,
  congelación, protocolo y confirmación de no haber visto predicciones. CLI solo
  valida: no escribe en `anotaciones/`. Anotación, sustitución y cierre son H6.
- (2026-11-09) Luis indica entrega oficial en GitHub antes del 11 de noviembre a
  las 20:00. Esto reemplaza el destino de entrega histórico GitLab para su proyecto
  individual, sin reescribir el historial previo. No se modifica remote, publica,
  hace merge ni push; preparar repositorio personal y comprobar acceso del profesor
  queda para integración en `desarrollo-luis`.
