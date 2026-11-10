# H6 — Captura gold ciega preparada

La interfaz y `mtx.gold.validar_gold()` están implementadas. No se ha creado una
muestra ni gold reales; faltan las aprobaciones H5 y la congelación.

## Antes de anotar

1. Aprobar explícitamente el alcance de revisión y la propuesta completa
   `config/criterios_anotacion.md`. Registrar cada aprobación por hash y fecha,
   sin modificar el texto aprobado. El protocolo de sustitución está en
   `config/protocolo.txt`; no sustituye automáticamente pasajes.
2. En Gazetteer, revisar cada candidato del alcance aprobado, aceptar/corregir o
   descartar personalmente y cerrar con nombre del revisor. La app conserva el
   historial y genera `config/gazetteer_aprobacion.json`.
3. Registrar los insumos legítimos antes de congelar: la guarda exige árbol limpio.
   Los archivos humanos H3 siguen sin seguimiento y no se incluyeron en estos
   commits técnicos; su versionado debe resolverse explícitamente, sin borrarlos.
4. Solo tras lo anterior, ejecutar `make congelar`. Luego, desde Gold en Streamlit,
   confirmar no haber visto predicciones y preparar la muestra. `make muestra-gold`
   verifica el manifiesto; no lo genera ni lo sustituye desde CLI.

## Captura

Arranque: `uv run --no-sync streamlit run src/mtx/app/app.py`. Usar el acceso Gold
de la barra lateral para trabajar sin cargar la vista de juicios.

- Seleccionar pasaje. Se muestran texto íntegro y marca gris; no se abre ninguna
  salida de reglas, NER, caché de predicciones ni panel de errores del sistema.
- Buscar el texto exacto y elegir expresamente la aparición por offsets y contexto.
  Elegir tipo sin valor preseleccionado y pulsar Agregar.
- Alternativamente seleccionar primer/último token. El recorte final conserva `$`.
- Corregir tipo/límites o marcar filas para eliminar y Guardar correcciones.
  El texto se toma de los límites elegidos por la persona; no se infieren spans.
- Pulsar Pasaje revisado completo; cero entidades es válido. Para corregir un
  pasaje cerrado, reabrirlo antes del cierre global.
- Al reabrir la app se conservan entidades y progreso por consulta. Las sesiones
  desfasadas se rechazan con aviso de recargar, sin sobrescribir decisiones.
- Completar todos los pasajes, escribir nombre y confirmar revisión ciega para
  cerrar el gold. Las correcciones posteriores requieren el protocolo explícito
  de nueva versión; no hay reapertura silenciosa.

## Contratos y protección

`gold_entidades.csv`: `passage_id,tipo,texto,inicio,fin`. `estado_gold.csv`:
`passage_id,texto_sha256,estado,n_entidades,revision`. El diario
`gold_revision.json` conserva revisión, hashes de archivos y fuentes; respaldos
en `historial_gold/`. Solo la app escribe datos reales mediante acciones humanas.
El cerrojo, `fsync`, reemplazo atómico y diario previo detectan concurrencia y
guardados interrumpidos; un estado parcial bloquea y conserva respaldos para
revisión, sin reparación automática.

Se verifica D15 antes del primer commit gold, muestra reproducible con semilla 42,
veinte IDs únicos/dos por consulta, pertenencia al ganador, hashes de texto,
estados cerrados, conteos, tipos, offsets, duplicados y ausencia de anidamiento.
Se permiten solapes parciales conforme a la propuesta IE. El cierre incluye hashes
de fuentes y gold; exporta el CSV oficial a la raíz solo tras validación completa.
Un pasaje cerrado sin entidades cuenta por el manifiesto y estado, sin centinelas.
La evaluación complementaria de veinte IDs corresponderá a H7.

Si existe selección P1, se mantiene disjunta y se presenta antes de evaluación;
esta tarea no genera ni activa ese conjunto opcional.
