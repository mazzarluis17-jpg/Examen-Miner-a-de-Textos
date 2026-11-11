"""H8: respuestas conservadoras con evidencia literal, sin reextraer entidades."""

import hashlib
import itertools
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

import pandas as pd

COLUMNAS = [
    "query_id",
    "campo_respuesta",
    "valor",
    "unidad",
    "relacion",
    "estado",
    "passage_id",
    "doc_id",
    "fecha_documento",
    "evidencia_inicio",
    "evidencia_fin",
    "cita",
    "entidades_referencia",
    "regla_relacion",
    "grupo_evento",
    "interlocutor",
]
ESTADOS = {"respaldado_en_texto", "ambiguo", "contradictorio", "no_encontrado"}
PRIORIDAD = {"respaldado_en_texto": 0, "contradictorio": 1, "ambiguo": 2, "no_encontrado": 3}


def normalizar(texto):
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFD", str(texto).lower())
            if unicodedata.category(c) != "Mn"
        ).split()
    )


def decimal_estable(valor):
    try:
        n = Decimal(str(valor))
        return format(n.normalize(), "f") if n.is_finite() else ""
    except InvalidOperation:
        return ""


def oraciones(texto):
    limites = [0, *[m.end() for m in re.finditer(r"[.!?]+(?=\s|$)", texto)]]
    if limites[-1] != len(texto):
        limites.append(len(texto))
    return [(a, b) for a, b in itertools.pairwise(limites) if a < b]


def contexto(texto, inicio, fin, radio=60):
    """Unión de ±60 caracteres y oraciones inmediatamente contiguas, sin reescribir."""
    segmentos = oraciones(texto)
    i = next(i for i, (a, b) in enumerate(segmentos) if a <= inicio < b)
    j = next(i for i, (a, b) in enumerate(segmentos) if a < fin <= b)
    a = min(max(0, inicio - radio), segmentos[max(0, i - 1)][0])
    b = max(min(len(texto), fin + radio), segmentos[min(len(segmentos) - 1, j + 1)][1])
    return a, b, texto[a:b]


def cargar_listas(raiz, politica):
    estados = pd.read_csv(raiz / "config/gazetteer_loc.csv", keep_default_na=False).iloc[:32]
    empresas = pd.read_csv(raiz / "kit/gazetteer_dependencias.csv", keep_default_na=False)
    empresas = empresas[empresas.tipo.map(normalizar).eq("organizacion empresarial")]
    listas = {"farmaceuticas": {normalizar(v) for v in politica["farmaceuticas"]}}
    for nombre, tabla in [
        ("entidades_federativas", estados),
        ("organizaciones_empresariales", empresas),
    ]:
        valores = set()
        for f in tabla.to_dict("records"):
            for campo in ["nombre", "siglas", "variantes"]:
                valores.update(normalizar(t) for t in str(f.get(campo, "")).split("|") if t)
        listas[nombre] = valores
    return listas


def validar_politica(politica, consultas):
    if politica.get("modelo") != "bm25_con_filtro" or politica.get("contexto_caracteres") != 60:
        raise ValueError("Política H8 distinta del ganador/contexto autorizados")
    if set(politica["consultas"]) != set(consultas.query_id):
        raise ValueError("Faltan consultas en el mapa H8")
    for f in consultas.itertuples():
        q = politica["consultas"][f.query_id]
        if q["pregunta"] != f.pregunta_extraccion or not q["campos"] or not q["anclas"]:
            raise ValueError("Pregunta o campos distintos de consultas congeladas")
        for patron in q["anclas"]:
            re.compile(patron)
        for campo in q["campos"].values():
            if (
                not campo["patrones_contexto"]
                or not campo["relacion"]
                or not campo.get("patrones_vinculo")
            ):
                raise ValueError("Campo sin contrato de relación")
            for patron in campo["patrones_contexto"]:
                re.compile(patron)
            for patron in campo["patrones_vinculo"]:
                if "{valor}" not in patron:
                    raise ValueError("El vínculo debe referirse al valor exacto")
                re.compile(patron.replace("{valor}", "entidad"))


