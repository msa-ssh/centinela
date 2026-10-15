"""Avisos de Centinela por Telegram."""
import sys

import requests

from centinela.config import TIMEOUT


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
