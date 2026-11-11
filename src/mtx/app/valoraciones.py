"""Persistencia de opiniones humanas H8: hashes, revisiones, cerrojo y respaldos."""

import fcntl
import json
import subprocess
import sys
from datetime import UTC, datetime

import pandas as pd
import yaml

from mtx.app.componentes import ErrorAnotacion, atomico, gold_cerrado, sha256
from mtx.respuestas import hash_tabla, validar_valoraciones


class YAMLHumano(yaml.SafeLoader):
    """No descarta silenciosamente entradas humanas con claves duplicadas."""


def _mapa(loader, node):
    resultado = {}
    for clave, valor in node.value:
        k = loader.construct_object(clave)
        if k in resultado:
            raise ErrorAnotacion("Claves YAML duplicadas; conservar y revisar el archivo")
        resultado[k] = loader.construct_object(valor)
    return resultado


YAMLHumano.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapa)


def cargar_contexto(raiz):
    """No carga modelos; solo abre predicciones derivadas tras comprobar cierre Gold."""
    if not gold_cerrado(raiz):
        raise ErrorAnotacion("Falta cierre Gold: no se muestran respuestas del sistema")
    sello = json.loads((raiz / "anotaciones/cierre_gold.json").read_text())
    if not sello.get("anotado_por") or not sello.get("fecha"):
        raise ErrorAnotacion("Cierre Gold inválido")
    control = json.loads((raiz / "anotaciones/gold_revision.json").read_text())
    if (
        sello["revision"] != control["revision"]
        or sello["archivos"] != control["archivos"]
        or sello["fuentes"] != control["fuentes"]
    ):
        raise ErrorAnotacion("Cierre Gold incompatible con su revisión")
    rutas = {**sello["fuentes"]}
    for k, nombre in [("Evaluación", "gold_entidades.csv"), ("estados", "estado_gold.csv")]:
        rutas[f"anotaciones/{nombre}"] = sello["archivos"][k]
    manifiesto = json.loads((raiz / "salida/10_manifiesto_respuestas.json").read_text())
    for p, h in [*manifiesto["entradas"].items(), *manifiesto["salidas"].items()]:
        if p == "anotaciones/valoraciones.yaml":
            continue  # Es el insumo humano editable; cada entrada tiene su propio hash de tabla.
        if p in rutas and rutas[p] != h:
            raise ErrorAnotacion("Manifiestos incompatibles: " + p)
        rutas[p] = h
    for p, h in rutas.items():
        if sha256((raiz / p).read_bytes()) != h:
            raise ErrorAnotacion("Evidencia obsoleta: " + p)
    consultas = pd.read_csv(raiz / "data/consultas.csv", dtype=str, keep_default_na=False)
    hashes = json.loads((raiz / "salida/10_hashes_tablas.json").read_text())
    if (
        len(consultas) != 10
        or consultas.query_id.nunique() != 10
        or set(hashes) != set(consultas.query_id)
    ):
        raise ErrorAnotacion("Se requieren exactamente diez consultas y tablas")
    tablas = {}
    for q, h in hashes.items():
        texto = (raiz / f"salida/tablas_respuesta/{q}.md").read_text()
        if hash_tabla(texto) != h:
            raise ErrorAnotacion("Tabla modificada: " + q)
        tablas[q] = texto.split("\nvaloracion:\n", 1)[0]
    for p in [
        "salida/10_hashes_tablas.json",
        "salida/10_manifiesto_respuestas.json",
        "anotaciones/cierre_gold.json",
        "anotaciones/gold_revision.json",
    ]:
        rutas[p] = sha256((raiz / p).read_bytes())
    respuestas = pd.read_csv(raiz / "salida/respuestas.csv", dtype=str, keep_default_na=False)
    return {
        "raiz": raiz,
        "consultas": consultas,
        "hashes": hashes,
        "tablas": tablas,
        "respuestas": respuestas,
        "fuentes": rutas,
    }


def comprobar_fuentes(ctx):
    for p, h in ctx["fuentes"].items():
        if not (ctx["raiz"] / p).exists() or sha256((ctx["raiz"] / p).read_bytes()) != h:
            raise ErrorAnotacion("Tablas o evidencias cambiaron: recarga antes de valorar")


def _leer(ctx):
    raiz = ctx["raiz"]
    ruta = raiz / "anotaciones/valoraciones.yaml"
    datos = ruta.read_bytes() if ruta.exists() else b""
    try:
        valores = yaml.load(datos, Loader=YAMLHumano) or {}
    except yaml.YAMLError as exc:
        raise ErrorAnotacion("YAML humano inválido; no se sobrescribe") from exc
    if not isinstance(valores, dict) or set(valores) - set(ctx["hashes"]):
        raise ErrorAnotacion("Consultas desconocidas en valoraciones; conservar archivo")
    if any(
        not isinstance(v, dict) or not isinstance(v.get("valoracion"), str)
        for v in valores.values()
    ):
        raise ErrorAnotacion("Esquema humano inválido: usar tabla_sha256 y valoracion")
    control = raiz / "anotaciones/valoraciones_estado.json"
    registro = (
        json.loads(control.read_text())
        if control.exists()
        else {"revision": 0, "sha256_yaml": sha256(datos)}
    )
    if not isinstance(registro.get("revision"), int) or registro["revision"] < 0:
        raise ErrorAnotacion("Revisión de valoraciones inválida")
    if registro.get("sha256_yaml") != sha256(datos):
        raise ErrorAnotacion(
            "Guardado interrumpido o edición externa: revisar respaldos sin sobrescribir"
        )
    return {"revision": registro["revision"], "sha256": sha256(datos), "valoraciones": valores}


