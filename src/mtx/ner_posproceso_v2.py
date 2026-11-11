"""Corrección autorizada posterior a D15; la versión congelada queda intacta."""

import json
import string

from mtx.ner_modelo import clave_cache, posprocesar, procesar_pasaje, validar_span

VERSION = "2-vacios-auditados"
DESCARTES = ["passage_id", "tipo", "inicio_original", "fin_original", "texto_original",
             "motivo", "version_posproceso"]


def posprocesar_auditado(texto, crudas, passage_id=""):
    """Única diferencia: audita y omite spans vacíos después del recorte original."""
    puntuacion = set(string.punctuation.replace("$", "") + "«»“”¿¡")
    conservadas, descartes = [], []
    for entidad in crudas:
        validar_span(texto, entidad)
        a, b = entidad["inicio"], entidad["fin"]
        while a < b and (texto[a].isspace() or texto[a] in puntuacion):
            a += 1
        while b > a and (texto[b-1].isspace() or texto[b-1] in puntuacion):
            b -= 1
        if a >= b:
            descartes.append(dict(zip(DESCARTES, [passage_id, entidad["tipo"],
                entidad["inicio"], entidad["fin"], entidad["texto"],
                "span_vacio_tras_recorte", VERSION])))
        else:
            # Sin cambiar etiqueta, límites ni objetos de la caché original.
            conservadas.append(entidad)
    entidades, uniones = posprocesar(texto, conservadas, passage_id)
    return entidades, uniones, descartes


def procesar_pasaje_auditado(texto, passage_id, parametros, directorio, proveedor):
    """Reutiliza inferencia y caché congeladas; nunca sobrescribe cachés vigentes."""
    ruta = directorio / f"{parametros['slug']}@{parametros['revision'][:12]}" / f"{passage_id}.json"
    previo = json.loads(ruta.read_text()) if ruta.exists() else None
    acierto = bool(previo and previo["clave"] == clave_cache(texto, parametros))
    try:
        entidades, uniones, datos, acierto = procesar_pasaje(
            texto, passage_id, parametros, directorio, proveedor)
        return entidades, uniones, datos, acierto, []
    except ValueError as exc:
        if str(exc) != "Span vacío después del recorte":
            raise
        datos = json.loads(ruta.read_text())
        if datos["clave"] != clave_cache(texto, parametros):
            raise ValueError("Caché incompatible; no se adapta") from exc
        entidades, uniones, descartes = posprocesar_auditado(texto, datos["crudas"], passage_id)
        if not descartes:
            raise
        return entidades, uniones, datos, acierto, descartes
