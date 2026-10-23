import sqlite3
from datetime import datetime, timedelta

from centinela.history import (
    borrar_antiguos,
    disponibilidad,
    guardar_recursos,
    guardar_resultados,
    marcar_informe,
    resumen_recursos,
    ultimo_informe,
)

LUNES = datetime(2026, 10, 12, 9, 0)
SEMANA = timedelta(days=7)


def test_historial_vacio_no_da_filas(tmp_path):
    ruta = tmp_path / "historial.db"
    assert disponibilidad(LUNES, LUNES + SEMANA, ruta) == []


def test_cuenta_rondas_buenas_por_web(tmp_path):
    ruta = tmp_path / "historial.db"
    for hora, ok in [(10, True), (11, True), (12, False), (13, True)]:
        resultados = [("https://a.example", "A", ok), ("https://b.example", "B", False)]
        guardar_resultados(resultados, LUNES.replace(hour=hora), ruta)

    assert disponibilidad(LUNES, LUNES + SEMANA, ruta) == [
        ("A", "https://a.example", 4, 3),
        ("B", "https://b.example", 4, 0),
    ]


def test_solo_cuenta_el_periodo_pedido(tmp_path):
    ruta = tmp_path / "historial.db"
    for momento in [LUNES - timedelta(days=1), LUNES, LUNES + SEMANA]:
        guardar_resultados([("https://a.example", "A", True)], momento, ruta)

    assert disponibilidad(LUNES, LUNES + SEMANA, ruta) == [("A", "https://a.example", 1, 1)]


def test_borra_las_filas_antiguas(tmp_path):
    ruta = tmp_path / "historial.db"
    for dias in [100, 1]:
        guardar_resultados([("https://a.example", "A", True)], LUNES - timedelta(days=dias), ruta)

    borrar_antiguos(90, LUNES, ruta)

    assert disponibilidad(LUNES - timedelta(days=365), LUNES, ruta) == [
        ("A", "https://a.example", 1, 1)
    ]


def test_sin_informes_devuelve_none(tmp_path):
    assert ultimo_informe(tmp_path / "historial.db") is None


def test_ultimo_informe_es_el_mas_reciente(tmp_path):
    ruta = tmp_path / "historial.db"
    marcar_informe(LUNES, ruta)
    marcar_informe(LUNES + SEMANA, ruta)
    assert ultimo_informe(ruta) == LUNES + SEMANA


def medidas(ram, limite_ram=90):
    return [
        ("servidor:disco:/", "Disco /", 40.0, 90),
        ("servidor:ram", "RAM", ram, limite_ram),
        ("servidor:carga", "Carga", 10.0, 100),
    ]


def test_sin_recursos_no_da_filas(tmp_path):
    assert resumen_recursos(LUNES, LUNES + SEMANA, tmp_path / "historial.db") == []


def test_resume_cada_recurso_en_el_orden_de_la_ronda(tmp_path):
    ruta = tmp_path / "historial.db"
    for hora, ram in [(10, 60.0), (11, 96.0), (12, 90.0)]:
        guardar_recursos(medidas(ram), LUNES.replace(hour=hora), ruta)

    assert resumen_recursos(LUNES, LUNES + SEMANA, ruta) == [
        ("Disco /", 3, 40.0, 40.0, 0),
        ("RAM", 3, 82.0, 96.0, 1),
        ("Carga", 3, 10.0, 10.0, 0),
    ]


def test_cuenta_las_altas_con_el_limite_de_cada_ronda(tmp_path):
    ruta = tmp_path / "historial.db"
    guardar_recursos(medidas(85.0, limite_ram=90), LUNES.replace(hour=10), ruta)
    guardar_recursos(medidas(85.0, limite_ram=80), LUNES.replace(hour=11), ruta)

    ram = resumen_recursos(LUNES, LUNES + SEMANA, ruta)[1]

    assert ram == ("RAM", 2, 85.0, 85.0, 1)


def test_solo_resume_el_periodo_pedido(tmp_path):
    ruta = tmp_path / "historial.db"
    for momento in [LUNES - timedelta(days=1), LUNES, LUNES + SEMANA]:
        guardar_recursos(medidas(50.0), momento, ruta)

    filas = resumen_recursos(LUNES, LUNES + SEMANA, ruta)

    assert [rondas for _etiqueta, rondas, *_resto in filas] == [1, 1, 1]


def test_borra_tambien_los_recursos_antiguos(tmp_path):
    ruta = tmp_path / "historial.db"
    for dias in [100, 1]:
        guardar_recursos(medidas(50.0), LUNES - timedelta(days=dias), ruta)

    borrar_antiguos(90, LUNES, ruta)

    filas = resumen_recursos(LUNES - timedelta(days=365), LUNES, ruta)
    assert [rondas for _etiqueta, rondas, *_resto in filas] == [1, 1, 1]


def test_una_base_antigua_recibe_la_tabla_nueva(tmp_path):
    ruta = tmp_path / "historial.db"
    fila = (LUNES.isoformat(), "https://a.example", "A", 1)
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("CREATE TABLE rondas (momento TEXT, url TEXT, nombre TEXT, ok INTEGER)")
        conexion.execute("INSERT INTO rondas VALUES (?, ?, ?, ?)", fila)

    guardar_recursos(medidas(50.0), LUNES, ruta)

    assert disponibilidad(LUNES, LUNES + SEMANA, ruta) == [("A", "https://a.example", 1, 1)]
    assert len(resumen_recursos(LUNES, LUNES + SEMANA, ruta)) == 3
