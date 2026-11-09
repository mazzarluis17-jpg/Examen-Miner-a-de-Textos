"""Contratos, resaltado y persistencia compartidos por las vistas de anotación."""
from __future__ import annotations

import fcntl
import hashlib
import html
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mtx import adaptadores_kit, corpus, pool, preproceso


class ErrorAnotacion(ValueError):
    """Estado incompatible: rechazar la escritura y conservar los datos."""


@dataclass
class Contexto:
    """Entradas verificadas; la vista solo recibe una proyección sin procedencia."""

    raiz: Path
    tabla: pd.DataFrame
    consultas: pd.DataFrame
    pasajes: pd.DataFrame
    huellas: dict[str, str]


@dataclass
class Estado:
    """CSV leído y versión observada por una sesión (comparación al guardar)."""

    juicios: pd.DataFrame
    revision: int
    sha256: str


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def huellas_actuales(raiz: Path, rutas) -> dict[str, str]:
    """Detecta cambios incluso si se conservan las fechas de los archivos."""
    return {r: adaptadores_kit.sha256_archivo(raiz / r) if (raiz / r).is_file() else "ausente"
            for r in rutas}


def cargar_contexto(raiz: Path) -> Contexto:
    """Verifica snapshot, pasajes, manifiesto y unión exacta, sin escribir nada."""
    try:
        if adaptadores_kit.verificar_hashes():
            raise ErrorAnotacion("El kit original cambió")
        meta = json.loads((raiz / "salida/04_pool_meta.json").read_text())
        rutas = set(meta["fuentes"]) | {
            "kit/data/discursos.parquet", "data/pasajes.parquet", "salida/01_limpieza.json",
            "salida/04_pool.csv", "salida/04_pool_meta.json", "data/consultas.csv",
            "config/criterios_relevancia.md", "config/criterios_relevancia_aprobacion.json"}
        huellas = huellas_actuales(raiz, sorted(rutas))
        if any(huellas[r] != h for r, h in meta["fuentes"].items()):
            raise ErrorAnotacion("Insumos del pool obsoletos; verificar con make pool")
        if huellas["kit/data/discursos.parquet"] != meta["sha256_corpus"]:
            raise ErrorAnotacion("Snapshot del corpus obsoleto")
        pasajes = pd.read_parquet(raiz / "data/pasajes.parquet")
        referencia = json.loads((raiz / "salida/01_limpieza.json").read_text())
        if corpus.hash_pasajes(pasajes) != referencia["hash_pasajes"]:
            raise ErrorAnotacion("Pasajes obsoletos; se conservan los juicios existentes")
        consultas = pd.read_csv(raiz / "data/consultas.csv", dtype=str, keep_default_na=False)
        ranking = pd.read_csv(raiz / "ranking.csv", dtype={"passage_id": str})
        reconstruido, _ = pool.construir(ranking, pasajes, consultas)
        if pool.serializar(reconstruido) != (raiz / "salida/04_pool.csv").read_bytes():
            raise ErrorAnotacion("El pool no coincide con sus insumos")
        return Contexto(raiz, reconstruido, consultas, pasajes, huellas)
    except (OSError, KeyError, ValueError) as exc:
        if isinstance(exc, ErrorAnotacion):
            raise
        raise ErrorAnotacion("Faltan insumos o hay contratos inválidos; ejecutar make pool") from exc


def comprobar_vigencia(ctx: Contexto) -> None:
    if huellas_actuales(ctx.raiz, ctx.huellas) != ctx.huellas:
        raise ErrorAnotacion("Insumos obsoletos: recarga la aplicación; no se guarda nada")


def criterio_aprobado(ctx: Contexto) -> bool:
    """Solo acepta constancia explícita ligada al hash del texto aprobado."""
    try:
        aprobacion = json.loads((ctx.raiz / "config/criterios_relevancia_aprobacion.json").read_text())
        return (aprobacion.get("sha256_criterio") ==
                ctx.huellas["config/criterios_relevancia.md"] and
                bool(aprobacion.get("aprobado_por")) and bool(aprobacion.get("fecha")) and
                json.loads((ctx.raiz / "salida/04_pool_meta.json").read_text())["fuentes"].get(
                    "config/criterios_relevancia.md") == aprobacion["sha256_criterio"])
    except (OSError, ValueError, KeyError):
        return False


