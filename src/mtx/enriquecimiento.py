"""Representaciones auxiliares H7; no modifica el normalizador congelado ni spans."""

import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation

from mtx.normalizacion import normalizar_fecha

EXTRAS = ["fuentes", "en_marca", "modelo_id", "modelo_revision", "puntaje_modelo",
          "version_extractor", "canonico", "texto_normalizado", "estado_identidad",
          "fecha_iso", "fecha_inicio", "fecha_fin", "precision_fecha", "fecha_relativo",
          "fecha_ancla", "resuelta_desde_ancla", "estado_fecha", "valor_num", "valor_min",
          "valor_max", "moneda", "escala", "estado_monto"]
NUMEROS = {"un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
           "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "cien": 100}


def numero_decimal(texto):
    """Decimal sin notación científica; rechaza cifras ambiguas o no soportadas."""
    tokens = re.findall(r"\d[\d,.]*|[a-záéíóú]+", texto.lower().replace("$", ""))
    total = Decimal(0)
    for t in tokens:
        if t in {"de", "pesos", "dólares", "dolares"}:
            break
        if t in {"mil", "millón", "millones", "billón", "billones"}:
            factor = 1000 if t == "mil" else 10**12 if t.startswith("bill") else 10**6
            total = (total or Decimal(1)) * factor
        elif t in NUMEROS:
            total += Decimal(NUMEROS[t])
        elif t[0].isdigit():
            if re.fullmatch(r"\d{1,3}\.\d{3}", t):
                return ""
            if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", t):
                return ""
            try:
                total += Decimal(t.replace(",", ""))
            except InvalidOperation:
                return ""
        else:
            return ""
    return format(total, "f") if tokens else ""


def monto_auxiliar(texto, contexto=""):
    """Moneda explícita, rangos y ambigüedades; nunca convierte ni suma pasajes."""
    t = texto.lower()
    moneda = "MXN" if "pesos" in t else "USD" if re.search(r"d[oó]lares", t) else ""
    escala = ("billones" if "bill" in t else "mil_millones" if "mil mill" in t else
              "millones" if "mill" in t else "mil" if re.search(r"\bmil\b", t) else "uno")
    salida = {"valor_num": "", "valor_min": "", "valor_max": "", "moneda": moneda,
                  "escala": escala, "estado_monto": "ambiguo"}
    rango = re.fullmatch(r"entre (\d+) y (\d+) (mil millones|millones|mil) de (pesos|dólares)", t)
    if rango:
        a = numero_decimal(rango[1] + " " + rango[3])
        b = numero_decimal(rango[2] + " " + rango[3])
        if a and b and Decimal(a) <= Decimal(b):
            salida.update(valor_min=a, valor_max=b, estado_monto="rango")
        return salida
    if "bill" in t and re.search(r"mil millones|10\^9", contexto.lower()):
        return salida
    valor = numero_decimal(t)
    salida.update(valor_num=valor, estado_monto=("resuelto" if moneda else "moneda_ambigua")
                  if valor else "ambiguo")
    return salida


def fecha_auxiliar(texto, ancla=""):
    """Absolutas e intervalos; relativos no implementados quedan explícitos."""
    salida = {"fecha_iso": "", "fecha_inicio": "", "fecha_fin": "", "precision_fecha": "",
                  "fecha_relativo": "", "fecha_ancla": ancla, "resuelta_desde_ancla": False,
                  "estado_fecha": "no_resoluble"}
    intervalo = re.fullmatch(r"del (\d{1,2}) al (\d{1,2}) de (\w+) de (\d{4})", texto.lower())
    if intervalo:
        a, b, mes, anio = intervalo.groups()
        inicio = normalizar_fecha(f"{a} de {mes} de {anio}")["fecha_iso"]
        fin = normalizar_fecha(f"{b} de {mes} de {anio}")["fecha_iso"]
        if inicio and fin and inicio <= fin:
            salida.update(fecha_inicio=inicio, fecha_fin=fin, precision_fecha="intervalo",
                          estado_fecha="resuelto")
        else:
            salida["estado_fecha"] = "invalida"
        return salida
    relativo = re.match(r"^(próximo|pasado|este|hace)\b", texto.lower())
    if relativo:
        salida["fecha_relativo"] = relativo[1]
    try:
        normal = normalizar_fecha(texto)
    except (ValueError, IndexError):
        return salida
    salida.update(fecha_iso=normal["fecha_iso"] or "",
                  precision_fecha=normal["precision"] or "",
                  estado_fecha=normal["estado_normalizacion"])
    # Año del discurso solo para día/mes sin año, permitido por PRD 6.10.
    if not salida["fecha_iso"] and not relativo and ancla and re.fullmatch(
            r"\d{1,2} de \w+", texto.lower()):
        try:
            anio = date.fromisoformat(str(ancla)[:10]).year
            normal = normalizar_fecha(f"{texto} de {anio}")
            if normal["fecha_iso"]:
                salida.update(fecha_iso=normal["fecha_iso"], precision_fecha=normal["precision"],
                              estado_fecha="resuelto", resuelta_desde_ancla=True)
        except ValueError:
            pass
    return salida


def enriquecer(publica, pasajes, modelo, revision, version, equivalencias=None, puntajes=None):
    """Añade campos separados; mantiene texto y offsets inmutables."""
    textos = pasajes.set_index("passage_id")
    equivalencias = equivalencias or {}
    puntajes = puntajes or {}
    filas = []
    for f in publica.to_dict("records"):
        p = textos.loc[f["passage_id"]]
        fila = {**f, **{c: "" for c in EXTRAS}}
        fila.update(fuentes=f["fuentes"], en_marca=f["fin"] <= p.inicio_cuerpo,
                    version_extractor=version, texto_normalizado="".join(c for c in
                    unicodedata.normalize("NFD", f["texto"].lower()) if
                    unicodedata.category(c) != "Mn"))
        if f["metodo"] in {"modelo", "ambos"}:
            fila.update(modelo_id=modelo, modelo_revision=revision,
                        puntaje_modelo=puntajes.get(tuple(f[k] for k in
                        ["passage_id", "tipo", "inicio", "fin"]), ""))
        if f["tipo"] in {"ORG", "LOC"}:
            fila["canonico"] = equivalencias.get(f["texto"].casefold(), "")
            fila["estado_identidad"] = "verificada" if fila["canonico"] else "sin_equivalencia"
        elif f["tipo"] == "MONTO":
            fila.update(monto_auxiliar(f["texto"], p.texto[max(0, f["inicio"]-60):f["fin"]+60]))
        elif f["tipo"] == "FECHA":
            fila.update(fecha_auxiliar(f["texto"], str(p.fecha)[:10]))
        filas.append(fila)
    import pandas as pd

    from mtx.fusion import COLUMNAS

    return pd.DataFrame(filas, columns=COLUMNAS + EXTRAS)
