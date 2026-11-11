# Examen 1 — Minería de Textos

**Luis Alfredo Ramírez Maza** · Licenciatura en Ciencia de Datos  
**Universidad Nacional Autónoma de México (UNAM)**  
**Facultad de Estudios Superiores Acatlán (FES Acatlán)**  
Asignatura: Minería de Textos · 11 de noviembre de 2026

## 1. Qué hace el sistema

Recupera pasajes de conferencias presidenciales mediante TF-IDF y BM25, con y sin
filtro temporal. Extrae PER, ORG, LOC, FECHA y MONTO con reglas y BETO; produce
respuestas con citas y estados de evidencia. Las relaciones ambiguas se conservan
como ambiguas. Los juicios, Gold y valoraciones son humanos.
El [reporte](reporte/reporte.pdf) contiene un borrador académico de seis páginas,
con estructura aprobada por Luis. **La prosa y conclusiones del segundo corte
están pendientes de revisión humana; el PDF aún no está aprobado como final**.
La presentación tiene cinco láminas; falta su revisión y ensayo humano.

## 2. Requisitos

Python 3.11, uv, Git y memoria suficiente para el corpus y el índice. La ejecución
usa Torch CPU. El entorno está fijado en uv.lock; requirements.txt es su exportación
sin dependencias de desarrollo. XeLaTeX y la fuente DejaVu Serif son necesarios
solo para compilar el reporte; la vía directa usada aquí no necesita Pandoc.

Debian: instalar uv conforme a su documentación y, para el PDF,
`sudo apt install texlive-xetex texlive-latex-extra fonts-dejavu`.
En macOS se pueden utilizar uv y MacTeX; en Windows, uv y una distribución TeX
con XeLaTeX. Todos los objetivos tienen alternativa Python, sin depender de make.
La exportación de figuras de Plotly usa Chrome/Kaleido; las figuras de resultados
ya están versionadas. No se requieren GPU ni descargas NER para reproducir cifras
usando las cachés oficiales versionadas.

## 3. Instalación desde cero y recuperación del corpus

Una vez publicado el repositorio personal, sustituir la URL de este ejemplo por
su dirección real; no utilizar el GitLab del profesor como destino de entrega.

```bash
git clone https://github.com/TU_USUARIO/text-mining-ir-er.git
cd text-mining-ir-er
git checkout desarrollo-luis
uv sync --locked
uv run --no-sync pytest -q tests/test_contratos_kit.py
uv run --no-sync python scripts/00c_recuperar_snapshot.py
```

El último comando obtiene exclusivamente carevies/discursos_AMLO en la revisión
2c463bb3d5bf58742b4d842917da1211c44d2e18. Reproduce la conversión del kit y la
limpieza/segmentación existente, valida el SHA-256 binario del corpus y de los
pasajes y el hash canónico de contenido antes de colocar los dos archivos ignorados
en kit/data/discursos.parquet y data/pasajes.parquet. No reemplaza datos existentes
ni modifica metadatos históricos. Si falta un hash o no coincide, se detiene;
no se cambia de revisión ni se corrigen referencias para forzar coincidencias.
En esta entrega congelada **no ejecutar el antiguo make corpus**, que vuelve a
escribir metadatos y auditorías históricas. Consultar [reproducibilidad](docs/reproducibilidad.md).

## 4. Reproducir resultados y abrir la aplicación

```bash
uv run --no-sync python scripts/05_evaluar_ir.py
uv run --no-sync python scripts/09_evaluar_ie.py
uv run --no-sync python scripts/10_tablas.py --exigir-valoraciones
uv run --no-sync python scripts/99_validar.py --permitir-pendientes
uv run --no-sync streamlit run src/mtx/app/app.py
```

`make resultados` equivale a los tres primeros scripts (tablas sin la opción
estricta); no necesita TeX. `make entrega` añade contratos, reporte, láminas y
validación estricta; se detiene mientras existan cierres humanos pendientes.
`--permitir-pendientes` enumera esos pendientes, no certifica una entrega cerrada.
Los evaluadores no cambian etiquetas y rechazan fuentes incompatibles.
La aplicación permite consultar juicios, Gold cerrado, gazetteer y las diez
valoraciones. La demo de resultados se ejecuta en terminal:

```bash
uv run --no-sync python scripts/13_demo.py --q Q3
```

