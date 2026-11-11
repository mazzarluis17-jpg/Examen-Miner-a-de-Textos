"""Contratos de entrega de H9. Valida sin escribir datos humanos ni resultados históricos."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pypdf import PdfReader

from mtx import adaptadores_kit, corpus, gold
from mtx.app import valoraciones
from mtx.entrega import RAIZ, sha

ESQUEMAS = {
    "ranking.csv": "query_id,modelo,variante,rango,passage_id,doc_id,fecha,posicion,puntaje",
    "juicios_relevancia.csv": "query_id,doc_id,passage_id,relevante",
    "resultados_ir.csv": ("query_id,modelo,P@5,P@10,AP,relevantes_recuperados,"
                           "relevantes_en_pool,no_juzgados"),
    "entidades.csv": "query_id,doc_id,passage_id,tipo,texto,inicio,fin,metodo",
    "gold_entidades.csv": "passage_id,tipo,texto,inicio,fin",
    "resultados_ie.csv": "metodo,tipo,precision,recall,f1,tp,predichas,gold",
}
CLAVES = {
    "ranking.csv": ["query_id", "modelo", "rango"],
    "juicios_relevancia.csv": ["query_id", "passage_id"],
    "resultados_ir.csv": ["query_id", "modelo"],
    "entidades.csv": ["query_id", "passage_id", "tipo", "inicio", "fin"],
    "gold_entidades.csv": ["passage_id", "tipo", "inicio", "fin"],
    "resultados_ie.csv": ["metodo", "tipo"],
}


def validar_csv(ruta: Path, nombre: str):
    """Esquema exacto, UTF-8 sin BOM, claves y dominios oficiales."""
    if ruta.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"BOM no permitido: {nombre}")
    df = pd.read_csv(ruta, keep_default_na=False)
    if list(df.columns) != ESQUEMAS[nombre].split(","):
        raise ValueError(f"Columnas incorrectas: {nombre}")
    if df.duplicated(CLAVES[nombre]).any():
        raise ValueError(f"Clave duplicada: {nombre}")
    tipos = {"PER", "ORG", "LOC", "FECHA", "MONTO"}
    if nombre == "resultados_ie.csv":
        tipos.add("TODOS")
    if "tipo" in df and not set(df.tipo) <= tipos:
        raise ValueError(f"Tipo desconocido: {nombre}")
    if nombre == "entidades.csv" and not set(df.metodo) <= {"regla", "modelo", "ambos"}:
        raise ValueError("Método de extracción desconocido")
    if "relevante" in df and not set(df.relevante) <= {0, 1}:
        raise ValueError("Etiqueta de relevancia inválida")
    return df


def verificar(raiz=RAIZ):
    """Retorna resultados comprobados y pendientes humanos explícitos."""
    raiz = Path(raiz)
    problemas_kit = adaptadores_kit.verificar_hashes(raiz / "kit", raiz / "docs/contratos_kit.md")
    if problemas_kit:
        raise ValueError("; ".join(problemas_kit))
    originales = pd.read_csv(raiz / "kit/consultas.csv").head(8)
    propias = pd.read_csv(raiz / "data/consultas.csv").head(8)
    pd.testing.assert_frame_equal(originales, propias[list(originales.columns)])
    tablas = {n: validar_csv(raiz / n, n) for n in ESQUEMAS}
    for nombre in ESQUEMAS:
        subdir = "anotaciones" if nombre in {"gold_entidades.csv", "juicios_relevancia.csv"} else "salida"
        if (raiz / nombre).read_bytes() != (raiz / subdir / nombre).read_bytes():
            raise ValueError(f"Exportación distinta de su fuente oficial: {nombre}")
    pasajes = pd.read_parquet(raiz / "data/pasajes.parquet")
    textos = pasajes.set_index("passage_id").texto.to_dict()
    for nombre in ("entidades.csv", "gold_entidades.csv"):
        for e in tablas[nombre].itertuples():
            if (e.passage_id not in textos or not 0 <= e.inicio < e.fin <= len(textos[e.passage_id])
                    or textos[e.passage_id][e.inicio:e.fin] != e.texto):
                raise ValueError(f"Offset inválido: {nombre}, {e.passage_id}")
    ranking = tablas["ranking.csv"]
    consultas = pd.read_csv(raiz / "data/consultas.csv").set_index("query_id")
    modelos = {"bm25_con_filtro", "bm25_sin_filtro", "tfidf_con_filtro", "tfidf_sin_filtro"}
    if set(ranking.modelo) != modelos or set(ranking.query_id) != set(consultas.index):
        raise ValueError("Modelos o consultas de ranking incorrectos")
    if len(ranking) != 400 or ranking.groupby(["query_id", "modelo"]).ngroups != 40:
        raise ValueError("Cobertura de ranking incorrecta")
    if not np.isfinite(ranking.puntaje).all() or ranking.duplicated(
            ["query_id", "modelo", "passage_id"]).any():
        raise ValueError("Puntajes o IDs de ranking inválidos")
    p = pasajes.set_index("passage_id")
    for (_, _), grupo in ranking.groupby(["query_id", "modelo"]):
        if sorted(grupo.rango) != list(range(1, 11)):
            raise ValueError("Rangos no consecutivos")
    for r in ranking.itertuples():
        if (r.passage_id not in textos or str(r.doc_id) != str(p.loc[r.passage_id, "doc_id"])
                or str(r.posicion) != str(p.loc[r.passage_id, "posicion"])
                or str(r.fecha) != str(p.loc[r.passage_id, "fecha"])[:10]):
            raise ValueError(f"Ranking incompatible con corpus: {r.passage_id}")
        if r.variante != r.modelo.split("_", 1)[1]:
            raise ValueError("Variante incoherente con modelo")
        if r.modelo.endswith("_con_filtro"):
            q = consultas.loc[r.query_id]
            if not q.desde <= r.fecha <= q.hasta:
                raise ValueError("Fecha fuera de ventana")
    pool = pd.read_csv(raiz / "salida/04_pool.csv")
    juicios = tablas["juicios_relevancia.csv"]
    if set(zip(pool.query_id, pool.passage_id)) != set(zip(juicios.query_id, juicios.passage_id)):
        raise ValueError("Cobertura del pool incompleta")
    for manifiesto in ("05_manifiesto_ir.json", "08_manifiesto_extraccion.json"):
        fuentes = json.loads((raiz / "salida" / manifiesto).read_text())["entradas"]
        for ruta, esperado in fuentes.items():
            if sha(raiz / ruta) != esperado:
                raise ValueError(f"Fuente congelada alterada: {ruta}")
    ctx = gold.cargar_contexto(raiz)
    estado = gold.leer(ctx)
    errores = gold.validar_gold(ctx["muestras"]["Evaluación"], estado["tablas"]["Evaluación"],
                               estado["tablas"]["estados"], ctx["pasajes"], ctx["ranking"])
    if errores:
        raise ValueError("; ".join(errores))
    cierre = json.loads((raiz / "anotaciones/cierre_gold.json").read_text())
    if cierre["archivos"] != estado["archivos"] or cierre["revision"] != estado["revision"]:
        raise ValueError("Cierre Gold obsoleto")
    vctx = valoraciones.cargar_contexto(raiz)
    valoradas = valoraciones.completadas(vctx, valoraciones.leer(vctx))
    if len(valoradas) != 10:
        raise ValueError("Faltan valoraciones humanas")
    # El kit se ejecuta sobre una carpeta temporal, sin sobrescribir cifras oficiales.
    with tempfile.TemporaryDirectory(prefix="mtx-validacion-") as tmp:
        for modo, referencia, prediccion, resultado in (
            ("ir", "juicios_relevancia.csv", "ranking.csv", "resultados_ir.csv"),
            ("ie", "gold_entidades.csv", "entidades.csv", "resultados_ie.csv"),
        ):
            salida = Path(tmp) / modo
            salida.mkdir()
            ruta = adaptadores_kit.ejecutar_evaluador(modo, raiz / referencia,
                                                     raiz / prediccion, salida)
            if Path(ruta).read_bytes() != (raiz / resultado).read_bytes():
                raise ValueError(f"Evaluación oficial distinta: {modo}")
    corpus_meta = json.loads((raiz / "data/corpus_meta.json").read_text())
    if sha(raiz / "kit/data/discursos.parquet") != corpus_meta["sha256_parquet"]:
        raise ValueError("Snapshot incompatible")
    historico = json.loads((raiz / "salida/01_limpieza.json").read_text())
    if corpus.hash_pasajes(pasajes) != historico["hash_pasajes"]:
        raise ValueError("Hash canónico de pasajes distinto")
    readme = (raiz / "README.md").read_text()
    if any(f"## {n}. " not in readme for n in range(1, 11)) or "Uso de IA" not in readme:
        raise ValueError("README incompleto")
    with tempfile.TemporaryDirectory(prefix="mtx-lock-") as tmp:
        salida_uv = subprocess.run(
            ["uv", "export", "--locked", "--offline", "--cache-dir", tmp,
             "--no-dev", "--format", "requirements-txt"], cwd=raiz,
            capture_output=True, text=True, check=True).stdout
        contenido = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("#"))
        if contenido(salida_uv) != contenido((raiz / "requirements.txt").read_text()):
            raise ValueError("requirements.txt distinto de uv.lock")
    paginas = len(PdfReader(raiz / "reporte/reporte.pdf").pages)
    diapositivas = len(Presentation(raiz / "laminas/laminas.pptx").slides)
    if not 4 <= paginas <= 6 or not 1 <= diapositivas <= 5:
        raise ValueError("Límites del examen incumplidos")
    prueba_clon = raiz / "salida/11_reproducibilidad_clon.json"
    reproducido = False
    if prueba_clon.exists():
        prueba = json.loads(prueba_clon.read_text())
        reproducido = (prueba.get("codigo_salida") == 0 and prueba.get("csv_distintos") == []
                       and len(prueba.get("hashes_csv", {})) >= 6
                       and all(sha(raiz / r) == h for r, h in prueba["hashes_csv"].items()))
    pendientes = ["Tres cortes de aprobación humana del reporte",
                 "Aprobación de láminas y guion; ensayo humano medido ≤8 minutos",
                 "Destino GitHub y acceso del profesor; publicación no autorizada",
                 "Etiqueta v1.0-entrega después de todos los cierres"]
    if not reproducido:
        pendientes.append("Reconstrucción completa desde clon sin entorno ni cachés")
    condiciones = {
        "1_kit_consultas": "verificado",
        "2_seis_csv": "verificado",
        "3_ranking": "verificado",
        "4_juicios": "verificado",
        "5_ir_oficial": "verificado",
        "6_entidades": "verificado",
        "7_gold_cerrado": "verificado",
        "8_ie_oficial_complementaria": "verificado",
        "9_respuestas_valoraciones": "verificado",
        "10_snapshot": "verificado",
        "11_reporte": "pendiente: primer corte sin prosa aprobada",
        "12_laminas_guion": "pendiente: aprobación y ensayo humano",
        "13_pruebas_clon": "verificado" if reproducido else "pendiente: reproducción desde cero",
        "14_readme_dependencias": "verificado",
        "15_publicacion": "pendiente: destino, acceso y etiqueta final",
    }
    return {"condiciones": condiciones, "csv": {n: {"filas": len(t), "sha256": sha(raiz / n)}
                    for n, t in tablas.items()},
            "paginas": paginas, "diapositivas": diapositivas,
            "valoraciones": len(valoradas), "gold": len(tablas["gold_entidades.csv"]),
            "evaluadores_oficiales": "idénticos byte a byte",
            "hash_pasajes": historico["hash_pasajes"],
            "pendiente": pendientes}
