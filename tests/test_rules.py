from datetime import datetime

from centinela.rules import decidir_avisos, ha_pasado

AHORA = datetime(2026, 10, 15, 12, 0, 0)
CONFIG = {
    "horas_recordatorio_caida": 6,
    "dias_aviso_certificado": 14,
    "horas_entre_avisos_certificado": 24,
}


def test_recuperada_avisa_con_minutos_caida():
    antes = {"ok": False, "desde": "2026-10-15T11:30:00", "ultimo_aviso": "2026-10-15T11:30:00"}
    avisos, nuevo = decidir_avisos("Web", antes, True, "200 en 100 ms", None, AHORA, CONFIG)
    assert avisos == ["🟢 Recuperada: Web (estuvo caída 30 min)"]
    assert nuevo["ok"] is True
    assert nuevo["desde"] == "2026-10-15T12:00:00"


def test_primera_vez_ok_no_avisa():
    avisos, nuevo = decidir_avisos("Web", {}, True, "200 en 100 ms", None, AHORA, CONFIG)
    assert avisos == []
    assert nuevo == {"ok": True, "desde": "2026-10-15T12:00:00"}


def test_primera_vez_caida_avisa():
    avisos, nuevo = decidir_avisos("Web", {}, False, "ConnectionError", None, AHORA, CONFIG)
    assert avisos == ["🔴 Caída: Web (ConnectionError)"]
    assert nuevo["ultimo_aviso"] == "2026-10-15T12:00:00"


def test_sigue_caida_sin_recordatorio_antes_de_6_horas():
    antes = {"ok": False, "desde": "2026-10-15T08:00:00", "ultimo_aviso": "2026-10-15T10:00:00"}
    avisos, nuevo = decidir_avisos("Web", antes, False, "ConnectionError", None, AHORA, CONFIG)
    assert avisos == []
    assert nuevo == antes


def test_sigue_caida_recordatorio_a_las_6_horas():
    antes = {"ok": False, "desde": "2026-10-15T08:00:00", "ultimo_aviso": "2026-10-15T06:00:00"}
    avisos, nuevo = decidir_avisos("Web", antes, False, "ConnectionError", None, AHORA, CONFIG)
    assert avisos == ["🔴 Sigue caída: Web desde 2026-10-15T08:00:00 (ConnectionError)"]
    assert nuevo["ultimo_aviso"] == "2026-10-15T12:00:00"


def test_certificado_por_caducar_avisa():
    antes = {"ok": True, "desde": "2026-10-15T08:00:00"}
    avisos, nuevo = decidir_avisos("Web", antes, True, "200 en 100 ms", 5, AHORA, CONFIG)
    assert avisos == ["🟡 Certificado de Web: caduca en 5 días"]
    assert nuevo["aviso_certificado"] == "2026-10-15T12:00:00"


def test_certificado_no_repite_antes_de_24_horas():
    antes = {"ok": True, "desde": "2026-10-15T08:00:00", "aviso_certificado": "2026-10-15T11:00:00"}
    avisos, _ = decidir_avisos("Web", antes, True, "200 en 100 ms", 5, AHORA, CONFIG)
    assert avisos == []


def test_ha_pasado():
    assert ha_pasado(None, 6, AHORA) is True
    assert ha_pasado("2026-10-15T11:00:00", 6, AHORA) is False
    assert ha_pasado("2026-10-15T06:00:00", 6, AHORA) is True
