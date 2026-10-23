import re

import pytest

import centinela.__main__ as programa
from centinela import __version__


def test_la_version_sigue_el_versionado_semantico():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_version_muestra_la_version_y_no_lee_nada(monkeypatch, capsys):
    monkeypatch.setattr(programa.sys, "argv", ["centinela", "--version"])
    monkeypatch.setattr(programa, "cargar_config", lambda: pytest.fail("no debe leer .env"))

    programa.main()

    assert capsys.readouterr().out == f"Centinela {__version__}\n"
