"""Centinela: vigila webs y avisa solo cuando algo cambia."""
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta

import psutil

from centinela.channels import avisar, crear_canales, destinos
from centinela.checks import dias_certificado, revisar
from centinela.config import cargar_config, leer_config
from centinela.history import (
    borrar_antiguos,
    disponibilidad,
    guardar_recursos,
    guardar_resultados,
    marcar_informe,
    ultimo_informe,
)
from centinela.report import formatear_informe, toca_informe
from centinela.rules import con_coma, decidir_avisos, decidir_avisos_recurso
from centinela.state import cargar_estado, guardar_estado
from centinela.system import medir

log = logging.getLogger(__name__)


PRIORIDAD_SYSLOG = {"DEBUG": 7, "INFO": 6, "WARNING": 4, "ERROR": 3, "CRITICAL": 2}
LIMITES = {"disco": 90, "ram": 90, "carga": 100}


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
        ok = probar_canales(crear_canales(leer_config(), token, chat_id))
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
    canales = crear_canales(config, token, chat_id)
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
            avisar(canales, destinos(sitio, config), aviso)

    medidas = []
    if "servidor" in config:
        try:
            avisos, estados, medidas = revisar_servidor(config["servidor"], estado, ahora, config)
        except (OSError, psutil.Error) as error:
            log.error(f"No se pudo revisar el servidor: {error}")
            avisos = []
            estados = {c: v for c, v in estado.items() if c.startswith("servidor:")}
        nuevo_estado.update(estados)
        for aviso in avisos:
            avisar(canales, destinos(config["servidor"], config), aviso)

    guardar_estado(nuevo_estado)

    try:
        guardar_resultados(resultados, ahora)
        if medidas:
            guardar_recursos(medidas, ahora)
        borrar_antiguos(config.get("dias_historial", 90), ahora)
    except sqlite3.Error as error:
        log.error(f"No se pudo guardar el historial: {error}")
    return config


def revisar_servidor(servidor, estado, ahora, config):
    """Mide disco, RAM y carga, escribe una línea en el log y devuelve (avisos, estados, medidas)."""
    nombre = servidor.get("nombre", "Servidor")
    avisos, estados, partes, medidas = [], {}, [], []
    alto = False
    for clave, tipo, etiqueta, valor in medir(servidor.get("discos", ["/"])):
        limite = servidor.get(f"{tipo}_max", LIMITES[tipo])
        alto = alto or valor > limite
        partes.append(f"{etiqueta} {con_coma(valor)} %")
        medidas.append((clave, etiqueta, valor, limite))
        nuevos, estados[clave] = decidir_avisos_recurso(
            nombre, etiqueta, estado.get(clave, {}), valor, limite, ahora, config
        )
        avisos.extend(nuevos)

    linea = f"🖥️ {nombre}: {', '.join(partes)}"
    if alto:
        log.warning(linea)
    else:
        log.info(linea)
    return avisos, estados, medidas


def probar_canales(canales):
    """Envía un mensaje de prueba por cada canal. Devuelve True si llegó por todos."""
    todos = True
    for nombre, enviar in canales.items():
        if enviar(f"Prueba de Centinela por el canal {nombre}: funciona"):
            log.info(f"✅ Canal {nombre}")
        else:
            log.error(f"❌ Canal {nombre}")
            todos = False
    return todos


def enviar_informe(token, chat_id, ahora=None):
    """Envía la disponibilidad de los últimos 7 días a los canales por defecto."""
    ahora = ahora or datetime.now()
    desde = ahora - timedelta(days=7)
    texto = formatear_informe(disponibilidad(desde, ahora), desde, ahora)
    config = leer_config()
    return avisar(crear_canales(config, token, chat_id), destinos({}, config), texto)


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
