# Propuesta de alcance de revisión H5

Estado: pendiente de aprobación explícita del alumno. PRD §6.7.4 exige revisión
humana y extensión útil, sin cuota. Este alcance no acepta ni rechaza entidades.

## Política propuesta

Conservar los 1,505 candidatos originales intactos. Buscar cada sigla (sensible a
mayúsculas) y nombre minado (sin distinguir mayúsculas) con límites de palabra en
los 99 textos completos del ganador H4. Medir cuáles de esas coincidencias están
contenidas en aliases de los gazetteers base, prescritos y LOC existentes.

Revisar todos los candidatos con al menos una coincidencia adicional **en el
cuerpo**, siguiendo el énfasis de minería del PRD. Ordenar por número de
coincidencias de cuerpo, cobertura de pasajes y total de coincidencias; desempatar
por sigla. No se impone frecuencia mínima ni cupo, ni se utiliza el gold, NER,
predicciones de reglas o una clasificación automática de candidatos.

Que una forma aparezca no prueba que sea ORG o LOC. El alumno decide su aceptación,
nombre y tipo, o rechazo. Los candidatos excluidos del alcance no se registran como
rechazados ni se incorporan al gazetteer.

## Subconjunto completo para aprobar

| Candidato | Coincidencias adicionales en cuerpo |
| --- | ---: |
| COVID | 13 |
| AMLO | 2 |
| III | 2 |
| MELINA | 1 |
| VEGA | 1 |
| IVA | 1 |
| SARS | 1 |
| UMAS | 1 |
| VACUNA | 1 |
| VII | 1 |
| VIII | 1 |

## Cobertura y exclusiones

Fuente: `salida/06_revision_alcance.json` y los CSV de auditoría correspondientes.

- Once candidatos incluyen las 25 coincidencias adicionales de cuerpo entre los
  candidatos originales, presentes en 16 de los 99 pasajes. No se pierde ninguna
  de estas coincidencias de cuerpo al acotar la revisión.
- Esos candidatos también tienen dos coincidencias adicionales de marca.
- Fuera del alcance: 1,456 candidatos sin coincidencias en este ámbito; seis con
  coincidencias ya cubiertas; 32 con coincidencias adicionales solo en marcas.
- Los candidatos excluidos tienen 328 coincidencias adicionales de marca, no de
  cuerpo. Se conservan en la auditoría: no se afirma que sean entidades correctas
  ni que la extensión las cubra. Las marcas siguen formando parte del gold.
- En total se observaron 369 coincidencias candidato–span; 14 están contenidas en
  aliases existentes. Son medidas léxicas, no recall ni F1 de extracción.

`06_revision_alcance.csv` contiene los once y su evidencia del ámbito;
`06_revision_auditoria.csv`, los 1,505 con motivo de alcance;
`06_revision_ocurrencias.csv`, pasaje y offsets de coincidencias literales.
El original `06_siglas_candidatas.csv` no se modifica. La propuesta es reproducible
byte por byte con `scripts/06c_alcance_gazetteer.py`; no regenerarla tras iniciar
decisiones sin reconciliación explícita.

## Aprobación y uso

Tras aprobación explícita, registrar fecha, persona y SHA-256 exacto de
`salida/06_revision_alcance.json` en `config/alcance_gazetteer_aprobacion.json`
(`sha256_propuesta`, `aprobado_por`, `fecha`) y la decisión en la bitácora.
Este archivo de aprobación **no existe todavía**.

La app muestra la propuesta pero bloquea decisiones hasta verificar esa constancia
y las fuentes. Después exige decisiones sobre los once para cerrar el gazetteer.
Mantiene separados los rechazos humanos y las exclusiones de alcance. El cierre
aprueba también los gazetteers prescritos y conserva todos los hashes anteriores.
