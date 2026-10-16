from datetime import datetime, timedelta

import centinela.__main__ as programa
from centinela.report import formatear_informe, toca_informe

DESDE = datetime(2026, 10, 12, 9, 0)
HASTA = datetime(2026, 10, 19, 9, 0)


def test_informe_con_varias_webs():
    filas = [
        ("GitHub", "https://github.com", 2016, 2012),
        ("Google", "https://www.google.com", 2016, 2016),
        ("Web de prueba", "https://esto-no-existe.example", 2016, 0),
    ]
    assert formatear_informe(filas, DESDE, HASTA) == (
        "📊 Informe semanal (12 oct – 19 oct)\n"
        "✅ GitHub: 99,8 % (2012 de 2016 rondas)\n"
        "✅ Google: 100 % (2016 de 2016 rondas)\n"
        "❌ Web de prueba: 0 % (0 de 2016 rondas)"
    )


def test_un_solo_fallo_no_se_redondea_a_100():
    filas = [("Web", "https://web.example", 2016, 2015)]
    assert "Web: 99,9 %" in formatear_informe(filas, DESDE, HASTA)


def test_por_debajo_del_99_lleva_cruz():
    filas = [("Web", "https://web.example", 100, 98)]
    assert "❌ Web: 98 % (98 de 100 rondas)" in formatear_informe(filas, DESDE, HASTA)


def test_sin_datos():
    assert formatear_informe([], DESDE, HASTA) == (
        "📊 Informe semanal (12 oct – 19 oct)\nSin datos en este periodo"
    )


def test_enviar_informe_usa_los_ultimos_7_dias(monkeypatch):
    pedidos, enviados = [], []

    def disponibilidad_falsa(desde, hasta):
        pedidos.append((desde, hasta))
        return [("Web", "https://web.example", 10, 10)]

    monkeypatch.setattr(programa, "disponibilidad", disponibilidad_falsa)
    monkeypatch.setattr(
        programa, "enviar_telegram", lambda token, chat_id, texto: enviados.append(texto) or True
    )

    assert programa.enviar_informe("token", "chat", HASTA) is True
    assert pedidos == [(DESDE, HASTA)]
    assert enviados == [formatear_informe([("Web", "https://web.example", 10, 10)], DESDE, HASTA)]


def test_toca_el_lunes_a_las_9():
    assert toca_informe(HASTA - timedelta(days=7), HASTA)


def test_no_toca_dos_veces_la_misma_semana():
    assert not toca_informe(HASTA, HASTA + timedelta(days=2))


def test_no_toca_antes_de_las_9():
    assert not toca_informe(DESDE, HASTA - timedelta(minutes=1))


def test_toca_aunque_el_lunes_estuviera_apagado():
    assert toca_informe(DESDE, HASTA + timedelta(days=1))


def preparar_informe(monkeypatch, ultimo, llega=True):
    marcados, enviados = [], []
    monkeypatch.setattr(programa, "ultimo_informe", lambda: ultimo)
    monkeypatch.setattr(programa, "marcar_informe", marcados.append)
    monkeypatch.setattr(
        programa, "enviar_informe", lambda token, chat_id, ahora: enviados.append(ahora) or llega
    )
    return marcados, enviados


def test_la_primera_vez_solo_apunta_la_fecha(monkeypatch):
    marcados, enviados = preparar_informe(monkeypatch, None)
    programa.informe_si_toca("token", "chat", HASTA)
    assert (marcados, enviados) == ([HASTA], [])


def test_cuando_toca_envia_y_apunta(monkeypatch):
    marcados, enviados = preparar_informe(monkeypatch, DESDE)
    programa.informe_si_toca("token", "chat", HASTA)
    assert (marcados, enviados) == ([HASTA], [HASTA])


def test_si_telegram_falla_no_apunta_y_reintenta(monkeypatch):
    marcados, enviados = preparar_informe(monkeypatch, DESDE, llega=False)
    programa.informe_si_toca("token", "chat", HASTA)
    assert (marcados, enviados) == ([], [HASTA])
