"""Contratos y edición humana del gold ciego; sin dependencias de extractores."""
from __future__ import annotations

import fcntl
import hashlib
import html
import json
import re
import subprocess
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

import pandas as pd

from mtx.ambito_ie import cargar_ambito
from mtx.app.componentes import ErrorAnotacion, atomico
from mtx.app.gazetteer import fuentes as fuentes_gazetteer
from mtx.muestreo import sortear_muestra

TIPOS = ("PER", "ORG", "LOC", "FECHA", "MONTO")
COLUMNAS = ["passage_id", "tipo", "texto", "inicio", "fin"]
ESTADOS = ["passage_id", "texto_sha256", "estado", "n_entidades", "revision"]
MUESTRA = ["query_id", "passage_id", "doc_id", "texto_sha256", "semilla", "version_muestra"]


def sha(datos):
    return hashlib.sha256(datos).hexdigest()


def verificar_d15(raiz):
    """No exige árbol limpio durante captura; sí insumos idénticos a la etiqueta."""
    tag = subprocess.run(["git", "rev-parse", "--verify", "reglas-congeladas^{commit}"],
                         cwd=raiz, capture_output=True, text=True, check=False)
    if tag.returncode:
        raise ErrorAnotacion("Pendiente congelación D15 y aprobaciones antes del gold")
    # H8 añade políticas de presentación, ajenas a los insumos congelados H5.
    # Se protegen TODOS los archivos config que existían en la etiqueta, incluidas
    # modificaciones y borrados, sin invalidar Gold por configuraciones posteriores.
    config_congelada = subprocess.check_output([
        "git", "ls-tree", "-r", "--name-only", "reglas-congeladas", "--", "config"
    ], cwd=raiz, text=True).splitlines()
    rutas = ["src/mtx/reglas.py", "src/mtx/normalizacion.py", "src/mtx/ner_modelo.py",
             *config_congelada, "data/modelo_ner.json", "data/mejor_modelo.json", "salida/06_revision_alcance.csv",
             "salida/06_revision_alcance.json", "salida/06_siglas_candidatas.csv"]
    if subprocess.run(["git", "diff", "--quiet", "reglas-congeladas", "--", *rutas], cwd=raiz, check=False).returncode:
        raise ErrorAnotacion("Insumos distintos de reglas-congeladas; no se escribe gold")
    historial = subprocess.check_output([
        "git", "log", "--reverse", "--format=%H", "--", "anotaciones/gold_entidades.csv",
        "anotaciones/estado_gold.csv", "anotaciones/muestra_gold.csv"], cwd=raiz, text=True).splitlines()
    if historial:
        primero = historial[0]
        if tag.stdout.strip() == primero or subprocess.run([
            "git", "merge-base", "--is-ancestor", tag.stdout.strip(), primero], cwd=raiz, check=False).returncode:
            raise ErrorAnotacion("La congelación debe preceder al primer commit gold")


def validar_spans(entidades, textos):
    """Offsets originales, tipos y duplicados; permite solapes parciales no anidados."""
    errores = []
    if list(entidades.columns) != COLUMNAS:
        return ["Columnas gold incorrectas"]
    vistos = set()
    spans = {}
    for fila in entidades.itertuples(index=False):
        try:
            a, b = int(fila.inicio), int(fila.fin)
            if str(fila.inicio) != str(a) or str(fila.fin) != str(b):
                raise ValueError
            texto = textos[fila.passage_id]
            assert fila.tipo in TIPOS and 0 <= a < b <= len(texto)
            assert bool(fila.texto) and texto[a:b] == fila.texto
        except (KeyError, ValueError, AssertionError, TypeError):
            errores.append(f"Span o tipo inválido: {fila.passage_id}")
            continue
        clave = (fila.passage_id, a, b)
        if clave in vistos:
            errores.append(f"Span duplicado o con dos tipos: {fila.passage_id}")
        vistos.add(clave)
        for x, y in spans.setdefault(fila.passage_id, []):
            if (a <= x and y <= b) or (x <= a and b <= y):
                errores.append(f"Entidades contenidas: {fila.passage_id}")
        spans[fila.passage_id].append((a, b))
    return errores


