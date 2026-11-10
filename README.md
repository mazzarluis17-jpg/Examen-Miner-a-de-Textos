# Sistema de recuperación y extracción de información sobre discursos presidenciales

Examen 1 de Minería de Textos (Licenciatura en Ciencia de Datos). Sistema en
Python que, sobre el corpus `carevies/discursos_AMLO` (versiones estenográficas
de conferencias y discursos de 2018 a 2024), recupera los 10 pasajes más
relevantes por consulta con TF-IDF y BM25 (con y sin filtro de fecha) y extrae
entidades PER, ORG, LOC, FECHA y MONTO combinando reglas con gazetteer y un NER
preentrenado para español.

## Estado

H0 a H4 implementados; H3 confirmado visualmente por Luis. Corpus y pasajes
recuperados con las huellas históricas; rankings y pool congelados. La evaluación
oficial seleccionó BM25 con filtro para toda IE (D08); métricas en
[`salida/resultados_ir.csv`](salida/resultados_ir.csv) y decisión versionada en
[`data/mejor_modelo.json`](data/mejor_modelo.json).

`make evaluar-ir` valida y evalúa sin recalcular rankings ni modificar juicios.
Produce resultados oficiales, vista temporal complementaria, auditorías y figuras.
Ver [procedimiento y resultados H4](docs/h4_evaluacion_ir.md). Los juicios fueron
realizados personalmente en Excel y transferidos con autorización a Streamlit;
no se atribuyen a captura íntegra directa en la interfaz.

Siguen H5 a H9: extracción, gold humano, evaluación IE, respuestas y entrega.
El README final de diez secciones y la declaración completa de uso de IA siguen
pendientes de H9. La suite rápida no usa red; `make test-lento` incluye los
contratos sobre los datos reales recuperados.

Uso mínimo hoy (Linux, Python 3.11 y `uv`):

```bash
make setup      # entorno, torch CPU, Chrome para kaleido
make contratos  # pruebas de contrato del kit (kit/ no se modifica)
make corpus     # descarga el corpus, limpia y segmenta: data/pasajes.parquet
make consultas  # data/consultas.csv = kit + Q9 + Q10
make test       # pruebas rápidas, sin red
```

## Documentos de referencia

La aplicación de juicios de H3 arranca con:

```bash
uv run --no-sync streamlit run src/mtx/app/app.py
```

También se puede usar `make app`. Lee los insumos locales sin red ni modelos NER.
La anotación permanece bloqueada hasta aprobar explícitamente
`config/criterios_relevancia.md` y registrar su hash. No se generan respuestas por
defecto. Guarda después de cada acción, permite reanudar y rechaza sesiones
desactualizadas. Ver [prueba manual y recuperación](docs/pruebas_app.md).


| Archivo | Qué es |
| --- | --- |
| `PRD_unificado_examen1_mineria_textos.md` | Especificación completa (v3.0, 4 de noviembre de 2026). Fuente de verdad del proyecto |
| `CLAUDE.md` / `AGENTS.md` | Orquestador para asistentes de programación: índice de skills, convenciones y qué no tocar |
| `docs/harness/ARCHITECTURE.md` | Mapa de componentes, flujos de datos, congelaciones e invalidación |
| `docs/harness/PROGRESS.md` | Estado del trabajo entre sesiones |
| `docs/decisiones.md` | Fase 0 y cada decisión con fecha (formato real del corpus, fechas, plotly) |
| `docs/contratos_kit.md` | Hashes y comportamiento verificado de `kit/` |
| `.claude/skills/` | Skills por hito (H0 a H9); `.agents/skills/` las expone a otros agentes |

## Entregables previstos

Seis CSV en la raíz (`ranking.csv`, `juicios_relevancia.csv`, `resultados_ir.csv`,
`entidades.csv`, `gold_entidades.csv`, `resultados_ie.csv`), reporte PDF de 4 a
6 páginas, presentación de 8 minutos con demo en vivo y `make entrega`
reproducible desde un clon limpio.
