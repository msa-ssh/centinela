"""Comprobaciones de Centinela: estado de cada web y su certificado."""
import socket
import ssl
import time
from urllib.parse import urlparse

import requests

from centinela.config import TIMEOUT


def revisar(url):
    """Comprueba una web. Devuelve (está_bien, detalle)."""
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(url, timeout=TIMEOUT)
        ms = (time.perf_counter() - inicio) * 1000
        return respuesta.ok, f"{respuesta.status_code} en {ms:.0f} ms"
    except requests.RequestException as error:
        return False, type(error).__name__


def dias_certificado(url):
    """Devuelve los días que faltan para que caduque el certificado, o None si no se pudo leer."""
    host = urlparse(url).hostname
    contexto = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as conexion:
            with contexto.wrap_socket(conexion, server_hostname=host) as tls:
                certificado = tls.getpeercert()
    except OSError:
        return None
    caduca = ssl.cert_time_to_seconds(certificado["notAfter"])
    return int((caduca - time.time()) // 86400)