def leer(ctx):
    lock = ctx["raiz"] / "anotaciones/.valoraciones.lock"
    if not lock.exists():
        return _leer(ctx)
    with lock.open("rb") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        return _leer(ctx)


def completadas(ctx, estado):
    return [
        q
        for q, h in ctx["hashes"].items()
        if not validar_valoraciones({q: estado["valoraciones"].get(q, {})}, {q: h})
    ]


def _respaldar(raiz, revision):
    historial = raiz / "anotaciones/historial_valoraciones"
    historial.mkdir(exist_ok=True)
    for nombre in ["valoraciones.yaml", "valoraciones_estado.json"]:
        ruta = raiz / "anotaciones" / nombre
        if ruta.exists():
            respaldo = historial / f"{revision}_{nombre}"
            if respaldo.exists() and respaldo.read_bytes() != ruta.read_bytes():
                raise ErrorAnotacion("Existe respaldo diferente; conservar y revisar")
            if not respaldo.exists():
                atomico(respaldo, ruta.read_bytes())


def guardar(ctx, observado, query_id, texto):
    """El único contenido nuevo es el texto suministrado explícitamente por el usuario."""
    if query_id not in ctx["hashes"] or not isinstance(texto, str):
        raise ErrorAnotacion("Consulta o texto inválidos")
    entrada = {"tabla_sha256": ctx["hashes"][query_id], "valoracion": texto}
    if validar_valoraciones({query_id: entrada}, {query_id: ctx["hashes"][query_id]}):
        raise ErrorAnotacion("Escribe tu valoración personal antes de guardar")
    raiz = ctx["raiz"]
    with (raiz / "anotaciones/.valoraciones.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        comprobar_fuentes(ctx)
        actual = _leer(ctx)
        if (actual["revision"], actual["sha256"]) != (observado["revision"], observado["sha256"]):
            raise ErrorAnotacion("Editado desde otra pestaña: recarga antes de guardar")
        valores = dict(actual["valoraciones"])
        valores[query_id] = {**valores.get(query_id, {}), **entrada}
        datos = yaml.safe_dump(valores, allow_unicode=True, sort_keys=False).encode()
        _respaldar(raiz, actual["revision"])
        registro = {
            "revision": actual["revision"] + 1,
            "sha256_yaml": sha256(datos),
            "query_id": query_id,
            "tabla_sha256": entrada["tabla_sha256"],
            "accion": "guardado explícito de texto suministrado por usuario",
            "fecha": datetime.now(UTC).isoformat(),
        }
        # Diario previo: una interrupción bloquea y conserva la versión respaldada.
        atomico(
            raiz / "anotaciones/valoraciones_estado.json",
            (json.dumps(registro, ensure_ascii=False, indent=2) + "\n").encode(),
        )
        atomico(raiz / "anotaciones/valoraciones.yaml", datos)
        return _leer(ctx)


def finalizar(ctx, observado):
    """Validación técnica de H8 tras diez opiniones humanas, sin ejecutar H9 ni Git."""
    raiz = ctx["raiz"]
    with (raiz / "anotaciones/.valoraciones.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        comprobar_fuentes(ctx)
        actual = _leer(ctx)
        if (actual["revision"], actual["sha256"]) != (observado["revision"], observado["sha256"]):
            raise ErrorAnotacion("Otra sesión modificó valoraciones: recarga")
        errores = validar_valoraciones(actual["valoraciones"], ctx["hashes"])
        if errores:
            raise ErrorAnotacion("; ".join(errores))
        _respaldar(raiz, actual["revision"])
        proceso = subprocess.run(
            [sys.executable, str(raiz / "scripts/10_tablas.py"), "--exigir-valoraciones"],
            cwd=raiz,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if proceso.returncode:
            raise ErrorAnotacion("Validación H8 incompleta: " + proceso.stderr[-1500:])
        for q, tabla in ctx["tablas"].items():
            if (raiz / f"salida/tablas_respuesta/{q}.md").read_text().split("\nvaloracion:\n", 1)[
                0
            ] != tabla:
                raise ErrorAnotacion("La evidencia de una tabla cambió; revisar antes de cerrar")
        for p, h in ctx["fuentes"].items():
            if p == "salida/10_manifiesto_respuestas.json" or p.startswith(
                "salida/tablas_respuesta/"
            ):
                continue  # Solo se incorpora el bloque humano; cuerpo comprobado arriba.
            if sha256((raiz / p).read_bytes()) != h:
                raise ErrorAnotacion("Entrada o respuesta cambió durante la validación")
        if _leer(ctx)["sha256"] != actual["sha256"]:
            raise ErrorAnotacion("El archivo humano cambió durante la validación")
        sello = {
            "naturaleza": "validación técnica; no opinión ni aprobación generada",
            "fecha": datetime.now(UTC).isoformat(),
            "revision": actual["revision"],
            "sha256_valoraciones": actual["sha256"],
            "tablas": ctx["hashes"],
            "consultas_valoradas": 10,
            "comando": proceso.args,
            "codigo_salida": 0,
        }
        ruta = raiz / "salida/10_cierre_h8.json"
        if ruta.exists():
            respaldo = (
                raiz
                / "anotaciones/historial_valoraciones"
                / f"cierre_{sha256(ruta.read_bytes())[:16]}.json"
            )
            if not respaldo.exists():
                atomico(respaldo, ruta.read_bytes())
        atomico(ruta, (json.dumps(sello, ensure_ascii=False, indent=2) + "\n").encode())
        return sello