def validar_parcial(juicios: pd.DataFrame, ctx: Contexto) -> None:
    """Admite pendientes, nunca IDs ajenos, duplicados ni etiquetas inválidas."""
    if list(juicios.columns) != pool.COLUMNAS_JUICIOS:
        raise ErrorAnotacion("Columnas de juicios incorrectas")
    if juicios.duplicated(["query_id", "passage_id"]).any():
        raise ErrorAnotacion("Juicios duplicados")
    referencia = ctx.tabla.set_index(["query_id", "passage_id"])
    for fila in juicios.itertuples():
        clave = (fila.query_id, fila.passage_id)
        if clave not in referencia.index or str(fila.doc_id) != str(referencia.loc[clave, "doc_id"]):
            raise ErrorAnotacion("Identificadores de juicios ajenos al pool")
        if str(fila.relevante) not in ("", "0", "1"):
            raise ErrorAnotacion("Relevancia inválida; no se modifica el archivo")


def _rutas(ctx: Contexto):
    directorio = ctx.raiz / "anotaciones"
    return (directorio / "juicios_relevancia.csv", directorio / "juicios_relevancia_estado.json")


def _leer(ctx: Contexto) -> Estado:
    ruta, control = _rutas(ctx)
    datos = ruta.read_bytes() if ruta.exists() else b""
    if datos.startswith(b"\xef\xbb\xbf"):
        raise ErrorAnotacion("Los juicios deben ser UTF-8 sin BOM")
    digest = sha256(datos)
    revision = 0
    if control.exists():
        registro = json.loads(control.read_text())
        if registro["fuentes"] != ctx.huellas:
            raise ErrorAnotacion("Juicios obsoletos: cambiaron los insumos; no se alteran")
        if digest == registro["sha256"]:
            revision = registro["revision"]
        elif digest == registro["anterior_sha256"]:
            revision = registro["anterior_revision"]
        else:
            raise ErrorAnotacion("CSV cambiado fuera de la sesión; recuperar respaldo o revisar")
    juicios = (pd.read_csv(ruta, dtype=str, keep_default_na=False) if datos
               else pd.DataFrame(columns=pool.COLUMNAS_JUICIOS))
    validar_parcial(juicios, ctx)
    return Estado(juicios, revision, digest)


def leer_estado(ctx: Contexto) -> Estado:
    """No crea anotaciones al arrancar. Bloqueo compartido si hay escritura previa."""
    bloqueo = ctx.raiz / "anotaciones/.juicios.lock"
    if not bloqueo.exists():
        return _leer(ctx)
    with bloqueo.open("rb") as archivo:
        fcntl.flock(archivo, fcntl.LOCK_SH)
        return _leer(ctx)


def atomico(ruta: Path, datos: bytes) -> None:
    """Temporal en el mismo directorio, fsync y reemplazo indivisible."""
    fd, nombre = tempfile.mkstemp(prefix="." + ruta.name, dir=ruta.parent)
    try:
        with os.fdopen(fd, "wb") as archivo:
            archivo.write(datos)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(nombre, ruta)
        directorio = os.open(ruta.parent, os.O_RDONLY)
        try:
            os.fsync(directorio)
        finally:
            os.close(directorio)
    finally:
        if os.path.exists(nombre):
            os.unlink(nombre)