Muestra consulta y ventana, ambos top-10 con filtro, pasajes completos, entidades y
respuesta con citas. Lee artefactos cacheados; no consulta fuentes externas ni
infiere nuevas entidades. La consulta libre fuera de las diez oficiales se rechaza
para no presentar un experimento nuevo como resultado congelado.

| Objetivo | Alternativa sin make |
|---|---|
| setup | uv sync --locked |
| contratos | uv run --no-sync pytest -q tests/test_contratos_kit.py |
| recuperar-datos | uv run --no-sync python scripts/00c_recuperar_snapshot.py |
| indice / ranking | scripts/02_indice.py / scripts/03_ranking.py (solo reconstrucción controlada) |
| pool | uv run --no-sync python scripts/04_pool.py |
| evaluar-ir | uv run --no-sync python scripts/05_evaluar_ir.py |
| ner / extraer | scripts/07c_ner_auditado.py / scripts/08_extraer.py |
| evaluar-ie | uv run --no-sync python scripts/09_evaluar_ie.py |
| tablas | uv run --no-sync python scripts/10_tablas.py --exigir-valoraciones |
| reporte / laminas | scripts/11_reporte.py / scripts/12_laminas.py |
| demo | uv run --no-sync python scripts/13_demo.py --q Q3 |
| validar | uv run --no-sync python scripts/99_validar.py |
| test / lint | uv run --no-sync pytest -q / uv run --no-sync ruff check src tests scripts |

Los nombres abreviados scripts/... se invocan con `uv run --no-sync python`.
Las mediciones ejecutadas en esta máquina y las verificaciones pendientes se
registran en salida/11_* y docs/reproducibilidad.md, sin estimar tiempos de instalación.

## 5. Flujo completo y decisiones humanas

El desarrollo original sigue H0–H9: contratos, corpus, índice y cuatro rankings,
pool y juicios temáticos, evaluación IR y ganador, reglas/gazetteer/NER congelados,
muestra Gold ciega y cierre personal, extracción/evaluación IE, respuestas y
valoraciones, reporte/presentación. El protocolo conserva la etiqueta
reglas-congeladas y los registros de aprobación. No volver a sortear Gold ni
reabrirlo para mejorar métricas. Las etiquetas existentes se reutilizan literalmente.
Los flujos de anotación tienen guardado atómico, revisión y respaldos oficiales.
Los Excel auxiliares personales no pertenecen al repositorio ni a los entregables.

## 6. Organización del repositorio

| Ruta | Función |
|---|---|
| kit/ | originales del profesor, inmutables y verificados por hashes |
| src/mtx/ | carga, ranking, reglas, NER, fusión, evaluación, respuestas y app |
| scripts/ | orquestación numerada, sin lógica duplicada de dominio |
| config/ | limpieza, stopwords, gazetteers, criterios y aprobaciones |
| data/ | consultas, metadatos, ganador, modelo y caché cruda NER versionada |
| anotaciones/ | persistencia humana, estados, cierres e historiales oficiales |
| salida/ | resultados, auditorías, manifiestos y diez tablas de respuesta |
| reporte/ | Markdown, tablas, figuras y PDF |
| laminas/ | presentación y guion |
| tests/ | contratos y pruebas, con fixtures sintéticas |
| docs/ | decisiones, contratos, arquitectura, progreso y defensa |

La reproducción en clon sin entorno ni cachés previos fue comprobada, incluida
la descarga fijada, reconstrucción del índice y rankings y comparación de 55 CSV.
Los tiempos y hashes medidos constan en salida/11_reproducibilidad_clon.json.

Los seis CSV oficiales se entregan en la raíz y deben ser idénticos a sus fuentes
en salida/ o anotaciones/. Se excluyen entornos, pesos, datos reconstruibles,
cerrojos y archivos auxiliares de TeX; las cachés crudas NER **sí** son obligatorias.

## 7. Decisiones y limitaciones

Ver [decisiones](docs/decisiones.md), [PRD](PRD_unificado_examen1_mineria_textos.md)
y [arquitectura](docs/harness/ARCHITECTURE.md). Ventanas por intervención 200/150/40,
marca visible excluida del índice, stemming español e índice invertido, BM25 con
idf positiva, k1=1.5 y b=0.75. El ganador se selecciona únicamente entre variantes
con filtro por MAP; empate a BM25. Las fechas de evaluación humana son temáticas:
el filtro se audita aparte. La evaluación IE exige coincidencia exacta del span.

