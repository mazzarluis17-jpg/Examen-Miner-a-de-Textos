"""Fusión D12 por clave exacta, sin consultar anotaciones humanas."""

import pandas as pd

COLUMNAS = ["query_id", "doc_id", "passage_id", "tipo", "texto", "inicio", "fin", "metodo"]
CLAVE = ["passage_id", "tipo", "inicio", "fin"]
SOLAPES = ["passage_id", "tipo_regla", "inicio_regla", "fin_regla", "tipo_modelo",
           "inicio_modelo", "fin_modelo", "clase", "longitud_solape"]


def fusionar(reglas, modelo, ranking, pasajes):
    """Extrae una vez por ID; asociaciones públicas después de la unión exacta."""
    textos = pasajes.set_index("passage_id")
    fuentes = []
    for tabla in [reglas, modelo]:
        tabla = tabla.copy()
        tabla[["inicio", "fin"]] = tabla[["inicio", "fin"]].astype(int)
        for f in tabla.itertuples():
            if (f.passage_id not in textos.index or f.tipo not in
                    {"PER", "ORG", "LOC", "FECHA", "MONTO"} or
                    not 0 <= f.inicio < f.fin <= len(textos.loc[f.passage_id, "texto"]) or
                    textos.loc[f.passage_id, "texto"][f.inicio:f.fin] != f.texto):
                raise ValueError("Entidad inválida antes de fusionar")
        if len(tabla) and tabla.groupby(CLAVE).texto.nunique().gt(1).any():
            raise ValueError("Textos incompatibles para una misma clave")
        fuentes.append({tuple(f[c] for c in CLAVE): f for f in
                        tabla.drop_duplicates(CLAVE).to_dict("records")})
    r, m = fuentes
    unicas, discrepancias = [], []
    for clave in sorted(r.keys() | m.keys()):
        entidad = dict(r.get(clave, m.get(clave)))
        entidad["metodo"] = "ambos" if clave in r and clave in m else (
            "regla" if clave in r else "modelo")
        entidad["fuentes"] = "|".join(filter(None, [
            str(r[clave].get("fuente", "regla")) if clave in r else "",
            "modelo" if clave in m else ""]))
        entidad.pop("query_id", None)
        unicas.append(entidad)
    for kr, er in r.items():
        for km, em in m.items():
            if kr[0] != km[0] or kr == km:
                continue
            solape = min(kr[3], km[3]) - max(kr[2], km[2])
            if solape > 0:
                discrepancias.append([kr[0], er["tipo"], kr[2], kr[3], em["tipo"],
                    km[2], km[3], "tipo_distinto" if kr[2:] == km[2:] else
                    "solape_parcial", solape])
    unica = pd.DataFrame(unicas, columns=["doc_id", *CLAVE, "texto", "metodo", "fuentes"])
    asociaciones = ranking[["query_id", "passage_id", "doc_id"]].drop_duplicates()
    publica = asociaciones.merge(unica.drop(columns="doc_id"), on="passage_id", how="inner")
    publica = publica.sort_values(["query_id", "passage_id", "inicio", "fin", "tipo"])
    oficial = publica[COLUMNAS].reset_index(drop=True)
    if oficial.duplicated(["query_id", *CLAVE]).any():
        raise ValueError("Clave pública duplicada")
    return oficial, unica, publica, pd.DataFrame(discrepancias, columns=SOLAPES)
