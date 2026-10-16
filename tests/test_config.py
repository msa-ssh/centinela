import pytest

from centinela.config import leer_config

CONFIG_VALIDA = """
timeout_segundos = 10

[[sitio]]
nombre = "Web"
url = "https://example.com"
"""


def test_config_valida(tmp_path):
    ruta = tmp_path / "config.toml"
    ruta.write_text(CONFIG_VALIDA, encoding="utf-8")
    config = leer_config(ruta)
    assert config["timeout_segundos"] == 10
    assert config["sitio"] == [{"nombre": "Web", "url": "https://example.com"}]


def test_config_falta_sale_con_1(tmp_path):
    with pytest.raises(SystemExit) as salida:
        leer_config(tmp_path / "no-existe.toml")
    assert salida.value.code == 1


def test_config_mal_formada_sale_con_1(tmp_path):
    ruta = tmp_path / "config.toml"
    ruta.write_text("timeout_segundos = \n", encoding="utf-8")
    with pytest.raises(SystemExit) as salida:
        leer_config(ruta)
    assert salida.value.code == 1