def seleccionar(fila, especificacion, listas):
    if fila["tipo"] != especificacion["tipo"]:
        return False
    filtro = especificacion.get("filtro", "")
    if filtro.startswith("unidad:"):
        return normalizar(fila.get("unidad", "")) == filtro.split(":", 1)[1]
    if filtro:
        return any(
            normalizar(fila.get(c, "")) in listas[filtro]
            for c in ["texto", "canonico", "texto_normalizado"]
        )
    return True


def preparar_candidatos(entidades, auxiliares, pasajes, ranking, exclusiones):
    """Filtra copias en memoria; registra exclusiones antes de agrupar o mapear."""
    pares = set(zip(ranking.query_id, ranking.passage_id))
    p = pasajes.set_index("passage_id")
    candidatos, contadores = (
        [],
        {(q, m): 0 for q in ranking.query_id.unique() for m in ["marca", "lista"]},
    )
    for origen, tabla in [
        ("entidades_enriquecidas", entidades),
        ("cantidades_auxiliares", auxiliares),
    ]:
        for f in tabla.to_dict("records"):
            f = dict(f)
            if (f["query_id"], f["passage_id"]) not in pares:
                raise ValueError("Entrada H7 fuera del top-10 ganador")
            a, b = int(f["inicio"]), int(f["fin"])
            psg = p.loc[f["passage_id"]]
            if not 0 <= a < b <= len(psg.texto) or psg.texto[a:b] != f["texto"]:
                raise ValueError("Offsets H7 incompatibles; no se corrigen desde H8")
            f.update(inicio=a, fin=b, tipo=f.get("tipo", f.get("tipo_aux")), origen=origen)
            if b <= int(psg.inicio_cuerpo):
                contadores[(f["query_id"], "marca")] += 1
                continue
            if f["tipo"] == "PER" and normalizar(f["texto"]) in exclusiones:
                contadores[(f["query_id"], "lista")] += 1
                continue
            candidatos.append(f)
    conteos = pd.DataFrame(
        [[q, m, n] for (q, m), n in sorted(contadores.items())], columns=["query_id", "motivo", "n"]
    )
    return candidatos, conteos


def tokens_globales(pasajes):
    """Reconstruye solo posiciones de tokens ya recuperados para deduplicar ventanas."""
    mapas = {}
    for f in pasajes.itertuples():
        clave = (str(f.doc_id), str(f.intervencion_id))
        mapa = mapas.setdefault(clave, {})
        for i, tok in enumerate(re.findall(r"\S+", f.texto[int(f.inicio_cuerpo) :])):
            posicion = int(f.token_inicio) + i
            if posicion in mapa and mapa[posicion] != tok:
                raise ValueError("Ventanas solapadas con tokens incompatibles")
            mapa[posicion] = tok
    return mapas


def fase_evento(texto, inicio, fin):
    """No confunde pagos anteriores/nuevos o propuestas/anuncios cercanos al valor."""
    patrones = {
        "anterior": r"antes|anterior|previo|recib[ií]an|era|eran",
        "nuevo": r"ahora|nuevo|nueva|recibir[aá]n|ser[aá]n?|a partir",
        "propuesta": r"propon|propuest|solicit",
        "anuncio": r"anunci|aprobad|acordad",
    }
    a, b = max(0, inicio - 60), min(len(texto), fin + 60)
    centro = (inicio + fin) / 2
    opciones = [
        (abs(a + m.start() - centro), fase)
        for fase, pat in patrones.items()
        for m in re.finditer(r"\b(?:" + pat + r")\w*", texto[a:b].lower())
    ]
    return min(opciones)[1] if opciones else "sin_fase_explicita"


