"""Extracción determinista sobre caracteres canónicos (PRD §6.7)."""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from mtx.config import RAIZ


@dataclass
class Entidad:
    """Span semiabierto; texto siempre tomado del pasaje original."""

    tipo: str
    texto: str
    inicio: int
    fin: int
    metodo: str = "regla"
    fuente: str = ""
    en_marca: bool = False


MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]
MES = "(?:" + "|".join(MESES) + ")"
DIA = r"(?:primero|[0-3]?\d)"
FECHA = re.compile(
    rf"(?<!\w)(?:del\s+{DIA}\s+al\s+{DIA}\s+de\s+{MES}"
    rf"(?:\s+de[l]?\s+\d{{4}})?|(?:(?:próximo|pasado|este)\s+)?{DIA}\s+de\s+{MES}"
    rf"(?:\s+de[l]?\s+\d{{4}})?|{MES}\s+de[l]?\s+\d{{4}}|\d{{1,2}}/\d{{1,2}}/\d{{2,4}})(?!\w)",
    re.IGNORECASE,
)
ANIO = re.compile(r"\b(?:en|desde|el año|de|a)\s+(?P<anio>(?:19|20)\d{2})(?!\w)", re.IGNORECASE)
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
PALABRAS = [
    "un",
    "una",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "cien",
]
CIFRA = rf"(?:(?:{NUM}|{'|'.join(PALABRAS)})(?:\s+mil(?!\w)(?:\s+(?:{NUM}))?)?|mil(?!\w)(?:\s+(?:{NUM}))?)"
ESCALA = r"(?:\s+(?:millones|millón|billones|billón))?"
MONEDA = r"\s+(?:de\s+)?(?:pesos|dólares|dolares)"
IZQ = r"(?<![\w$.,])"
MONTO = re.compile(
    rf"{IZQ}(?:\$\s?{CIFRA}{ESCALA}(?:{MONEDA})?|{CIFRA}{ESCALA}{MONEDA})(?!\w)", re.IGNORECASE
)
PORCENTAJE = re.compile(rf"{IZQ}(?:{NUM})\s*(?:por\s+ciento|%)(?!\w)", re.IGNORECASE)
CANTIDAD = re.compile(
    rf"{IZQ}{CIFRA}{ESCALA}\s+(?:de\s+)?(?P<unidad>dosis|litros|elementos|sucursales|hectáreas|beneficiarios|sembradores|kilómetros)(?!\w)",
    re.IGNORECASE,
)
PRIORIDAD = {
    f: i
    for i, f in enumerate(["regex_fecha", "regex_monto", "gazetteer_loc", "gazetteer_org", "marca"])
}
CARGOS = re.compile(
    r"^(?:PRESIDENT[EA]|SECRETARI[OA]|SUBSECRETARI[OA]|DIRECTOR[ÁA]? GENERAL|GOBERNADOR[ÁA]?)\s+",
    re.IGNORECASE,
)


