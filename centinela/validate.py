"""Comprobación de config.toml y .env antes de usarlos, sin enviar nada ni mostrar secretos."""
import logging
import os
from difflib import get_close_matches

from dotenv import load_dotenv

from centinela.config import RAIZ, VARIABLES_SMTP, leer_config

log = logging.getLogger(__name__)

OBLIGATORIAS = {
    "intervalo_minutos": (1, 1440),
    "timeout_segundos": (1, 120),
    "dias_aviso_certificado": (1, 365),
    "horas_entre_avisos_certificado": (1, 720),
    "horas_recordatorio_caida": (1, 720),
}
OPCIONALES = {"dias_historial": (8, 3650)}
CLAVES_GENERALES = {*OBLIGATORIAS, *OPCIONALES, "avisos", "canales", "sitio", "servidor"}
CLAVES_SITIO = {"nombre", "url", "texto", "avisos"}
CLAVES_SERVIDOR = {"nombre", "discos", "disco_max", "ram_max", "carga_max", "avisos"}
LIMITES_SERVIDOR = {"disco_max": (1, 100), "ram_max": (1, 100), "carga_max": (1, 1000)}
TIPOS_CANAL = {"telegram", "discord", "correo"}


def claves_desconocidas(tabla, permitidas, donde):
    """Una línea por cada clave que no existe, con la más parecida si la hay."""
    problemas = []
    for clave in sorted(set(tabla) - permitidas):
        parecida = get_close_matches(clave, permitidas, n=1)
        pista = f" (¿quiso decir «{parecida[0]}»?)" if parecida else ""
        problemas.append(f"{donde}: clave desconocida «{clave}»{pista}")
    return problemas


def fuera_de_rango(valor, minimo, maximo, donde):
    """Comprueba que el valor sea un número entre minimo y maximo."""
    if isinstance(valor, bool) or not isinstance(valor, int | float):
        return [f"{donde} debe ser un número"]
    if not minimo <= valor <= maximo:
        return [f"{donde} debe estar entre {minimo} y {maximo} (vale {valor})"]
    return []


def canales_desconocidos(avisos, nombres, donde):
    """Una línea por cada canal de la lista avisos que no está definido."""
    return [f"{donde}: el canal «{nombre}» no existe" for nombre in avisos if nombre not in nombres]


def comprobar_canal(nombre, canal, entorno):
    """Revisa un [canales.x] y que sus variables estén en .env, sin mirar sus valores."""
    donde = f"[canales.{nombre}]"
    problemas = claves_desconocidas(canal, {"tipo", "variable", "para"}, donde)
    tipo = canal.get("tipo")
    if tipo not in TIPOS_CANAL:
        return [*problemas, f"{donde}: tipo «{tipo}» desconocido (telegram, discord o correo)"]
    if tipo == "correo":
        if not canal.get("para"):
            problemas.append(f"{donde}: falta la clave para")
        faltan = [variable for variable in VARIABLES_SMTP.values() if not entorno.get(variable)]
        problemas.extend(f"{donde}: falta {variable} en .env" for variable in faltan)
        return problemas
    variable = canal.get("variable")
    if not variable:
        problemas.append(f"{donde}: falta la clave variable")
    elif not entorno.get(variable):
        problemas.append(f"{donde}: falta {variable} en .env")
    return problemas


def comprobar_config(config, entorno):
    """Devuelve la lista de problemas de config.toml y .env; vacía si todo está bien."""
    problemas = claves_desconocidas(config, CLAVES_GENERALES, "config.toml")
    for clave, (minimo, maximo) in OBLIGATORIAS.items():
        if clave not in config:
            problemas.append(f"config.toml: falta {clave}")
        else:
            problemas += fuera_de_rango(config[clave], minimo, maximo, clave)
    for clave, (minimo, maximo) in OPCIONALES.items():
        if clave in config:
            problemas += fuera_de_rango(config[clave], minimo, maximo, clave)
    for variable in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"):
        if not entorno.get(variable):
            problemas.append(f"Falta {variable} en .env")

    canales = config.get("canales", {})
    for nombre, canal in canales.items():
        problemas += comprobar_canal(nombre, canal, entorno)
    nombres = {"telegram", *canales}
    problemas += canales_desconocidos(config.get("avisos", []), nombres, "avisos")

    sitios = config.get("sitio", [])
    if not sitios:
        problemas.append("config.toml: no hay ningún [[sitio]]")
    for numero, sitio in enumerate(sitios, 1):
        donde = f"[[sitio]] {sitio.get('nombre', numero)}"
        problemas += claves_desconocidas(sitio, CLAVES_SITIO, donde)
        if "nombre" not in sitio:
            problemas.append(f"{donde}: falta la clave nombre")
        if not str(sitio.get("url", "")).startswith(("http://", "https://")):
            problemas.append(f"{donde}: la url debe empezar por http:// o https://")
        problemas += canales_desconocidos(sitio.get("avisos", []), nombres, donde)

    if "servidor" in config:
        servidor = config["servidor"]
        problemas += claves_desconocidas(servidor, CLAVES_SERVIDOR, "[servidor]")
        for clave, (minimo, maximo) in LIMITES_SERVIDOR.items():
            if clave in servidor:
                problemas += fuera_de_rango(servidor[clave], minimo, maximo, f"[servidor] {clave}")
        problemas += canales_desconocidos(servidor.get("avisos", []), nombres, "[servidor]")
    return problemas


def comprobar_permisos(ruta):
    """Avisa si otros usuarios del sistema pueden leer o escribir el archivo."""
    try:
        permisos = ruta.stat().st_mode & 0o777
    except FileNotFoundError:
        return []
    if permisos & 0o077:
        return [f"{ruta.name}: permisos {permisos:o}, otros usuarios pueden leerlo (chmod 600 {ruta.name})"]
    return []


def comprobar_instalacion():
    """Revisa .env y config.toml, escribe cada problema en el log y devuelve True si no hay ninguno."""
    load_dotenv(RAIZ / ".env")
    problemas = comprobar_permisos(RAIZ / ".env") + comprobar_permisos(RAIZ / "config.toml")
    problemas += comprobar_config(leer_config(), os.environ)
    for problema in problemas:
        log.error(f"❌ {problema}")
    if problemas:
        log.error(f"{len(problemas)} problema(s): corríjalos antes de ponerlo en marcha")
    else:
        log.info("✅ config.toml y .env correctos")
    return not problemas
