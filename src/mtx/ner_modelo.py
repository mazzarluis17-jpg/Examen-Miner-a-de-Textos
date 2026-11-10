"""NER CPU: ventanas completas, caché cruda y posproceso independiente (D18)."""

from __future__ import annotations

import hashlib
import json
import re
import string
import time
from pathlib import Path

from mtx.app.componentes import atomico

MAPA = {"PER": "PER", "PERSON": "PER", "ORG": "ORG", "LOC": "LOC", "GPE": "LOC"}


def clave_cache(texto, parametros):
    """El lote y la versión de posproceso no invalidan inferencia."""
    claves = (
        "repo_id",
        "revision",
        "tokenizador",
        "max_length_real",
        "solapamiento",
        "aggregation_strategy",
        "device",
        "mapa_etiquetas",
    )
    datos = {k: parametros[k] for k in claves}
    datos["texto_sha256"] = hashlib.sha256(texto.encode()).hexdigest()
    return hashlib.sha256(json.dumps(datos, sort_keys=True).encode()).hexdigest()


def cargar_pipeline(parametros, cache_dir=None, solo_local=False):
    """Carga perezosa; exige revisión inmutable y cabeza de clasificación NER."""
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

    if not re.fullmatch("[a-f0-9]{40}", parametros["revision"]):
        raise ValueError("La revisión debe ser un SHA completo")
    argumentos = {
        "revision": parametros["revision"],
        "cache_dir": cache_dir,
        "local_files_only": solo_local,
    }
    tokenizador = AutoTokenizer.from_pretrained(
        parametros["tokenizador"], use_fast=True, **argumentos
    )
    modelo = AutoModelForTokenClassification.from_pretrained(parametros["repo_id"], **argumentos)
    if not tokenizador.is_fast:
        raise ValueError("Se exige tokenizador rápido con offsets")
    etiquetas = {
        str(v).removeprefix("B-").removeprefix("I-") for v in modelo.config.id2label.values()
    }
    if not {"PER", "ORG", "LOC"}.issubset(etiquetas):
        raise ValueError("La cabeza no expone las etiquetas NER requeridas")
    limite = min(modelo.config.max_position_embeddings, tokenizador.model_max_length)
    if parametros["max_length_real"] != limite:
        raise ValueError(f"Límite configurado distinto del real: {limite}")
    return pipeline(
        "token-classification",
        model=modelo,
        tokenizer=tokenizador,
        aggregation_strategy="simple",
        device=-1,
    )


def fragmentar(texto, tokenizador, max_length_real, solapamiento):
    """Ventanas de subtokens; incluye espacios iniciales/finales y última cola."""
    capacidad = max_length_real - tokenizador.num_special_tokens_to_add(pair=False)
    if not 0 <= solapamiento < capacidad:
        raise ValueError("Solapamiento incompatible con capacidad real")
    offsets = tokenizador(
        texto, add_special_tokens=False, return_offsets_mapping=True, truncation=False
    )["offset_mapping"]
    if not offsets:
        return [(0, len(texto))] if texto else []
    ventanas = []
    for i in range(0, len(offsets), capacidad - solapamiento):
        j = min(i + capacidad, len(offsets))
        inicio = offsets[i][0] if i else 0
        fin = offsets[j - 1][1] if j < len(offsets) else len(texto)
        # Incluir huecos entre tokens sin perder cobertura con solapamiento cero.
        if ventanas and inicio > ventanas[-1][1]:
            inicio = ventanas[-1][1]
        fragmento = texto[inicio:fin]
        n = len(tokenizador(fragmento, add_special_tokens=False)["input_ids"])
        if n > capacidad:
            raise ValueError("Retokenización excede capacidad: no se permite truncar")
        ventanas.append((inicio, fin))
        if j == len(offsets):
            break
    if ventanas[0][0] != 0 or ventanas[-1][1] != len(texto):
        raise ValueError("Cobertura incompleta")
    return ventanas


def validar_span(texto, entidad):
    """Rechaza offsets incompatibles; jamás reconstruye desde word del modelo."""
    a, b = entidad["inicio"], entidad["fin"]
    if not 0 <= a < b <= len(texto) or texto[a:b] != entidad["texto"]:
        raise ValueError("Span NER incompatible con texto canónico")


