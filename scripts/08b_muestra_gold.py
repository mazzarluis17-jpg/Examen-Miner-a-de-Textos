"""Verifica manifiesto; la creación se realiza exclusivamente desde la app."""

import hashlib

from mtx.ambito_ie import cargar_ambito
from mtx.app.gazetteer import congelado
from mtx.config import RAIZ
from mtx.muestreo import sortear_muestra

if __name__ == "__main__":
    try:
        if not congelado(RAIZ):
            raise ValueError("Pendiente D15: make congelar antes de muestra-gold")
        ranking, pasajes = cargar_ambito(RAIZ)
        ruta = RAIZ / "anotaciones/muestra_gold.csv"
        if not ruta.exists():
            raise ValueError(
                "Pendiente preparar muestra desde Gold en make app. No se escribe desde CLI."
            )
        esperada = (
            sortear_muestra(ranking, pasajes).to_csv(index=False, lineterminator="\n").encode()
        )
        if hashlib.sha256(ruta.read_bytes()).digest() != hashlib.sha256(esperada).digest():
            raise ValueError("Muestra obsoleta: conservar y revisar; no sobrescribir")
        print("Muestra válida: reproducible, sin leer gold ni predicciones.")
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc))
