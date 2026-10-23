import os

import centinela.__main__ as programa

AHORA = 1_800_000_000


def estado_de_hace(tmp_path, minutos):
    ruta = tmp_path / "estado.json"
    ruta.write_text("{}\n", encoding="utf-8")
    momento = AHORA - minutos * 60
    os.utime(ruta, (momento, momento))
    return ruta


def preparar(monkeypatch, intervalo=5):
    monkeypatch.setattr(programa, "leer_config", lambda: {"intervalo_minutos": intervalo})


def test_sano_si_la_ultima_ronda_es_reciente(monkeypatch, tmp_path):
    preparar(monkeypatch)

    assert programa.salud(AHORA, estado_de_hace(tmp_path, 4)) is True


def test_enfermo_si_pasan_tres_intervalos(monkeypatch, tmp_path, caplog):
    preparar(monkeypatch)

    assert programa.salud(AHORA, estado_de_hace(tmp_path, 16)) is False
    assert "La última ronda fue hace 16 min (límite 15 min)" in caplog.text


def test_el_limite_depende_del_intervalo(monkeypatch, tmp_path):
    preparar(monkeypatch, intervalo=10)

    assert programa.salud(AHORA, estado_de_hace(tmp_path, 25)) is True


def test_enfermo_si_nunca_hubo_ronda(monkeypatch, tmp_path, caplog):
    preparar(monkeypatch)

    assert programa.salud(AHORA, tmp_path / "estado.json") is False
    assert "Todavía no se ha guardado ninguna ronda" in caplog.text
