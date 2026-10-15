#!/usr/bin/env python3
"""Centinela: vigila webs y avisa si algo falla."""
import sys

from centinela.checks import revisar
from centinela.config import cargar_config, leer_config
from centinela.notify import enviar_telegram


def main():
    token, chat_id = cargar_config()
    if "--prueba" in sys.argv:
        ok = enviar_telegram(token, chat_id, "Prueba de Centinela: funciona")
        sys.exit(0 if ok else 1)
    config = leer_config()
    for sitio in config["sitio"]:
        ok, detalle = revisar(sitio["url"])
        icono = "✅" if ok else "❌"
        print(f"{icono} {sitio['nombre']}  ({detalle})")
        if not ok:
            enviar_telegram(token, chat_id, f"❌ {sitio['nombre']} no responde ({detalle})")


if __name__ == "__main__":
    main()
