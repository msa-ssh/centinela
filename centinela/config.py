"""Configuración de Centinela: credenciales y config.toml."""
import os
import sys
import tomllib

from dotenv import load_dotenv

TIMEOUT = 10  # segundos máximos de espera por web


def cargar_config():
    """Lee el token y el chat_id del .env. Sale con código 1 si falta alguno."""
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        print("Falta TELEGRAM_TOKEN en .env", file=sys.stderr)
        sys.exit(1)
    if not chat_id:
        print("Falta TELEGRAM_CHAT_ID en .env", file=sys.stderr)
        sys.exit(1)

    return token, chat_id


def leer_config(ruta="config.toml"):
    """Devuelve config.toml como diccionario. Sale con código 1 si falta o está mal."""
    try:
        with open(ruta, "rb") as archivo:
            return tomllib.load(archivo)
    except FileNotFoundError:
        print(f"Falta {ruta}: cópielo de config.example.toml", file=sys.stderr)
        sys.exit(1)
    except tomllib.TOMLDecodeError as error:
        print(f"{ruta} tiene un error de formato: {error}", file=sys.stderr)
        sys.exit(1)
