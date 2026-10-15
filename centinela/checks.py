"""Comprobaciones de Centinela: estado de cada web."""
import time

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
