#!/usr/bin/env python3
"""Centinela: vigila webs y avisa si algo falla."""
import sys
import time

import requests

from centinela.config import TIMEOUT, cargar_config, leer_sitios


def revisar(url):
    """Comprueba una web. Devuelve (está_bien, detalle)."""
    inicio = time.perf_counter()
    try:
        respuesta = requests.get(url, timeout=TIMEOUT)
        ms = (time.perf_counter() - inicio) * 1000
        return respuesta.ok, f"{respuesta.status_code} en {ms:.0f} ms"
    except requests.RequestException as error:
        return False, type(error).__name__


def enviar_telegram(token, chat_id, texto):
    """Envía un mensaje a Telegram. Devuelve True si llegó."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = {"chat_id": chat_id, "text": texto}
    try:
        respuesta = requests.post(url, data=datos, timeout=TIMEOUT)
    except requests.RequestException as error:
        print(f"No se pudo enviar a Telegram: {type(error).__name__}", file=sys.stderr)
        return False
    if not respuesta.ok:
        print(f"Telegram respondió {respuesta.status_code}", file=sys.stderr)
        return False
    return True


def main():
    token, chat_id = cargar_config()
    if "--prueba" in sys.argv:
        ok = enviar_telegram(token, chat_id, "Prueba de Centinela: funciona")
        sys.exit(0 if ok else 1)
    for url in leer_sitios():
        ok, detalle = revisar(url)
        icono = "✅" if ok else "❌"
        print(f"{icono} {url}  ({detalle})")
        if not ok:
            enviar_telegram(token, chat_id, f"❌ {url} no responde ({detalle})")


if __name__ == "__main__":
    main()
