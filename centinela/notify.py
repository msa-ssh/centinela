"""Avisos de Centinela por Telegram."""
import logging

import requests

from centinela.config import TIMEOUT

log = logging.getLogger(__name__)


def enviar_telegram(token, chat_id, texto):
    """Envía un mensaje a Telegram. Devuelve True si llegó."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = {"chat_id": chat_id, "text": texto}
    try:
        respuesta = requests.post(url, data=datos, timeout=TIMEOUT)
    except requests.RequestException as error:
        log.error(f"No se pudo enviar a Telegram: {type(error).__name__}")
        return False
    if not respuesta.ok:
        log.error(f"Telegram respondió {respuesta.status_code}")
        return False
    return True
