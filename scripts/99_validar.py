"""Valida contratos de entrega sin cambiar archivos congelados ni decisiones humanas."""
import argparse
import json

from mtx.entrega import RAIZ
from mtx.validacion_entrega import verificar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permitir-pendientes", action="store_true",
                        help="Valida lo técnico y enumera cierres humanos pendientes")
    args = parser.parse_args()
    resultado = verificar()
    destino = RAIZ / "salida/11_validacion_entrega.json"
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if resultado["pendiente"] and not args.permitir_pendientes:
        raise SystemExit("Entrega aún no cerrada: consultar los pendientes del informe.")


if __name__ == "__main__":
    main()
