# Recuperación controlada de H1 — 2026-11-09

Referencia: commit del profesor `0e52244`, rama `desarrollo-luis`.
Se usó Python 3.11.2 de `.venv`, sin descargar otra revisión ni modificar el kit.

## Procedimiento

1. Recuperar `carevies/discursos_AMLO`, revisión
   `2c463bb3d5bf58742b4d842917da1211c44d2e18`, split `train`, con cachés
   exclusivamente en `/tmp/mtx-recuperacion/`.
2. Leer el Arrow indicado en `inspeccion_corpus.json` mediante `Dataset.from_file()`.
   Convertir a pandas y aplicar las operaciones de carga originales: renombres de
   `adaptadores_kit.cargar_modulo_corpus().RENOMBRES`, conversión de fechas,
   eliminación de texto nulo, índice consecutivo y `doc_id` en el orden original.
3. Escribir `/tmp/mtx-recuperacion/discursos_candidato.parquet` con `index=False`.
4. Ejecutar `corpus.limpiar_ruido(df)` y `corpus.segmentar_con_descartes(limpio)`
   con los parámetros existentes 200/150/40. Escribir el candidato en `/tmp`.
5. Comprobar conteo y `corpus.hash_pasajes()`. Comparar cada fila del ranking con
   los metadatos del pasaje, y texto (primeros 400 caracteres), título e interlocutor
   contra `salida/03_ranking_detalle.csv`.
6. Solo tras superar las comprobaciones, copiar los candidatos a
   `kit/data/discursos.parquet` y `data/pasajes.parquet` (ambos ignorados por Git).

No se ejecutó `make corpus`: habría reescrito las referencias históricas.
No se reconstruyeron tokens, índice ni TF-IDF. Para repetir la recuperación se
reutilizan las funciones existentes, sin cambiar la segmentación ni la asignación de IDs.
Los hashes y resultados medidos están en `salida/01_recuperacion_validacion.json`.

## Pool técnico

`make pool` usa los pasajes validados y los rankings existentes. Su manifiesto
`salida/04_pool_meta.json` identifica fuentes, semilla y hashes sin fechas variables.
El CSV se baraja por consulta con semilla 42 sobre IDs ordenados. La procedencia se
conserva solo para auditoría y deberá ocultarse en la app de juicios.

El pool se genera por autorización explícita del alumno antes de escribir los
criterios humanos. Esto no habilita la anotación ni certifica su congelación final:
`config/criterios_relevancia.md` y su aprobación `[VALIDAR]` siguen pendientes.
Antes del primer juicio se debe volver a ejecutar `make pool` para incorporar el
hash del criterio. Nunca se generan etiquetas por defecto.
