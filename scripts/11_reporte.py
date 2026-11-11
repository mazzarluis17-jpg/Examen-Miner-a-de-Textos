"""Compila el borrador académico sin regenerar ni aprobar prosa."""
import argparse

from mtx.reporte import compilar, generar_figura

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figuras", action="store_true", help="Reexporta solo la figura editorial H9")
    args = parser.parse_args()
    if args.figuras:
        generar_figura()
    compilar()
