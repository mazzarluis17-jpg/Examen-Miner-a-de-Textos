"""Verifica prerrequisitos humanos y técnicos antes de crear reglas-congeladas."""

import subprocess

from mtx.config import RAIZ
from mtx.congelacion import verificar_congelacion

if __name__ == "__main__":
    try:
        verificar_congelacion(RAIZ)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc))
    subprocess.run(
        [
            "git",
            "tag",
            "-a",
            "reglas-congeladas",
            "-m",
            "Reglas, gazetteers y convenciones congelados antes del gold",
        ],
        cwd=RAIZ,
        check=True,
    )