La versión 2-vacios-auditados es una corrección expresamente autorizada después
de D15: descarta solo spans que quedan vacíos al recortar puntuación/espacios,
conservando su predicción cruda y auditoría. La versión congelada no se altera;
no existe una métrica completa previa porque el proceso original abortó.
BETO no reconoce por sí mismo FECHA/MONTO. Los alias, fragmentación de entidades,
marcas y confusión LOC/ORG limitan la precisión. La coocurrencia no demuestra
relaciones institucionales ni causales. No se suman montos de eventos diferentes.

## 8. Resultados principales

<!-- resultados:inicio -->
Métricas oficiales IR (promedios literales del evaluador):

```csv
modelo,P@5,P@10,MAP
bm25_con_filtro,0.7600,0.7700,0.6150
bm25_sin_filtro,0.7600,0.7500,0.5922
tfidf_con_filtro,0.6600,0.5800,0.3998
tfidf_sin_filtro,0.6800,0.6000,0.4131
```

F1 oficial combinado por tipo:

```csv
tipo,f1
FECHA,0.2857
LOC,0.8354
MONTO,1.0000
ORG,0.7467
PER,0.2692
```
<!-- resultados:fin -->

La evaluación oficial IE contiene los 19 pasajes con entidades; la complementaria
incluye también el pasaje revisado vacío y obtiene F1 combinado 0.7022. No son
intercambiables. Las respuestas producen 451 filas: 126 respaldadas, 322 ambiguas
y tres sin evidencia. Las diez valoraciones son opiniones humanas, no métricas
automáticas. Véanse salida/10_validacion_h8.json y anotaciones/valoraciones.yaml.

## 9. Uso de IA

El profesor inició el repositorio mediante Claude Code. La continuación utilizó
Codex para programación de src/mtx/, scripts/, tests/, herramientas de anotación,
validación, depuración, generación reproducible de tablas y documentación técnica.
El historial Git y docs/decisiones.md permiten seguir esas unidades de trabajo.
README, guion y borrador académico de H9 fueron redactados por Codex a partir
de los archivos de resultados. Luis aprobó la estructura y selección de tablas.
**La prosa académica y sus conclusiones están pendientes del segundo corte
de revisión del alumno**; no se afirma una validación
que todavía no ocurrió.

Luis realizó personalmente los juicios de relevancia y el Gold mediante archivos
auxiliares externos; su transferencia a la persistencia nativa fue autorizada y
validada. Los cierres formales y las valoraciones de H8 se realizaron personalmente
en Streamlit. Se preservan los registros de aprobación de criterios y gazetteer.
No se atribuye la captura original de todos los juicios/Gold a la interfaz.
El asistente no generó etiquetas humanas ni valoraciones y no utilizó el Gold para
ajustar parámetros o elegir BETO. El código se verificó con contratos, pruebas,
Ruff y comparación literal con el evaluador original. La defensa y el ensayo son
responsabilidad del alumno; la guía técnica no acredita por sí misma comprensión.

## 10. Dependencias y función

| Dependencias | Función |
|---|---|
| pandas, numpy, pyarrow | tablas, operaciones y parquet |
| scikit-learn | TF-IDF sublineal y normalización |
| nltk, regex | stopwords, stemming y patrones |
| datasets | recuperación del snapshot de Hugging Face |
| transformers, torch CPU | BETO fijado por revisión |
| streamlit | anotación y valoración humanas |
| pyyaml | configuración y valoraciones |
| rich | demo en terminal |
| plotly, kaleido | figuras exportables |
| python-pptx, pypdf | presentación y comprobación del PDF |
| pytest, ruff | pruebas y análisis estático (desarrollo) |
| rank_bm25 | contraste de fórmula en pruebas, no ranking oficial |

Las utilerías de presentación y validación siguen el PRD v3.0. No se atribuye al
profesor una autorización adicional que no esté documentada. Véase uv.lock para
las versiones exactas y requirements.txt para la exportación de ejecución.


Referencias metodológicas del reporte: [BM25](https://doi.org/10.1561/1500000019),
[BERT](https://aclanthology.org/N19-1423/) y
[BETO](https://pml4dc.github.io/iclr2020/program/pml4dc_10.html).
La figura editorial H9 se regenera con
`uv run --no-sync python scripts/11_reporte.py --figuras`; requiere Chrome/Kaleido,
no altera las figuras históricas y no recalcula rankings. Sin esa opción,
`make reporte` lee la prosa existente y compila sin modificarla.
