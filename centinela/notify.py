"""Avisos de Centinela por Telegram, Discord y correo."""
import logging
import smtplib
import ssl
from email.message import EmailMessage

import requests

from centinela.config import TIMEOUT

log = logging.getLogger(__name__)
LIMITE_DISCORD = 2000


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


def enviar_discord(webhook, texto):
    """Envía un mensaje a un canal de Discord por su webhook. Devuelve True si llegó."""
    datos = {"content": texto[:LIMITE_DISCORD]}
    try:
        respuesta = requests.post(webhook, json=datos, timeout=TIMEOUT)
    except requests.RequestException as error:
        log.error(f"No se pudo enviar a Discord: {type(error).__name__}")
        return False
    if not respuesta.ok:
        log.error(f"Discord respondió {respuesta.status_code}")
        return False
    return True


def enviar_correo(smtp, para, texto):
    """Envía un correo cifrado con STARTTLS. Devuelve True si el servidor lo aceptó."""
    mensaje = EmailMessage()
    mensaje["Subject"] = f"Centinela: {texto.splitlines()[0]}"
    mensaje["From"] = smtp["usuario"]
    mensaje["To"] = para
    mensaje.set_content(texto)
    contexto = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp["servidor"], smtp["puerto"], timeout=TIMEOUT) as conexion:
            conexion.starttls(context=contexto)
            conexion.login(smtp["usuario"], smtp["clave"])
            conexion.send_message(mensaje)
    except OSError as error:
        log.error(f"No se pudo enviar el correo: {type(error).__name__}")
        return False
    return True
