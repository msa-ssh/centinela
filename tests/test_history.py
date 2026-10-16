from datetime import datetime, timedelta

from centinela.history import (
    borrar_antiguos,
    disponibilidad,
    guardar_resultados,
    marcar_informe,
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
