# H8 — Respuestas con evidencia verificable

## Alcance y estado

El hito técnico genera las diez respuestas sobre los top-10 de `bm25_con_filtro`.
Los valores proceden exclusivamente de las entidades enriquecidas y cantidades
auxiliares de H7. No se ejecuta extracción, inferencia ni evaluación, no se
consultan fuentes externas y no se modifica el Gold cerrado.

Las diez tablas se pueden revisar antes de escribir valoraciones (PRD 6.13 y
flujo 11.1). H8 no se declara entregable humano completo hasta que Luis escriba
las diez valoraciones personales vigentes. H9 no se inicia en esta tarea.

## Reproducción

```bash
uv run --no-sync python scripts/10_tablas.py
# Equivalente:
make tablas
```

Los contenidos se reproducen de forma determinista; tiempos y `commit_codigo`
describen cada ejecución y pueden variar entre commits.

La política está en `config/tablas_respuesta.yaml`, versión
`h8-v2-vinculos-explicitos`. La política inicial se fijó antes de generar;
se corrigió posteriormente la confusión técnica entre coocurrencia y relación.
El cambio, sin valoraciones humanas previas, se documenta con ambos hashes en
`salida/10_cambios_politica.json` y `docs/decisiones.md`. No se alteran las
predicciones ni los parámetros de H7 para obtener mejores tablas.

## Evidencia y límites

`salida/respuestas.csv` conserva las dieciséis columnas exactas de PRD 6.13.
Cada fila con valor tiene su documento, pasaje, fecha documental, hablante,
cita literal y offsets Python inclusivo/exclusivo. `entidades_referencia`
contiene JSON con el span principal y los spans de apoyo, su origen H7 y offsets.
La fecha documental no sustituye a una fecha de evento no extraída.

Se exige ancla temática y patrón del campo en ±60 caracteres y oración contigua.
Para marcar respaldo se exige además un vínculo léxico explícito con el valor
en su oración; anclas en otra oración requieren anáfora explícita. El patrón
pertenece a la entidad más cercana, sin transferir participación, operación o
pago a otra entidad de la misma cita. Los fragmentos o alternativas contenidas,
preguntas, negaciones y contextos competidores quedan ambiguos. Son decisiones
de presentación H8, no modificaciones ni correcciones de entidades H7.

Una clasificación `respaldado_en_texto` no acredita veracidad ni corrige posibles
errores semánticos del NER: significa que pasó las comprobaciones textuales
configuradas. Las valoraciones humanas deben examinar precisamente estas
limitaciones. Ningún campo vacío se completa por conocimiento externo.

La lista de exclusión se aplica solo a PER para funcionarios/responsables; no
elimina ORG, LOC o cantidades. Los spans de la marca se excluyen de las tablas,
pero no de los archivos IE. Los contadores están en `salida/10_exclusiones.csv`.
Las farmacéuticas siguen D14; los estados se contrastan con las 32 entradas
federativas y variantes ya documentadas; las organizaciones empresariales se
filtran por el tipo del kit, sin inventar nuevas clasificaciones.

Se agrupan únicamente alias ya verificados (`canonico`), o texto normalizado si
no los hay. La reconstrucción de posiciones globales usa exclusivamente tokens
de las ventanas recuperadas de la misma intervención. Ventanas solapadas no
cuentan como confirmaciones independientes. Se mantienen frecuencia total,
pasajes, discursos y eventos distintos en `salida/10_agregados.csv`.
`salida/10_evidencias_completas.csv` conserva el detalle anterior a deduplicar.

No se suman inversiones ni se convierten monedas. Los pagos anteriores/nuevos,
propuestas/anuncios, unidades y eventos distintos no se mezclan. Valores
comparables incompatibles de un campo exclusivo y del mismo evento quedan
contradictorios, sin resolverlos por mayoría. El corte de ocho valores se aplica
solo al Markdown; el CSV no pierde los demás valores o estados.

## Archivos

- `salida/respuestas.csv`: respuesta por campo y evento, con evidencia exacta.
- `salida/tablas_respuesta/Q1.md` a `Q10.md`, y `todas.md`.
- `salida/10_agregados.csv`, `10_evidencias_completas.csv`, `10_exclusiones.csv`.
- `salida/10_cobertura_respuestas.csv`, `10_validacion_h8.json`.
- `salida/10_hashes_tablas.json`, `10_manifiesto_respuestas.json`, `10_tiempos.json`.
- `salida/10_valoraciones_plantilla.yaml`: diez entradas sin opiniones ni aprobaciones.

