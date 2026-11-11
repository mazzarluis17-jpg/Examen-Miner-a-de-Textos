"""T14 y contratos H8, exclusivamente con textos y entidades sintéticos."""

import hashlib

import pandas as pd
import pytest

from mtx.respuestas import (
    COLUMNAS,
    contexto,
    generar_respuestas,
    hash_tabla,
    preparar_candidatos,
    renderizar_tablas,
    validar_respuestas,
    validar_valoraciones,
)


def construir(
    texto,
    valores,
    tipo="ORG",
    patron="particip",
    ancla="proyecto",
    reportero=False,
    exclusivo=False,
):
    p = pd.DataFrame(
        [
            {
                "passage_id": "1_0",
                "doc_id": 1,
                "fecha": "2021-01-01",
                "texto": texto,
                "inicio_cuerpo": 0,
                "intervencion_id": "1_i0",
                "token_inicio": 0,
                "token_fin": len(texto.split()),
                "interlocutor": "REPORTERO" if reportero else "FUNCIONARIA",
                "es_reportero": reportero,
            }
        ]
    )
    filas = []
    desde = 0
    for t in valores:
        a = texto.index(t, desde)
        desde = a + len(t)
        filas.append(
            {
                "query_id": "Q1",
                "passage_id": "1_0",
                "tipo": tipo,
                "texto": t,
                "inicio": a,
                "fin": a + len(t),
                "canonico": "",
                "texto_normalizado": t.lower(),
                "moneda": "MXN" if tipo == "MONTO" else "",
                "valor_num": t.split()[0] if tipo == "MONTO" else "",
                "fecha_iso": "",
            }
        )
    entidades = pd.DataFrame(
        filas,
        columns=[
            "query_id",
            "passage_id",
            "tipo",
            "texto",
            "inicio",
            "fin",
            "canonico",
            "texto_normalizado",
            "moneda",
            "valor_num",
            "fecha_iso",
        ],
    )
    aux = pd.DataFrame(
        columns=["query_id", "passage_id", "tipo_aux", "texto", "inicio", "fin", "unidad"]
    )
    rank = pd.DataFrame([{"query_id": "Q1", "passage_id": "1_0", "doc_id": 1}])
    consultas = pd.DataFrame(
        [
            {
                "query_id": "Q1",
                "pregunta_extraccion": "Pregunta de prueba",
                "consulta": "Consulta",
                "desde": "2020-01-01",
                "hasta": "2022-01-01",
            }
        ]
    )
    politica = {
        "modelo": "bm25_con_filtro",
        "contexto_caracteres": 60,
        "max_valores_tabla": 8,
        "consultas": {
            "Q1": {
                "pregunta": "Pregunta de prueba",
                "anclas": [ancla],
                "campos": {
                    "campo": {
                        "tipo": tipo,
                        "filtro": "",
                        "patrones_contexto": [patron],
                        "patrones_vinculo": [
                            r"(?:" + patron + r")[^.!?]{0,65}{valor}",
                            r"{valor}[^.!?]{0,65}(?:" + patron + r")",
                        ],
                        "relacion": "relación de prueba",
                        "exclusivo": exclusivo,
                        "unidad": "",
                    }
                },
            }
        },
    }
    return entidades, aux, p, rank, consultas, politica


def ejecutar(datos):
    return generar_respuestas(*datos, [], {})


def test_t14_reportero_no_atribuido_y_coocurrencia_ambigua():
    d = construir(
        "¿Banco Alfa dispone de 100 pesos y Banco Beta de 200 pesos para el proyecto?",
        ["Banco Alfa", "Banco Beta"],
        reportero=True,
    )
    antes = d[0].copy(deep=True)
    r, _, _, _ = ejecutar(d)
    assert r.estado.eq("ambiguo").all()
    assert r.interlocutor.eq("REPORTERO").all() and r.relacion.str.startswith("pregunta;").all()
    pd.testing.assert_frame_equal(d[0], antes)