def evento(pasaje, fila, mapas, unidad, fase):
    base = int(pasaje.inicio_cuerpo)
    locales = list(re.finditer(r"\S+", pasaje.texto[base:]))
    posicion = int(pasaje.token_inicio) + sum(t.end() <= fila["inicio"] - base for t in locales)
    mapa = mapas[(str(pasaje.doc_id), str(pasaje.intervencion_id))]
    anteriores = [i + 1 for i, tok in mapa.items() if i < posicion and re.search(r"[.!?]$", tok)]
    inicio = max(anteriores) if anteriores else min(mapa)
    datos = [
        fila["query_id"],
        str(pasaje.doc_id),
        str(pasaje.intervencion_id),
        inicio,
        unidad,
        fase,
    ]
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False).encode()).hexdigest()[:20]


def oracion_del_span(texto, inicio, fin):
    segmentos = oraciones(texto)
    i = next(i for i, (a, b) in enumerate(segmentos) if a <= inicio < b)
    j = next(i for i, (a, b) in enumerate(segmentos) if a < fin <= b)
    return texto[segmentos[i][0] : segmentos[j][1]]


def ancla_local(texto, fila, consulta, cita):
    propia = oracion_del_span(texto, fila["inicio"], fila["fin"]).lower()
    if any(re.search(p, propia) for p in consulta["anclas"]):
        return True
    return bool(
        re.search(
            r"\b(?:este|esta|estas|estos)\s+(?:proyecto|obra|programa|corredor|vacunas|dosis|pensi[oó]n|sucursales|refiner[ií]a|aeropuerto)",
            propia,
        )
    ) and any(re.search(p, cita.lower()) for p in consulta["anclas"])


def limites_inequivocos(fila, texto, elegibles):
    a, b = fila["inicio"], fila["fin"]
    if (a > 0 and texto[a - 1].isalnum() and texto[a].isalnum()) or (
        b < len(texto) and texto[b - 1].isalnum() and texto[b].isalnum()
    ):
        return False
    if any(
        e["passage_id"] == fila["passage_id"]
        and e["tipo"] == fila["tipo"]
        and e["inicio"] <= a
        and b <= e["fin"]
        and (e["inicio"], e["fin"]) != (a, b)
        for e in elegibles
    ):
        return False
    return not (
        fila["tipo"] in {"CANTIDAD", "MONTO"}
        and re.search(r"\b\d[\d,.]*\s+$", texto[max(0, a - 20) : a])
    )


def relacion_directa(fila, elegibles, especificacion, consulta, a, cita, texto):
    """Ancla y patrón requeridos; un patrón de otra entidad no se transfiere."""
    if not ancla_local(texto, fila, consulta, cita) or not limites_inequivocos(
        fila, texto, elegibles
    ):
        return ""
    propia = oracion_del_span(texto, fila["inicio"], fila["fin"])
    if re.search(
        r"\b(?:no|nunca|tampoco)\s+(?:\w+\s+){0,2}(?:particip|constru|opera|paga|entreg)",
        propia.lower(),
    ):
        return ""
    cercano = texto[max(0, fila["inicio"] - 60) : fila["fin"] + 60].lower()
    if any(re.search(p, cercano) for p in especificacion.get("contextos_competidores", [])):
        return ""
    vinculos = [
        i
        for i, p in enumerate(especificacion["patrones_vinculo"])
        if re.search(p.replace("{valor}", re.escape(fila["texto"])), propia, re.IGNORECASE)
    ]
    if not vinculos:
        return ""
    for numero, patron in enumerate(especificacion["patrones_contexto"]):
        for coincidencia in re.finditer(patron, cita.lower()):
            punto = a + (coincidencia.start() + coincidencia.end()) / 2
            distancia = lambda e, centro=punto: abs((e["inicio"] + e["fin"]) / 2 - centro)
            cercanas = [
                e
                for e in elegibles
                if e["passage_id"] == fila["passage_id"]
                and e["inicio"] < a + len(cita)
                and e["fin"] > a
            ]
            if distancia(fila) <= min(map(distancia, cercanas), default=float("inf")):
                return f"patron_{numero + 1}:{patron};vinculo_{vinculos[0] + 1}"
    return ""


