"""04 · Construye o verifica el pool técnico sin producir juicios humanos."""
from __future__ import annotations

import json

import pandas as pd

from mtx import adaptadores_kit, config, corpus, pool


def main() -> None:
    """Exige referencias históricas vigentes y genera solo salida/04_pool.csv."""
    if adaptadores_kit.verificar_hashes():
        raise SystemExit("El kit no coincide con sus hashes originales")
    meta = json.loads(config.CORPUS_META.read_text())
    ruta_corpus = config.RAIZ / "kit/data/discursos.parquet"
    if adaptadores_kit.sha256_archivo(ruta_corpus) != meta["sha256_parquet"]:
        raise SystemExit("El corpus no coincide con el snapshot histórico")
    pasajes = pd.read_parquet(config.PASAJES_PARQUET)
    referencia = json.loads((config.DIR_SALIDA / "01_limpieza.json").read_text())
    if corpus.hash_pasajes(pasajes) != referencia["hash_pasajes"]:
        raise SystemExit("Los pasajes no coinciden con la huella histórica")
    ranking = pd.read_csv(config.RAIZ / "ranking.csv", dtype={"passage_id": str})
    consultas = pd.read_csv(config.CONSULTAS_CSV, dtype=str)
    tabla, avisos = pool.construir(ranking, pasajes, consultas)
    fuentes = ["data/corpus_meta.json", "data/consultas.csv", "ranking.csv",
               "config/limpieza.yaml", "config/stopwords_es.txt", "config/stoplist_extra.txt",
               "src/mtx/corpus.py", "src/mtx/preproceso.py", "src/mtx/indice.py",
               "src/mtx/ranking.py", "src/mtx/pool.py", "scripts/04_pool.py"]
    criterio = config.DIR_CONFIG / "criterios_relevancia.md"
    if criterio.exists():
        fuentes.append("config/criterios_relevancia.md")
    manifiesto = {
        "semilla": config.SEMILLA, "hash_pasajes": referencia["hash_pasajes"],
        "sha256_corpus": meta["sha256_parquet"], "pares": len(tabla),
        "criterio_presente": criterio.exists(),
        "fuentes": {f: adaptadores_kit.sha256_archivo(config.RAIZ / f) for f in fuentes},
    }
    ruta_meta = config.DIR_SALIDA / "04_pool_meta.json"
    juicios = config.DIR_ANOTACIONES / "juicios_relevancia.csv"
    if juicios.exists() and (not ruta_meta.exists() or json.loads(
            ruta_meta.read_text()) != manifiesto):
        anterior = json.loads(ruta_meta.read_text()) if ruta_meta.exists() else {}
        diferencias = [k for k in set(anterior) | set(manifiesto)
                       if anterior.get(k) != manifiesto.get(k)]
        raise SystemExit(f"Fuentes del pool cambiadas con juicios: {sorted(diferencias)}. "
                         "Revisar hashes; no se sobrescribe nada.")
    cambio = pool.guardar(tabla, config.DIR_SALIDA / "04_pool.csv", juicios)
    contenido_meta = json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n"
    if not ruta_meta.exists() or ruta_meta.read_text() != contenido_meta:
        ruta_meta.write_text(contenido_meta, encoding="utf-8")
    print(f"Pool {'generado' if cambio else 'verificado sin cambios'}: {len(tabla)} pares")
    print(tabla.groupby("query_id", sort=False).size().to_string())
    for aviso in avisos:
        print("AVISO:", aviso)
    print("Antes del primer juicio: el alumno debe fijar y aprobar "
          "config/criterios_relevancia.md. Este pool técnico no constituye un cierre humano.")


if __name__ == "__main__":
    main()
