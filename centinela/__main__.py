"""Centinela: vigila webs y avisa solo cuando algo cambia."""
import logging
import os
import sys
import time
from datetime import datetime

from centinela.checks import dias_certificado, revisar
from centinela.config import cargar_config, leer_config
from centinela.notify import enviar_telegram
from centinela.rules import decidir_avisos
from centinela.state import cargar_estado, guardar_estado

log = logging.getLogger(__name__)


PRIORIDAD_SYSLOG = {"DEBUG": 7, "INFO": 6, "WARNING": 4, "ERROR": 3, "CRITICAL": 2}


class FormatoJournal(logging.Formatter):
    def format(self, registro):
        return f"<{PRIORIDAD_SYSLOG[registro.levelname]}>{super().format(registro)}"


def main():
    formato = "%(levelname)s %(name)s: %(message)s"
    manejador = logging.StreamHandler()
    if "JOURNAL_STREAM" in os.environ:
        manejador.setFormatter(FormatoJournal(formato))
    else:
        manejador.setFormatter(logging.Formatter(formato))
    logging.basicConfig(level=logging.INFO, handlers=[manejador])
    token, chat_id = cargar_config()
    if "--prueba" in sys.argv:
        ok = enviar_telegram(token, chat_id, "Prueba de Centinela: funciona")
        sys.exit(0 if ok else 1)

    if "--bucle" in sys.argv:
        while True:
            config = ronda(token, chat_id)
            time.sleep(config["intervalo_minutos"] * 60)
    ronda(token, chat_id)


def ronda(token, chat_id):
    """Revisa todas las webs una vez, avisa si hace falta y devuelve la configuración leída."""
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
    return config


if __name__ == "__main__":
    main()
