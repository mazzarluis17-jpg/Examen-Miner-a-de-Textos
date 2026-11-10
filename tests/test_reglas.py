"""T11 · Ejemplos sintéticos del PRD; nunca anotaciones humanas."""

import pytest

from mtx.normalizacion import normalizar_fecha, normalizar_numero
from mtx.reglas import (
    Entidad,
    cargar_gazetteers,
    extraer_auxiliares,
    extraer_con_auditoria,
    extraer_reglas,
    minar_siglas,
    resolver_colisiones,
)

FECHAS = [
    "15 de diciembre de 2023",
    "primero de enero de 2020",
    "1 de septiembre del 2021",
    "enero de 2021",
    "diciembre del 2019",
    "15/12/2023",
    "1/1/19",
    "próximo 15 de enero",
    "pasado 20 de noviembre",
    "este 1 de julio",
    "diciembre de 2021",
    "del 1 al 15 de enero de 2021",
    "31 de febrero",
]
MONTOS = [
    "20 mil millones de pesos",
    "2 mil 500 millones de pesos",
    "1,200 millones de pesos",
    "$1,200 millones",
    "$ 5 mil",
    "5 mil pesos",
    "500 pesos",
    "2 mil millones de dólares",
    "100 millones de dólares",
    "1.5 billones de pesos",
    "6 mil 300 pesos",
    "mil 200 pesos",
    "un millón de pesos",
    "dos mil millones de pesos",
    "1500 pesos",
]


@pytest.mark.parametrize(
    "tipo,span", [("FECHA", f) for f in FECHAS] + [("MONTO", m) for m in MONTOS]
)
def test_positivos_exactos(tipo, span):
    texto = "😀 se anuncia el " + span + " hoy."
    entidades = [e for e in extraer_reglas(texto, 0) if e.tipo == tipo]
    assert [e.texto for e in entidades] == [span]
    assert all(texto[e.inicio : e.fin] == e.texto for e in entidades)


@pytest.mark.parametrize(
    "texto",
    [
        "15 personas",
        "página 15",
        "2 horas",
        "15 de los 32 estados",
        "15 de cada 100",
        "2019",
        "20 mil personas",
        "15 millones de dosis",
        "3 millones de árboles",
        "20 por ciento",
        "20%",
        "página 20",
    ],
)
def test_negativos(texto):
    assert not [e for e in extraer_reglas(texto, 0) if e.tipo in {"FECHA", "MONTO"}]


@pytest.mark.parametrize("prefijo", ["en ", "el año ", "desde "])
def test_anio_contextual(prefijo):
    assert [e.texto for e in extraer_reglas(prefijo + "2019", 0)] == ["2019"]


@pytest.mark.parametrize(
    "texto,iso,estado",
    [
        ("15 de diciembre de 2023", "2023-12-15", "resuelto"),
        ("enero de 2021", "2021-01", "resuelto"),
        ("2019", "2019", "resuelto"),
        ("31 de febrero", None, "fecha_invalida"),
        ("1/1/19", None, "no_resoluble"),
        ("31 de febrero de 2020", None, "fecha_invalida"),
        ("próximo 15 de enero", None, "no_resoluble"),
    ],
)
def test_normalizar_fecha(texto, iso, estado):
    n = normalizar_fecha(texto)
    assert n["fecha_iso"] == iso
    assert n["estado_normalizacion"] == estado


@pytest.mark.parametrize(
    "texto,valor",
    [
        ("2 mil 500 millones de pesos", 2500000000),
        ("6 mil 300 pesos", 6300),
        ("mil 200 pesos", 1200),
        ("un millón de pesos", 1000000),
        ("dos mil millones de pesos", 2000000000),
        ("1.5 billones de pesos", 1500000000000),
    ],
)
def test_valores_monto(texto, valor):
    assert normalizar_numero(texto) == (valor, "resuelto")


def test_ambiguedad():
    assert normalizar_numero("1.200 pesos") == (None, "ambiguo")


@pytest.mark.parametrize(
    "texto,valor,unidad",
    [
        ("20%", 20, "porcentaje"),
        ("20 por ciento", 20, "porcentaje"),
        ("3.5 por ciento", 3.5, "porcentaje"),
        ("15 millones de dosis", 15000000, "dosis"),
        ("100 mil litros", 100000, "litros"),
        ("30 mil elementos", 30000, "elementos"),
        ("200 mil sembradores", 200000, "sembradores"),
        ("10 sucursales", 10, "sucursales"),
        ("10 hectáreas", 10, "hectáreas"),
        ("10 beneficiarios", 10, "beneficiarios"),
        ("10 kilómetros", 10, "kilómetros"),
    ],
)
def test_auxiliares(texto, valor, unidad):
    assert not extraer_reglas(texto, 0)
    (a,) = extraer_auxiliares(texto)
    assert a["texto"] == texto and a["valor_num"] == valor and a["unidad"] == unidad


