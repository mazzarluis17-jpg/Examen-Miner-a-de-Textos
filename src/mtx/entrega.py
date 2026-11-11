"""Artefactos de H9 derivados exclusivamente de resultados existentes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[2]
AUTOR = "Luis Alfredo Ramírez Maza"


def sha(ruta):
    """Huella binaria SHA-256."""
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def tablas():
    """Lee métricas oficiales, sin volver a evaluar ni redondear sus entradas."""
    ir = pd.read_csv(RAIZ / "salida/resultados_ir.csv")
    ir = ir[ir.query_id == "PROMEDIO (MAP = AP)"].set_index("modelo")[["P@5", "P@10", "AP"]]
    ie = pd.read_csv(RAIZ / "salida/resultados_ie.csv")
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
    """Compila el esqueleto del primer corte; nunca sobrescribe prosa aprobada."""
    destino = RAIZ / "reporte"
    destino.mkdir(exist_ok=True)
    ir, ie = tablas()
    ir_tabla = ir.reset_index().rename(columns={"AP": "MAP"})
    ir_tabla.to_csv(destino / "tablas/ir.csv", index=False)
    ie.to_csv(destino / "tablas/ie.csv", index=False)
    titulos = ["Portada compacta", "Datos, limpieza y segmentación",
               "Preprocesamiento e índice invertido", "Ranking y evaluación de IR",
               "Extracción con reglas y con modelo", "Evaluación de IE y análisis de errores",
               "Tablas de respuesta", "Uso de IA, limitaciones y reproducibilidad"]
    md = destino / "reporte.md"
    if not md.exists():
        md.write_text("# Examen 1 — Minería de Textos\n\n" + AUTOR
                      + "\n\nUNAM — FES Acatlán · Licenciatura en Ciencia de Datos"
                      + "\n\n11 de noviembre de 2026\n\n"
                      + "\n\n".join(f"## {i}. {t}\n\n[VALIDAR: primer corte, sin prosa]"
                                       for i, t in enumerate(titulos, 1)) + "\n")
    partes = [r"\documentclass[11pt,a4paper]{article}",
              r"\usepackage[margin=2.2cm]{geometry}",
              r"\usepackage{fontspec,booktabs,graphicx,amsmath}",
              r"\setmainfont{DejaVu Serif}", r"\begin{document}",
              r"\begin{center}\Large Examen 1 — Minería de Textos\\[8pt]",
              tex(AUTOR) + r"\\ Universidad Nacional Autónoma de México\\",
              r"Facultad de Estudios Superiores Acatlán\\",
              r"Licenciatura en Ciencia de Datos\\ 11 de noviembre de 2026\end{center}"]
    for i, titulo in enumerate(titulos, 1):
        if i in (3, 5, 7):
            partes.append(r"\newpage")
        partes.append(r"\section*{" + f"{i}. {titulo}" + "}")
        partes.append("Esqueleto técnico del primer corte. Prosa pendiente de aprobación humana.")
        if i == 2:
            limpieza = json.loads((RAIZ / "salida/01_limpieza.json").read_text())
            partes.append(tabla_tex(pd.DataFrame([
                ["Pasajes", limpieza["pasajes"]],
                ["Discursos excluidos", limpieza["discursos_excluidos"]],
                ["Ventanas cortas descartadas", limpieza["ventanas_descartadas_por_min_tokens"]],
            ], columns=["Indicador", "Valor"])))
        if i == 4:
            partes.append(tabla_tex(ir_tabla))
            partes.append(r"\includegraphics[width=0.9\linewidth,height=6cm,keepaspectratio]"
                          r"{figuras/ir_ap_por_consulta.png}")
        if i == 6:
            partes.append(tabla_tex(ie[ie.tipo == "TODOS"][["metodo", "precision", "recall", "f1"]]))
            partes.append(r"\includegraphics[width=0.85\linewidth,height=5cm,keepaspectratio]"
                          r"{figuras/ie_f1_por_tipo_metodo.png}")
        if i == 7:
            cobertura = pd.read_csv(RAIZ / "salida/10_cobertura_respuestas.csv")
            # El detalle completo permanece en las diez tablas oficiales.
            partes.append(r"\small" + tabla_tex(cobertura.groupby(["query_id", "estado"])["n"].sum().unstack(fill_value=0).reset_index().rename(columns={"respaldado_en_texto": "Respaldadas", "ambiguo": "Ambiguas", "no_encontrado": "Sin evidencia"})) + r"\normalsize")
    partes.append(r"\end{document}")
    (destino / "esqueleto.tex").write_text("\n".join(partes))
    subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                    "-jobname=reporte", "esqueleto.tex"], cwd=destino,
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    paginas = len(PdfReader(destino / "reporte.pdf").pages)
    if not 4 <= paginas <= 6:
        raise ValueError(f"Reporte fuera del límite: {paginas} páginas")
    print(f"Reporte: {paginas} páginas; primer corte pendiente de aprobación.")
