"""Configuraciones posteriores H8 no alteran ni invalidan insumos existentes D15."""

import subprocess

import pytest

from mtx.gold import verificar_d15


def git(raiz, *args):
    return subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


def test_config_nueva_compatible_sin_debilitar_archivos_congelados(tmp_path):
    git(tmp_path, "init")
    (tmp_path / "config").mkdir()
    original = tmp_path / "config/criterios_anotacion.md"
    original.write_text("Fixture sintética congelada")
    git(tmp_path, "add", "config")
    git(
        tmp_path,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "Fixture",
    )
    git(tmp_path, "tag", "reglas-congeladas")
    (tmp_path / "config/tablas_respuesta.yaml").write_text("politica: h8")
    git(tmp_path, "add", "config/tablas_respuesta.yaml")
    git(
        tmp_path,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "Política H8 de fixture",
    )
    verificar_d15(tmp_path)
    original.write_text("Modificación indebida")
    with pytest.raises(ValueError, match="Insumos distintos"):
        verificar_d15(tmp_path)
    original.unlink()
    with pytest.raises(ValueError, match="Insumos distintos"):
        verificar_d15(tmp_path)
