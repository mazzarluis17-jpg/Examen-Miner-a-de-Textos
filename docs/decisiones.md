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

- (2026-11-10) Luis aprobó explícitamente, sin modificaciones, el alcance de revisión
  de once candidatos y el texto íntegro de `config/criterios_anotacion.md`.
  SHA-256 de la propuesta de alcance:
  `e7a97be6b2a106991d5833ae1465aa5a76adc67538145618bd36b5308b1b7884`.
  SHA-256 de los criterios IE:
  `3ae1e19e1ff5032708fc6f6269792d3e31239c3314a3ad0108f67a15bd2ccb47`.
  Constancias en `config/alcance_gazetteer_aprobacion.json` y
  `config/criterios_anotacion_aprobacion.json`. Se conservan ambos documentos
  aprobados byte por byte, incluidos sus encabezados históricos de propuesta;
  el estado vigente se acredita mediante esas constancias. La aprobación del
  alcance no acepta ninguno de los once ni rechaza los otros 1,494. Streamlit queda
  habilitado para revisión personal; no hay decisiones de candidatos, congelación,
  muestra ni gold creados durante este registro.

- (2026-11-10) Por instrucción de Luis se propone alcance acotado antes de D15,
  pendiente de aprobación explícita. Se conservan 1,505 candidatos; se proponen los
  once con coincidencias adicionales de sigla/nombre minado en cuerpos de los 99
  pasajes únicos del ganador, descontando coincidencias contenidas en aliases de
  base/prescritos/LOC. Se auditan presencia completa y marcas; las exclusiones de
  alcance no son rechazos humanos. No se usan gold ni predicciones para seleccionar.
  Política, cobertura y hashes en `salida/06_revision_alcance.json` y
  `docs/h5_revision_acotada.md`. La app exige la aprobación por hash del alcance
  antes de permitir decisiones y exige revisar el subconjunto completo para cerrar.
- (2026-11-10) Criterios IE y protocolo preparados como borrador autorizado, no
  aprobados. Gold se implementa con validación de D15, muestra reproducible y fuentes,
  tipos/spans y cierre de los veinte IDs, incluido cero entidades. Diario y CSV
  separados mantienen columnas contractuales y detectan interrupciones/concurrencia;
  no se recuperan ni reescriben silenciosamente anotaciones. Todo ejemplo de prueba
  es sintético en temporales. No se crean muestras, aprobaciones ni gold reales.

- (2026-11-10) Integración autorizada de `desarrollo-h5` (`e164ca6`) sobre
  `desarrollo-luis` (`c69581c`) mediante merge real, sin squash ni rebase. Respaldo
  externo H3 íntegro y comparado con los archivos actuales; documentación local
  apartada en `/tmp/mtx-merge-h5-20261110-013248/` y reconciliada después. Se combinan
  las decisiones de ambas ramas, incluidas procedencia y aprobaciones legítimas
  de H3; no se crea un commit separado de transferencia. El único conflicto Git
  fue `docs/harness/PROGRESS.md`, resuelto conservando H4 completado y H5 técnico,
  con pendientes humanos actualizados. Archivos humanos y congelados sin cambios
  de contenido; rama/worktree H5 intactos. No se regenera H3/H4, se cambia el remote,
  se hace push ni se avanza a H6. Auditoría: `salida/06_integracion_h5.json`.

- (2026-11-10) Luis confirmó visualmente los juicios de H3 y autorizó H4. Se evalúa
  exclusivamente la revisión 197 y los rankings congelados, mediante el adaptador
  del kit intacto. D08 fija `bm25_con_filtro` por mayor MAP oficial entre variantes
  con filtro; fuentes, hashes y métricas en `salida/05_validacion_h4.json` y
  `data/mejor_modelo.json`. La vista con ventana es complementaria y no interviene
  en la selección. Las etiquetas descriptivas de consultas usan DF/N >= 0.10 y
  longitud superior a la mediana, sin modificar el ranking. Siglas y nombres son
  heurísticas auditables. Las equivalencias de PRD §6.6 se usan solo para describir.
  Se conservan resultados distintos si existiesen, sin sobrescribir cifras previas.
  Exportación gráfica local verificada fuera del sandbox, sin descargas.

- (2026-11-10) Transferencia explícitamente autorizada por Luis de sus 176 juicios
  humanos realizados en Excel, desde
  `/home/luis/Descargas/juicios_humanos_excel_para_validacion.csv` (SHA-256
  `dc42015ef38a69ca0215ac24573249432c212e581a83ecaf67dbe95b2e144134`).
  Luis ratificó los cinco valores discrepantes del CSV como definitivos: se
  actualizaron esos cinco, se conservaron 17 coincidencias y se incorporaron 154
  pares faltantes mediante `componentes.guardar_accion()`, sin inferir etiquetas.
  Las revisiones pasaron de 38 a 197, con respaldos del CSV y del estado previos y
  el historial atómico habitual. Procedencia y verificaciones detalladas en
  `anotaciones/historial_juicios/transferencia_excel_2026-11-10T00-50-08-06-00_procedencia.json`.
  La procedencia es importación asistida desde Excel, no captura directa de todos
  los juicios en la interfaz de Streamlit. Coincidencia exacta con el CSV:
  113 relevantes, 63 no relevantes, cero pendientes; validador sin errores ni avisos.
  AppTest verificó 176/176 en Estado y las diez consultas, y reapertura sin pérdida.
  No se ejecutó H4 ni se exportaron juicios a la raíz. H4 espera confirmación visual
  de Luis. No se realizaron operaciones de escritura en Git.

