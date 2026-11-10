# Criterios IE — propuesta pendiente de aprobación

Este documento requiere aprobación explícita del alumno antes de congelar H5.
La herramienta no genera ni sugiere entidades. Se anota desde cero, sin consultar
predicciones de reglas o NER, y se revisa el pasaje completo, incluida su marca.

## Tipos y límites

- **PER:** nombre completo presente de una persona, sin cargo adyacente.
  `secretario de Salud, Jorge Alcocer Varela` → `Jorge Alcocer Varela`.
- **ORG:** nombre o sigla completos de instituciones, dependencias, empresas,
  partidos y organismos. Farmacéuticas y marcas de vacuna son ORG (D14);
  `vacuna` genérica queda fuera. `Secretaría de Salud de Tabasco` es una ORG
  completa, sin LOC anidado.
- **LOC:** estados, municipios, países y obras con nombre propio. Tren Maya,
  AIFA, Dos Bocas y refinería Olmeca son LOC.
- **FECHA:** expresión absoluta o relativa interpretable como fecha; incluir
  modificadores (`próximo 15 de enero`, `pasado 20 de noviembre`, `este 1 de julio`)
  y excluir artículos y preposiciones introductorios. `en 2019` → `2019`;
  cuatro cifras sin contexto temporal no son FECHA. Mes/año también es FECHA.
  Un intervalo explícito (`del 1 al 15 de enero`) es una entidad completa;
  enumeraciones son entidades separadas. Dos dígitos no autorizan inventar siglo;
  la normalización puede quedar sin resolver. Una fecha calendáricamente imposible
  no se considera una fecha válida.
- **MONTO:** dinero con cifra, escala y moneda o símbolo completos:
  `20 mil millones de pesos`, `$1,200 millones`. Conservar `$`; ese símbolo no
  implica automáticamente MXN. Porcentajes, dosis, litros, elementos, sucursales
  y beneficiarios no se anotan como MONTO ni como un sexto tipo: son auxiliares.

## Offsets, marcas y solapes

Se usan índices de carácter Python sobre el texto original completo e inmutable:
`inicio` inclusivo, `fin` exclusivo y `texto[inicio:fin] == texto_entidad`.
No son bytes ni posiciones del HTML. No modificar espacios, acentos o mayúsculas;
dejar fuera espacios extremos y puntuación ajena, conservando símbolos monetarios.
Las entidades de la marca se anotan igual que en el cuerpo; el cargo queda fuera
de PER. PREGUNTA e INTERLOCUTOR(A) son marcas genéricas, no entidades.

No duplicar una entidad. Una entidad contenida en otra se evita según la regla de
entidad completa (por ejemplo ORG con lugar interno); spans parcialmente solapados
que no se contienen pueden coexistir. No asignar dos tipos al mismo span: resolver
la ambigüedad personalmente con esta guía. Las excepciones deben acordarse antes
del gold, sin adaptar el criterio a predicciones del sistema.

## Cierre, sustitución y modo ciego

Un pasaje revisado puede cerrarse con cero entidades. No añadir centinelas.
La sustitución solo procede por menos de 25 palabras de contenido tras stoplist,
más de la mitad de palabras de protocolo o corrupción/truncamiento técnico;
nunca por carecer de entidades. Se documenta antes de ver predicciones y se usa
el siguiente candidato del mismo sorteo reproducible, sin ampliar el top-10.
No se sustituye automáticamente desde la app.

El gold de evaluación tiene 20 IDs únicos, dos por consulta, semilla 42, del
top-10 con filtro del ganador global. Se anotan todos los tipos presentes desde
cero. El alumno declara revisado cada pasaje y ejecuta el cierre global.
No se muestran predicciones hasta `anotaciones/cierre_gold.json` válido.
El gold no selecciona ni ajusta modelos. Tras congelación o cierre, correcciones
exigen revisión humana explícita, motivo, nueva versión y conservación de resultados.
