import pytest

from centinela.config import cargar_smtp, leer_config

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

    
SMTP_ENV = {
    "SMTP_SERVIDOR": "smtp.example.com",
    "SMTP_PUERTO": "587",
    "SMTP_USUARIO": "centinela@example.com",
    "SMTP_CLAVE": "clave-secreta",
}


def poner_smtp(monkeypatch, **cambios):
    for variable, valor in (SMTP_ENV | cambios).items():
        if valor is None:
            monkeypatch.delenv(variable, raising=False)
        else:
            monkeypatch.setenv(variable, valor)


def test_smtp_completo(monkeypatch):
    poner_smtp(monkeypatch)
    assert cargar_smtp() == {
        "servidor": "smtp.example.com",
        "puerto": 587,
        "usuario": "centinela@example.com",
        "clave": "clave-secreta",
    }


def test_smtp_incompleto_devuelve_none(monkeypatch, caplog):
    poner_smtp(monkeypatch, SMTP_CLAVE=None)
    assert cargar_smtp() is None
    assert "Faltan en .env: SMTP_CLAVE" in caplog.text


def test_smtp_con_puerto_mal_escrito(monkeypatch, caplog):
    poner_smtp(monkeypatch, SMTP_PUERTO="58t")
    assert cargar_smtp() is None
    assert "SMTP_PUERTO" in caplog.text
    assert "clave-secreta" not in caplog.text