@pytest.mark.parametrize(
    "texto,tipo",
    [
        ("Tren Maya", "LOC"),
        ("Dos Bocas", "LOC"),
        ("Ciudad de México", "LOC"),
        ("Secretaría de Salud de Tabasco", "ORG"),
        ("Johnson & Johnson", "ORG"),
        ("PAN", "ORG"),
        ("IMSS", "ORG"),
    ],
)
def test_gazetteer(texto, tipo):
    (e,) = extraer_reglas(texto, 0)
    assert (e.texto, e.tipo) == (texto, tipo)


def test_siglas_limites():
    assert not extraer_reglas("pan sat IMSSá áIMSS", 0)
    assert [e.texto for e in extraer_reglas("SEDENA: ", 8)] == ["SEDENA"]


def test_gazetteer_entradas_obligatorias():
    obligatorias = [
        "IMSS",
        "ISSSTE",
        "Pemex",
        "CFE",
        "Sedena",
        "Semar",
        "Conagua",
        "Fonatur",
        "Insabi",
        "Cofepris",
        "Birmex",
        "Pfizer",
        "AstraZeneca",
        "CanSino",
        "COVAX",
        "Coparmex",
        "CCE",
        "Concanaco",
        "Conasami",
        "Morena",
        "PAN",
        "PRI",
        "PRD",
        "ONU",
        "OMS",
        "OPS",
        "FMI",
        "Banxico",
        "SAT",
        "STPS",
        "SICT",
        "Sener",
        "Sedatu",
        "ICA",
    ]
    obligatorias += [
        "Sputnik V",
        "Banco Mundial",
        "Guardia Nacional",
        "Secretaría del Bienestar",
        "Grupo Carso",
    ]
    nombres = {e[0] for e in cargar_gazetteers()}
    assert set(obligatorias) <= nombres


@pytest.mark.parametrize(
    "marca,persona",
    [
        ("SECRETARIO DE SALUD, JORGE ALCOCER VARELA: ", "JORGE ALCOCER VARELA"),
        ("PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR: ", "ANDRÉS MANUEL LÓPEZ OBRADOR"),
        ("PREGUNTA: ", None),
        ("INTERLOCUTOR: ", None),
        ("INTERLOCUTORA: ", None),
    ],
)
def test_marca(marca, persona):
    e = [e for e in extraer_reglas(marca + "cuerpo", len(marca)) if e.tipo == "PER"]
    assert [x.texto for x in e] == ([persona] if persona else [])
    assert all(x.en_marca and x.fuente == "marca" for x in e)


def test_colisiones():
    fecha = Entidad("FECHA", "abc", 0, 3, fuente="regex_fecha")
    monto = Entidad("MONTO", "abc", 0, 3, fuente="regex_monto")
    assert resolver_colisiones([monto, fecha])[0] == [fecha]
    texto = "Secretaría de Salud de Tabasco"
    entidades, auditoria = extraer_con_auditoria(texto, 0)
    assert len(entidades) == 1 and auditoria
    assert all(c["ganadora"]["texto"] == texto for c in auditoria)


def test_mineria_no_usa_marca():
    filas = [
        {"texto": "MARCA IGNORADA: Instituto de Prueba (IP) IMSS IMSS pan", "inicio_cuerpo": 16}
    ]
    r = minar_siglas(filas)
    assert "MARCA" not in {x["sigla"] for x in r}
    assert next(x for x in r if x["sigla"] == "IMSS")["frecuencia"] == 2
    assert next(x for x in r if x["sigla"] == "IP")["nombre_propuesto"] == "Instituto de Prueba"


@pytest.mark.lento
def test_offsets_200_pasajes_reales():
    import pandas as pd

    from mtx.config import PASAJES_PARQUET

    if not PASAJES_PARQUET.exists():
        pytest.skip("Recuperar corpus H1 antes de integración")
    pasajes = pd.read_parquet(PASAJES_PARQUET).sample(n=200, random_state=42)
    total = 0
    for fila in pasajes.itertuples():
        for e in extraer_reglas(fila.texto, int(fila.inicio_cuerpo)):
            assert 0 <= e.inicio < e.fin <= len(fila.texto)
            assert fila.texto[e.inicio : e.fin] == e.texto
            total += 1
    assert total > 0


def test_moneda_no_inferida_desde_simbolo():
    from mtx.normalizacion import normalizar_monto

    assert normalizar_monto("$500")["moneda"] is None
    assert normalizar_monto("500 pesos")["moneda"] == "MXN"
    assert normalizar_monto("2 mil millones de dólares")["valor_num"] == 2000000000


def test_marca_no_confunde_cargo_como_persona():
    marca = "JORGE ALCOCER VARELA, SECRETARIO DE SALUD: "
    assert not [e for e in extraer_reglas(marca, len(marca)) if e.tipo == "PER"]
    (org,) = extraer_reglas("IMSS: cuerpo", 6)
    assert org.en_marca and org.fuente == "marca"