def guardar_accion(ctx: Contexto, estado: Estado, query_id: str, passage_id: str,
                   valor: str | None) -> Estado:
    """Solo escribe por acción humana; None guarda navegación sin alterar etiquetas."""
    comprobar_vigencia(ctx)
    if not criterio_aprobado(ctx):
        raise ErrorAnotacion("Criterio pendiente de aprobación explícita")
    if valor not in (None, "", "0", "1"):
        raise ErrorAnotacion("Acción inválida")
    referencia = ctx.tabla.set_index(["query_id", "passage_id"])
    if (query_id, passage_id) not in referencia.index:
        raise ErrorAnotacion("Pasaje ajeno al pool")
    ruta, control = _rutas(ctx)
    ruta.parent.mkdir(exist_ok=True)
    with (ruta.parent / ".juicios.lock").open("a+b") as bloqueo:
        fcntl.flock(bloqueo, fcntl.LOCK_EX)
        comprobar_vigencia(ctx)
        actual = _leer(ctx)
        if (actual.revision, actual.sha256) != (estado.revision, estado.sha256):
            raise ErrorAnotacion("Editado desde otra pestaña: recarga antes de guardar")
        nuevos = actual.juicios.copy()
        mascara = nuevos.query_id.eq(query_id) & nuevos.passage_id.eq(passage_id)
        if valor == "" and mascara.any() and nuevos.loc[mascara, "relevante"].ne("").any():
            raise ErrorAnotacion("Omitir no borra un juicio existente; usa anterior para revisarlo")
        if valor is not None:
            if mascara.any():
                nuevos.loc[mascara, "relevante"] = valor
            else:
                nuevos.loc[len(nuevos)] = [query_id, str(referencia.loc[
                    (query_id, passage_id), "doc_id"]), passage_id, valor]
        validar_parcial(nuevos, ctx)
        contenido = nuevos.to_csv(index=False, lineterminator="\n").encode("utf-8")
        historia = ruta.parent / "historial_juicios"
        historia.mkdir(exist_ok=True)
        # Respaldo antes del intento: una interrupción conserva el CSV vigente.
        previo = ruta.read_bytes() if ruta.exists() else b""
        respaldo = historia / f"revision_{actual.revision}_{actual.sha256}.csv"
        if not respaldo.exists():
            atomico(respaldo, previo)
        registro = {"revision": actual.revision + 1, "sha256": sha256(contenido),
                    "anterior_revision": actual.revision, "anterior_sha256": actual.sha256,
                    "fuentes": ctx.huellas}
        # Diario preparado antes de reemplazar CSV: lector admite hash previo o nuevo.
        atomico(control, (json.dumps(registro, indent=2) + "\n").encode())
        atomico(ruta, contenido)
        return Estado(nuevos, registro["revision"], registro["sha256"])


def primer_pendiente(tabla: pd.DataFrame, juicios: pd.DataFrame) -> int:
    """Retoma el primer omitido o ausente en el orden reproducible del pool."""
    cerrados = set(map(tuple, juicios.loc[juicios.relevante.isin(["0", "1"]),
                                        ["query_id", "passage_id"]].values))
    return next((i for i, f in enumerate(tabla.itertuples())
                 if (f.query_id, f.passage_id) not in cerrados), 0)


def resaltar(texto: str, consulta: str) -> str:
    """Marca tokens por stem usando offsets originales y HTML escapado."""
    terminos = set(preproceso.tokenizar(consulta))
    spans = [(m.start(), m.end()) for m in preproceso.RE_TOKEN.finditer(texto)
             if terminos.intersection(preproceso.tokenizar(m.group()))]
    partes, fin = [], 0
    for inicio, hasta in spans:
        partes.extend([html.escape(texto[fin:inicio]),
                       "<mark>" + html.escape(texto[inicio:hasta]) + "</mark>"])
        fin = hasta
    partes.append(html.escape(texto[fin:]))
    return '<div style="white-space:pre-wrap">' + "".join(partes) + "</div>"


def gold_cerrado(raiz: Path) -> bool:
    """Las vistas H3 no leen predicciones, exista o no cierre del gold."""
    return (raiz / "anotaciones/cierre_gold.json").exists()


def cobertura(ctx: Contexto, estado: Estado):
    """Reutiliza el validador oficial del proyecto para el cierre, sin exportar."""
    juicios = estado.juicios.copy()
    juicios["doc_id"] = pd.to_numeric(juicios.doc_id, errors="coerce")
    juicios["relevante"] = pd.to_numeric(juicios.relevante, errors="coerce")
    return pool.validar_juicios(juicios, ctx.tabla, ctx.pasajes)
