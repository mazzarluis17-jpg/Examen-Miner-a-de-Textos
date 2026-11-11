# Reproducción de la entrega

## Fuente y preservación

Fuente oficial: carevies/discursos_AMLO, revisión
2c463bb3d5bf58742b4d842917da1211c44d2e18. El procedimiento de recuperación es
scripts/00c_recuperar_snapshot.py. No utiliza la punta móvil del dataset y no
reescribe data/corpus_meta.json, kit ni las auditorías históricas. Solo instala
los dos parquet ignorados después de validar ambos hashes binarios y el hash
canónico de pasajes. Si la serialización difiere con otras versiones, se detiene:
restablecer uv.lock y analizar versiones; nunca cambiar hashes de referencia.

Los 176 juicios, 138 entidades Gold y diez valoraciones son archivos humanos
oficiales versionados junto con revisiones, cierres e historiales. Los Excel
personales no se distribuyen. Los pesos de BETO no se distribuyen: las cachés
crudas oficiales permiten reproducir la extracción sin volver a inferir.
La revisión del modelo figura en data/modelo_ner.json. El campo histórico de estado
provisional se conserva como registro, y su congelación efectiva se acredita con
la etiqueta reglas-congeladas y las aprobaciones; no se reescribe retroactivamente.

## Desde un clon

Seguir README secciones 2–4. La alternativa a make setup es uv sync --locked;
las stopwords de respaldo ya están versionadas. No se necesita descargarlas para
reproducir los tokens. Los objetivos de extracción usan scripts/07c_ner_auditado.py
y scripts/08_extraer.py; no ejecutar el antiguo posproceso congelado sobre el
caso vacío, ni modificar las cachés crudas.

Para cifras: make resultados. Para documentos: make reporte laminas. El compilador
utilizado es XeLaTeX directo (vía permitida por la skill reporte-pdf); Pandoc no
está instalado en este entorno. La estructura fue aprobada explícitamente por Luis. El segundo corte contiene
un borrador de seis páginas, con prosa y conclusiones pendientes de revisión
humana. scripts/11_reporte.py lee el Markdown existente, genera tablas y compila
con reporte/plantilla.tex, sin sobrescribir sus párrafos. La opción --figuras
regenera únicamente la figura editorial H9; los resultados y figuras de H4
permanecen intactos. No se presenta este borrador como PDF final aprobado.
make validar es estricto y devuelve error mientras los cierres de revisión,
ensayo y publicación sigan pendientes. --permitir-pendientes enumera lo que sí
se comprobó y lo que falta, sin afirmar que la entrega está cerrada.

Los seis CSV tienen comparación binaria con sus fuentes. Los evaluadores
originales se ejecutan en carpetas temporales y su salida coincide byte a byte.
La validación comprueba offsets Python (inicio inclusivo, fin exclusivo), IDs,
ventanas, coberturas, revisiones, fuentes congeladas y hashes del corpus.

## Mediciones y alcance

Las latencias reales de la demo se registran en salida/11_demo_tiempos.json.
No representan un ensayo oral. Los resultados completos de la validación están
en salida/11_validacion_entrega.json. La reconstrucción se ejecutó en /tmp/mtx-h9-clon-6176a5f desde el commit
6176a5f, sin entorno ni cachés uv/HF previos. uv preparó 93 paquetes en 33.56 s
e instaló en 0.233 s (mediciones del instalador). Se descargó exclusivamente
la revisión fijada y se reconstruyeron los datos ignorados con todos sus hashes
originales. make resultados terminó con código 0; los 55 CSV comparados son
idénticos byte a byte. El tiempo total de descarga/procesamiento no se registró
y no se estima. El detalle está en salida/11_reproducibilidad_clon.json.
make entrega estricto sigue pendiente del reporte aprobado y del ensayo humano;
no se confunde la reproducción de cifras con el cierre académico de H9.

## Publicación personal, todavía no realizada

No se ha publicado ni se ha comprobado el acceso del profesor a un destino personal.
No cambiar origin ni publicar en GitLab. Una vez que Luis revise y autorice la URL,
crear un repositorio personal GitHub, conservar ambas ramas históricas y la
etiqueta de congelación. No crear v1.0-entrega ni afirmar una entrega final antes
de los cierres humanos y del acceso verificado exigidos por el PRD.


## Verificación de índice y rankings sin alterar referencias

También se ejecutó make indice ranking dentro del clon temporal, con el entorno
nuevo y los mismos parámetros congelados. Los 400 resultados y los 55 CSV
comparados resultaron idénticos. Los hashes binarios de tokens e índice coinciden;
únicamente la fecha construido de indice_meta.json difiere, como corresponde a
una construcción nueva. El índice tardó 36.7 s en esa ejecución. Los valores y
huellas están en salida/11_reproducibilidad_clon.json. Esta prueba debe realizarse
en una copia desechable para no sustituir la marca histórica del proyecto de entrega.
No se volvió a inferir BETO ni se usó Gold para ajustar el sistema.
