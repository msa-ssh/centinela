"""Configuración de Centinela: credenciales y lista de webs."""
import os
import sys
from pathlib import Path

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


def leer_sitios(ruta="sitios.txt"):
    """Devuelve las URLs del archivo, sin líneas vacías ni comentarios."""
    lineas = Path(ruta).read_text().splitlines()
    return [l.strip() for l in lineas if l.strip() and not l.startswith("#")]