def inferir_crudo(texto, predictor, parametros):
    """Lotes explícitos; proyección y prioridad borde/confianza en solapamientos."""
    ventanas = fragmentar(
        texto, predictor.tokenizer, parametros["max_length_real"], parametros["solapamiento"]
    )
    etiquetas = {
        str(v).removeprefix("B-").removeprefix("I-")
        for v in predictor.model.config.id2label.values()
    }
    candidatas, descartadas = [], 0
    lote = parametros["lote"]
    for i in range(0, len(ventanas), lote):
        bloque = ventanas[i : i + lote]
        resultados = predictor([texto[a:b] for a, b in bloque], batch_size=lote)
        if len(resultados) != len(bloque):
            raise ValueError("Pipeline devolvió un número incorrecto de ventanas")
        for (a, b), filas in zip(bloque, resultados):
            for fila in filas:
                etiqueta = fila["entity_group"]
                if etiqueta not in etiquetas:
                    raise ValueError("Etiqueta ausente en id2label")
                if etiqueta in {"MISC", "OTH"}:
                    descartadas += 1
                    continue
                if etiqueta not in MAPA:
                    raise ValueError(f"Etiqueta NER no soportada: {etiqueta}")
                inicio, fin = a + int(fila["start"]), a + int(fila["end"])
                if not a <= inicio < fin <= b:
                    raise ValueError("Offset fuera de la ventana")
                entidad = {
                    "tipo": MAPA[etiqueta],
                    "texto": texto[inicio:fin],
                    "inicio": inicio,
                    "fin": fin,
                    "confianza": float(fila["score"]),
                    "cortada": (inicio == a and a > 0) or (fin == b and b < len(texto)),
                }
                validar_span(texto, entidad)
                candidatas.append(entidad)
    elegidas = []
    for e in sorted(
        candidatas, key=lambda e: (e["cortada"], -e["confianza"], e["inicio"], -e["fin"])
    ):
        if not any(
            e["tipo"] == g["tipo"] and e["inicio"] < g["fin"] and g["inicio"] < e["fin"]
            for g in elegidas
        ):
            elegidas.append(e)
    return sorted(elegidas, key=lambda e: (e["inicio"], e["fin"])), descartadas


def posprocesar(texto, crudas, passage_id=""):
    """Recorte y uniones U15; devuelve auditoría interpalabra por separado."""
    entidades, uniones = [], []
    puntuacion = set(string.punctuation.replace("$", "") + "«»“”¿¡")
    for original in sorted(crudas, key=lambda e: (e["inicio"], e["fin"])):
        validar_span(texto, original)
        e = original.copy()
        a, b = e["inicio"], e["fin"]
        while a < b and (texto[a].isspace() or texto[a] in puntuacion):
            a += 1
        while b > a and (texto[b - 1].isspace() or texto[b - 1] in puntuacion):
            b -= 1
        if a == b:
            raise ValueError("Span vacío después del recorte")
        e.update(inicio=a, fin=b, texto=texto[a:b])
        if entidades:
            previa = entidades[-1]
            hueco = texto[previa["fin"] : a]
            if previa["tipo"] == e["tipo"] and a >= previa["fin"] and hueco in {"", " "}:
                if hueco == " ":
                    uniones.append(
                        {
                            "passage_id": passage_id,
                            "tipo": e["tipo"],
                            "inicio_1": previa["inicio"],
                            "fin_1": previa["fin"],
                            "inicio_2": a,
                            "fin_2": b,
                            "inicio_union": previa["inicio"],
                            "fin_union": b,
                            "texto_union": texto[previa["inicio"] : b],
                            "confianza_1": previa["confianza"],
                            "confianza_2": e["confianza"],
                        }
                    )
                previa.update(
                    fin=b,
                    texto=texto[previa["inicio"] : b],
                    confianza=min(previa["confianza"], e["confianza"]),
                )
                continue
        entidades.append(e)
    for e in entidades:
        validar_span(texto, e)
    return entidades, uniones


def procesar_pasaje(texto, passage_id, parametros, directorio: Path, proveedor, forzar=False):
    """No carga pesos en aciertos. Posproceso siempre desde predicciones crudas."""
    if not re.fullmatch(r"[\w-]+", passage_id):
        raise ValueError("Identificador inseguro para caché")
    clave = clave_cache(texto, parametros)
    ruta = directorio / f"{parametros['slug']}@{parametros['revision'][:12]}" / f"{passage_id}.json"
    datos = json.loads(ruta.read_text()) if ruta.exists() else None
    acierto = bool(datos and datos["clave"] == clave and not forzar)
    if not acierto:
        inicio = time.perf_counter()
        predictor = proveedor()
        crudas, descartadas = inferir_crudo(texto, predictor, parametros)
        import transformers

        datos = {
            "clave": clave,
            "parametros": parametros,
            "texto_sha256": hashlib.sha256(texto.encode()).hexdigest(),
            "crudas": crudas,
            "descartadas": descartadas,
            "segundos": time.perf_counter() - inicio,
            "version_transformers": transformers.__version__,
        }
        ruta.parent.mkdir(parents=True, exist_ok=True)
        atomico(ruta, (json.dumps(datos, ensure_ascii=False, indent=2) + "\n").encode())
    entidades, uniones = posprocesar(texto, datos["crudas"], passage_id)
    return entidades, uniones, datos, acierto
