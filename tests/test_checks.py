import time
from contextlib import nullcontext

import requests

from centinela import checks


class RespuestaFalsa:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = text


class TLSFalso:
    def __init__(self, certificado):
        self.certificado = certificado

    def __enter__(self):
        return self

    def __exit__(self, *error):
        return False

    def getpeercert(self):
        return self.certificado


class ContextoFalso:
    def __init__(self, certificado):
        self.certificado = certificado

    def wrap_socket(self, conexion, server_hostname):
        return TLSFalso(self.certificado)


def test_revisar_web_bien(monkeypatch):
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(200))
    ok, detalle = checks.revisar("https://example.com")
    assert ok is True
    assert detalle.startswith("200 en ")


def test_revisar_error_del_servidor(monkeypatch):
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(500))
    ok, detalle = checks.revisar("https://example.com")
    assert ok is False
    assert detalle.startswith("500 en ")


def test_revisar_sin_conexion(monkeypatch):
    def falla(url, timeout):
        raise requests.ConnectionError

    monkeypatch.setattr(checks.requests, "get", falla)
    assert checks.revisar("https://example.com") == (False, "ConnectionError")


def test_revisar_tiempo_agotado(monkeypatch):
    def falla(url, timeout):
        raise requests.Timeout

    monkeypatch.setattr(checks.requests, "get", falla)
    assert checks.revisar("https://example.com") == (False, "Timeout")


def test_revisar_con_el_texto_esperado(monkeypatch):
    pagina = "<button>Añadir al carrito</button>"
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(200, pagina))
    ok, detalle = checks.revisar("https://example.com", texto="Añadir al carrito")
    assert ok is True
    assert detalle.startswith("200 en ")


def test_revisar_sin_el_texto_esperado(monkeypatch):
    pagina = "<h1>Error al cargar la tienda</h1>"
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(200, pagina))
    ok, detalle = checks.revisar("https://example.com", texto="Añadir al carrito")
    assert (ok, detalle) == (False, "falta el texto «Añadir al carrito»")


def test_revisar_texto_distingue_mayusculas(monkeypatch):
    pagina = "<button>Añadir al carrito</button>"
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(200, pagina))
    ok, _detalle = checks.revisar("https://example.com", texto="añadir al carrito")
    assert ok is False


def test_revisar_error_del_servidor_con_texto(monkeypatch):
    pagina = "<button>Añadir al carrito</button>"
    monkeypatch.setattr(checks.requests, "get", lambda url, timeout: RespuestaFalsa(500, pagina))
    ok, detalle = checks.revisar("https://example.com", texto="Añadir al carrito")
    assert ok is False
    assert detalle.startswith("500 en ")


def test_dias_certificado(monkeypatch):
    caduca = time.gmtime(time.time() + 10 * 86400 + 3600)
    certificado = {"notAfter": time.strftime("%b %d %H:%M:%S %Y GMT", caduca)}
    monkeypatch.setattr(checks.socket, "create_connection", lambda *a, **k: nullcontext())
    monkeypatch.setattr(checks.ssl, "create_default_context", lambda: ContextoFalso(certificado))
    assert checks.dias_certificado("https://example.com") == 10


def test_dias_certificado_sin_conexion(monkeypatch):
    def falla(*args, **kwargs):
        raise OSError

    monkeypatch.setattr(checks.socket, "create_connection", falla)
    assert checks.dias_certificado("https://example.com") is None
