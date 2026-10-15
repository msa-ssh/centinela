"""Configuración de Centinela: credenciales y config.toml."""
import logging
import os
import sys
import tomllib
from pathlib import Path

from dotenv import load_dotenv

log = logging.getLogger(__name__)
RAIZ = Path(__file__).resolve().parent.parent

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
