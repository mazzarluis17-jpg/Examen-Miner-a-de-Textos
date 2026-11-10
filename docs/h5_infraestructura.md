# H5 · Infraestructura técnica y contratos

Trabajo aislado en `desarrollo-h5`, desde `4cd65f1`. Commits de implementación:
`808bc9d` (reglas), `fb481f8` (NER) y `35998d4` (app y congelación). Fuente: PRD v3.0
§3.3, §3.6, §6.7, §6.8, §6.10, §6.11, D09–D15, D18, §12.2 y T09/T11/T12.
No se consultan juicios H3 ni anotaciones gold. No se ejecuta H4 por delegación.
Estas notas describen el trabajo aislado original; el estado integrado actual
se registra en la sección Integración y en `docs/harness/PROGRESS.md`.

## Componentes y contratos

| Archivo | Entrada → salida / aceptación |
| --- | --- |
| `src/mtx/reglas.py` | `extraer_reglas(texto, inicio_cuerpo) → list[Entidad]`; cinco tipos, offsets Python semiabiertos, texto original con marca. `extraer_con_auditoria` añade supresiones por longitud y prioridad del PRD. |
| `src/mtx/normalizacion.py` | Fechas absolutas ISO y escalas monetarias, sin modificar entidades; estados explícitos para fecha inválida, año ambiguo, relativo no resuelto y moneda ambigua. |
| `config/gazetteer_prescrito.csv` | Solo adiciones expresamente enumeradas en §6.7.4/D14. No contiene decisiones sobre candidatos minados. |
| `config/gazetteer_loc.csv` | Entidades federativas y variantes, lugares, obras y países exigidos por §6.7.5; LOC. |
| `scripts/06_reglas.py --minar` | Corpus canónico → `salida/06_siglas_candidatas.csv`: `sigla,nombre_propuesto,frecuencia,ejemplo`. Ninguna aceptación. Frecuencia sobre pasajes con ventanas, no discursos únicos. |
| `scripts/06_reglas.py` | Ámbito H4 → `salida/06_entidades_reglas.csv`, `06_colisiones_reglas.csv` y `cantidades_auxiliares.csv` con columnas exactas del PRD. Sin H4 falla antes de extraer. |
| `src/mtx/app/{gazetteer,vista_gazetteer}.py` | Candidatos y base de solo lectura → decisiones humanas, exportación `config/gazetteer_extendido.csv` y cierre con hashes. Respaldo, exclusión mutua y revisión. |
| `src/mtx/ambito_ie.py` | `data/mejor_modelo.json` con `modelo` igual a `tfidf_con_filtro` o `bm25_con_filtro`, ranking y pasajes. Devuelve pares consulta-pasaje y textos únicos, máximo 100. Contrato para integrar H4. |
| `src/mtx/ner_modelo.py` | Pipeline CPU perezoso; límite real menos especiales, ventanas subtokens con solapamiento 64, cobertura y capacidad verificadas, sin truncamiento silencioso. Deduplica dando prioridad al span no cortado y luego a confianza. |
| `scripts/07_ner.py` | Ámbito H4 → caché cruda por pasaje, ocho columnas en `salida/entidades_beto.csv`, crudas separadas, uniones y manifiesto `07_ejecucion_ner.json`. No lee gold ni juicios. |
| `src/mtx/muestreo.py` | Función pura `sortear_muestra`: emparejamiento global, semilla 42, dos plazas por consulta, IDs únicos y hashes. Preferencia alta/baja; si no es viable explica conflicto. No escribe `anotaciones/`. |
| `src/mtx/congelacion.py`, `scripts/06b_congelar.py` | Verificación de aprobaciones y P06 antes de crear etiqueta. `make congelar` exige además suite de reglas y NER en verde. |

La caché guarda texto hash, identidad/revisión de modelo y tokenizador,
fragmentación, inferencia, crudas, descartes MISC/OTH, tiempo y versión de
Transformers. El lote y la versión de posproceso no invalidan inferencia.
Cambiar texto/parámetros invalida la clave; `--forzar` reinfiere expresamente.
Un acierto no carga pesos. El posproceso conserva `$`, recorta extremos,
une intrapalabra e interpalabra y registra cada unión interpalabra.
Un exceso de capacidad al retokenizar genera error explícito.

## Ejecución

```bash
make minar-siglas
make app
# Activar "Abrir revisión Gazetteer (sin cargar juicios)".
# Revisar cada candidato; aceptar/corregir o descartar; cerrar con nombre del revisor.
# El alumno escribe y aprueba sus criterios de anotación antes de congelar.
make congelar
# Solo tras completar H4 en la rama principal:
make reglas
uv run python scripts/07_ner.py --modelo beto --cache-pesos /tmp/mtx-hf --solo-local
```

