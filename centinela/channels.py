"""Canales de aviso de Centinela: por dónde se envía cada mensaje y a quién."""
import logging
import os
from functools import partial

from centinela.config import cargar_smtp
from centinela.notify import enviar_correo, enviar_discord, enviar_telegram

log = logging.getLogger(__name__)
POR_DEFECTO = "telegram"


def crear_canales(config, token, chat_id):
    """Convierte [canales] de config.toml en {nombre: función que recibe el texto}."""
    canales = {POR_DEFECTO: partial(enviar_telegram, token, chat_id)}
    definidos = config.get("canales", {})
    smtp = None
    if any(canal.get("tipo") == "correo" for canal in definidos.values()):
        smtp = cargar_smtp()
    for nombre, canal in definidos.items():
        funcion = crear_canal(nombre, canal, token, smtp)
        if funcion:
            canales[nombre] = funcion
    return canales


def crear_canal(nombre, canal, token, smtp):
    """Devuelve la función que envía por este canal, o None si le falta algo."""
    tipo = canal.get("tipo")
    if tipo == "correo":
        if not smtp:
            log.error(f"Canal {nombre}: faltan los datos SMTP en .env")
            return None
        if not canal.get("para"):
            log.error(f"Canal {nombre}: falta la clave para en config.toml")
            return None
        return partial(enviar_correo, smtp, canal["para"])

    if tipo not in ("discord", "telegram"):
        log.error(f"Canal {nombre}: tipo desconocido «{tipo}»")
        return None
    variable = canal.get("variable", "")
    secreto = os.getenv(variable)
    if not secreto:
        log.error(f"Canal {nombre}: falta {variable or 'la clave variable'} en .env")
        return None
    if tipo == "discord":
        return partial(enviar_discord, secreto)
    return partial(enviar_telegram, token, secreto)


def destinos(tabla, config):
    """Devuelve los canales de una web o del servidor; si no tiene, los de por defecto."""
    return tabla.get("avisos", config.get("avisos", [POR_DEFECTO]))


def avisar(canales, nombres, texto):
    """Envía el texto a cada canal de la lista. Devuelve True si llegó a todos."""
    validos = []
    for nombre in nombres:
        if nombre in canales:
            validos.append(nombre)
        else:
            log.error(f"Canal desconocido en avisos: {nombre}")
    if not validos:
        validos = [POR_DEFECTO]
    llegados = [canales[nombre](texto) for nombre in validos]
    return all(llegados)
