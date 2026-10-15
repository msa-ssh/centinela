#!/usr/bin/env python3
"""Centinela: vigila webs y avisa solo cuando algo cambia."""
import logging
import sys
from datetime import datetime

from centinela.checks import dias_certificado, revisar
from centinela.config import cargar_config, leer_config
from centinela.notify import enviar_telegram
from centinela.rules import decidir_avisos
from centinela.state import cargar_estado, guardar_estado

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    token, chat_id = cargar_config()
    if "--prueba" in sys.argv:
        ok = enviar_telegram(token, chat_id, "Prueba de Centinela: funciona")
        sys.exit(0 if ok else 1)

    config = leer_config()
    timeout = config["timeout_segundos"]
    estado = cargar_estado()
    nuevo_estado = {}
    ahora = datetime.now()

    for sitio in config["sitio"]:
        nombre, url = sitio["nombre"], sitio["url"]
        ok, detalle = revisar(url, timeout)
        dias = dias_certificado(url, timeout) if url.startswith("https://") else None
        icono = "✅" if ok else "❌"
        certificado = f", certificado: {dias} días" if dias is not None else ""
        if ok:
            log.info(f"{icono} {nombre} ({detalle}{certificado})")
        else:
            log.warning(f"{icono} {nombre} ({detalle}{certificado})")

        avisos, nuevo_estado[url] = decidir_avisos(
            nombre, estado.get(url, {}), ok, detalle, dias, ahora, config
        )
        for aviso in avisos:
            enviar_telegram(token, chat_id, aviso)

    guardar_estado(nuevo_estado)


if __name__ == "__main__":
    main()