def validar_gold(muestra, entidades, estados, pasajes, ranking, total=20, exigir_cierre=True):
    """T10: la cobertura viene del manifiesto/estados, no de las filas con entidades."""
    errores = []
    if (list(muestra.columns) != MUESTRA or list(estados.columns) != ESTADOS or
            list(entidades.columns) != COLUMNAS):
        return ["Columnas de muestra o estados incorrectas"]
    if len(muestra) != total or muestra.passage_id.duplicated().any():
        errores.append("La muestra exige IDs únicos y el tamaño contractual")
    if total == 20 and (muestra.query_id.nunique() != 10 or
                        not muestra.groupby("query_id").size().eq(2).all()):
        errores.append("Se exigen dos pasajes por cada una de diez consultas")
    if total == 6 and muestra.query_id.nunique() != 6:
        errores.append("Selección exige seis consultas distintas")
    if not pd.to_numeric(muestra.semilla, errors="coerce").eq(42).all():
        errores.append("Semilla distinta de 42")
    if estados.passage_id.duplicated().any() or (exigir_cierre and
            set(estados.passage_id) != set(muestra.passage_id)):
        errores.append("Estados incompletos o duplicados")
    if exigir_cierre and not estados.estado.eq("cerrado").all():
        errores.append("Faltan pasajes revisados completos")
    p = pasajes.set_index("passage_id")
    textos = p.texto.to_dict()
    permitidos = set(zip(ranking.query_id, ranking.passage_id))
    for f in muestra.itertuples():
        if (f.passage_id not in textos or sha(textos[f.passage_id].encode()) != f.texto_sha256 or
                (f.query_id, f.passage_id) not in permitidos or
                str(p.loc[f.passage_id, "doc_id"]) != str(f.doc_id)):
            errores.append(f"Muestra obsoleta o fuera del ganador: {f.passage_id}")
    if not set(entidades.passage_id) <= set(muestra.passage_id):
        errores.append("Entidades fuera de la muestra")
    errores.extend(validar_spans(entidades, textos))
    for f in estados.itertuples():
        if (f.passage_id not in textos or f.texto_sha256 != sha(textos[f.passage_id].encode()) or
                str(f.n_entidades) != str(int(entidades.passage_id.eq(f.passage_id).sum()))):
            errores.append(f"Estado/hash/conteo incompatible: {f.passage_id}")
        if not str(f.revision).isdigit() or int(f.revision) < 1:
            errores.append(f"Revisión inválida: {f.passage_id}")
    return errores


