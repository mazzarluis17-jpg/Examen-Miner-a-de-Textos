"""05 · Ejecuta evaluación oficial de rankings congelados y selecciona ganador D08."""
from mtx import config, evaluacion


def main():
    """No genera juicios ni rankings: valida, evalúa y audita sus versiones actuales."""
    ganador = evaluacion.ejecutar_ir(config.RAIZ)
    print(f"Ganador global: {ganador['modelo']} · MAP={ganador['MAP']:.4f}")
    print("Resultados oficiales: resultados_ir.csv; vista temporal complementaria en salida/.")


if __name__ == "__main__":
    main()