El manifiesto de H8 es independiente del manifiesto H7: no lo sobrescribe.
El validador de congelación usa el inventario real de `config/` en la etiqueta:
las políticas nuevas de presentación no alteran los insumos congelados; todos
los archivos que sí estaban en H5 se siguen comprobando, incluso si se borran.

## Trabajo exclusivo del alumno

1. Revisar las diez tablas y sus citas en `salida/tablas_respuesta/todas.md`.
2. Copiar la plantilla, si todavía no existe el archivo humano:

   ```bash
   cp -n salida/10_valoraciones_plantilla.yaml anotaciones/valoraciones.yaml
   ```

3. Escribir personalmente `valoracion` para Q1–Q10, dos o tres líneas por
   consulta: credibilidad, información faltante y errores. Conservar el hash.
4. Ejecutar:

   ```bash
   uv run --no-sync python scripts/10_tablas.py --exigir-valoraciones
   ```

Cada entrada usa `Q1: {tabla_sha256: ..., valoracion: ...}`. La validación exige
las diez entradas no vacías y hashes vigentes; no certifica autoría humana ni
calidad de una opinión mediante código. El asistente no redacta esas opiniones.

`tabla_sha256` identifica el contenido técnico de la tabla, excluyendo su bloque
humano para evitar autorreferencia. El cuerpo incorpora la huella de todas las
filas de evidencia de la consulta, incluso las que no caben entre los ocho
valores presentados. Así un cambio de valores, estados o pasajes invalida la
valoración. Un hash obsoleto muestra `[VALIDAR] pendiente del alumno`; nunca se
actualiza silenciosamente el archivo humano ni se sustituye su texto.

## Valoraciones desde Streamlit

La ruta rápida reutiliza la aplicación existente:

```bash
uv run --no-sync streamlit run src/mtx/app/app.py
```

Activar **Abrir valoraciones H8 (sin cargar juicios)**. Se presenta una consulta
a la vez con su pregunta, tablas de respuesta y citas. El desplegable de
evidencia completa permite revisar documento, pasaje, fecha, hablante y offsets.
No se carga NER ni se ejecuta extracción. No hay notas numéricas, opiniones
sugeridas ni texto de valoración precargado.

Escribir personalmente dos o tres líneas sobre credibilidad, faltantes y errores
y pulsar **Guardar valoración y continuar**. Se avanza a la primera pendiente;
el selector permite volver a una consulta. Guardar antes de salir o cambiar
de consulta. Al reabrir, se recuperan texto y progreso. Una valoración cuyo hash
ya no coincide no se cuenta como vigente; su texto anterior se conserva para
revisión personal, sin aprobación automática del nuevo contenido.

La app escribe `anotaciones/valoraciones.yaml` con el contrato existente, y
`valoraciones_estado.json` con revisión y hash; conserva versiones en
`historial_valoraciones/`. Usa cerrojo, escritura atómica con fsync y diario
previo: concurrencia o interrupciones bloquean, sin sobrescritura silenciosa.
No se modifica ningún archivo humano al abrir la sección.

Al guardar la décima opinión vigente se ejecuta automáticamente
`scripts/10_tablas.py --exigir-valoraciones`. Se verifica que el archivo humano,
respuestas y cuerpos de tablas permanezcan intactos; solo se incorporan los
bloques de valoración y metadatos de validación. `salida/10_cierre_h8.json` es
un registro técnico, no una opinión ni una aprobación inventada. La pantalla
muestra H8 validado cuando coinciden revisión, archivo humano y hashes. Si la
validación se interrumpe, las opiniones siguen guardadas y existe un botón
para reintentar. No se ejecuta H9 ni se realizan operaciones Git desde la app.

El versionado de los archivos humanos se realiza después de que existan; el
commit de infraestructura no incluye opiniones simuladas o plantillas como
si fueran respuestas del alumno. Pruebas exclusivamente sintéticas verifican
la transición 0/10 a 10/10 y la invocación del comando estricto. La prueba real
de apertura permanece 0/10 sin crear el YAML humano.