@lru_cache
def cargar_gazetteers(raiz: Path = RAIZ):
    """Base inmutable, entradas prescritas y extensión solo cuando existe."""
    entradas = []
    for ruta in [
        raiz / "kit/gazetteer_dependencias.csv",
        raiz / "config/gazetteer_prescrito.csv",
        raiz / "config/gazetteer_loc.csv",
        raiz / "config/gazetteer_extendido.csv",
    ]:
        if not ruta.exists():
            continue
        with ruta.open(encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                tipo = fila.get("etiqueta") or ("LOC" if fila["tipo"] == "obra" else "ORG")
                if tipo not in {"ORG", "LOC"}:
                    raise ValueError("Etiqueta inválida del gazetteer")
                for campo in ("nombre", "variantes", "siglas"):
                    for nombre in fila.get(campo, "").split("|"):
                        if nombre.strip():
                            entradas.append((nombre.strip(), tipo, campo == "siglas"))
    return tuple(sorted(set(entradas), key=lambda x: (-len(x[0]), x)))


def resolver_colisiones(entidades):
    """Devuelve ganadoras y auditoría determinista de cada supresión."""
    elegidas, colisiones = [], []
    unicas = {(e.tipo, e.inicio, e.fin, e.fuente): e for e in entidades}
    for entidad in sorted(
        unicas.values(), key=lambda e: (-(e.fin - e.inicio), PRIORIDAD[e.fuente], e.inicio, e.texto)
    ):
        ganadora = next(
            (g for g in elegidas if entidad.inicio < g.fin and g.inicio < entidad.fin), None
        )
        if ganadora:
            colisiones.append({"ganadora": asdict(ganadora), "suprimida": asdict(entidad)})
        else:
            elegidas.append(entidad)
    return sorted(elegidas, key=lambda e: (e.inicio, e.fin, e.tipo)), colisiones


def extraer_con_auditoria(texto: str, inicio_cuerpo: int, entradas=None):
    """Reglas y supresiones; no modifica ni normaliza el texto fuente."""
    if not 0 <= inicio_cuerpo <= len(texto):
        raise ValueError("inicio_cuerpo fuera del pasaje")
    candidatas = []

    def agregar(tipo, inicio, fin, fuente):
        candidatas.append(
            Entidad(
                tipo, texto[inicio:fin], inicio, fin, fuente=fuente, en_marca=inicio < inicio_cuerpo
            )
        )

    for patron, tipo, fuente in [(FECHA, "FECHA", "regex_fecha"), (MONTO, "MONTO", "regex_monto")]:
        for m in patron.finditer(texto):
            agregar(tipo, m.start(), m.end(), fuente)
    for m in ANIO.finditer(texto):
        agregar("FECHA", m.start("anio"), m.end("anio"), "regex_fecha")
    entradas = cargar_gazetteers() if entradas is None else entradas
    for nombre, tipo, sigla in entradas:
        sensible = sigla and len(nombre) <= 5
        patron = re.compile(
            r"(?<!\w)" + re.escape(nombre) + r"(?!\w)", 0 if sensible else re.IGNORECASE
        )
        for m in patron.finditer(texto):
            agregar(
                tipo,
                m.start(),
                m.end(),
                "marca"
                if m.end() <= inicio_cuerpo and tipo == "ORG"
                else "gazetteer_" + tipo.lower(),
            )
        if sensible:
            for m in re.finditer(
                r"(?<!\w)" + re.escape(nombre.upper()) + r"(?!\w)", texto[:inicio_cuerpo]
            ):
                agregar(tipo, m.start(), m.end(), "marca")
    # Solo lugares conocidos, sin consumir palabras arbitrarias tras "de".
    for lugar, tipo, _sigla in entradas:
        if tipo != "LOC":
            continue
        patron = r"(?<!\w)" + re.escape("Secretaría de Salud de " + lugar) + r"(?!\w)"
        for m in re.finditer(patron, texto, re.IGNORECASE):
            agregar(
                "ORG", m.start(), m.end(), "marca" if m.end() <= inicio_cuerpo else "gazetteer_org"
            )
    marca = texto[:inicio_cuerpo].rstrip(": ")
    inicio = marca.rfind(",") + 1 if "," in marca else 0
    candidato = marca[inicio:].strip()
    if "," not in marca:
        candidato = CARGOS.sub("", candidato)
    palabras = candidato.split()
    if (
        (candidato != marca or "," in marca)
        and 2 <= len(palabras) <= 5
        and not CARGOS.match(candidato)
        and all(re.fullmatch(r"[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü-]*", p) for p in palabras)
    ):
        inicio = marca.rfind(candidato)
        agregar("PER", inicio, inicio + len(candidato), "marca")
    return resolver_colisiones(candidatas)


def extraer_reglas(texto: str, inicio_cuerpo: int) -> list[Entidad]:
    """API pública del PRD §6.7.9."""
    return extraer_con_auditoria(texto, inicio_cuerpo)[0]


def extraer_auxiliares(texto: str):
    """Cantidades ajenas a los cinco tipos oficiales; offsets originales."""
    from mtx.normalizacion import normalizar_numero

    filas = []
    for patron, tipo in [(PORCENTAJE, "PORCENTAJE"), (CANTIDAD, "CANTIDAD")]:
        for m in patron.finditer(texto):
            unidad = "porcentaje" if tipo == "PORCENTAJE" else m.group("unidad").lower()
            valor, estado = normalizar_numero(m.group())
            filas.append(
                {
                    "texto": m.group(),
                    "inicio": m.start(),
                    "fin": m.end(),
                    "tipo_aux": tipo,
                    "valor_num": valor,
                    "unidad": unidad,
                    "estado_normalizacion": estado,
                    "regla_id": tipo.lower() + "_v1",
                }
            )
    return filas


def minar_siglas(pasajes, stoplist=()):
    """Solo candidatos del cuerpo; ninguna aceptación automática."""
    conteos, ejemplos, nombres = Counter(), {}, {}
    stoplist = {s.upper() for s in stoplist}
    for fila in pasajes:
        cuerpo = fila["texto"][fila["inicio_cuerpo"] :]
        for m in re.finditer(r"\b[A-ZÁÉÍÓÚÑ]{3,7}\b", cuerpo):
            sigla = m.group()
            if sigla not in stoplist:
                conteos[sigla] += 1
                ejemplos.setdefault(sigla, cuerpo[max(0, m.start() - 80) : m.end() + 80])
        patron = r"((?:[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+(?:de|del|la|los|y))?\s+){1,7}[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)\s*\(([A-Z]{2,8})\)"
        for m in re.finditer(patron, cuerpo):
            nombres.setdefault(m[2], m[1])
            if m[2] not in conteos:
                conteos[m[2]] = 1
                ejemplos[m[2]] = m.group()
    return [
        {
            "sigla": s,
            "nombre_propuesto": nombres.get(s, ""),
            "frecuencia": conteos[s],
            "ejemplo": ejemplos[s],
        }
        for s in sorted(conteos, key=lambda s: (-conteos[s], s))
    ]
