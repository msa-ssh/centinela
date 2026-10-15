#!/usr/bin/env python3
"""Centinela: vigila webs y avisa si algo falla."""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

TIMEOUT = 10  # segundos máximos de espera por web


def cargar_config():
    """Lee el token y el chat_id del .env. Sale con código 1 si falta alguno."""
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        print("Falta TELEGRAM_TOKEN en .env", file=sys.stderr)
        sys.exit(1)
    if not chat_id:
        print("Falta TELEGRAM_CHAT_ID en .env", file=sys.stderr)
        sys.exit(1)

    return token, chat_id


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
    token, chat_id = cargar_config()
    for url in leer_sitios():
        ok, detalle = revisar(url)
        icono = "✅" if ok else "❌"
        print(f"{icono} {url}  ({detalle})")


if __name__ == "__main__":
    main()
