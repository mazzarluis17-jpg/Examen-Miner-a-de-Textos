"""Evaluador oficial IE, complemento P04 y errores sin reajustar el extractor."""

import json
import subprocess
import tempfile
import time
from pathlib import Path

import pandas as pd
import plotly.express as px

from mtx import config
from mtx.adaptadores_kit import ejecutar_evaluador, sha256_archivo, verificar_hashes
from mtx.evaluacion import escribir_conservando
from mtx.evaluacion_ie import (
    analizar_errores,
    detalle_ie,
    validar_entidades,
    verificar_cierre,
)


def main():
    inicio = time.perf_counter()
    raiz = config.RAIZ
    ctx, estado = verificar_cierre(raiz)
    if verificar_hashes():
        raise ValueError("Kit distinto del original")
    pred = pd.read_csv(raiz/"entidades.csv", keep_default_na=False)
    validar_entidades(pred, ctx["pasajes"])
    modelo = json.loads((raiz/"data/modelo_ner.json").read_text())
    manifiesto_ext = json.loads((raiz/"salida/08_manifiesto_extraccion.json").read_text())
    if manifiesto_ext["modelo"] != modelo:
        raise ValueError("Extracción no corresponde al NER congelado")
    for ruta, h in manifiesto_ext["entradas"].items():
        if sha256_archivo(raiz/ruta) != h:
            raise ValueError("Fuente de extracción obsoleta: " + ruta)
    ref = estado["tablas"]["Evaluación"].copy()
    ref[["inicio", "fin"]] = ref[["inicio", "fin"]].astype(int)
    ids = set(ctx["muestras"]["Evaluación"].passage_id)
    evaluados_kit = set(ref.passage_id)
    with tempfile.TemporaryDirectory(prefix="mtx-ie-") as temporal:
        salida = ejecutar_evaluador("ie", raiz/"gold_entidades.csv", raiz/"entidades.csv",
            Path(temporal), registro=raiz/"salida/09_evaluador_oficial.json")
        oficial = pd.read_csv(salida)
        for ruta in [raiz/"resultados_ie.csv", raiz/"salida/resultados_ie.csv"]:
            escribir_conservando(ruta, salida.read_bytes())
    detalle = detalle_ie(ref, pred, evaluados_kit)
    complemento = detalle_ie(ref, pred, ids)
    for f in oficial.itertuples():
        fila = detalle[detalle.metodo.eq(f.metodo) & detalle.tipo.eq(f.tipo)].iloc[0]
        if (f.tp != fila.TP or f.predichas != fila.TP+fila.FP or f.gold != fila.soporte or
                any(abs(getattr(f, col)-round(fila[local],4)) > 1e-8 for col, local in
                    [("precision", "P"), ("recall", "R"), ("f1", "F1")])):
            raise ValueError("Detalle independiente no coincide con kit")
    enriquecidas = pd.read_csv(raiz/"salida/entidades_enriquecidas.csv", keep_default_na=False)
    obras = pd.read_csv(raiz/"kit/gazetteer_dependencias.csv")
    nombres_obras = obras.loc[obras.tipo.eq("obra"), "nombre"].tolist()
    errores = analizar_errores(ref, enriquecidas, ctx["pasajes"], ids, nombres_obras)
    resumen = errores.groupby(["categoria", "tipo", "metodo"]).size().reset_index(name="n")
    for nombre, tabla in [("09_ie_detalle.csv",detalle), ("09_evaluacion_20_ids.csv",complemento),
            ("09_analisis_errores.csv",errores), ("09_resumen_errores.csv",resumen)]:
        escribir_conservando(raiz/"salida"/nombre, tabla.to_csv(index=False).encode())
    categorias = ["entidad_partida", "sigla_no_reconocida", "monto_sin_unidad",
                  "obra_LOC_vs_ORG", "en_marca"]
    auditoria = {c: {"observado": bool(errores.categoria.eq(c).any()),
        "ejemplo": errores[errores.categoria.eq(c)].head(1).to_dict("records")} for c in categorias}
    # Comparación informativa crudo/posproceso: nunca decide ni ajusta el NER.
    crudas = pd.read_csv(raiz/"salida/07_crudas_beto.csv", keep_default_na=False)
    efectos = []
    for etiqueta, tabla in [("crudo_sin_recorte_ni_union",crudas),
                            ("posproceso_congelado",pred)]:
        f = detalle_ie(ref, tabla, evaluados_kit)
        f = f[f.metodo.eq("modelo")].copy()
        f["configuracion"] = etiqueta
        efectos.append(f)
    pd.concat(efectos).to_csv(raiz/"salida/09_efecto_posproceso.csv",index=False)
    figuras = raiz/"reporte/figuras"
    figuras.mkdir(parents=True,exist_ok=True)
    px.bar(oficial[oficial.tipo.ne("TODOS")],x="tipo",y="f1",color="metodo",
           barmode="group",title="IE oficial: F1 por tipo y método").write_image(
           figuras/"ie_f1_por_tipo_metodo.png",width=1000,height=550)
    px.bar(resumen.groupby(["categoria","metodo"]).n.sum().reset_index(),
           x="categoria",y="n",color="metodo",barmode="group",
           title="Categorías no exclusivas de errores IE").write_image(
           figuras/"ie_errores_por_categoria.png",width=1100,height=550)
    alertas = []
    if oficial.loc[oficial.metodo.eq("combinado") & oficial.tipo.eq("TODOS"),"f1"].iloc[0]<.30:
        alertas.append("F1 bajo: offsets, tipos, IDs y detalle independiente verificados")
    if any(f.f1 == 1 and f.gold>5 for f in oficial.itertuples()):
        alertas.append("F1 perfecto: revisar trazabilidad; cierre humano anterior a inferencia")
    (raiz/"salida/09_auditoria_ie.json").write_text(json.dumps({
        "pasajes_kit": len(evaluados_kit),"pasajes_complementaria": len(ids),
        "pasajes_gold_vacios": sorted(ids-evaluados_kit),"alertas": alertas,"categorias": auditoria,
        "nota": "en_marca describe ubicación; no prueba efecto causal de mayúsculas",
        "comparacion_ner": "no realizada: modelo principal fijado por criterio técnico antes del Gold"
    },ensure_ascii=False,indent=2)+"\n")
    entradas = ["gold_entidades.csv", "anotaciones/cierre_gold.json", "anotaciones/estado_gold.csv",
        "anotaciones/muestra_gold.csv", "entidades.csv", "kit/evaluar.py", "kit/corpus.py",
        "data/modelo_ner.json", "data/mejor_modelo.json", "config/ner.yaml",
        "src/mtx/reglas.py", "src/mtx/ner_modelo.py", "src/mtx/fusion.py",
        "src/mtx/enriquecimiento.py", "src/mtx/evaluacion_ie.py", "scripts/09_evaluar_ie.py",
        "config/gazetteer_extendido.csv", "config/gazetteer_loc.csv",
        "config/gazetteer_prescrito.csv", "config/criterios_anotacion.md"]
    versiones = {p:sha256_archivo(raiz/p) for p in entradas}
    manifiesto = {"esquema": 1,"productor": "scripts/09_evaluar_ie.py","modelo": modelo,
        "commit": subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "reglas_congeladas": subprocess.check_output(["git","rev-parse","reglas-congeladas^{}"],
                                                  text=True).strip(),
        "entradas": versiones,"extraccion": manifiesto_ext,
        "gold_procedencia": "Anotación humana externa de Luis; transferencia autorizada; cierre en app"}
    (raiz/"salida/manifiesto_ejecucion.json").write_text(
        json.dumps(manifiesto,ensure_ascii=False,indent=2)+"\n")
    tiempos = raiz/"salida/tiempos_ejecucion.json"
    datos = json.loads(tiempos.read_text()) if tiempos.exists() else {}
    datos["09_evaluar_ie"] = time.perf_counter()-inicio
    datos["07_ner"] = json.loads((raiz/"salida/07_ejecucion_ner.json").read_text())
    tiempos.write_text(json.dumps(datos,ensure_ascii=False,indent=2)+"\n")
    print(oficial[oficial.tipo.eq("TODOS")].to_string(index=False))


if __name__ == "__main__":
    main()
