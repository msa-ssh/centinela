#!/usr/bin/env python3
"""Centinela: vigila webs y avisa si algo falla."""
import sys

from centinela.checks import revisar
from centinela.config import cargar_config, leer_sitios
from centinela.notify import enviar_telegram


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