def generar_respuestas(
    entidades, auxiliares, pasajes, ranking, consultas, politica, exclusiones, listas
):
    validar_politica(politica, consultas)
    candidatos, conteos = preparar_candidatos(
        entidades, auxiliares, pasajes, ranking, {normalizar(v) for v in exclusiones}
    )
    p = pasajes.set_index("passage_id")
    mapas = tokens_globales(pasajes)
    filas = []
    for q in consultas.query_id:
        especificacion_q = politica["consultas"][q]
        por_consulta = [f for f in candidatos if f["query_id"] == q]
        for campo, especificacion in especificacion_q["campos"].items():
            elegibles = [f for f in por_consulta if seleccionar(f, especificacion, listas)]
            if not elegibles:
                vacia = dict.fromkeys(COLUMNAS, "")
                vacia.update(
                    query_id=q,
                    campo_respuesta=campo,
                    estado="no_encontrado",
                    relacion=especificacion["relacion"],
                )
                filas.append(vacia)
            for f in elegibles:
                pasaje = p.loc[f["passage_id"]]
                a, b, cita = contexto(pasaje.texto, f["inicio"], f["fin"])
                patron = relacion_directa(
                    f, elegibles, especificacion, especificacion_q, a, cita, pasaje.texto
                )
                pregunta = bool(pasaje.es_reportero) or "¿" in oracion_del_span(
                    pasaje.texto, f["inicio"], f["fin"]
                )
                fase = fase_evento(pasaje.texto, f["inicio"], f["fin"])
                acto = (
                    "pregunta"
                    if pregunta
                    else "anuncio"
                    if fase in {"nuevo", "anuncio"}
                    else "respuesta"
                )
                unidad = especificacion.get("unidad") or f.get("moneda", "")
                estado = "respaldado_en_texto" if patron and not pregunta else "ambiguo"
                sentido = ""
                if campo in {"perdidas", "litros"}:
                    cerca = pasaje.texto[max(0, f["inicio"] - 60) : f["fin"] + 60].lower()
                    recupera = bool(re.search(r"recuper|rescat|decomis", cerca))
                    robo = bool(re.search(r"rob|perd|sustra", cerca))
                    sentido = (
                        "; recuperación"
                        if recupera and not robo
                        else "; robo/pérdida"
                        if robo and not recupera
                        else "; sentido no inequívoco"
                    )
                    if recupera == robo:
                        estado = "ambiguo"
                identidad = (
                    f.get("canonico") or f.get("texto_normalizado") or normalizar(f["texto"])
                )
                refs = [
                    {
                        "rol": "principal",
                        "origen": f["origen"],
                        "tipo": f["tipo"],
                        "clave_valor": normalizar(identidad),
                        "texto": f["texto"],
                        "inicio": f["inicio"],
                        "fin": f["fin"],
                    }
                ]
                for e in por_consulta:
                    if (
                        e["passage_id"] == f["passage_id"]
                        and a <= e["inicio"] < e["fin"] <= b
                        and e != f
                    ):
                        refs.append(
                            {
                                "rol": "apoyo",
                                "origen": e["origen"],
                                "tipo": e["tipo"],
                                "texto": e["texto"],
                                "inicio": e["inicio"],
                                "fin": e["fin"],
                            }
                        )
                grupo = evento(pasaje, f, mapas, unidad, fase)
                numerico = decimal_estable(f.get("valor_num", ""))
                comparar = (
                    numerico
                    if f["tipo"] in {"MONTO", "CANTIDAD", "PORCENTAJE"}
                    else f.get("fecha_iso", "")
                )
                filas.append(
                    {
                        "query_id": q,
                        "campo_respuesta": campo,
                        "valor": f["texto"],
                        "unidad": unidad,
                        "relacion": f"{acto}; {especificacion['relacion']}; {fase}{sentido}",
                        "estado": estado,
                        "passage_id": f["passage_id"],
                        "doc_id": str(pasaje.doc_id),
                        "fecha_documento": str(pasaje.fecha)[:10],
                        "evidencia_inicio": a,
                        "evidencia_fin": b,
                        "cita": cita,
                        "entidades_referencia": json.dumps(
                            refs, ensure_ascii=False, sort_keys=True
                        ),
                        "regla_relacion": f"{q}.{campo}.{patron}"
                        if patron
                        else "sin_patron_de_relacion",
                        "grupo_evento": grupo,
                        "interlocutor": pasaje.interlocutor,
                        "_clave": normalizar(identidad),
                        "_comparar": comparar,
                        "_exclusivo": especificacion.get("exclusivo", False),
                    }
                )
    brutas = pd.DataFrame(filas)
    for nombre, defecto in [("_exclusivo", False), ("_comparar", ""), ("_clave", "")]:
        if nombre not in brutas:
            brutas[nombre] = defecto
    # Solo valores comparables del mismo evento y campo exclusivo; unidades/fases ya separadas.
    comparables = brutas[
        (brutas.estado.eq("respaldado_en_texto"))
        & brutas._exclusivo.fillna(False).astype(bool)
        & brutas._comparar.fillna("").ne("")
    ]
    for _, grupo in comparables.groupby(["query_id", "campo_respuesta", "grupo_evento"]):
        if grupo._comparar.nunique() > 1:
            brutas.loc[grupo.index, "estado"] = "contradictorio"
    agregados = []
    for (q, campo, clave), grupo in brutas[brutas.estado.ne("no_encontrado")].groupby(
        ["query_id", "campo_respuesta", "_clave"], sort=True
    ):
        agregados.append(
            {
                "query_id": q,
                "campo_respuesta": campo,
                "clave_valor": clave,
                "frecuencia_total": len(grupo),
                "n_pasajes_distintos": grupo.passage_id.nunique(),
                "n_discursos_distintos": grupo.doc_id.nunique(),
                "n_eventos_distintos": grupo.grupo_evento.nunique(),
            }
        )
    agregados = pd.DataFrame(
        agregados,
        columns=[
            "query_id",
            "campo_respuesta",
            "clave_valor",
            "frecuencia_total",
            "n_pasajes_distintos",
            "n_discursos_distintos",
            "n_eventos_distintos",
        ],
    )
    brutas["_orden"] = brutas.estado.map(PRIORIDAD)
    brutas = brutas.sort_values(
        ["query_id", "campo_respuesta", "_orden", "doc_id", "passage_id", "evidencia_inicio"]
    )
    deduplicadas = brutas.drop_duplicates(["query_id", "campo_respuesta", "_clave", "grupo_evento"])
    resultado = deduplicadas[COLUMNAS].fillna("").reset_index(drop=True)
    auditoria = brutas[COLUMNAS].fillna("").reset_index(drop=True)
    return resultado, conteos, agregados, auditoria


