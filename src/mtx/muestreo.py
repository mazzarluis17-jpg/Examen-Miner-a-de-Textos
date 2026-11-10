"""Preparación H5: emparejamiento global reproducible, sin anotar entidades."""

import hashlib
import random

import pandas as pd


def sortear_muestra(ranking, pasajes, semilla=42):
    """Dos plazas por consulta, preferencia por mitad alta y baja, IDs únicos."""
    rng = random.Random(semilla)
    consultas = sorted(ranking.query_id.unique())
    candidatos = {}
    for q in consultas:
        filas = ranking[ranking.query_id.eq(q)].sort_values(["rango", "passage_id"])
        if filas.passage_id.duplicated().any():
            raise ValueError("Ranking duplicado por consulta")
        altos = list(filas.loc[filas.rango <= 5, "passage_id"])
        rng.shuffle(altos)
        bajos = list(filas.loc[filas.rango > 5, "passage_id"])
        rng.shuffle(bajos)
        candidatos[(q, 0)] = altos + bajos
        candidatos[(q, 1)] = bajos + altos
    dueno = {}

    def asignar(plaza, visitados):
        for pid in candidatos[plaza]:
            if pid in visitados:
                continue
            visitados.add(pid)
            if pid not in dueno or asignar(dueno[pid], visitados):
                dueno[pid] = plaza
                return True
        return False

    fallidas = [p for p in candidatos if not asignar(p, set())]
    if fallidas:
        raise ValueError(
            "Asignación global imposible; consultas en conflicto: "
            + ", ".join(sorted({p[0] for p in fallidas}))
        )
    textos = pasajes.set_index("passage_id")
    filas = []
    for pid, (q, plaza) in sorted(dueno.items(), key=lambda x: (x[1], x[0])):
        fila = textos.loc[pid]
        filas.append(
            {
                "query_id": q,
                "passage_id": pid,
                "doc_id": fila.doc_id,
                "texto_sha256": hashlib.sha256(fila.texto.encode()).hexdigest(),
                "semilla": semilla,
                "version_muestra": "1",
            }
        )
    return pd.DataFrame(filas)