- (2026-11-09, 17:19 CDMX) Luis aprobó explícitamente, sin modificaciones, el texto
  de `config/criterios_relevancia.md` presentado en conversación. SHA-256 aprobado:
  `ae67ac2b0f1066dd71293c9ca8075aae9473ff1a9956e028c759ee6158fe9f87`.
  Constancia: `config/criterios_relevancia_aprobacion.json`. Se conserva el archivo
  aprobado byte por byte, incluido su encabezado histórico de propuesta; el estado
  vigente lo determina la constancia ligada al hash. Pool verificado sin cambios;
  aplicación habilitada para decisiones personales de Luis. No se generan etiquetas.

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

- (2026-11-09) Cierre H5: se normalizan a LF los CSV prescritos nuevos y se
  recortan espacios de extremos solo en los contextos de candidatos minados.
  No se modifica texto canónico ni offsets; minería regenerada y T11 con 200
  pasajes reales nuevamente verde. No hay congelación ni decisiones humanas.

## 2026-11-10 — Cierre humano H5 y autorización de congelación

Luis cerró personalmente la revisión en Streamlit: constancia
`config/gazetteer_aprobacion.json`, fecha 2026-11-11T00:25:07.664368+00:00
(10 de noviembre en CDMX), revisión 11. Once candidatos descartados por el
alumno, cero ampliaciones; base original de 76 entradas intacta y 1,494
candidatos fuera del alcance no revisados. Se conservan los gazetteers
prescritos y LOC aprobados mediante ese cierre, además de la base del kit.
Criterios IE y alcance cuentan con aprobación explícita y hashes vigentes.

El alumno autorizó versionar los archivos necesarios y congelar H5. Se
registran los archivos humanos existentes y respaldos con su contenido exacto
para satisfacer el árbol limpio requerido por D15; no se crean etiquetas de
relevancia ni revisiones humanas nuevas. Los juicios mantienen su procedencia
Excel autorizada y revisión 197; no se atribuyen a captura directa en la app.
Respaldo externo verificado en `/tmp/mtx-h5-congelacion-20261110-182613/`;
se verifican las 21 entradas del manifiesto H4 sin reevaluar ni regenerar.
La etiqueta `reglas-congeladas` se creará mediante el objetivo oficial tras
pruebas; solo después la app preparará el manifiesto ciego semilla 42, sin
consultar predicciones ni producir entidades gold. BETO permanece fijado por
criterio técnico (D09); no se compara un segundo modelo ni se crea selección.

## 2026-11-10 — D15 ejecutada y muestra ciega H6 preparada

`make congelar` creó la etiqueta anotada `reglas-congeladas` sobre `d4ca0a7`,
antes de crear o versionar cualquier muestra o gold. Después se llamó a
`app.preparacion_gold.preparar_muestra`, sin modificar la aplicación: semilla 42,
emparejamiento global de veinte IDs únicos, dos por consulta del top-10 del
ganador congelado. Manifiesto `anotaciones/muestra_gold.csv`, SHA-256
`cbaac558917bf3a581ac64f21b5862735bc877e27df3724322cf0a8c89b53bb1`.
No se consultaron predicciones ni se generaron entidades, estados cerrados o
aprobaciones humanas. Los veinte pasajes superan los umbrales objetivos de
contenido y protocolo; no hay sustituciones. Auditoría en
`salida/08_preparacion_h6.json`; AppTest ciego 0/20 sin errores.
Los 302 archivos protegidos del respaldo mantienen sus hashes. El siguiente
commit registra solo muestra y documentación posterior a D15, sin alterar
reglas, criterios, configuración ni decisiones humanas.

## 2026-11-10 — Cierre humano H6 verificado y comienzo de H7

Luis cerró personalmente Gold en Streamlit: revisión 20, veinte pasajes revisados
y 138 entidades, incluido `1133_87` cerrado sin entidades. Sello, fuentes, hashes
y exportación oficial de raíz coinciden; `validar_gold()` sin errores. Las
anotaciones proceden de trabajo humano en Excel auxiliar externo y transferencia
autorizada con persistencia oficial; no se atribuyen a captura directa completa
en Streamlit. Los auxiliares no se incluyen en Git ni entregables. Correcciones
previas expresamente autorizadas: offsets [0:71] de dos ORG en las marcas de
P01/P02 y conservación como ORG [340:387] del Corredor en P03, eliminando la
LOC anidada [367:387]; ninguna otra entidad cambiada durante la transferencia.

Respaldo externo previo H7 verificado en `/tmp/mtx-h7-protegidos-20261110-202712/`.
Se versionan únicamente persistencia, historial, muestra y cierre oficiales.
D15 permanece en `d4ca0a7`, anterior al primer commit gold. Se autoriza ahora
la inferencia con el único BETO técnico ya fijado; no se selecciona ni se ajusta
un modelo con Gold. H7 incorpora fusión exacta D12 y evaluación, manteniendo
intactos reglas, posproceso, gazetteers y normalizador congelados. El
enriquecimiento auxiliar prudente se añade aparte sin cambiar spans ni métricas.
