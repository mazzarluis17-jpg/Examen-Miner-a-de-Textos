"""T12 · Pipeline sintético offline; nunca usa anotaciones ni caché del repo."""

import itertools
import re
from copy import deepcopy
from types import SimpleNamespace

import pytest

from mtx.config import cargar_yaml
from mtx.ner_modelo import clave_cache, fragmentar, inferir_crudo, posprocesar, procesar_pasaje


class Tokenizador:
    """Un subtoken por palabra en el fixture."""

    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, texto, **kwargs):
        offsets = [(m.start(), m.end()) for m in re.finditer(r"\S+", texto)]
        return {"offset_mapping": offsets, "input_ids": list(range(len(offsets)))}


class Predictor:
    tokenizer = Tokenizador()
    model = SimpleNamespace(
        config=SimpleNamespace(
            id2label={0: "B-PERSON", 1: "I-PERSON", 2: "B-GPE", 3: "B-MISC", 4: "B-ORG"}
        )
    )

    def __init__(self):
        self.llamadas = 0

    def __call__(self, textos, **kwargs):
        self.llamadas += 1
        salida = []
        for t in textos:
            filas = []
            for palabra, etiqueta in [("López", "PERSON"), ("Madrid", "GPE"), ("Obra", "MISC")]:
                for m in re.finditer(palabra, t):
                    filas.append(
                        {
                            "entity_group": etiqueta,
                            "score": 0.8,
                            "word": palabra,
                            "start": m.start(),
                            "end": m.end(),
                        }
                    )
            salida.append(filas)
        return salida


@pytest.fixture
def p():
    return cargar_yaml("ner.yaml")["modelos"][0].copy()


def test_ventanas_cobertura_ultima_cola_y_limite():
    texto = "  😀 " + "palabra " * 1200 + " final  "
    ventanas = fragmentar(texto, Tokenizador(), 16, 4)
    assert ventanas[0][0] == 0 and ventanas[-1][1] == len(texto)
    assert all(b >= c for (a, b), (c, d) in itertools.pairwise(ventanas))
    assert all(len(Tokenizador()(texto[a:b])["input_ids"]) <= 14 for a, b in ventanas)
    assert fragmentar(" ", Tokenizador(), 16, 4) == [(0, 1)]
    with pytest.raises(ValueError):
        fragmentar(texto, Tokenizador(), 16, 14)


def test_etiquetas_y_descarte(p):
    crudas, descartadas = inferir_crudo("López Madrid Obra", Predictor(), p)
    assert [(e["tipo"], e["texto"]) for e in crudas] == [("PER", "López"), ("LOC", "Madrid")]
    assert descartadas == 1
    predictor = Predictor()
    predictor.model = SimpleNamespace(config=SimpleNamespace(id2label={0: "B-ORG"}))
    with pytest.raises(ValueError, match="id2label"):
        inferir_crudo("López", predictor, p)


def test_recorte_union_e_invariante():
    texto = "😀 (López Obrador), $500"
    crudas = [
        {"tipo": "PER", "texto": texto[2:8], "inicio": 2, "fin": 8, "confianza": 0.8},
        {"tipo": "PER", "texto": texto[9:18], "inicio": 9, "fin": 18, "confianza": 0.9},
        {"tipo": "ORG", "texto": texto[19:], "inicio": 19, "fin": len(texto), "confianza": 0.6},
    ]
    # Los límites son sintéticos sobre el texto original, incluida puntuación.
    entidades, uniones = posprocesar(texto, crudas, "prueba")
    assert entidades[0]["texto"] == "López Obrador"
    assert entidades[1]["texto"] == "$500"
    assert len(uniones) == 1 and uniones[0]["texto_union"] == "López Obrador"
    assert all(texto[e["inicio"] : e["fin"]] == e["texto"] for e in entidades)
    assert crudas[0]["texto"] == "(López"
    roto = deepcopy(crudas)
    roto[0]["texto"] = "otro"
    with pytest.raises(ValueError):
        posprocesar(texto, roto)


def test_union_intrapalabra():
    texto = "López"
    crudas = [
        {"tipo": "PER", "texto": texto[a:b], "inicio": a, "fin": b, "confianza": 0.9}
        for a, b in [(0, 2), (2, 5)]
    ]
    entidades, uniones = posprocesar(texto, crudas)
    assert entidades[0]["texto"] == texto and not uniones


def test_t12_prioridad_borde_y_deduplicacion(p):
    class Borde(Predictor):
        def __call__(self, textos, **kwargs):
            salida = []
            for t in textos:
                filas = []
                for m in re.finditer("López", t):
                    filas.append(
                        {
                            "entity_group": "PERSON",
                            "start": m.start(),
                            "end": m.end(),
                            "score": 0.99 if m.end() == len(t) else 0.5,
                            "word": "irrelevante",
                        }
                    )
                salida.append(filas)
            return salida

    p.update(max_length_real=6, solapamiento=2)
    texto = "uno dos tres López cinco seis siete ocho nueve"
    crudas, _ = inferir_crudo(texto, Borde(), p)
    assert len(crudas) == 1
    assert crudas[0]["confianza"] == 0.5 and not crudas[0]["cortada"]


def test_cache_sin_cargar_modelo_y_version_posproceso(tmp_path, p):
    predictor = Predictor()
    procesar_pasaje("López", "1_0", p, tmp_path, lambda: predictor)
    assert predictor.llamadas == 1
    p["version_posproceso"] = "2"

    def prohibido():
        pytest.fail("No debe cargar pesos en acierto de caché")

    entidades, _, _datos, acierto = procesar_pasaje("López", "1_0", p, tmp_path, prohibido)
    assert acierto and entidades[0]["texto"] == "López"
    procesar_pasaje("López", "1_0", p, tmp_path, lambda: predictor, forzar=True)
    assert predictor.llamadas == 2
    for campo, valor in [("revision", "a" * 40), ("solapamiento", 32), ("max_length_real", 256)]:
        otro = p.copy()
        otro[campo] = valor
        assert clave_cache("López", p) != clave_cache("López", otro)
    assert clave_cache("López", p) != clave_cache("Otro", p)
    with pytest.raises(ValueError):
        procesar_pasaje("López", "../ruta", p, tmp_path, prohibido)
