"""Comprobaciones de Centinela: estado de cada web y su certificado."""
import socket
import ssl
import time
from urllib.parse import urlparse

import requests

from centinela.config import TIMEOUT


def revisar(url, timeout=TIMEOUT, texto=None):
    """Comprueba una web y, si se indica, que contenga un texto. Devuelve (está_bien, detalle)."""
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(url, timeout=timeout)
        ms = (time.perf_counter() - inicio) * 1000
        if respuesta.ok and texto and texto not in respuesta.text:
            return False, f"falta el texto «{texto}»"
        return respuesta.ok, f"{respuesta.status_code} en {ms:.0f} ms"
    except requests.RequestException as error:
        return False, type(error).__name__


def dias_certificado(url, timeout=TIMEOUT):
    """Devuelve los días que faltan para que caduque el certificado, o None si no se pudo leer."""
    host = urlparse(url).hostname
    contexto = ssl.create_default_context()
    try:
        with (
            socket.create_connection((host, 443), timeout=timeout) as conexion,
            contexto.wrap_socket(conexion, server_hostname=host) as tls,
        ):
            certificado = tls.getpeercert()
    except OSError:
        return None
    caduca = ssl.cert_time_to_seconds(certificado["notAfter"])
    return int((caduca - time.time()) // 86400)
