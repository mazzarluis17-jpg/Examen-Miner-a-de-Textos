"""Artefactos de H9 derivados exclusivamente de resultados existentes."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
AUTOR = "Luis Alfredo Ramírez Maza"


def sha(ruta):
    """Huella binaria SHA-256."""
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def tablas(raiz=RAIZ):
    """Lee métricas oficiales, sin volver a evaluar ni redondear sus entradas."""
    ir = pd.read_csv(Path(raiz) / "salida/resultados_ir.csv")
    ir = ir[ir.query_id == "PROMEDIO (MAP = AP)"].set_index("modelo")[["P@5", "P@10", "AP"]]
    ie = pd.read_csv(Path(raiz) / "salida/resultados_ie.csv")
    return ir, ie


def tex(texto):
    """Escapa texto literal para XeLaTeX."""
    reemplazos = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#",
                  "$": r"\$", "{": r"\{", "}": r"\}"}
    return "".join(reemplazos.get(c, c) for c in str(texto))


def tabla_tex(df):
    """Tabla compacta de resultados reales."""
    cabecera = " & ".join(tex(c) for c in df.columns) + r" \\ \midrule" + "\n"
    filas = []
    for fila in df.itertuples(index=False, name=None):
        filas.append(" & ".join(tex(f"{v:.4f}" if isinstance(v, float) else v)
                                 for v in fila) + r" \\")
    return (r"\par\medskip\noindent\begin{tabular}{" + "l" * len(df.columns)
            + "}\n" + r"\toprule" + "\n" + cabecera + "\n".join(filas)
            + "\n" + r"\bottomrule\end{tabular}\par\medskip" + "\n")



def reporte():
    """Entrada compatible que compila el Markdown sin regenerar prosa."""
    from .reporte import compilar

    return compilar()