def validar_respuestas(
    tabla, pasajes, ranking, politica, entidades=None, auxiliares=None, listas=None, exclusiones=()
):
    errores = []
    if list(tabla.columns) != COLUMNAS:
        return ["Columnas de respuestas incorrectas"]
    pares = set(zip(ranking.query_id, ranking.passage_id))
    p = pasajes.set_index("passage_id")
    claves = set()
    referencias = set()
    candidatos = []
    if entidades is not None:
        candidatos, _ = preparar_candidatos(
            entidades, auxiliares, pasajes, ranking, {normalizar(v) for v in exclusiones}
        )
        for origen, fuente in [
            ("entidades_enriquecidas", entidades),
            ("cantidades_auxiliares", auxiliares),
        ]:
            for f in fuente.to_dict("records"):
                referencias.add(
                    (
                        f["query_id"],
                        f["passage_id"],
                        origen,
                        f.get("tipo", f.get("tipo_aux")),
                        f["texto"],
                        int(f["inicio"]),
                        int(f["fin"]),
                    )
                )
    for f in tabla.itertuples():
        if (
            f.estado not in ESTADOS
            or f.query_id not in politica["consultas"]
            or f.campo_respuesta not in politica["consultas"][f.query_id]["campos"]
        ):
            errores.append("Estado, consulta o campo inválido")
            continue
        claves.add((f.query_id, f.campo_respuesta))
        if f.estado == "no_encontrado":
            if any(
                str(getattr(f, c))
                for c in [
                    "valor",
                    "passage_id",
                    "doc_id",
                    "fecha_documento",
                    "cita",
                    "evidencia_inicio",
                    "evidencia_fin",
                    "entidades_referencia",
                ]
            ):
                errores.append("Fila no_encontrado contiene evidencia o valor")
            continue
        try:
            a, b = int(f.evidencia_inicio), int(f.evidencia_fin)
            pasaje = p.loc[f.passage_id]
            assert (f.query_id, f.passage_id) in pares
            assert 0 <= a < b <= len(pasaje.texto) and pasaje.texto[a:b] == f.cita
            assert f.valor and str(f.doc_id) == str(pasaje.doc_id)
            assert (
                f.interlocutor == pasaje.interlocutor
                and f.fecha_documento == str(pasaje.fecha)[:10]
            )
            refs = json.loads(f.entidades_referencia)
            principales = [e for e in refs if e["rol"] == "principal"]
            assert len(principales) == 1 and principales[0]["texto"] == f.valor
            for e in refs:
                assert (
                    a <= e["inicio"] < e["fin"] <= b
                    and pasaje.texto[e["inicio"] : e["fin"]] == e["texto"]
                )
                assert e["fin"] > int(pasaje.inicio_cuerpo)
                if referencias:
                    assert (
                        f.query_id,
                        f.passage_id,
                        e["origen"],
                        e["tipo"],
                        e["texto"],
                        e["inicio"],
                        e["fin"],
                    ) in referencias
            if f.estado in {"respaldado_en_texto", "contradictorio"}:
                assert f.regla_relacion != "sin_patron_de_relacion" and not bool(
                    pasaje.es_reportero
                )
                if entidades is not None:
                    especificacion = politica["consultas"][f.query_id]["campos"][f.campo_respuesta]
                    elegibles = [
                        e
                        for e in candidatos
                        if e["query_id"] == f.query_id
                        and seleccionar(e, especificacion, listas or {})
                    ]
                    principal = next(
                        e
                        for e in elegibles
                        if e["passage_id"] == f.passage_id
                        and e["texto"] == f.valor
                        and e["inicio"] == principales[0]["inicio"]
                        and e["fin"] == principales[0]["fin"]
                    )
                    regla = relacion_directa(
                        principal,
                        elegibles,
                        especificacion,
                        politica["consultas"][f.query_id],
                        a,
                        f.cita,
                        pasaje.texto,
                    )
                    assert regla and f.regla_relacion == f"{f.query_id}.{f.campo_respuesta}.{regla}"
                    assert "¿" not in oracion_del_span(
                        pasaje.texto, principal["inicio"], principal["fin"]
                    )
        except (AssertionError, ValueError, KeyError, TypeError, StopIteration):
            errores.append(f"Evidencia inválida: {f.query_id}/{f.campo_respuesta}/{f.passage_id}")
    esperadas = {(q, c) for q, v in politica["consultas"].items() for c in v["campos"]}
    if claves != esperadas:
        errores.append("Cobertura incompleta de consultas/campos")
    return errores