`make reglas` y `make ner` se detienen si falta el ganador IR, sin inventarlo.
El directorio `/tmp/mtx-hf` es de esta sesión y puede desaparecer: no forma parte
de la entrega. El script puede recuperar la revisión fija en una ejecución
posterior con red. Una vez poblada la caché versionada no requiere pesos para
reprocesar los mismos textos. No se pobló la caché real en esta sesión: falta H4.

La vista conserva un diario antes de publicar el CSV. Si se interrumpe entre
ambos archivos, bloquea cambios posteriores y conserva los respaldos. Recuperar
el CSV desde las decisiones del diario requiere revisión explícita del alumno;
no se efectúa una reparación silenciosa. Si cambian las fuentes de candidatos,
la revisión queda obsoleta y se conserva para reconciliación humana.

## Evidencia y pruebas

- P06 real: `salida/07_verificacion_ner.json`, ejemplos exclusivamente sintéticos,
  mapa real BIO, tokenizador rápido, revisión, memoria pico y tiempo de carga e
  inferencia conjunta. El aviso de pesos sobrantes `bert.pooler.*` corresponde al
  pooler no usado por clasificación de tokens; la cabeza NER cargó y funcionó.
- `tests/test_reglas.py`: todos los mínimos §6.7.1–3, moneda, gazetteer, marcas,
  colisiones, minería y T11 de offsets en 200 pasajes reales (marcador `lento`).
- `tests/test_ner_posproceso.py`: etiquetas, recorte, uniones, T12 con oración
  larga y borde, cobertura y caché sin red.
- `tests/test_h5_infraestructura.py`: ámbito bloqueado sin H4, congelación bloqueada
  sin aprobación, T09, concurrencia, respaldo e interrupción de revisión humana.
- Resultado consolidado en `salida/06_pruebas_h5.json`.

## Pendiente para cerrar H5

1. H3 y H4 ya están completados en `desarrollo-luis`; el ámbito del ganador global
   se conserva íntegro. La aprobación de relevancia existente permanece intacta.
2. El alumno revisa íntegramente los candidatos en la app. El botón de cierre
   crea `config/gazetteer_aprobacion.json`, con hashes de base, entradas prescritas,
   lugares, candidatos y CSV extendido. Registrar aprobación en decisiones.
3. El alumno fija `config/criterios_anotacion.md` con la tabla de §3.6, marca,
   D11/D13/D14 y excepciones. La constancia de aprobación sigue el contrato H3:
   `config/criterios_anotacion_aprobacion.json` con `sha256_criterio`,
   `aprobado_por`, `fecha`. No existe ni se ha simulado esa aprobación.
4. El principal tiene verificación técnica P06 y decisión **provisional** por
   criterio técnico, sin F1. No hay comparación ni aprobación humana simulada.
5. Congelar solo tras lo anterior y con árbol limpio. Después usar el botón «Preparar muestra ciega» de Gold, con confirmación de
   no haber visto predicciones y `config/protocolo.txt` presente. La app escribe
   exclusivamente el manifiesto inmutable; `make muestra-gold` lo verifica.
   El flujo de anotación Gold, sustitución y cierre pertenecen a H6 y no se implementaron.
   No se sortearon ni escribieron muestras reales anticipadamente.
6. Tras H4, ejecutar reglas y NER sobre el ámbito, conservar caché en Git y mantener
   las predicciones ocultas al anotador. La fusión de ocho columnas es H7 y consumirá
   estas salidas; no se genera `entidades.csv` final antes de sus prerrequisitos.

La comparación con segundo NER y selección humana es P1; no se inicia mientras
faltan P0. La infraestructura mantiene crudas y unidas para evaluar posteriormente
el efecto del posproceso sin retocar el gold.

## Integración

La integración autorizada en `desarrollo-luis` se realiza mediante merge real de
`e164ca6` sobre `c69581c`, sin squash, cherry-pick ni rebase. Se conservan todos los
commits y el worktree de origen. El único conflicto Git fue el registro de progreso;
se reconcilió con H4 cerrado y H5 técnico, recuperando las notas locales protegidas.
Las aprobaciones, juicios, historial, criterios, pool, rankings y resultados H4
mantienen sus hashes. Evidencia y pruebas en `salida/06_integracion_h5.json`.
No se regeneraron las evaluaciones ni se hizo push. Las decisiones humanas listadas
arriba siguen pendientes; esta integración no aprueba gazetteers ni abre H6.

El destino oficial indicado por Luis es GitHub, aunque el remote histórico y
las decisiones previas documentan GitLab. Publicación y acceso del profesor deben
resolverse en la rama principal antes de entrega; no se cambia el remote aquí.
