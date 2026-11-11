"""Compilación del Markdown académico sin regenerar ni aprobar su prosa."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import yaml
from pypdf import PdfReader

from mtx.entrega import RAIZ, tablas
from mtx.entrega import tex as escapar_base


def tex(texto):
    """Permite cortes tipográficos en rutas y revisiones largas, conservando caracteres."""
    valor = escapar_base(texto).replace(r'\_', r'\_\allowbreak{}')
    valor = valor.replace('/', r'/\allowbreak{}')
    return re.sub(r'[0-9a-f]{30,}',
                  lambda m: r'\allowbreak{}'.join(m[0][i:i+10]
                                                 for i in range(0, len(m[0]), 10)), valor)


def literal(texto):
    """Escapa texto y conserva únicamente las fórmulas delimitadas por dólares."""
    trozos = re.split(r'(\$[^$]+\$)', str(texto))
    return ''.join(t if t.startswith('$') else tex(t) for t in trozos)


def tabla(columnas, filas, formato, titulo):
    """Tabla fija que no se corta entre páginas, con columnas de ancho controlado."""
    piezas = [r'\par\medskip\noindent\begin{minipage}{\linewidth}',
              r'\textbf{' + tex(titulo) + r'}\par\smallskip',
              r'\begin{tabularx}{\linewidth}{@{}' + formato.replace('X', 'Y') + r'@{}}\toprule',
              ' & '.join(tex(c) for c in columnas) + r' \\ \midrule']
    piezas.extend(' & '.join(tex(c) for c in fila) + r' \\' for fila in filas)
    piezas.extend([r'\bottomrule\end{tabularx}\end{minipage}\par\medskip'])
    return '\n'.join(piezas)


def generar_tablas(raiz=RAIZ):
    """Deriva tablas y citas literales; no cambia respuestas ni valoraciones."""
    raiz = Path(raiz)
    ir, ie = tablas(raiz)
    limpieza = json.loads((raiz / 'salida/01_limpieza.json').read_text())
    filas = [["Discursos originales", limpieza['discursos']],
             ["Duplicados exactos / casi duplicados", (f"{limpieza['duplicados_exactos']} / "
                                                       f"{limpieza['casi_duplicados']}")],
             ["Acotaciones retiradas / fechas reparadas", (f"{limpieza['acotaciones_eliminadas']} / "
                f"{limpieza['fechas_reparadas']}")],
             ["Ventana / paso / mínimo (palabras)", "200 / 150 / 40"],
             ["Pasajes / ventanas cortas descartadas", (f"{limpieza['pasajes']} / "
                 f"{limpieza['ventanas_descartadas_por_min_tokens']}")]]
    resultado = {'corpus': tabla(['Operación', 'Conteo'], filas, 'Xr',
                                 'Tabla 1. Corpus y limpieza auditada')}
    texto_postings = (raiz / 'salida/02_postings.md').read_text()
    filas = []
    for seccion in texto_postings.split('## ')[1:]:
        nombre = seccion.split(' →')[0]
        df, idf = re.search(r'df = (\d+) de N = \d+; idf BM25 = ([\d.]+)', seccion).groups()
        postings = re.findall(r'^\| (\d+_\d+) \| [^|]+ \| (\d+) \|', seccion, re.MULTILINE)[:3]
        filas.append([nombre, df, idf, '; '.join(f'{pid}: {tf}' for pid, tf in postings)])
    resultado['postings'] = tabla(['Término', 'df', 'idf BM25', 'Pasaje: tf'], filas,
                                 'lrrX', 'Tabla 2. Muestras de postings')
    ventana = pd.read_csv(raiz / 'salida/05_resultados_ir_ventana.csv')
    ventana = ventana[ventana.query_id == 'PROMEDIO (MAP = AP)'].set_index('modelo')
    filas = []
    for modelo, r in ir.iterrows():
        v = ventana.loc[modelo]
        nombre = modelo.replace('bm25', 'BM25').replace('tfidf', 'TF-IDF').replace('_', ' ')
        filas.append([nombre, *[f'{r[k]:.4f}' for k in ['P@5', 'P@10', 'AP']],
                      *[f'{v[k]:.4f}' for k in ['P@5', 'P@10', 'AP']]])
    resultado['ir'] = tabla(['Variante', 'P@5', 'P@10', 'MAP', 'P@5*', 'P@10*', 'MAP*'],
                             filas, 'Xrrrrrr', 'Tabla 3. IR oficial y con ventana (*)')
    globales = ie[ie.tipo == 'TODOS']
    filas = [[r.metodo, f'{r.precision:.4f}', f'{r.recall:.4f}', f'{r.f1:.4f}']
             for r in globales.itertuples()]
    resultado['ie'] = tabla(['Método', 'Precisión', 'Recall', 'F1'], filas, 'Xrrr',
                             'Tabla 4. IE oficial global (19 pasajes con entidades)')
    filas = []
    for tipo in ['PER', 'ORG', 'LOC', 'FECHA', 'MONTO']:
        fila = [tipo]
        for metodo in ['regla', 'modelo', 'combinado']:
            r = ie[(ie.tipo == tipo) & (ie.metodo == metodo)].iloc[0]
            fila.append(f'{r.precision:.4f}/{r.recall:.4f}/{r.f1:.4f}')
        filas.append(fila)
    resultado['tipos'] = tabla(['Tipo', 'Reglas: P/R/F1', 'BETO: P/R/F1', 'Combinado: P/R/F1'],
                                filas, 'lXXX', 'Tabla 5. IE oficial por tipo')
    respuestas = pd.read_csv(raiz / 'salida/respuestas.csv', keep_default_na=False)
    opiniones = yaml.safe_load((raiz / 'anotaciones/valoraciones.yaml').read_text())
    temas = ['Tren Maya', 'Vacunas', 'Dos Bocas', 'AIFA', 'Sembrando Vida', 'Huachicol',
             'Pensiones', 'Salario mínimo', 'Banco del Bienestar', 'Interoceánico']
    limites = ['Montos ausentes', 'Relaciones por verificar', 'Inversión ambigua',
               'Constructor/costo ambiguos', 'Operador ambiguo', 'Litros ambiguos',
               'Fecha ausente', 'Empresas ausentes', 'Eventos distintos', 'Costo total ambiguo']
    filas = []
    for i, (tema, limite) in enumerate(zip(temas, limites), 1):
        q = f'Q{i}'
        candidatas = respuestas[(respuestas.query_id == q) &
                               (respuestas.estado == 'respaldado_en_texto')]
        preferidas = {"Q6": ("perdidas", "65 mil millones de pesos"),
                      "Q9": ("sucursales", "dos mil 296 sucursales"),
                      "Q10": ("lugares_conecta", "Salina Cruz")}
        if q in preferidas:
            campo, valor_elegido = preferidas[q]
            candidatas = candidatas[(candidatas.campo_respuesta == campo) &
                                     (candidatas.valor == valor_elegido)]
        r = candidatas.iloc[0]
        opinion = opiniones[q]['valoracion']
        ultima = re.split(r'(?<=[.!?])\s+', opinion.strip())[-1]
        cita = ' '.join(ultima.split()[:8])
        if not opinion.find(cita) >= 0:
            raise ValueError(f'La cita humana no es literal: {q}')
        if len(ultima.split()) > 8:
            cita += '…'
        valor = str(r.valor)
        filas.append([q + ': ' + tema + '. ' + valor + '. ' + limite + '.',
                      f'{r.passage_id} [{r.evidencia_inicio}:{r.evidencia_fin}]',
                      '«' + cita + '»'])
    resultado['respuestas'] = tabla(['Consulta, ejemplo y límite', 'Pasaje [inicio:fin]',
                                     'Valoración humana (extracto)'], filas,
                                    'XXX',
                                    'Tabla 6. Respuestas compactas y revisión humana')
    destino = raiz / 'reporte/tablas'
    destino.mkdir(exist_ok=True)
    for nombre, contenido in resultado.items():
        (destino / f'{nombre}.tex').write_text(contenido + '\n')
    ir.reset_index().rename(columns={'AP': 'MAP'}).to_csv(destino / 'ir.csv', index=False)
    ie.to_csv(destino / 'ie.csv', index=False)
    return resultado


def convertir_md(texto, tablas_tex):
    """Convierte el subconjunto explícito de Markdown usado en el documento."""
    partes = []
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        i += 1
        if not linea:
            partes.append(r'\par')
        elif linea == '<!-- pagina -->':
            partes.append(r'\newpage')
        elif (m := re.fullmatch(r'<!-- tabla: (\w+) -->', linea)):
            partes.append(tablas_tex[m[1]])
        elif linea == '$$':
            formula = []
            while i < len(lineas) and lineas[i].strip() != '$$':
                formula.append(lineas[i])
                i += 1
            if i >= len(lineas):
                raise ValueError('Fórmula sin cierre')
            i += 1
            partes.append(r'\[' + '\n'.join(formula) + r'\]')
        elif linea.startswith('# '):
            partes.append(r'\begin{center}\Large\bfseries ' + tex(linea[2:])
                          + r'\end{center}')
        elif linea.startswith('## '):
            partes.append(r'\section*{' + tex(linea[3:]) + '}')
        elif linea.startswith('### '):
            partes.append(r'\subsection*{' + tex(linea[4:]) + '}')
        elif (m := re.fullmatch(r'!\[(.+)\]\((.+)\)', linea)):
            partes.append(r'\par\noindent\includegraphics[width=\linewidth,height=5.5cm,'
                          r'keepaspectratio]{' + m[2] + r'}\par\noindent '
                          + tex(m[1]) + r'\par')
        elif '```' in linea or '`' in linea:
            raise ValueError('El reporte no admite bloques ni fragmentos de código')
        else:
            partes.append(literal(linea))
    return '\n'.join(partes)


def generar_figura(raiz=RAIZ):
    """Figura editorial de H9, sin modificar las figuras congeladas de H4."""
    import plotly.graph_objects as go

    raiz = Path(raiz)
    datos = pd.read_csv(raiz / "salida/05_ir_por_consulta.csv")
    figura = go.Figure()
    orden = [f"Q{i}" for i in range(1, 11)]
    colores = ["#18364D", "#528B8D", "#A28141", "#866189"]
    modelos = ["bm25_con_filtro", "bm25_sin_filtro", "tfidf_con_filtro", "tfidf_sin_filtro"]
    for modelo, color in zip(modelos, colores):
        valores = datos.set_index("query_id").loc[orden, "AP__" + modelo]
        nombre = modelo.replace("bm25", "BM25").replace("tfidf", "TF-IDF").replace("_", " ")
        figura.add_bar(x=orden, y=valores, name=nombre, marker_color=color)
    figura.update_layout(template="plotly_white", barmode="group", width=1600, height=530,
                         margin={'l': 70, 'r': 20, 't': 65, 'b': 55},
                         font={'family': "DejaVu Sans", 'size': 25},
                         legend={'orientation': "h", 'x': 0, 'y': 1.18, 'font': {'size': 23}},
                         yaxis={'title': "AP@10", 'range': [0, 1.04], 'dtick': .2},
                         xaxis={'title': None})
    figura.write_image(raiz / "reporte/figuras/h9_ir_ap.png")


def insertar_resultados(texto, bloque):
    """Sustituye exclusivamente el bloque derivado del README."""
    inicio = "<!-- resultados:inicio -->"
    fin = "<!-- resultados:fin -->"
    if texto.count(inicio) != 1 or texto.count(fin) != 1:
        raise ValueError("Marcadores de resultados ausentes o duplicados")
    antes, resto = texto.split(inicio)
    _, despues = resto.split(fin)
    return antes + inicio + "\n" + bloque + "\n" + fin + despues


def actualizar_readme(raiz):
    """Regenera solo métricas, preservando autoría y texto revisado."""
    ir, ie = tablas(raiz)
    bloque = "Métricas oficiales IR (promedios literales del evaluador):\n\n```csv\n"
    bloque += ir.rename(columns={"AP": "MAP"}).to_csv(float_format="%.4f") + "```\n\n"
    bloque += "F1 oficial combinado por tipo:\n\n```csv\n"
    bloque += ie.loc[(ie.metodo == "combinado") & (ie.tipo != "TODOS"),
                     ["tipo", "f1"]].to_csv(index=False, float_format="%.4f") + "```"
    ruta = Path(raiz) / "README.md"
    actual = ruta.read_text()
    nuevo = insertar_resultados(actual, bloque)
    if nuevo != actual:
        ruta.write_text(nuevo)


def compilar(raiz=RAIZ):
    """Lee prosa existente, regenera tablas y compila sin sobrescribir Markdown."""
    raiz = Path(raiz)
    md = raiz / 'reporte/reporte.md'
    contenido = md.read_text()
    fuentes = ["salida/01_estadisticas_corpus.json", "salida/01_limpieza.json",
               "data/indice_meta.json", "salida/02_memoria.json", "salida/02_postings.md",
               "salida/resultados_ir.csv", "salida/05_resultados_ir_ventana.csv",
               "salida/05_ir_ganador_por_consulta.csv", "salida/resultados_ie.csv",
               "salida/09_evaluacion_20_ids.csv", "salida/09_auditoria_ie.json",
               "salida/09_efecto_posproceso.csv", "salida/respuestas.csv",
               "anotaciones/valoraciones.yaml", "salida/11_reproducibilidad_clon.json"]
    from mtx.entrega import sha

    auditoria = {"fuentes": {p: sha(raiz / p) for p in fuentes},
                 "indice": json.loads((raiz / "data/indice_meta.json").read_text()),
                 "estado": "corte 1 aprobado por Luis; corte 2 pendiente de revisión humana"}
    (raiz / "salida/11_fuentes_reporte.json").write_text(
        json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n")
    tablas_tex = generar_tablas(raiz)
    actualizar_readme(raiz)
    cuerpo = convertir_md(contenido, tablas_tex)
    plantilla = (raiz / 'reporte/plantilla.tex').read_text()
    generado = raiz / 'reporte/documento.tex'
    generado.write_text(plantilla.replace('%% CUERPO %%', cuerpo))
    proceso = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                              '-jobname=reporte', generado.name], cwd=generado.parent,
                             capture_output=True, text=True, check=False)
    if proceso.returncode:
        raise RuntimeError(proceso.stdout[-3500:])
    paginas = len(PdfReader(generado.parent / 'reporte.pdf').pages)
    if not 4 <= paginas <= 6:
        raise ValueError(f'Reporte fuera del límite: {paginas} páginas')
    if md.read_text() != contenido:
        raise ValueError('La compilación modificó la prosa')
    print(f'Reporte: {paginas} páginas; borrador de prosa (corte 2), sin aprobación final.')
    return paginas
