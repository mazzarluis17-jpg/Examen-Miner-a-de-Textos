"""Normalización prudente: nunca altera spans ni inventa fechas relativas."""

import re
from datetime import date

from mtx.reglas import MESES, PALABRAS


def normalizar_numero(texto):
    """Escalas habladas; billón español = 10**12; punto de miles ambiguo."""
    t = texto.lower().replace("$", "").strip()
    m = re.match(r"[\d,.]+|\w+", t)
    if not m:
        return None, "no_resoluble"
    if re.fullmatch(r"\d{1,3}\.\d{3}", m[0]):
        return None, "ambiguo"
    numeros = dict(zip(PALABRAS, [1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]))
    total = 0.0
    for token in re.findall(r"\d[\d,.]*|[a-záéíóú]+", t):
        if token == "mil":
            total = (total or 1) * 1000
        elif token in {"millón", "millones", "billón", "billones"}:
            total = (total or 1) * (10**12 if token.startswith("bill") else 10**6)
        elif token in numeros:
            total += numeros[token]
        elif token[0].isdigit():
            total += float(token.replace(",", ""))
        else:
            break
    return total, "resuelto"


def normalizar_fecha(texto):
    """ISO absoluto; años de dos dígitos y relativos quedan sin resolver."""
    t = texto.lower()
    salida = {"fecha_iso": None, "precision": None, "estado_normalizacion": "no_resoluble"}
    if re.fullmatch(r"\d{4}", t):
        return {"fecha_iso": t, "precision": "anio", "estado_normalizacion": "resuelto"}
    if t.startswith(("del ", "próximo ", "pasado ", "este ")):
        return salida
    dia, mes, anio = None, None, None
    if "/" in t:
        partes = t.split("/")
        dia, mes = map(int, partes[:2])
        if len(partes[2]) != 4:
            return salida
        anio = int(partes[2])
    else:
        for i, nombre in enumerate(MESES, 1):
            if nombre in t:
                mes = i
                break
        m = re.search(r"^(primero|\d{1,2}) de ", t)
        dia = (1 if m[1] == "primero" else int(m[1])) if m else None
        m = re.search(r"\b(\d{4})$", t)
        anio = int(m[1]) if m else None
    if mes is None:
        return salida
    try:
        date(anio or 2000, mes, dia if dia is not None else 1)
    except ValueError:
        salida["estado_normalizacion"] = "fecha_invalida"
        return salida
    if anio is None:
        return salida
    iso = f"{anio:04}-{mes:02}" + (f"-{dia:02}" if dia is not None else "")
    return {
        "fecha_iso": iso,
        "precision": "dia" if dia is not None else "mes",
        "estado_normalizacion": "resuelto",
    }


def normalizar_monto(texto):
    """Símbolo $ sin denominación es ambiguo; no se asume moneda nacional."""
    valor, estado = normalizar_numero(texto)
    t = texto.lower()
    moneda = "MXN" if "pesos" in t else "USD" if "dólares" in t or "dolares" in t else None
    return {
        "valor_num": valor,
        "moneda": moneda,
        "estado_normalizacion": estado if moneda or estado != "resuelto" else "moneda_ambigua",
    }