def cargar_contexto(raiz: Path):
    """Solo lee manifiestos y texto; nunca abre predicciones ni caché NER."""
    verificar_d15(raiz)
    criterio = json.loads((raiz/"config/criterios_anotacion_aprobacion.json").read_text())
    if (not criterio.get("aprobado_por") or not criterio.get("fecha") or
            criterio.get("sha256_criterio") != sha((raiz/"config/criterios_anotacion.md").read_bytes())):
        raise ErrorAnotacion("Criterios IE sin aprobación vigente")
    gaz = json.loads((raiz/"config/gazetteer_aprobacion.json").read_text())
    if (gaz.get("fuentes") != fuentes_gazetteer(raiz) or not gaz.get("aprobado_por") or
            gaz.get("sha256_extendido") != sha((raiz/"config/gazetteer_extendido.csv").read_bytes())):
        raise ErrorAnotacion("Gazetteer sin aprobación vigente")
    ranking, pasajes = cargar_ambito(raiz)
    muestras = {"Evaluación": pd.read_csv(raiz/"anotaciones/muestra_gold.csv", dtype=str,
                                         keep_default_na=False)}
    esperado = sortear_muestra(ranking, pasajes).to_csv(index=False, lineterminator="\n").encode()
    if sha((raiz/"anotaciones/muestra_gold.csv").read_bytes()) != sha(esperado):
        raise ErrorAnotacion("Muestra distinta del sorteo reproducible; conservar y revisar")
    seleccion = raiz/"anotaciones/muestra_seleccion.csv"
    if seleccion.exists():
        muestras["Selección"] = pd.read_csv(seleccion, dtype=str, keep_default_na=False)
        if set(muestras["Evaluación"].passage_id) & set(muestras["Selección"].passage_id):
            raise ErrorAnotacion("Muestras de evaluación y selección no disjuntas")
    # Valida manifiesto sin exigir decisiones humanas todavía.
    for nombre, muestra in muestras.items():
        errores = validar_gold(muestra, pd.DataFrame(columns=COLUMNAS), pd.DataFrame(columns=ESTADOS),
                               pasajes, ranking, 20 if nombre == "Evaluación" else 6,
                               exigir_cierre=False)
        if errores:
            raise ErrorAnotacion("; ".join(errores))
    rutas = ["config/criterios_anotacion.md", "config/criterios_anotacion_aprobacion.json",
             "config/protocolo.txt", "config/gazetteer_aprobacion.json", "config/gazetteer_extendido.csv",
             "data/modelo_ner.json", "data/mejor_modelo.json", "data/pasajes.parquet",
             "salida/ranking.csv", "anotaciones/muestra_gold.csv"]
    if seleccion.exists():
        rutas.append("anotaciones/muestra_seleccion.csv")
    return {"raiz": raiz, "muestras": muestras, "pasajes": pasajes, "ranking": ranking,
            "fuentes": {p: sha((raiz/p).read_bytes()) for p in rutas}}


def comprobar_fuentes(ctx):
    verificar_d15(ctx["raiz"])
    if any(sha((ctx["raiz"]/p).read_bytes()) != h for p, h in ctx["fuentes"].items()):
        raise ErrorAnotacion("Gold obsoleto por cambio de insumos; conservar y revisar")


def archivos_gold(ctx):
    rutas = {"Evaluación": "gold_entidades.csv"}
    if "Selección" in ctx["muestras"]:
        rutas["Selección"] = "gold_seleccion.csv"
    return rutas


def _leer(ctx):
    raiz = ctx["raiz"]
    archivos = {**archivos_gold(ctx), "estados": "estado_gold.csv"}
    datos = {k: (raiz/"anotaciones"/p).read_bytes() if (raiz/"anotaciones"/p).exists() else b""
             for k, p in archivos.items()}
    if any(b.startswith(b"\xef\xbb\xbf") for b in datos.values()):
        raise ErrorAnotacion("Gold debe ser UTF-8 sin BOM")
    hashes = {k: sha(v) for k, v in datos.items()}
    registro = raiz/"anotaciones/gold_revision.json"
    revision = 0
    if registro.exists():
        control = json.loads(registro.read_text())
        if control["fuentes"] != ctx["fuentes"] or control["archivos"] != hashes:
            raise ErrorAnotacion("Guardado gold interrumpido/obsoleto: revisar respaldos sin sobrescribir")
        revision = control["revision"]
    tablas = {k: pd.read_csv(raiz/"anotaciones"/archivos[k], dtype=str, keep_default_na=False)
              if v else pd.DataFrame(columns=ESTADOS if k == "estados" else COLUMNAS)
              for k, v in datos.items()}
    textos = ctx["pasajes"].set_index("passage_id").texto.to_dict()
    for k in archivos_gold(ctx):
        errores = validar_spans(tablas[k], textos)
        if not set(tablas[k].passage_id) <= set(ctx["muestras"][k].passage_id):
            errores.append("Gold fuera de muestra")
        if errores:
            raise ErrorAnotacion("; ".join(errores))
    if list(tablas["estados"].columns) != ESTADOS or tablas["estados"].passage_id.duplicated().any():
        raise ErrorAnotacion("Estados gold inválidos")
    todos = {p for m in ctx["muestras"].values() for p in m.passage_id}
    for f in tablas["estados"].itertuples():
        n = sum(int(tablas[k].passage_id.eq(f.passage_id).sum()) for k in archivos_gold(ctx))
        if (f.passage_id not in todos or f.estado not in {"pendiente", "cerrado"} or
                f.texto_sha256 != sha(textos[f.passage_id].encode()) or str(n) != f.n_entidades):
            raise ErrorAnotacion("Estado gold obsoleto o incompatible")
    return {"revision": revision, "archivos": hashes, "tablas": tablas}


