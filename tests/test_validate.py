import logging
from pathlib import Path

from centinela import validate
from centinela.config import leer_config
from centinela.validate import comprobar_config, comprobar_permisos

ENTORNO = {"TELEGRAM_TOKEN": "token-secreto", "TELEGRAM_CHAT_ID": "123"}


def config_valida(**cambios):
    config = {
        "intervalo_minutos": 5,
        "timeout_segundos": 10,
        "dias_aviso_certificado": 14,
        "horas_entre_avisos_certificado": 24,
        "horas_recordatorio_caida": 6,
        "sitio": [{"nombre": "Web", "url": "https://web.example"}],
    }
    return config | cambios


def test_una_configuracion_correcta_no_tiene_problemas():
    assert comprobar_config(config_valida(), ENTORNO) == []


def test_una_errata_en_una_clave_sugiere_la_buena():
    config = config_valida(servidor={"nombre": "VM", "dsco_max": 90})

    assert comprobar_config(config, ENTORNO) == [
        "[servidor]: clave desconocida «dsco_max» (¿quiso decir «disco_max»?)"
    ]


def test_falta_una_clave_obligatoria():
    config = config_valida()
    del config["timeout_segundos"]

    assert comprobar_config(config, ENTORNO) == ["config.toml: falta timeout_segundos"]


def test_valores_fuera_de_rango_o_que_no_son_numeros():
    config = config_valida(intervalo_minutos=0, servidor={"disco_max": 150, "ram_max": "90"})

    assert comprobar_config(config, ENTORNO) == [
        "intervalo_minutos debe estar entre 1 y 1440 (vale 0)",
        "[servidor] disco_max debe estar entre 1 y 100 (vale 150)",
        "[servidor] ram_max debe ser un número",
    ]


def test_cero_recordatorios_es_valido():
    assert comprobar_config(config_valida(horas_recordatorio_caida=0), ENTORNO) == []


def test_url_sin_http_y_sin_sitios():
    config = config_valida(sitio=[{"nombre": "Tienda", "url": "tienda.example"}])
    assert comprobar_config(config, ENTORNO) == [
        "[[sitio]] Tienda: la url debe empezar por http:// o https://"
    ]

    assert comprobar_config(config_valida(sitio=[]), ENTORNO) == [
        "config.toml: no hay ningún [[sitio]]"
    ]


def test_canales_que_no_existen_en_avisos():
    config = config_valida(
        avisos=["telegram", "equipo"],
        sitio=[{"nombre": "Web", "url": "https://web.example", "avisos": ["tienda"]}],
        servidor={"avisos": ["socio"]},
    )

    assert comprobar_config(config, ENTORNO) == [
        "avisos: el canal «equipo» no existe",
        "[[sitio]] Web: el canal «tienda» no existe",
        "[servidor]: el canal «socio» no existe",
    ]


def test_faltan_variables_sin_mostrar_secretos():
    config = config_valida(
        canales={
            "equipo": {"tipo": "discord", "variable": "DISCORD_WEBHOOK_EQUIPO"},
            "tienda": {"tipo": "correo", "para": "dueno@tienda.example"},
            "raro": {"tipo": "whatsapp"},
        }
    )
    entorno = ENTORNO | {"SMTP_SERVIDOR": "smtp.example.com", "SMTP_CLAVE": "clave-secreta"}

    problemas = comprobar_config(config, entorno)

    assert problemas == [
        "[canales.equipo]: falta DISCORD_WEBHOOK_EQUIPO en .env",
        "[canales.tienda]: falta SMTP_PUERTO en .env",
        "[canales.tienda]: falta SMTP_USUARIO en .env",
        "[canales.raro]: tipo «whatsapp» desconocido (telegram, discord o correo)",
    ]
    assert not any("secret" in problema for problema in problemas)


def test_falta_el_token_de_telegram():
    assert comprobar_config(config_valida(), {"TELEGRAM_CHAT_ID": "123"}) == [
        "Falta TELEGRAM_TOKEN en .env"
    ]


def test_permisos_abiertos(tmp_path):
    ruta = tmp_path / ".env"
    ruta.write_text("TELEGRAM_TOKEN=x\n", encoding="utf-8")

    ruta.chmod(0o644)
    assert comprobar_permisos(ruta) == [
        ".env: permisos 644, otros usuarios pueden leerlo (chmod 600 .env)"
    ]

    ruta.chmod(0o600)
    assert comprobar_permisos(ruta) == []


def test_sin_archivo_no_hay_problema_de_permisos(tmp_path):
    assert comprobar_permisos(tmp_path / ".env") == []


def test_comprobar_instalacion_escribe_cada_problema(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(validate, "RAIZ", tmp_path)
    monkeypatch.setattr(validate, "leer_config", lambda: config_valida(intervalo_minutos=0))
    monkeypatch.setenv("TELEGRAM_TOKEN", "token-secreto")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    assert validate.comprobar_instalacion() is False
    assert "❌ intervalo_minutos debe estar entre 1 y 1440 (vale 0)" in caplog.text
    assert "token-secreto" not in caplog.text


def test_comprobar_instalacion_correcta(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(validate, "RAIZ", tmp_path)
    monkeypatch.setattr(validate, "leer_config", config_valida)
    monkeypatch.setenv("TELEGRAM_TOKEN", "token-secreto")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    with caplog.at_level(logging.INFO):
        assert validate.comprobar_instalacion() is True
    assert "✅ config.toml y .env correctos" in caplog.text


def test_la_plantilla_de_ejemplo_es_valida():
    config = leer_config(Path(__file__).resolve().parent.parent / "config.example.toml")
    assert comprobar_config(config, ENTORNO) == []
