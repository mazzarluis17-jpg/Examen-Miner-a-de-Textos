# Comprobación manual de la aplicación

La suite automatizada usa exclusivamente etiquetas sobre fixtures sintéticos en
`tmp_path`. La aplicación real no crea archivos al arrancar. Luis aprobó
`config/criterios_relevancia.md` el 2026-11-09 sin modificaciones, con constancia
ligada a su SHA-256. El 2026-11-10 autorizó transferir sus 176 juicios realizados
en Excel: 113 relevantes y 63 no relevantes. No se atribuyen falsamente a captura
directa íntegra en Streamlit. AppTest verificó la cobertura total por consulta y
la reapertura; Luis confirmó visualmente el resultado y H4 quedó completado.

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
7. En Gold, tras aprobar H5 y D15, preparar manifiesto ciego y comprobar búsqueda
   exacta con elección explícita entre apariciones repetidas. La captura ya está
   implementada; no carga ni muestra predicciones.
8. En H6 (pendiente), comprobar selección por tokens con `$`, duplicados y offsets
   Unicode. H3 prueba escape HTML y resaltado sobre offsets con emoji, `<` y `&`.
9. En H5, usar los candidatos ya minados y el alcance aprobado por hash; abrir
   Gazetteer desde la barra lateral sin cargar juicios. Revisar evidencia; aceptar/corregir con nombre/tipo
   explícitos o descartar. Reabrir y verificar revisión/respaldos; otra sesión
   desfasada debe bloquearse. El cierre exige revisar todos los candidatos del
   alcance aprobado; los excluidos técnicamente no son rechazos humanos.
   Tras `reglas-congeladas`, comprobar que se impide toda escritura.
10. En H6 (pendiente), comprobar cierre del gold y habilitación posterior de
    predicciones. H3 no lee entidades ni caché NER, aunque esos archivos existan.

## Aprobación y congelación antes del primer juicio

El asistente presenta la propuesta completa y espera aprobación explícita. Solo
después registra la decisión fechada y crea
`config/criterios_relevancia_aprobacion.json` con `sha256_criterio`, `aprobado_por`
y `fecha`. El hash corresponde al texto final, no al borrador previo a cambios.
La constancia ya existe por aprobación explícita de Luis el 2026-11-09;
iniciar la app nunca constituye por sí solo una aprobación.
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
ni se ejecuta la evaluación IR durante H3. Captura, corrección y cierre Gold están
implementados y bloqueados hasta sus prerrequisitos. La alternativa CLI sigue
pendiente; el flujo principal es Streamlit. Ver `docs/h6_anotacion.md`.
