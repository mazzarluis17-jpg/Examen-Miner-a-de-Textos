"""Genera cinco láminas a partir de artefactos oficiales; aprobación humana pendiente."""
import json

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from mtx.entrega import AUTOR, RAIZ, tablas


def main():
    ir, ie = tablas()
    limpieza = json.loads((RAIZ / "salida/01_limpieza.json").read_text())
    estadisticas = json.loads((RAIZ / "salida/01_estadisticas_corpus.json").read_text())
    postings = (RAIZ / "salida/02_postings.md").read_text().split("## huachicol")[1]
    lineas = [linea for linea in postings.splitlines() if linea.strip()]
    posting_breve = "Huachicol, stem huachicol\n" + lineas[1] + "\n\n"
    filas = [linea for linea in lineas if linea.startswith("| ")][1:4]
    posting_breve += "\n".join(filas)
    posting_breve += "\n\nFuente: salida/02_postings.md; lista completa en data/indice.pkl."

    presentacion = Presentation()
    presentacion.slide_width, presentacion.slide_height = Inches(13.333), Inches(7.5)
    textos = [
        ("Examen 1 — Minería de Textos",
         "Universidad Nacional Autónoma de México\n"
         "Facultad de Estudios Superiores Acatlán\nLicenciatura en Ciencia de Datos\n"
         + AUTOR + "\n11 de noviembre de 2026",
         ("Discursos → limpieza → pasajes → índice → top-10 → entidades → respuestas\n\n"
         f"{estadisticas['discursos']} discursos; {limpieza['pasajes']} pasajes.\n"
         "Revisión fija y hashes verificables.")),
        ("Segmentación e índice",
         ("Intervenciones y ventanas de 200 palabras\nPaso 150; mínimo 40\n"
         "Marca visible para evidencia; excluida del índice\nStopwords y stemming español"),
         posting_breve),
        ("Recuperación de información",
         ("TF-IDF sublineal y coseno\nBM25 propio: k1=1.5, b=0.75\n"
         "Juicios temáticos; filtro temporal separado\nGanador por MAP con filtro"),
         ir.rename(columns={"AP": "MAP"}).round(4).to_string()),
        ("Extracción y evaluación",
         ("Reglas + gazetteers + BETO fijo\nGold humano cerrado antes de predicciones\n"
         "Fusión por span exacto\nPosproceso 2-vacios-auditados: un descarte vacío"),
         ie.loc[ie.tipo == "TODOS", ["metodo", "precision", "recall", "f1"]]
         .to_string(index=False)
         + "\n\nOficial: 19 pasajes con entidades.\nComplementaria: 20 pasajes, "
         "F1 combinado 0.7022.\nErrores: entidad partida, siglas, LOC/ORG y marca."),
        ("Demo, evidencia y limitaciones",
         ("Consulta → top-10 → entidades → tabla\nmake demo Q=Q3\n"
         "Cinco minutos de exposición, dos de demo\nUn minuto de margen"),
         ("Q3: responsable Rocío Nahle; organizaciones e inversión ambiguas.\n\n"
         "No inferir relaciones por coocurrencia.\nDistinguir evidencia, ambigüedad y ausencia.\n"
         "Diez valoraciones personales conservadas.\nEnsayo y aprobación del alumno pendientes.")),
    ]
    for numero, (titulo, izquierda, derecha) in enumerate(textos, 1):
        slide = presentacion.slides.add_slide(presentacion.slide_layouts[6])
        for x, y, w, h, texto, tam in [
            (.5, .35, 12.3, .9, titulo, 28),
            (.5, 1.5, 4.6, 4.9, izquierda, 20),
            (5.5, 1.5, 7.2, 4.9, derecha, 17),
            (.5, 7, 12, .3, f"{AUTOR} | {numero}/5", 11),
        ]:
            caja = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
            caja.text_frame.word_wrap = True
            for i, linea in enumerate(texto.splitlines()):
                parrafo = caja.text_frame.paragraphs[0] if i == 0 else caja.text_frame.add_paragraph()
                parrafo.text = linea
                parrafo.font.size = Pt(tam)
                parrafo.font.color.rgb = RGBColor.from_string("18364D")
        if numero == 3:
            slide.shapes.add_picture(str(RAIZ / "reporte/figuras/ir_ap_por_consulta.png"),
                                     Inches(5.5), Inches(3.4), width=Inches(7.2))
    destino = RAIZ / "laminas/laminas.pptx"
    destino.parent.mkdir(exist_ok=True)
    presentacion.save(destino)
    print("Presentación: 5 diapositivas, aprobación y ensayo humanos pendientes.")


if __name__ == "__main__":
    main()
