"""Demo reproducible de una de las diez consultas oficiales."""
import argparse

from mtx.demo import cargar, mostrar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--q", default="Q3")
    parser.add_argument("--consulta")
    args = parser.parse_args()
    q = args.q
    if args.consulta:
        coincidencias = cargar()["consultas"].loc[lambda d: d.consulta == args.consulta]
        if len(coincidencias) != 1:
            parser.error("Esta entrega reproduce únicamente las diez consultas congeladas; "
                         "no ejecuta un experimento nuevo ni inferencia en caliente.")
        q = coincidencias.iloc[0].query_id
    mostrar(q)


if __name__ == "__main__":
    main()
