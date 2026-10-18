"""Configuración de Centinela: credenciales y config.toml."""
import logging
import os
import sys
import tomllib
from pathlib import Path

from dotenv import load_dotenv

log = logging.getLogger(__name__)
RAIZ = Path(__file__).resolve().parent.parent
RUTA_ESTADO = Path(os.getenv("CENTINELA_ESTADO", RAIZ / "estado.json"))
RUTA_HISTORIAL = Path(os.getenv("CENTINELA_HISTORIAL", RAIZ / "historial.db"))

TIMEOUT = 10  # segundos máximos de espera por web


def cargar_config():
    """Lee el token y el chat_id del .env. Sale con código 1 si falta alguno."""
    load_dotenv(RAIZ / ".env")
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        log.error("Falta TELEGRAM_TOKEN en .env")
        sys.exit(1)
    if not chat_id:
        log.error("Falta TELEGRAM_CHAT_ID en .env")
        sys.exit(1)

    return token, chat_id


def leer_config(ruta=RAIZ / "config.toml"):
    """Devuelve config.toml como diccionario. Sale con código 1 si falta o está mal."""
    try:
        with open(ruta, "rb") as archivo:
            return tomllib.load(archivo)
    except FileNotFoundError:
        log.error(f"Falta {ruta}: cópielo de config.example.toml")
        sys.exit(1)
    except tomllib.TOMLDecodeError as error:
        log.error(f"{ruta} tiene un error de formato: {error}")
        sys.exit(1)


VARIABLES_SMTP = {
    "servidor": "SMTP_SERVIDOR",
    "puerto": "SMTP_PUERTO",
    "usuario": "SMTP_USUARIO",
    "clave": "SMTP_CLAVE",
}


def cargar_smtp():
    """Lee los datos del servidor de correo del .env. Devuelve None si falta alguno."""
    smtp = {clave: os.getenv(variable) for clave, variable in VARIABLES_SMTP.items()}
    faltan = [VARIABLES_SMTP[clave] for clave, valor in smtp.items() if not valor]
    if faltan:
        log.error(f"Faltan en .env: {', '.join(faltan)}")
        return None
    try:
        smtp["puerto"] = int(smtp["puerto"])
    except ValueError:
        log.error("SMTP_PUERTO en .env debe ser un número, por ejemplo 587")
        return None
    return smtp
