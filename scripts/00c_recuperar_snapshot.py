"""Recupera el snapshot fijado y reconstruye solo datos ignorados; no cambia históricos."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from mtx import adaptadores_kit, config, corpus
from mtx.entrega import sha


def main():
    meta = json.loads(config.CORPUS_META.read_text())
    historico = json.loads((config.RAIZ / "salida/01_limpieza.json").read_text())
    destino_corpus = config.RAIZ / "kit/data/discursos.parquet"
    destino_pasajes = config.PASAJES_PARQUET
    with tempfile.TemporaryDirectory(prefix="mtx-snapshot-") as tmp:
        trabajo = Path(tmp)
        original = trabajo / "discursos.parquet"
        if destino_corpus.exists():
            shutil.copyfile(destino_corpus, original)
        else:
            ds = load_dataset(meta["dataset"], revision=meta["commit_dataset"], split="train",
                              cache_dir=str(trabajo / "cache"))
            df = ds.to_pandas()
            df = df.rename(columns={c: adaptadores_kit.cargar_modulo_corpus().RENOMBRES.get(c, c)
                                    for c in df.columns})
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            df = df.dropna(subset=["texto"]).reset_index(drop=True)
            df.insert(0, "doc_id", range(len(df)))
            df.to_parquet(original, index=False)
        if sha(original) != meta["sha256_parquet"]:
            raise ValueError("Snapshot distinto del histórico: no se instala ni cambia metadatos")
        df = pd.read_parquet(original)
        if len(df) != meta["filas"] or list(df.columns) != meta["columnas"]:
            raise ValueError("Esquema o conteo del snapshot incorrecto")
        if destino_pasajes.exists():
            pasajes = pd.read_parquet(destino_pasajes)
        else:
            limpio, _ = corpus.limpiar_ruido(df)
            pasajes = corpus.segmentar_con_descartes(limpio)[0]
        if (len(pasajes) != historico["pasajes"] or
                corpus.hash_pasajes(pasajes) != historico["hash_pasajes"]):
            raise ValueError("Pasajes incompatibles; ningún archivo oficial fue sustituido")
        reconstruido = trabajo / "pasajes.parquet"
        pasajes.to_parquet(reconstruido, index=False)
        fuentes = json.loads((config.RAIZ / "salida/05_manifiesto_ir.json").read_text())["entradas"]
        if sha(reconstruido) != fuentes["data/pasajes.parquet"]:
            raise ValueError("Parquet binario distinto: revisar versiones, no reescribir históricos")
        for fuente, destino in ((original, destino_corpus), (reconstruido, destino_pasajes)):
            if not destino.exists():
                destino.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(fuente, destino)
        print(f"Snapshot {meta['commit_dataset']}: {len(df)} discursos; "
              f"{len(pasajes)} pasajes; hashes originales correctos.")


if __name__ == "__main__":
    main()
