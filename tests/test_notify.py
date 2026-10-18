import requests

from centinela import notify

WEBHOOK = "https://discord.com/api/webhooks/123/token-secreto"


class RespuestaFalsa:
    def __init__(self, status_code):
        self.status_code = status_code
        self.ok = status_code < 400


def test_discord_envia_el_texto(monkeypatch):
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json))
        return RespuestaFalsa(204)

    monkeypatch.setattr(notify.requests, "post", post)

    assert notify.enviar_discord(WEBHOOK, "🔴 Caída: Web") is True
    assert llamadas == [(WEBHOOK, {"content": "🔴 Caída: Web"})]


def test_discord_recorta_los_mensajes_largos(monkeypatch):
    enviados = []

    def post(url, json, timeout):
        enviados.append(json["content"])
        return RespuestaFalsa(204)

    monkeypatch.setattr(notify.requests, "post", post)

    notify.enviar_discord(WEBHOOK, "a" * 2500)

    assert len(enviados[0]) == 2000


def test_discord_con_error_devuelve_false(monkeypatch, caplog):
    monkeypatch.setattr(notify.requests, "post", lambda url, json, timeout: RespuestaFalsa(404))

    assert notify.enviar_discord(WEBHOOK, "Hola") is False
    assert "Discord respondió 404" in caplog.text


def test_un_fallo_de_red_no_muestra_el_webhook(monkeypatch, caplog):
    def falla(url, json, timeout):
        raise requests.ConnectionError(f"No se pudo conectar con {url}")

    monkeypatch.setattr(notify.requests, "post", falla)

    assert notify.enviar_discord(WEBHOOK, "Hola") is False
    assert "ConnectionError" in caplog.text
    assert "token-secreto" not in caplog.text
