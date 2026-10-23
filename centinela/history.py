"""Historial de Centinela: rondas de cada web y recursos del servidor en historial.db."""
import sqlite3
from datetime import datetime, timedelta

from centinela.config import RUTA_HISTORIAL


def conectar(ruta):
    """Abre historial.db y crea las tablas si no existen."""
    conexion = sqlite3.connect(ruta)
    conexion.execute(
        "CREATE TABLE IF NOT EXISTS rondas (momento TEXT, url TEXT, nombre TEXT, ok INTEGER)"
    )
    conexion.execute(
        "CREATE TABLE IF NOT EXISTS recursos "
        "(momento TEXT, clave TEXT, etiqueta TEXT, valor REAL, limite REAL)"
    )
    conexion.execute("CREATE TABLE IF NOT EXISTS informes (enviado TEXT)")
    return conexion


def guardar_resultados(resultados, momento, ruta=RUTA_HISTORIAL):
    """Guarda una fila por cada (url, nombre, ok) de la ronda."""
    marca = momento.isoformat(timespec="seconds")
    filas = [(marca, url, nombre, ok) for url, nombre, ok in resultados]
    with conectar(ruta) as conexion:
        conexion.executemany("INSERT INTO rondas VALUES (?, ?, ?, ?)", filas)


def guardar_recursos(medidas, momento, ruta=RUTA_HISTORIAL):
    """Guarda una fila por cada (clave, etiqueta, valor, limite) del servidor."""
    marca = momento.isoformat(timespec="seconds")
    filas = [(marca, *medida) for medida in medidas]
    with conectar(ruta) as conexion:
        conexion.executemany("INSERT INTO recursos VALUES (?, ?, ?, ?, ?)", filas)


def borrar_antiguos(dias, ahora, ruta=RUTA_HISTORIAL):
    """Borra las rondas y los recursos con más de esos días."""
    limite = (ahora - timedelta(days=dias)).isoformat(timespec="seconds")
    with conectar(ruta) as conexion:
        conexion.execute("DELETE FROM rondas WHERE momento < ?", (limite,))
        conexion.execute("DELETE FROM recursos WHERE momento < ?", (limite,))


def disponibilidad(desde, hasta, ruta=RUTA_HISTORIAL):
    """Devuelve [(nombre, url, total, buenas)] de cada web entre desde (incluido) y hasta (excluido)."""
    consulta = """
        SELECT nombre, url, COUNT(*), SUM(ok)
        FROM rondas
        WHERE momento >= ? AND momento < ?
        GROUP BY url
        ORDER BY nombre
    """
    periodo = (desde.isoformat(timespec="seconds"), hasta.isoformat(timespec="seconds"))
    with conectar(ruta) as conexion:
        return conexion.execute(consulta, periodo).fetchall()


def resumen_recursos(desde, hasta, ruta=RUTA_HISTORIAL):
    """Devuelve [(etiqueta, rondas, media, maximo, altas)] de cada recurso entre desde y hasta."""
    consulta = """
        SELECT etiqueta, COUNT(*), AVG(valor), MAX(valor), SUM(valor > limite)
        FROM recursos
        WHERE momento >= ? AND momento < ?
        GROUP BY clave
        ORDER BY MIN(rowid)
    """
    periodo = (desde.isoformat(timespec="seconds"), hasta.isoformat(timespec="seconds"))
    with conectar(ruta) as conexion:
        return conexion.execute(consulta, periodo).fetchall()


def ultimo_informe(ruta=RUTA_HISTORIAL):
    """Devuelve el momento del último informe enviado, o None si nunca se envió."""
    with conectar(ruta) as conexion:
        (enviado,) = conexion.execute("SELECT MAX(enviado) FROM informes").fetchone()
    return datetime.fromisoformat(enviado) if enviado else None


def marcar_informe(momento, ruta=RUTA_HISTORIAL):
    """Apunta que se envió un informe en ese momento."""
    marca = momento.isoformat(timespec="seconds")
    with conectar(ruta) as conexion:
        conexion.execute("INSERT INTO informes VALUES (?)", (marca,))
