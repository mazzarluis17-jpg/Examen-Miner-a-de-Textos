"""H8 reproducible: respuestas y evidencias; las valoraciones siguen siendo humanas."""

import argparse
import json
import subprocess
import time

import pandas as pd
import yaml

from mtx import config
from mtx.adaptadores_kit import sha256_archivo, verificar_hashes
from mtx.ambito_ie import cargar_ambito
from mtx.respuestas import (
    cargar_listas,
    generar_respuestas,
    renderizar_tablas,
    validar_respuestas,
    validar_valoraciones,
)


def publicar(ruta, datos):
    """Publicación atómica de derivados H8; no escribe datos humanos ni entradas H7."""
    from mtx.app.componentes import atomico

    atomico(ruta, datos.encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exigir-valoraciones",
        action="store_true",
        help="Devuelve error si faltan las diez valoraciones humanas vigentes",
    )
    args = parser.parse_args()
    inicio = time.perf_counter()
    raiz = config.RAIZ
    consultas = pd.read_csv(raiz / "data/consultas.csv", keep_default_na=False)
    politica = yaml.safe_load((raiz / "config/tablas_respuesta.yaml").read_text())
    excluidas = yaml.safe_load((raiz / "config/excluir_tablas.yaml").read_text())[
        "per_funcionarios"
    ]
    ranking, pasajes = cargar_ambito(raiz)
    if (
        set(ranking.modelo) != {politica["modelo"]}
        or ranking.query_id.nunique() != 10
        or not ranking.groupby("query_id").size().eq(10).all()
        or ranking.duplicated(["query_id", "passage_id"]).any()
    ):
        raise ValueError("H8 requiere los diez top-10 del ganador congelado")
    if verificar_hashes():
        raise ValueError("Kit distinto del original")
    # Verificación de fuentes de cierre sin escribir anotaciones ni ejecutar extracción.
    sello = json.loads((raiz / "anotaciones/cierre_gold.json").read_text())
    for p, h in sello["fuentes"].items():
        if sha256_archivo(raiz / p) != h:
            raise ValueError("Fuente del cierre Gold modificada: " + p)
    for campo, p in [
        ("Evaluación", "anotaciones/gold_entidades.csv"),
        ("estados", "anotaciones/estado_gold.csv"),
    ]:
        if sha256_archivo(raiz / p) != sello["archivos"][campo]:
            raise ValueError("Gold cerrado modificado")
    manifiesto_h7 = json.loads((raiz / "salida/manifiesto_ejecucion.json").read_text())
    for p, h in manifiesto_h7["entradas"].items():
        if sha256_archivo(raiz / p) != h:
            raise ValueError("Fuente H7 modificada: " + p)
    entidades = pd.read_csv(raiz / "salida/entidades_enriquecidas.csv", keep_default_na=False)
    auxiliares = pd.read_csv(raiz / "salida/cantidades_auxiliares.csv", keep_default_na=False)
    insumos = [
        "data/consultas.csv",
        "data/mejor_modelo.json",
        "data/pasajes.parquet",
        "salida/ranking.csv",
        "salida/entidades_enriquecidas.csv",
        "salida/entidades.csv",
        "salida/cantidades_auxiliares.csv",
        "salida/manifiesto_ejecucion.json",
        "config/tablas_respuesta.yaml",
        "config/excluir_tablas.yaml",
        "config/gazetteer_loc.csv",
        "kit/gazetteer_dependencias.csv",
        "src/mtx/respuestas.py",
        "scripts/10_tablas.py",
    ]
    ruta_valoraciones = raiz / "anotaciones/valoraciones.yaml"
    valoraciones = (
        yaml.safe_load(ruta_valoraciones.read_text()) or {} if ruta_valoraciones.exists() else {}
    )
    if ruta_valoraciones.exists():
        insumos.append("anotaciones/valoraciones.yaml")
    huellas = {p: sha256_archivo(raiz / p) for p in insumos}
    listas = cargar_listas(raiz, politica)
    resultados, exclusiones, agregados, evidencias = generar_respuestas(
        entidades,
        auxiliares,
        pasajes,
        ranking,
        consultas,
        politica,
        excluidas,
        listas,
    )
    errores = validar_respuestas(
        resultados, pasajes, ranking, politica, entidades, auxiliares, listas, excluidas
    )
    if errores:
        raise ValueError("; ".join(errores))
    tablas, hashes, pendientes = renderizar_tablas(
        resultados, consultas, politica, exclusiones, agregados, valoraciones
    )
    destino = raiz / "salida/tablas_respuesta"
    destino.mkdir(parents=True, exist_ok=True)
    for q, texto in tablas.items():
        publicar(destino / f"{q}.md", texto)
    publicar(destino / "todas.md", "\n\n".join(tablas[q] for q in consultas.query_id))
    for nombre, tabla in [
        ("respuestas.csv", resultados),
        ("10_exclusiones.csv", exclusiones),
        ("10_agregados.csv", agregados),
        ("10_evidencias_completas.csv", evidencias),
    ]:
        publicar(raiz / "salida" / nombre, tabla.to_csv(index=False, lineterminator="\n"))
    resumen = (
        resultados.groupby(["query_id", "campo_respuesta", "estado"]).size().reset_index(name="n")
    )
    publicar(raiz / "salida/10_cobertura_respuestas.csv", resumen.to_csv(index=False))
    publicar(
        raiz / "salida/10_hashes_tablas.json",
        json.dumps(hashes, ensure_ascii=False, indent=2) + "\n",
    )
    plantilla = {q: {"tabla_sha256": h, "valoracion": ""} for q, h in hashes.items()}
    ruta_plantilla = raiz / "salida/10_valoraciones_plantilla.yaml"
    if ruta_plantilla.exists():
        anterior = yaml.safe_load(ruta_plantilla.read_text()) or {}
        if any(isinstance(v, dict) and v.get("valoracion") for v in anterior.values()):
            raise ValueError("La plantilla contiene texto humano: conservar sin sobrescribir")
    publicar(
        ruta_plantilla,
        "# Copiar a anotaciones/valoraciones.yaml y escribir personalmente 2–3 líneas por consulta.\n"
        "# ¿Es creíble?, ¿qué falta?, ¿qué está mal? No conservar opiniones generadas por IA.\n"
        "# tabla_sha256 identifica la tabla técnica, sin su bloque de valoración.\n"
        + yaml.safe_dump(plantilla, allow_unicode=True, sort_keys=False),
    )
    fallos_humanos = validar_valoraciones(valoraciones, hashes)
    estado = {
        "h8_tecnico": "completo",
        "valoraciones_validas": 10 - len(fallos_humanos),
        "valoraciones_pendientes": fallos_humanos,
        "h8_completo": not fallos_humanos,
        "filas_respuesta": len(resultados),
        "consultas": 10,
        "errores_tecnicos": errores,
        "nota": "Las tablas sin valoraciones personales aún no son entregables finales (R08).",
    }
    publicar(
        raiz / "salida/10_validacion_h8.json",
        json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
    )
    salidas = [
        "salida/respuestas.csv",
        "salida/10_exclusiones.csv",
        "salida/10_agregados.csv",
        "salida/10_evidencias_completas.csv",
        "salida/10_cobertura_respuestas.csv",
        *[f"salida/tablas_respuesta/{q}.md" for q in consultas.query_id],
        "salida/tablas_respuesta/todas.md",
    ]
    manifiesto = {
        "esquema": 1,
        "productor": "scripts/10_tablas.py",
        "modelo": politica["modelo"],
        "commit_codigo": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "entradas": huellas,
        "salidas": {p: sha256_archivo(raiz / p) for p in salidas},
        "hashes_tablas": hashes,
        "politica_sha256": huellas["config/tablas_respuesta.yaml"],
    }
    publicar(
        raiz / "salida/10_manifiesto_respuestas.json",
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n",
    )
    for p, h in huellas.items():
        if sha256_archivo(raiz / p) != h:
            raise ValueError("H8 modificó una entrada: " + p)
    publicar(
        raiz / "salida/10_tiempos.json",
        json.dumps({"segundos": time.perf_counter() - inicio}) + "\n",
    )
    print(resumen.groupby(["query_id", "estado"]).n.sum().unstack(fill_value=0).to_string())
    print(f"H8 técnico completo. Valoraciones humanas pendientes: {len(fallos_humanos)}.")
    if args.exigir_valoraciones and (pendientes or fallos_humanos):
        raise SystemExit("[VALIDAR] Faltan valoraciones humanas vigentes; no generar reporte.")


if __name__ == "__main__":
    main()
