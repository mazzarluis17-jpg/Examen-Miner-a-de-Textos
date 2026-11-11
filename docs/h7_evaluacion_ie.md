# H7 — Fusión y evaluación IE

La extracción usa los 99 IDs únicos del top-10 con filtro del ganador H4.
D12 une exclusivamente `(passage_id,tipo,inicio,fin)`; asociaciones a consultas
se publican después. El kit deduplica por pasaje. El enriquecimiento se mantiene
en `enriquecimiento.py`, sin tocar el normalizador congelado, ni texto u offsets.
Los montos auxiliares usan Decimal y las fechas de precisión parcial no inventan día.

## Comandos previstos

```bash
.venv/bin/python scripts/06_reglas.py
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 .venv/bin/python scripts/07_ner.py --cache-pesos hf_home
.venv/bin/python scripts/08_extraer.py
.venv/bin/python scripts/09_evaluar_ie.py
```

Los pasos 08 y 09 verifican el cierre real y sus hashes. El evaluador oficial se
invoca mediante el adaptador del kit en un temporal y se conservan sus bytes;
el detalle independiente comprueba TP/FP/FN y cifras. La complementaria incluye
los veinte IDs, incluso `1133_87`, vacío. Las categorías de errores no son
exclusivas; en_marca no demuestra un efecto causal de mayúsculas. No se compara
ni selecciona otro NER mediante Gold.

## Bloqueo observado antes de obtener cifras

La caché temporal de pesos de H5 ya no existía: se recuperó la misma revisión
inmutable, sin sustituir el modelo. El paso 07 se detuvo en `1812_0`: una LOC
cruda de una comilla `[945:946]` queda vacía tras el recorte; el código congelado
lanza `Span vacío después del recorte`. Evidencia en `salida/07_bloqueo_ner.json`.
Se conservan las cachés crudas obtenidas y no se elimina la predicción ni se
modifica el posproceso congelado. No existe extracción final ni resultados IE
oficiales. No presentar resultados parciales como evaluación completa.

La decisión pendiente es conservar D15 con H7 bloqueado o autorizar una versión
separada y auditada posterior al congelamiento. Esta última no sustituye la
referencia congelada y debe identificarse expresamente como posterior a D15.

## Entregables después de resolver el bloqueo

`entidades.csv` y sus vistas única/enriquecida; discrepancias de spans; resultados
IE literales del kit; detalle con soporte; complementaria sobre veinte IDs;
errores y resumen por categoría; comparación informativa crudo/posproceso;
figuras IE; manifiesto y tiempos. H8 requiere tablas y valoraciones humanas;
H9 requiere reporte, presentación/demo y validación final reproducible.
