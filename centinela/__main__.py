"""Centinela: vigila webs y avisa solo cuando algo cambia."""
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta

from centinela.checks import dias_certificado, revisar
from centinela.config import cargar_config, leer_config
from centinela.history import (
    borrar_antiguos,
    disponibilidad,
    guardar_resultados,
    marcar_informe,
    ultimo_informe,
)
from centinela.notify import enviar_telegram
from centinela.report import formatear_informe, toca_informe
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

    if "--informe" in sys.argv:
        ok = enviar_informe(token, chat_id)
        sys.exit(0 if ok else 1)

    if "--bucle" in sys.argv:
        while True:
            config = ronda(token, chat_id)
            informe_si_toca(token, chat_id)
            time.sleep(config["intervalo_minutos"] * 60)
    ronda(token, chat_id)


def ronda(token, chat_id):
    """Revisa todas las webs una vez, avisa si hace falta y devuelve la configuración leída."""
    config = leer_config()
    timeout = config["timeout_segundos"]
    estado = cargar_estado()
    nuevo_estado = {}
    resultados = []
    ahora = datetime.now()

    for sitio in config["sitio"]:
        nombre, url = sitio["nombre"], sitio["url"]
        ok, detalle = revisar(url, timeout, sitio.get("texto"))
        resultados.append((url, nombre, ok))
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

    try:
        guardar_resultados(resultados, ahora)
        borrar_antiguos(config.get("dias_historial", 90), ahora)
    except sqlite3.Error as error:
        log.error(f"No se pudo guardar el historial: {error}")
    return config


def enviar_informe(token, chat_id, ahora=None):
    """Envía por Telegram la disponibilidad de los últimos 7 días. Devuelve True si llegó."""
    ahora = ahora or datetime.now()
    desde = ahora - timedelta(days=7)
    texto = formatear_informe(disponibilidad(desde, ahora), desde, ahora)
    return enviar_telegram(token, chat_id, texto)


def informe_si_toca(token, chat_id, ahora=None):
    """En modo --bucle, envía el informe una vez por semana. La primera vez solo apunta la fecha."""
    ahora = ahora or datetime.now()
    try:
        ultimo = ultimo_informe()
        primera_vez = ultimo is None
        if primera_vez or (toca_informe(ultimo, ahora) and enviar_informe(token, chat_id, ahora)):
            marcar_informe(ahora)
    except sqlite3.Error as error:
        log.error(f"No se pudo preparar el informe: {error}")


if __name__ == "__main__":
    main()
