#!/usr/bin/env python3
"""Centinela: vigila webs y avisa si algo falla."""
import time
from pathlib import Path

import requests

TIMEOUT = 10  # segundos máximos de espera por web


def leer_sitios(ruta="sitios.txt"):
    """Devuelve las URLs del archivo, sin líneas vacías ni comentarios."""
    lineas = Path(ruta).read_text().splitlines()
    return [l.strip() for l in lineas if l.strip() and not l.startswith("#")]


def revisar(url):
    """Comprueba una web. Devuelve (está_bien, detalle)."""
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(url, timeout=TIMEOUT)
        ms = (time.perf_counter() - inicio) * 1000
        return respuesta.ok, f"{respuesta.status_code} en {ms:.0f} ms"
    except requests.RequestException as error:
        return False, type(error).__name__


def main():
    for url in leer_sitios():
        ok, detalle = revisar(url)
        icono = "✅" if ok else "❌"
        print(f"{icono} {url}  ({detalle})")


if __name__ == "__main__":
    main()