def test_exclusiones_solo_per_y_marca():
    texto = "ANA: Andrés Manuel López Obrador y Banco Alfa en México."
    d = construir(texto, ["ANA", "Andrés Manuel López Obrador", "Banco Alfa", "México"])
    ent = d[0].copy()
    ent.loc[0, "tipo"] = "PER"
    ent.loc[1, "tipo"] = "PER"
    ent.loc[3, "tipo"] = "LOC"
    p = d[2].copy()
    p.loc[0, "inicio_cuerpo"] = 5
    h = hashlib.sha256(ent.to_csv(index=False).encode()).hexdigest()
    c, n = preparar_candidatos(ent, d[1], p, d[3], {"andres manuel lopez obrador"})
    assert [f["texto"] for f in c] == ["Banco Alfa", "México"]
    assert (
        n.set_index("motivo").loc["marca", "n"] == 1
        and n.set_index("motivo").loc["lista", "n"] == 1
    )
    assert hashlib.sha256(ent.to_csv(index=False).encode()).hexdigest() == h
    ent.loc[1, "tipo"] = "ORG"
    assert any(
        f["texto"] == "Andrés Manuel López Obrador"
        for f in preparar_candidatos(ent, d[1], p, d[3], {"andres manuel lopez obrador"})[0]
    )


def test_ventanas_solapadas_no_son_confirmaciones_independientes():
    d = list(construir("Banco Alfa participa en proyecto.", ["Banco Alfa"]))
    d[0] = pd.concat([d[0], d[0].assign(passage_id="1_1")], ignore_index=True)
    d[2] = pd.concat([d[2], d[2].assign(passage_id="1_1")], ignore_index=True)
    d[3] = pd.concat([d[3], d[3].assign(passage_id="1_1")], ignore_index=True)
    r, _, a, e = ejecutar(d)
    assert len(r) == 1 and len(e) == 2
    assert a.iloc[0].n_pasajes_distintos == 2 and a.iloc[0].n_discursos_distintos == 1
    assert a.iloc[0].n_eventos_distintos == 1 and a.iloc[0].frecuencia_total == 2


@pytest.mark.parametrize(
    "texto,patron,estado",
    [
        ("Pensión adultos mayores: pago 100 pesos.", "bimestr", "ambiguo"),
        ("Pensión adultos mayores: pago bimestral 100 pesos.", "bimestr", "respaldado_en_texto"),
        ("Salario mínimo diario de 100 pesos.", "diari|al día", "respaldado_en_texto"),
        (
            "Sembrando Vida paga 100 pesos mensuales por beneficiario.",
            "mensual|por beneficiario",
            "respaldado_en_texto",
        ),
    ],
)
def test_periodicidad_solo_con_evidencia(texto, patron, estado):
    d = construir(
        texto, ["100 pesos"], tipo="MONTO", patron=patron, ancla="pensión|salario|sembrando vida"
    )
    assert ejecutar(d)[0].iloc[0].estado == estado


def test_presupuesto_no_recibe_relacion_de_pago_individual():
    texto = (
        "Sembrando Vida tiene presupuesto de 100 pesos y paga 200 pesos mensuales por beneficiario."
    )
    d = construir(
        texto,
        ["100 pesos", "200 pesos"],
        tipo="MONTO",
        patron="mensual|por beneficiario",
        ancla="sembrando vida",
    )
    r = ejecutar(d)[0].set_index("valor")
    assert r.loc["100 pesos", "estado"] == "ambiguo"
    assert r.loc["200 pesos", "estado"] == "respaldado_en_texto"


def test_contradicciones_mismo_evento_sin_resolver_por_mayoria():
    d = construir(
        "Pensión bimestral de 100 pesos, pago bimestral de 200 pesos.",
        ["100 pesos", "200 pesos"],
        tipo="MONTO",
        patron="bimestr",
        ancla="pensión",
        exclusivo=True,
    )
    r = ejecutar(d)[0]
    assert r.estado.eq("contradictorio").all() and r.grupo_evento.nunique() == 1


