"""Historial de Centinela: una fila por web y por ronda en historial.db."""
import sqlite3
from datetime import timedelta

from centinela.config import RUTA_HISTORIAL


def conectar(ruta):
    """Abre historial.db y crea la tabla rondas si no existe."""
    conexion = sqlite3.connect(ruta)
    conexion.execute(
        "CREATE TABLE IF NOT EXISTS rondas (momento TEXT, url TEXT, nombre TEXT, ok INTEGER)"
    )
    return conexion


def guardar_resultados(resultados, momento, ruta=RUTA_HISTORIAL):
    """Guarda una fila por cada (url, nombre, ok) de la ronda."""
    marca = momento.isoformat(timespec="seconds")
    filas = [(marca, url, nombre, ok) for url, nombre, ok in resultados]
    with conectar(ruta) as conexion:
        conexion.executemany("INSERT INTO rondas VALUES (?, ?, ?, ?)", filas)


def borrar_antiguos(dias, ahora, ruta=RUTA_HISTORIAL):
    """Borra las filas con más de esos días."""
    limite = (ahora - timedelta(days=dias)).isoformat(timespec="seconds")
    with conectar(ruta) as conexion:
        conexion.execute("DELETE FROM rondas WHERE momento < ?", (limite,))


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
