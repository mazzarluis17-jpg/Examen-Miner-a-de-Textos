# Guion de exposición y demo

Luis Alfredo Ramírez Maza · Licenciatura en Ciencia de Datos · UNAM, FES Acatlán.
Examen 1 — Minería de Textos · 11 de noviembre de 2026.

**Borrador para revisión del alumno. No acredita un ensayo realizado.**

## Lámina 1: problema y corpus (0:00–1:00)

Señalar el flujo de discursos a respuestas. La unidad recuperable es un pasaje,
no una conferencia completa. Explicar que se fijaron revisión del dataset,
limpieza y marcas de interlocutor antes de los juicios. Señalar la diferencia
entre recuperar pasajes y demostrar relaciones entre las entidades mencionadas.

## Lámina 2: segmentación e índice (1:00–2:00)

Explicar ventanas de 200 palabras con paso 150 y descarte bajo 40. La marca se
conserva en el texto para la evidencia, pero se excluye del índice con inicio_cuerpo.
Mostrar postings reales de huachicol y explicar df, frecuencia e idf. No atribuir
una mejora a una sensibilidad no ejecutada. Indicar que duplicar la ventana cambia
los IDs y obliga a rehacer todos los juicios; no se hizo sobre el experimento cerrado.

## Lámina 3: recuperación (2:00–3:15)

Comparar los cuatro promedios de resultados_ir.csv. Explicar la regla del ganador:
mayor MAP entre las variantes con filtro y empate a BM25. Los juicios son temáticos;
la fecha es una restricción de candidatos que se audita aparte. Mostrar Q3 como
consulta difícil; la recuperación léxica no resuelve todas las relaciones que pide
la pregunta. Explicar TF-IDF sublineal, normalización coseno y saturación BM25.

## Lámina 4: extracción (3:15–4:30)

Explicar reglas, gazetteer y BETO con revisión fija. Gold humano cerrado antes de
inferir, sin ajuste a sus etiquetas. Mostrar P/R/F1 oficiales y aclarar 19 pasajes
con entidades frente a la complementaria de 20. Explicar el único descarte de una
comilla vacía y su autorización posterior a D15; la versión congelada y las cachés
crudas siguen intactas. Referir tres errores observados: entidad partida,
SEDENA omitida y obra confundida LOC/ORG. No atribuir relaciones a coocurrencias.

## Lámina 5: límites y transición (4:30–5:00)

Señalar estados respaldado, ambiguo y no encontrado. Las valoraciones son humanas.
Presentar Q3 y avisar que la demo utiliza resultados congelados y no fuentes en red.

## Demo en vivo (5:00–7:00)

Desde la raíz ejecutar `make demo Q=Q3`, o bien
`uv run --no-sync python scripts/13_demo.py --q Q3`.
Mostrar en orden: consulta y ventana; top-10 TF-IDF/BM25; pasajes completos;
entidades con tipo, offsets y método; tabla de respuesta y fragmentos de evidencia.
Aclarar que una mención de costo o de organización no constituye automáticamente
una inversión o un responsable del proyecto. Q3 mantiene sus campos ambiguos.
Para inspección cómoda se puede redirigir la salida a un archivo temporal y usar
un visor de texto; el programa no altera datos ni llama al modelo.

Contingencia: salida/11_demo_guardada.txt es una **salida guardada, no una demo en
vivo**. Si se utiliza, anunciarlo explícitamente.

## Margen (7:00–8:00)

Reservado para navegación o una pregunta. El reparto es un presupuesto, no un
registro de tiempo medido. **Ensayo humano cronometrado: pendiente.** Registrar
fecha y tiempo real después de ensayar; no completar este campo automáticamente.
Las latencias técnicas de dos ejecuciones están en salida/11_demo_tiempos.json;
no son el tiempo de una exposición oral.

## Preguntas probables

| Pregunta | Respuesta y evidencia |
|---|---|
| ¿Por qué pasajes y 200 palabras? | Acotan el tema y los offsets dentro de una intervención. Decisión congelada; no se atribuye una sensibilidad no realizada. salida/01_limpieza.json. |
| ¿Cuánto ruido se quitó? | Usar conteos auditados de acotaciones, duplicados y fechas reparadas; salida/01_limpieza.json y auditorías 01_. |
| ¿Por qué excluir la marca del índice? | Evita recuperar por el nombre repetido de quien habla y conserva evidencia literal. inicio_cuerpo y D03. |
| ¿Por qué huachicol tiene ese idf? | Su df limita la proporción de pasajes que lo contienen; mostrar su posting real en salida/02_postings.md. |
| ¿BM25 coincide con rank_bm25? | No: esta variante suma 1 dentro del logaritmo de idf y evita pesos negativos; k1=1.5, b=0.75. |
| ¿Qué cambia el filtro? | Restringe fechas inclusivas; no cambia la etiqueta temática. salida/05_comparacion_filtros.csv. |
| ¿Qué consulta fue difícil? | Consultar AP por consulta en salida/05_ir_ganador_por_consulta.csv; Q3 tiene extracción relacional ambigua. |
| ¿Se eligió BETO con Gold? | No, elección técnica anterior al Gold, revisión fija y cierre antes de predicciones. D09/D15 y cierre_gold.json. |
| ¿Qué falló en IE? | Fronteras, siglas, LOC/ORG y marcas; casos concretos en salida/09_auditoria_ie.json. Monto sin unidad no observado. |
| ¿Qué cambiaría con embeddings? | Podrían recuperar paráfrasis y sinónimos sin coincidencia léxica; no se ejecutó ese experimento ni se atribuye una mejora numérica. |
| ¿Se pueden sumar los montos? | No sin verificar evento, fecha, unidad y relación; las ventanas pueden repetir la misma afirmación. |
| ¿Quién hizo las anotaciones? | Luis, con auxiliares externos importados de forma autorizada; cierres y valoraciones personales en Streamlit. README Uso de IA. |
