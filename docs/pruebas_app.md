# Comprobación manual de la aplicación

La suite automatizada usa exclusivamente etiquetas sobre fixtures sintéticos en
`tmp_path`. La aplicación real no crea archivos al arrancar. Los juicios del alumno
no han comenzado; falta aprobar `config/criterios_relevancia.md`.

## Diez pasos de revisión humana

1. Arrancar con `uv run --no-sync streamlit run src/mtx/app/app.py`: aparecen Estado,
   Juicios, Gold y Gazetteer sin descargar datos ni cargar NER.
2. Abrir Estado: pool verificado; criterio pendiente humano y anotación bloqueada
   mientras falte aprobación. Ningún artefacto se considera válido por existir.
3. Tras aprobación explícita y registro de su hash, abrir Juicios: consulta,
   pregunta y texto completo resaltado; fecha con recordatorio temático. No aparecen
   procedencia, puntajes ni rangos de recuperación. El contador indica posición de
   presentación, no rango de recuperación.
4. Leer y pulsar 1 o 0; comprobar autoguardado. Omitir deja vacío un pendiente y
   conserva una decisión existente. Anterior permite revisitar sin cambiar etiquetas.
5. Cerrar y reabrir: recuperar respuestas y primer pendiente por consulta. Guardar
   no asigna etiquetas; Recargar desde disco descarta solo el estado de la sesión.
6. Abrir dos sesiones, responder en una y guardar desde la otra: se rechaza la
   sesión antigua con aviso de recargar. Las decisiones anteriores se conservan.
7. En H6 (pendiente), comprobar búsqueda Gold y selección entre apariciones
   repetidas. Actualmente Gold informa pendiente y no muestra predicciones.
8. En H6 (pendiente), comprobar selección por tokens con `$`, duplicados y offsets
   Unicode. H3 prueba escape HTML y resaltado sobre offsets con emoji, `<` y `&`.
9. En H5 (pendiente), comprobar aceptar/corregir/descartar gazetteer y bloqueo tras
   congelación. Actualmente la pestaña no escribe datos de ese hito.
10. En H6 (pendiente), comprobar cierre del gold y habilitación posterior de
    predicciones. H3 no lee entidades ni caché NER, aunque esos archivos existan.

## Aprobación y congelación antes del primer juicio

El asistente presenta la propuesta completa y espera aprobación explícita. Solo
después registra la decisión fechada y crea
`config/criterios_relevancia_aprobacion.json` con `sha256_criterio`, `aprobado_por`
y `fecha`. El hash corresponde al texto final, no al borrador previo a cambios.
Este archivo no existe todavía; no hay aprobación implícita por iniciar la app.
Ejecutar `make pool` antes del primer juicio para incorporar el hash del criterio
y recargar la app. Una modificación posterior bloquea escrituras y exige revisión.

## Persistencia y recuperación

`anotaciones/juicios_relevancia.csv` conserva exactamente las cuatro columnas del
contrato. Un omitido es un campo vacío; no se completa el resto del pool.
`juicios_relevancia_estado.json` guarda revisión, hashes anterior/nuevo y huellas
de insumos; `historial_juicios/` conserva CSV previos. Solo la app crea estos archivos
al recibir acciones humanas. La exclusión mutua con `flock` cubre lectura y escritura
en Debian y evita carreras entre sesiones. El temporal se sincroniza y se reemplaza
con `os.replace`; también se sincroniza el directorio.

El diario se prepara antes de reemplazar el CSV. Si una interrupción deja el CSV
anterior, la lectura reconoce su hash y revisión, sin perder decisiones ni promover
el intento incompleto. Si el CSV tiene otro hash, se bloquea: no se repara ni se
reescribe automáticamente. Los respaldos permiten una recuperación humana explícita.
El archivo `.juicios.lock` es un cerrojo local, sin contenido de anotación.

La validación parcial permite retomar pendientes; la cobertura total se verifica
con `pool.validar_juicios()` y se presenta en Estado. No se exportan juicios a la raíz
ni se ejecuta la evaluación IR durante H3. La alternativa CLI, Gold y Gazetteer
quedan para las etapas correspondientes; no se implementan funciones ficticias.