def leer(ctx):
    """No crea archivos al abrir; usa lectura compartida si existe cerrojo."""
    lock = ctx["raiz"]/"anotaciones/.gold.lock"
    if not lock.exists():
        return _leer(ctx)
    with lock.open("rb") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        return _leer(ctx)


def guardar(ctx, observado, conjunto, pid, filas, cerrar=False):
    """Persiste únicamente spans y cierre elegidos por el usuario."""
    comprobar_fuentes(ctx)
    raiz = ctx["raiz"]
    if (raiz/"anotaciones/cierre_gold.json").exists():
        raise ErrorAnotacion("Gold cerrado: correcciones exigen revisión explícita y nueva versión")
    if conjunto not in ctx["muestras"] or pid not in set(ctx["muestras"][conjunto].passage_id):
        raise ErrorAnotacion("Pasaje ajeno al manifiesto")
    if list(filas.columns) != COLUMNAS or not filas.passage_id.eq(pid).all():
        raise ErrorAnotacion("Edición contiene entidades de otro pasaje")
    errores = validar_spans(filas, ctx["pasajes"].set_index("passage_id").texto.to_dict())
    if errores:
        raise ErrorAnotacion("; ".join(errores))
    with (raiz/"anotaciones/.gold.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        comprobar_fuentes(ctx)
        actual = _leer(ctx)
        if (actual["revision"], actual["archivos"]) != (observado["revision"], observado["archivos"]):
            raise ErrorAnotacion("Editado desde otra pestaña: recarga antes de guardar")
        tablas = {k: v.copy() for k, v in actual["tablas"].items()}
        resto = tablas[conjunto][tablas[conjunto].passage_id.ne(pid)]
        tablas[conjunto] = pd.concat([resto, filas.astype(str)], ignore_index=True)
        estado = tablas["estados"][tablas["estados"].passage_id.ne(pid)]
        texto = ctx["pasajes"].set_index("passage_id").loc[pid, "texto"]
        registro = [pid, sha(texto.encode()), "cerrado" if cerrar else "pendiente",
                    str(len(filas)), str(actual["revision"] + 1)]
        tablas["estados"] = pd.concat([estado, pd.DataFrame([registro], columns=ESTADOS)], ignore_index=True)
        archivos = {**archivos_gold(ctx), "estados": "estado_gold.csv"}
        contenidos = {k: t.to_csv(index=False, lineterminator="\n").encode() for k, t in tablas.items()}
        historial = raiz/"anotaciones/historial_gold"
        historial.mkdir(exist_ok=True)
        for p in [*archivos.values(), "gold_revision.json"]:
            ruta = raiz/"anotaciones"/p
            if ruta.exists():
                respaldo = historial/f"{actual['revision']}_{p}"
                if respaldo.exists() and respaldo.read_bytes() != ruta.read_bytes():
                    raise ErrorAnotacion("Existe respaldo distinto; conservar y revisar")
                if not respaldo.exists():
                    atomico(respaldo, ruta.read_bytes())
        nuevo = {"revision": actual["revision"] + 1, "fuentes": ctx["fuentes"],
                 "archivos": {k: sha(v) for k, v in contenidos.items()}}
        atomico(raiz/"anotaciones/gold_revision.json", (json.dumps(nuevo, indent=2)+'\n').encode())
        for k, contenido in contenidos.items():
            atomico(raiz/"anotaciones"/archivos[k], contenido)
        return _leer(ctx)


def cerrar_gold(ctx, observado, persona):
    """Cierre humano global con validación y hashes, incluidos pasajes sin entidades."""
    comprobar_fuentes(ctx)
    raiz = ctx["raiz"]
    with (raiz/"anotaciones/.gold.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        comprobar_fuentes(ctx)
        actual = _leer(ctx)
        if actual["revision"] != observado["revision"] or actual["archivos"] != observado["archivos"]:
            raise ErrorAnotacion("Otra sesión cambió el gold: recarga")
        if not persona.strip():
            raise ErrorAnotacion("Indica el nombre de quien realizó la anotación")
        for conjunto, muestra in ctx["muestras"].items():
            estados = actual["tablas"]["estados"]
            estados = estados[estados.passage_id.isin(muestra.passage_id)]
            errores = validar_gold(muestra, actual["tablas"][conjunto], estados,
                ctx["pasajes"], ctx["ranking"], 20 if conjunto == "Evaluación" else 6)
            if errores:
                raise ErrorAnotacion("; ".join(errores))
        destino = raiz/"anotaciones/cierre_gold.json"
        if destino.exists():
            raise ErrorAnotacion("Existe cierre previo; no se sobrescribe")
        sello = {"anotado_por": persona.strip(), "fecha": datetime.now(UTC).isoformat(),
                 "revision": actual["revision"], "fuentes": ctx["fuentes"], "archivos": actual["archivos"]}
        contenido = (raiz/"anotaciones/gold_entidades.csv").read_bytes()
        exportacion = raiz/"gold_entidades.csv"
        if exportacion.exists() and exportacion.read_bytes() != contenido:
            raise ErrorAnotacion("Existe exportación distinta; conservar y revisar")
        atomico(exportacion, contenido)
        atomico(destino, (json.dumps(sello, ensure_ascii=False, indent=2)+'\n').encode())


def ocurrencias(texto, buscado):
    """Todas las apariciones, sin escoger automáticamente la primera."""
    if not buscado:
        return []
    resultado, desde = [], 0
    while (pos := texto.find(buscado, desde)) >= 0:
        resultado.append((pos, pos + len(buscado)))
        desde = pos + 1
    return resultado


def tokens(texto):
    return [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", texto)]


def span_tokens(texto, primero, ultimo, recortar=True):
    ts = tokens(texto)
    if not 0 <= primero <= ultimo < len(ts):
        raise ErrorAnotacion("Selección de tokens invertida o fuera del texto")
    inicio, fin = ts[primero][0], ts[ultimo][1]
    if recortar:
        while fin > inicio and texto[fin-1] in '.,;:!?)"»':
            fin -= 1
    return inicio, fin


def renderizar(texto, entidades, inicio_cuerpo):
    """HTML por tramos originales; admite solapes parciales sin duplicar texto."""
    limites = sorted({0, len(texto), inicio_cuerpo, *[int(x) for x in entidades.inicio],
                      *[int(x) for x in entidades.fin]})
    salida = []
    for a, b in pairwise(limites):
        tramo = html.escape(texto[a:b])
        tipos = [f.tipo for f in entidades.itertuples() if int(f.inicio) <= a < int(f.fin)]
        if tipos:
            tramo = '<mark title="'+html.escape(', '.join(tipos))+'">'+tramo+'</mark>'
        if a < inicio_cuerpo:
            tramo = '<span style="color:#666;background:#eee">'+tramo+'</span>'
        salida.append(tramo)
    return '<div style="white-space:pre-wrap">'+''.join(salida)+'</div>'