def test_pagos_anteriores_y_nuevos_no_se_contradicen():
    d = construir(
        "Pensión bimestral antes de 100 pesos, bimestral ahora de 200 pesos.",
        ["100 pesos", "200 pesos"],
        tipo="MONTO",
        patron="bimestr",
        ancla="pensión",
        exclusivo=True,
    )
    assert "contradictorio" not in set(ejecutar(d)[0].estado)


def test_contrato_evidencia_16_columnas_y_no_encontrado():
    d = construir("El proyecto continúa.", [])
    r = ejecutar(d)[0]
    assert list(r.columns) == COLUMNAS and r.iloc[0].estado == "no_encontrado"
    assert not validar_respuestas(r, d[2], d[3], d[5], d[0], d[1])
    r.loc[0, "valor"] = "inventado"
    assert validar_respuestas(r, d[2], d[3], d[5], d[0], d[1])


def test_offsets_validos_y_tampering_detectado():
    d = construir("Banco Alfa participa en proyecto.", ["Banco Alfa"])
    r = ejecutar(d)[0]
    assert not validar_respuestas(r, d[2], d[3], d[5], d[0], d[1])
    r.loc[0, "cita"] = "cita alterada"
    assert validar_respuestas(r, d[2], d[3], d[5], d[0], d[1])


def test_contexto_limita_a_radio_y_oraciones_contiguas():
    texto = "Lejano. Anterior. Entidad presente. Siguiente. Fuera."
    a, b, c = contexto(texto, texto.index("Entidad"), texto.index("Entidad") + 7, radio=0)
    assert c == texto[a:b] and "Lejano" not in c and "Fuera" not in c
    assert "Anterior" in c and "Siguiente" in c


def test_auxiliares_conservan_unidad_y_no_se_inyectan_en_entidades():
    d = list(
        construir(
            "Vacunación: llegaron 100 dosis.", [], tipo="CANTIDAD", patron="llegaron", ancla="vacun"
        )
    )
    texto = d[2].iloc[0].texto
    a = texto.index("100 dosis")
    d[1] = pd.DataFrame(
        [
            {
                "query_id": "Q1",
                "passage_id": "1_0",
                "tipo_aux": "CANTIDAD",
                "texto": "100 dosis",
                "inicio": a,
                "fin": a + 9,
                "unidad": "dosis",
                "valor_num": "100",
            }
        ]
    )
    d[5]["consultas"]["Q1"]["campos"]["campo"].update(filtro="unidad:dosis", unidad="dosis")
    r = ejecutar(d)[0]
    assert r.iloc[0].valor == "100 dosis" and r.iloc[0].unidad == "dosis" and d[0].empty


def test_corte_ocho_solo_en_markdown_y_hash_no_depende_de_opinion():
    nombres = [f"Empresa{i:02}" for i in range(11)]
    texto = ", ".join(nombres) + " participan en el proyecto."
    d = construir(texto, nombres)
    r, n, a, _ = ejecutar(d)
    tablas, h, pend = renderizar_tablas(r, d[4], d[5], n, a, {})
    assert (
        len(r) == 11
        and sum(line.startswith("| Empresa") for line in tablas["Q1"].splitlines()) == 8
        and len(pend) == 1
    )
    assert hash_tabla(tablas["Q1"]) == h["Q1"]
    humanos = {"Q1": {"tabla_sha256": h["Q1"], "valoracion": "Opinión ficticia de fixture."}}
    tablas2, h2, pend2 = renderizar_tablas(r, d[4], d[5], n, a, humanos)
    assert not pend2 and h2 == h and tablas2 != tablas
    assert validar_valoraciones(humanos, {"Q1": "otro hash"})
    assert validar_valoraciones({"Q1": {"valoracion": ""}}, h)