def hash_tabla(contenido):
    """Contenido técnico anterior al bloque humano, sin hash autorreferente."""
    return hashlib.sha256(contenido.split("\nvaloracion:\n", 1)[0].encode()).hexdigest()


def validar_valoraciones(valoraciones, hashes):
    errores = []
    for q, h in hashes.items():
        entrada = valoraciones.get(q, {})
        if (
            not isinstance(entrada, dict)
            or not isinstance(entrada.get("valoracion"), str)
            or not entrada["valoracion"].strip()
            or "[VALIDAR]" in entrada["valoracion"]
        ):
            errores.append(f"{q}: [VALIDAR] pendiente del alumno")
        elif entrada.get("tabla_sha256") != h:
            errores.append(f"{q}: valoración invalidada por cambio de tabla")
    return errores


def escapar(valor):
    return str(valor).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def renderizar_tablas(respuestas, consultas, politica, exclusiones, agregados, valoraciones):
    """El corte de ocho se aplica solo a Markdown; todo el detalle queda en CSV."""
    tablas, hashes, pendientes = {}, {}, []
    for q in consultas.itertuples():
        filas = respuestas[respuestas.query_id.eq(q.query_id)]
        hdatos = hashlib.sha256(filas.to_csv(index=False, lineterminator="\n").encode()).hexdigest()
        ex = exclusiones[exclusiones.query_id.eq(q.query_id)].set_index("motivo").n.to_dict()
        lineas = [
            f"# {q.query_id} — {q.pregunta_extraccion}",
            "",
            f"Consulta: {q.consulta}",
            "",
            f"Modelo: {politica['modelo']}; ventana: {q.desde} a {q.hasta}.",
            f"Exclusiones: marca {ex.get('marca', 0)}; lista PER {ex.get('lista', 0)}.",
            "Respaldado en texto significa que el corpus lo afirma, no que sea verdad.",
            "Frecuencias y eventos independientes: `salida/10_agregados.csv`.",
            f"Huella de evidencia completa: `{hdatos}`.",
        ]
        for campo in politica["consultas"][q.query_id]["campos"]:
            grupo = filas[filas.campo_respuesta.eq(campo)]
            lineas += [
                "",
                f"## {campo}",
                "",
                "| Valor | Tipo o rol | Estado | Pasaje | Fecha del discurso | Cita breve |",
                "|---|---|---|---|---|---|",
            ]
            valores = []
            grupo = grupo.copy()
            grupo["_clave_render"] = grupo.apply(
                lambda f: (
                    json.loads(f.entidades_referencia)[0].get("clave_valor", normalizar(f.valor))
                    if f.estado != "no_encontrado"
                    else ""
                ),
                axis=1,
            )
            for clave, sub in grupo.groupby("_clave_render", sort=False):
                total = agregados[
                    (agregados.query_id.eq(q.query_id))
                    & agregados.campo_respuesta.eq(campo)
                    & agregados.clave_valor.eq(clave)
                ]
                n_doc = int(total.iloc[0].n_discursos_distintos) if len(total) else 0
                orden = sub.estado.map(PRIORIDAD).min()
                primero = sub.assign(_orden=sub.estado.map(PRIORIDAD)).sort_values("_orden").iloc[0]
                valores.append((orden, -n_doc, str(primero.valor), primero))
            for _, _, valor, f in sorted(valores, key=lambda t: t[:3])[
                : politica["max_valores_tabla"]
            ]:
                if f.estado == "no_encontrado":
                    lineas.append("| Sin evidencia en el top-10 | — | no_encontrado | — | — | — |")
                else:
                    refs = json.loads(f.entidades_referencia)
                    tipo = next(e["tipo"] for e in refs if e["rol"] == "principal")
                    # La cita CSV se conserva completa; la tabla muestra un extracto alrededor del valor.
                    posicion = f.cita.find(valor)
                    inicio = max(0, posicion - 55)
                    fin = min(len(f.cita), max(posicion + len(valor) + 55, inicio + 120))
                    breve = (
                        ("…" if inicio else "")
                        + f.cita[inicio:fin]
                        + ("…" if fin < len(f.cita) else "")
                    )
                    lineas.append(
                        "| "
                        + " | ".join(
                            map(
                                escapar,
                                [
                                    valor,
                                    tipo + "; " + f.relacion,
                                    f.estado,
                                    f.passage_id,
                                    f.fecha_documento,
                                    breve,
                                ],
                            )
                        )
                        + " |"
                    )
        cuerpo = "\n".join(lineas) + "\n"
        h = hash_tabla(cuerpo)
        hashes[q.query_id] = h
        fallos = validar_valoraciones(
            {q.query_id: valoraciones.get(q.query_id, {})}, {q.query_id: h}
        )
        pendientes.extend(fallos)
        texto = (
            valoraciones[q.query_id]["valoracion"]
            if not fallos
            else "[VALIDAR] pendiente del alumno"
        )
        tablas[q.query_id] = cuerpo + "\nvaloracion:\n" + texto + "\n"
    return tablas, hashes, pendientes
