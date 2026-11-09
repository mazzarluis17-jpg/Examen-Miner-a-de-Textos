"""Pool reproducible de cuatro variantes y validación de juicios (D06, D07)."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pandas as pd

from . import corpus

VARIANTES = ("tfidf_con_filtro", "bm25_con_filtro", "tfidf_sin_filtro", "bm25_sin_filtro")
COLUMNAS = ["query_id", "passage_id", "doc_id", "fecha", "en_ventana", "variantes",
            "mejor_rango_tfidf", "mejor_rango_bm25", "texto", "texto_sha256"]
COLUMNAS_JUICIOS = ["query_id", "doc_id", "passage_id", "relevante"]


def construir(ranking: pd.DataFrame, pasajes: pd.DataFrame, consultas: pd.DataFrame,
              semilla: int = 42) -> tuple[pd.DataFrame, list[str]]:
    """Une top-10 por consulta, valida referencias y baraja IDs con semilla fija."""
    if pasajes.passage_id.duplicated().any() or consultas.query_id.duplicated().any():
        raise ValueError("IDs duplicados en pasajes o consultas")
    if ranking.duplicated(["query_id", "modelo", "rango"]).any() or ranking.duplicated(
            ["query_id", "modelo", "passage_id"]).any():
        raise ValueError("Claves duplicadas en ranking")
    if set(ranking.query_id) != set(consultas.query_id):
        raise ValueError("Las consultas del ranking no coinciden")
    if set(ranking.modelo) != set(VARIANTES):
        raise ValueError("Se requieren las cuatro variantes oficiales")
    p = pasajes.set_index("passage_id")
    faltantes = set(ranking.passage_id) - set(p.index)
    if faltantes:
        raise ValueError(f"Pasajes ausentes: {sorted(faltantes)}")
    filas, avisos = [], []
    for q in consultas.itertuples(index=False):
        r = ranking[ranking.query_id == q.query_id]
        for modelo in VARIANTES:
            rangos = sorted(r.loc[r.modelo == modelo, "rango"].tolist())
            if not rangos or rangos != list(range(1, len(rangos) + 1)) or len(rangos) > 10:
                raise ValueError(f"Rangos inválidos: {q.query_id} {modelo}")
            if len(rangos) < 10:
                avisos.append(f"{q.query_id} {modelo}: solo {len(rangos)} resultados")
        ids = sorted(set(r.passage_id))
        random.Random(semilla).shuffle(ids)
        if not 15 <= len(ids) <= 40:
            avisos.append(f"{q.query_id}: pool de {len(ids)} pasajes; revisar rango esperado 15–40")
        desde, hasta = pd.Timestamp(q.desde), pd.Timestamp(q.hasta)
        if pd.isna(desde) or pd.isna(hasta) or desde > hasta:
            raise ValueError(f"Ventana inválida: {q.query_id}")
        for pid in ids:
            meta = p.loc[pid]
            origen = r[r.passage_id == pid]
            fecha = pd.Timestamp(meta.fecha)
            if not origen.doc_id.eq(meta.doc_id).all() or not origen.posicion.eq(
                    meta.posicion).all():
                raise ValueError(f"Metadatos incompatibles: {pid}")
            fechas = pd.to_datetime(origen.fecha)
            if not (fechas.eq(fecha) | (fechas.isna() & pd.isna(fecha))).all():
                raise ValueError(f"Fecha incompatible: {pid}")
            huella = corpus.sha256_texto(meta.texto)
            if huella != meta.texto_sha256:
                raise ValueError(f"Hash de texto incompatible: {pid}")
            rangos_modelo = []
            for modelo in ("tfidf", "bm25"):
                valores = origen.loc[origen.modelo.str.startswith(modelo + "_"), "rango"]
                rangos_modelo.append(int(valores.min()) if len(valores) else pd.NA)
            filas.append([q.query_id, pid, int(meta.doc_id),
                          "" if pd.isna(fecha) else fecha.strftime("%Y-%m-%d"),
                          bool(pd.notna(fecha) and desde <= fecha <= hasta),
                          "|".join(v for v in VARIANTES if v in set(origen.modelo)),
                          *rangos_modelo, meta.texto, huella])
    resultado = pd.DataFrame(filas, columns=COLUMNAS)
    for col in ("mejor_rango_tfidf", "mejor_rango_bm25"):
        resultado[col] = resultado[col].astype("Int64")
    return resultado, avisos


def serializar(tabla: pd.DataFrame) -> bytes:
    """CSV canónico UTF-8 sin BOM, con LF y columnas contractuales."""
    return tabla[COLUMNAS].to_csv(index=False, lineterminator="\n").encode("utf-8")


def guardar(tabla: pd.DataFrame, ruta: Path, juicios: Path) -> bool:
    """Conserva el pool idéntico; impide reemplazar uno cambiado si existen juicios."""
    contenido = serializar(tabla)
    if ruta.exists():
        anterior = ruta.read_bytes()
        if hashlib.sha256(anterior).digest() == hashlib.sha256(contenido).digest():
            return False
        if juicios.exists():
            viejo = pd.read_csv(ruta, keep_default_na=False)
            claves = ["query_id", "passage_id"]
            a = set(map(tuple, viejo[claves].values))
            b = set(map(tuple, tabla[claves].values))
            cambios = viejo.merge(tabla, on=claves, suffixes=("_antes", "_ahora"))
            diferentes = [tuple(row[k] for k in claves) for _, row in cambios.iterrows()
                          if any(str(row[c + "_antes"]) != str(row[c + "_ahora"])
                                 for c in COLUMNAS if c not in claves)]
            raise ValueError(f"Pool cambiado con juicios: añadidos={sorted(b-a)}, "
                             f"retirados={sorted(a-b)}, modificados={diferentes}; "
                             "también puede cambiar el orden. No se sobrescribe nada.")
    elif juicios.exists():
        raise ValueError("Hay juicios sin pool original; recuperar el pool antes de continuar")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".csv.tmp")
    temporal.write_bytes(contenido)
    temporal.replace(ruta)
    return True


def validar_juicios(juicios: pd.DataFrame, tabla: pd.DataFrame,
                   pasajes: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Valida sin escribir ni inferir relevancia. Devuelve errores y avisos."""
    errores, avisos = [], []
    if list(juicios.columns) != COLUMNAS_JUICIOS:
        return ["Columnas de juicios incorrectas"], []
    claves = ["query_id", "passage_id"]
    if juicios.duplicated(claves).any():
        errores.append("Juicios duplicados")
    esperadas = set(map(tuple, tabla[claves].values))
    recibidas = set(map(tuple, juicios[claves].values))
    if esperadas != recibidas:
        errores.append(f"Cobertura incompleta o ajena: faltan {sorted(esperadas-recibidas)}, "
                       f"sobran {sorted(recibidas-esperadas)}")
    if not juicios.relevante.isin([0, 1]).all():
        errores.append("Relevancia fuera de {0, 1} o pendiente")
    p = pasajes.set_index("passage_id")
    for fila in tabla.itertuples():
        if fila.passage_id not in p.index or corpus.sha256_texto(
                p.loc[fila.passage_id, "texto"]) != fila.texto_sha256:
            errores.append(f"Texto obsoleto: {fila.passage_id}")
    unidos = juicios.merge(tabla[claves + ["doc_id"]], on=claves, suffixes=("", "_pool"))
    if not unidos.doc_id.eq(unidos.doc_id_pool).all():
        errores.append("doc_id incompatible con el pool")
    if not errores:
        for q, grupo in juicios.groupby("query_id"):
            if not grupo.relevante.eq(1).any():
                avisos.append(f"{q}: cero relevantes; el kit devuelve AP=0; discutir en reporte")
    return errores, avisos
