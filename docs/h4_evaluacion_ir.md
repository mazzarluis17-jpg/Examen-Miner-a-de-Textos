# H4 — Evaluación de recuperación de información

Luis confirmó visualmente el cierre humano de H3 antes de autorizar H4. Se usa
la revisión 197 de persistencia, sin modificar juicios ni rankings. La procedencia
de los juicios es personal en Excel, seguida de transferencia autorizada a la app;
no se atribuye a captura íntegra directa en Streamlit.

## Resultado oficial

Fuente íntegra: `salida/resultados_ir.csv` (copia idéntica en la raíz).

| Variante | P@5 | P@10 | MAP |
| --- | ---: | ---: | ---: |
| BM25 con filtro | 0.7600 | 0.7700 | 0.6150 |
| BM25 sin filtro | 0.7600 | 0.7500 | 0.5922 |
| TF-IDF con filtro | 0.6600 | 0.5800 | 0.3998 |
| TF-IDF sin filtro | 0.6800 | 0.6000 | 0.4131 |

El ganador global es `bm25_con_filtro`: D08 compara exclusivamente MAP oficial
entre las variantes con filtro. Supera a TF-IDF con filtro por 0.2152; no hay
empate ni diferencia menor a 0.01. La regla de empate exacto a BM25 permanece
implementada y probada. La decisión y los hashes están en `data/mejor_modelo.json`.

BM25 obtiene mayor AP en siete consultas; TF-IDF en Q6, Q7 y Q9. No se escoge
modelo por consulta: la misma variante global alimentará toda IE. Fuente:
`salida/05_ir_ganador_por_consulta.csv`. El filtro mejora el MAP de BM25 en 0.0228
y reduce el de TF-IDF en 0.0133 (`salida/05_comparacion_filtros.csv`); no se afirma
que el filtro siempre mejore la relevancia temática.

AP se calcula sobre el top-10, con denominador igual a todos los relevantes del
pool de la consulta. El kit redondea AP por consulta y después promedia, generando
el MAP oficial. No es una estimación del recall sobre todo el corpus.

## Vista temporal complementaria

`salida/05_juicios_con_ventana.csv` conserva el juicio original y añade
`relevante_ventana = relevante AND en_ventana`. El CSV auxiliar para el evaluador
está separado; nunca se cambia el archivo humano. Los resultados en
`salida/05_resultados_ir_ventana.csv` usan un denominador distinto y no deciden
el ganador. MAP complementario: BM25 con filtro 0.6622, BM25 sin filtro 0.5288,
TF-IDF con filtro 0.4517 y TF-IDF sin filtro 0.3593.

`salida/05_soporte_ventana.csv` cuenta relevantes temáticos dentro, fuera y sin
fecha. Q6 tiene diez relevantes temáticos fuera de ventana; esto explica parte
de la diferencia entre vistas sin convertirlos en juicios temáticos negativos.

## Auditorías para las siguientes etapas

- `05_ir_por_consulta.csv`: tabla ancha de métricas, soporte y cobertura.
- `05_etiquetas_consultas.csv`: longitud tras preprocesamiento, mediana y DF de
  términos. DF alto significa `df/N >= 0.10`; consulta larga significa longitud
  superior a la mediana. Nombres y siglas son heurísticas, no anotación humana.
- `config/sinonimos_consultas.yaml`: equivalencias ya especificadas en PRD §6.6,
  solo descriptivas. No se expanden consultas ni se recalculan rankings.
- `05_pasajes_ganador.csv`: cien asociaciones consulta–pasaje y 99 IDs únicos,
  con texto, hashes e `inicio_cuerpo`, listos para H5–H8; no hay entidades sugeridas.
- `05_auditoria_h8.csv`: consultas, preguntas, ventanas y soporte del ganador.
  La extracción y las respuestas siguen pendientes.
- Tres figuras PNG y sus versiones HTML locales en `reporte/figuras/ir_*`.

Los conteos y verificaciones anteriores proceden de `salida/05_validacion_h4.json`.

## Ejecución y trazabilidad

Ejecutar `make evaluar-ir`, o directamente:

```bash
uv run --no-sync python scripts/05_evaluar_ir.py
```

El script verifica el contexto congelado y los juicios con los validadores de H3,
invoca exclusivamente `adaptadores_kit.ejecutar_evaluador()` sobre copias temporales
idénticas, valida las salidas y publica las exportaciones sin renombrar columnas.
Si ya existe una cifra distinta, se detiene en vez de sobrescribirla. Las figuras
usan Chrome local mediante Kaleido; no se descarga Chrome ni se usa la red.
En el sandbox de Codex la exportación gráfica quedó bloqueada; funcionó al repetir
la ejecución fuera del sandbox con autorización. Esto no alteró métricas ni insumos.

`05_ejecucion_oficial.json` y `05_ejecucion_ventana.json` guardan comando real,
salida estándar, errores y hashes. `05_manifiesto_ir.json` y la etapa H4 del
manifiesto global identifican entradas y productos. El registro global es
incremental: no afirma que IE o la entrega ya sean reproducibles.

Suite completa: 183 pruebas aprobadas y una omitida (prueba de arranque con criterio
real pendiente: el criterio ya está aprobado); Ruff limpio. Se regeneraron ambos
resultados con el kit en temporales y coincidieron byte por byte. Las referencias,
los criterios, el pool y los juicios originales conservaron sus hashes.

H5 requiere reglas y gazetteers, revisión humana de siglas y criterios IE aprobados,
NER fijado técnicamente y congelación antes del gold. H6 requiere veinte pasajes
gold anotados a ciegas por el alumno. H7 realiza fusión y evaluación IE; H8 genera
tablas con evidencia y recoge las valoraciones personales.