def test_determinismo_y_fuentes_no_modificadas():
    d = construir("Banco Alfa participa en proyecto.", ["Banco Alfa"])
    assert ejecutar(d)[0].to_csv(index=False) == ejecutar(d)[0].to_csv(index=False)


def test_medio_mencionado_no_prueba_participacion():
    d = construir(
        "El medio Diario Alfa comenta el proyecto de construcción.",
        ["Diario Alfa"],
        patron="constru",
        ancla="proyecto",
    )
    d[5]["consultas"]["Q1"]["campos"]["campo"]["patrones_vinculo"] = [
        r"{valor}[^.!?]{0,30}(?:construye|participa)"
    ]
    assert ejecutar(d)[0].iloc[0].estado == "ambiguo"


def test_ancla_en_otra_oracion_no_transfiere_relacion_sin_anafora():
    d = construir(
        "Se informó del proyecto. Banco Alfa participa en otra actividad.", ["Banco Alfa"]
    )
    assert ejecutar(d)[0].iloc[0].estado == "ambiguo"


def test_negacion_y_fragmento_quedan_ambiguos_sin_cambiar_entidades():
    d = construir("Banco Alfa no participa en el proyecto.", ["Banco Alfa"])
    assert ejecutar(d)[0].iloc[0].estado == "ambiguo"
    d = construir("Banco Alfa participa en el proyecto.", ["anco Alfa"])
    assert ejecutar(d)[0].iloc[0].estado == "ambiguo"
    assert ejecutar(d)[0].iloc[0].valor == "anco Alfa"


def test_falso_respaldado_es_detectado_por_validador():
    d = construir("Banco Alfa menciona el proyecto.", ["Banco Alfa"])
    r = ejecutar(d)[0]
    r.loc[0, "estado"] = "respaldado_en_texto"
    r.loc[0, "regla_relacion"] = "regla_inventada"
    assert validar_respuestas(r, d[2], d[3], d[5], d[0], d[1])


def test_solape_real_con_offsets_locales_diferentes():
    completo = "Presentación breve. Banco Alfa participa en el proyecto común. Despedida."
    d = list(construir(completo, ["Banco Alfa"]))
    segundo = " ".join(completo.split()[2:])
    e = d[0].copy()
    e["passage_id"] = "1_1"
    e["inicio"] = 0
    e["fin"] = len("Banco Alfa")
    p = d[2].copy()
    p["passage_id"] = "1_1"
    p["texto"] = segundo
    p["token_inicio"] = 2
    d[0] = pd.concat([d[0], e], ignore_index=True)
    d[2] = pd.concat([d[2], p], ignore_index=True)
    d[3] = pd.concat([d[3], d[3].assign(passage_id="1_1")], ignore_index=True)
    r, _, a, _ = ejecutar(d)
    assert len(r) == 1 and a.iloc[0].n_eventos_distintos == 1
    assert a.iloc[0].n_pasajes_distintos == 2


def test_alias_solo_se_agrupa_con_canonico_verificado():
    d = construir("Banco Alfa e IA participan en el proyecto.", ["Banco Alfa", "IA"])
    assert len(ejecutar(d)[0]) == 2
    d[0]["canonico"] = "Entidad canónica de fixture"
    r, _, a, evidencia = ejecutar(d)
    assert len(r) == 1 and len(evidencia) == 2 and len(a) == 1


def test_unidades_diferentes_no_son_contradiccion():
    d = construir(
        "Pensión bimestral de 100 pesos, pago bimestral de 200 dólares.",
        ["100 pesos", "200 dólares"],
        tipo="MONTO",
        patron="bimestr",
        ancla="pensión",
        exclusivo=True,
    )
    d[0].loc[1, "moneda"] = "USD"
    assert "contradictorio" not in set(ejecutar(d)[0].estado)
