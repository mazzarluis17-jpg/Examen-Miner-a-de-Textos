"""Propone alcance léxico para revisión humana, sin aceptar ni rechazar siglas."""
from mtx.alcance_gazetteer import preparar
from mtx.config import RAIZ

if __name__ == "__main__":
    informe = preparar(RAIZ)
    print(f"Propuesta: {informe['propuestos']} de {informe['originales']}; pendiente aprobación.")
