# H7 — Extracción y evaluación IE completadas

## Versión y trazabilidad

Posproceso `2-vacios-auditados`, autorizado explícitamente después de D15.
La versión congelada y la etiqueta `reglas-congeladas` permanecen intactas.
Único cambio: omitir y auditar spans vacíos después del recorte original.
No se modificaron Gold, reglas, pesos BETO, etiquetas ni límites de las demás predicciones.
El modelo y su revisión se conservan en `data/modelo_ner.json`, elegidos por criterio técnico antes del Gold.

Se procesaron 99 pasajes únicos del ganador IR: 901 entidades únicas y 909 asociaciones públicas.
Hubo un descarte: LOC de una comilla en `1812_0`, [945:946]. Registro:
`salida/07_descartes_vacios.csv`; la caché cruda conserva la predicción original.
En 98 pasajes v1 y v2 producen exactamente el mismo resultado; el restante aborta en v1.

## Métricas del evaluador original para la versión posterior a D15

Fuente literal: `resultados_ie.csv`, idéntica a `salida/resultados_ie.csv`.
No existe F1 anterior completo de v1: ejecución abortada. No se inventa un cero ni se sustituye una cifra previa.
Registro por método y tipo en `salida/09_cambios_post_congelamiento.csv`.

| Método | Precisión | Recall | F1 | TP | Predichas | Gold |
|---|---:|---:|---:|---:|---:|---:|
| regla | 0.7245 | 0.5145 | 0.6017 | 71 | 98 | 138 |
| modelo | 0.6947 | 0.6594 | 0.6766 | 91 | 131 | 138 |
| combinado | 0.6257 | 0.8116 | 0.7066 | 112 | 179 | 138 |

El combinado mejora recall y F1, con menor precisión. BETO no cubre FECHA/MONTO;
esa ausencia aparece expresamente en `salida/09_ie_detalle.csv`.

## Pasaje vacío y evaluación complementaria

El kit evalúa 19 pasajes con entidades; la complementaria usa los 20 IDs oficiales.
`1133_87` permanece revisado sin entidades. Dos FP del modelo en ese pasaje se
incluyen solo en la complementaria, sin modificar la cifra oficial del kit.
Fuente: `salida/09_evaluacion_20_ids.csv`.

| Método | Precisión (20 IDs) | Recall | F1 |
|---|---:|---:|---:|
| regla | 0.7245 | 0.5145 | 0.6017 |
| modelo | 0.6842 | 0.6594 | 0.6716 |
| combinado | 0.6188 | 0.8116 | 0.7022 |

## Errores y alertas

Las categorías son no exclusivas. Fuentes: `salida/09_analisis_errores.csv`,
`salida/09_resumen_errores.csv` y `salida/09_auditoria_ie.json`. Se revisaron los ejemplos:

| Categoría | Caso observado |
|---|---|
| entidad_partida | `1458_12`: Istmo de Tehuantepec → Is | de | huantepec |
| sigla_no_reconocida | `326_25`: SEDENA →  |
| monto_sin_unidad | No apareció |
| obra_LOC_vs_ORG | `228_7`: Corredor Interoceánico del Istmo de Tehuantepec → Corredor Interoceánico del Istmo de Tehuantepec |
| en_marca | `1277_28`:  → SERVIDORA DE LA NACIÓN |

`en_marca` describe ubicación del error; no demuestra un efecto causal de las mayúsculas.
El desacuerdo ORG/LOC del Corredor se conserva tal como lo anotó y autorizó Luis; no se retoca Gold.
La alerta de F1=1 en MONTO (9 entidades) se conserva: revisión de trazabilidad en
`salida/09_revision_alertas.json`; sin ajustar reglas ni etiquetas.

## Efecto informativo del posproceso

`salida/09_efecto_posproceso.csv` separa crudo, recorte con unión intrapalabra
y posproceso completo. Así el efecto de unir entre palabras no se confunde con el recorte.
No se utiliza esta comparación para seleccionar ni ajustar el modelo.

| Configuración | F1 modelo, TODOS |
|---|---:|
| crudo_sin_recorte_ni_union | 0.5292 |
| recorte_sin_union_interpalabra | 0.6667 |
| posproceso_v2_posterior_D15 | 0.6766 |

## Reproducción

```bash
uv run --no-sync python scripts/06_reglas.py
uv run --no-sync python scripts/07c_ner_auditado.py --solo-local
uv run --no-sync python scripts/08_extraer.py
uv run --no-sync python scripts/09_evaluar_ie.py
```

Las 99 cachés versionadas evitan descargar o cargar pesos al reproducir.
Las figuras usan Chrome local. No se usa red. La segunda corrida NER tuvo 99 aciertos de caché y cero inferencias.
Los CSV deterministas y las dos figuras se verifican por SHA-256; tiempos y commit de manifiestos son metadatos variables.
La versión auxiliar de extracción depende de hashes de código, no de commits posteriores solo de datos.
Pruebas: 336 aprobadas, 9 deseleccionadas; Ruff limpio. Sin cambios a H3–H6 ni al kit.

## Pendientes de entrega

H8: tablas por consulta, `respuestas.csv`, evidencia y valoraciones personales del alumno.
H9: reporte PDF de 4–6 páginas con aprobación humana, presentación de máximo cinco láminas,
guion/demo, README y validación reproducible final. No se avanza esos hitos en esta sesión.
