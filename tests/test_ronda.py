import logging
import sqlite3

import centinela.__main__ as programa

CONFIG = {
    "timeout_segundos": 1,
    "dias_aviso_certificado": 14,
    "horas_entre_avisos_certificado": 24,
    "horas_recordatorio_caida": 6,
    "sitio": [{"nombre": "Web", "url": "http://web.example"}],
}


def preparar(monkeypatch):
    enviados = []
    monkeypatch.setattr(programa, "leer_config", lambda: CONFIG)
    monkeypatch.setattr(programa, "cargar_estado", dict)
    monkeypatch.setattr(programa, "guardar_estado", lambda estado: None)
    monkeypatch.setattr(
        programa, "revisar", lambda url, timeout, texto=None: (False, "ConnectionError")
    )
    monkeypatch.setattr(
        programa, "enviar_telegram", lambda token, chat_id, texto: enviados.append(texto)
    )
    monkeypatch.setattr(programa, "borrar_antiguos", lambda dias, ahora: None)
    return enviados


def test_ronda_guarda_cada_web_en_el_historial(monkeypatch):
    preparar(monkeypatch)
    guardados = []
    monkeypatch.setattr(
        programa, "guardar_resultados", lambda resultados, momento: guardados.extend(resultados)
    )

    programa.ronda("token", "chat")

    assert guardados == [("http://web.example", "Web", False)]


def test_un_fallo_del_historial_no_impide_el_aviso(monkeypatch):
    enviados = preparar(monkeypatch)

    def falla(resultados, momento):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(programa, "guardar_resultados", falla)

    programa.ronda("token", "chat")

    assert enviados == ["🔴 Caída: Web (ConnectionError)"]


def test_ronda_pasa_el_texto_de_cada_web(monkeypatch):
    preparar(monkeypatch)
    sitios = [
        {"nombre": "Tienda", "url": "http://tienda.example", "texto": "Añadir al carrito"},
        {"nombre": "Blog", "url": "http://blog.example"},
    ]
    monkeypatch.setattr(programa, "leer_config", lambda: CONFIG | {"sitio": sitios})
    monkeypatch.setattr(programa, "guardar_resultados", lambda resultados, momento: None)
    textos = []

    def revisar(url, timeout, texto=None):
        textos.append(texto)
        return True, "200 en 5 ms"

    monkeypatch.setattr(programa, "revisar", revisar)

    programa.ronda("token", "chat")

    assert textos == ["Añadir al carrito", None]


MEDIDAS = [
    ("servidor:disco:/", "disco", "Disco /", 93.5),
    ("servidor:ram", "ram", "RAM", 40.0),
    ("servidor:carga", "carga", "Carga", 10.0),
]


def preparar_servidor(monkeypatch, servidor, medidas=MEDIDAS):
    enviados = preparar(monkeypatch)
    guardados = {}
    monkeypatch.setattr(programa, "leer_config", lambda: CONFIG | {"servidor": servidor})
    monkeypatch.setattr(programa, "guardar_resultados", lambda resultados, momento: None)
    monkeypatch.setattr(programa, "guardar_estado", guardados.update)
    monkeypatch.setattr(programa, "medir", lambda discos: medidas)
    return enviados, guardados


def test_ronda_avisa_si_un_recurso_pasa_el_limite(monkeypatch):
    enviados, guardados = preparar_servidor(monkeypatch, {"nombre": "VM", "disco_max": 90})

    programa.ronda("token", "chat")

    assert enviados == [
        "🔴 Caída: Web (ConnectionError)",
        "🟠 Disco / de VM al 93,5 % (límite 90 %)",
    ]
    assert guardados["servidor:disco:/"]["ok"] is False
    assert guardados["servidor:ram"]["ok"] is True


def test_ronda_usa_los_limites_por_defecto(monkeypatch):
    enviados, _ = preparar_servidor(monkeypatch, {"nombre": "VM"})

    programa.ronda("token", "chat")

    assert "🟠 Disco / de VM al 93,5 % (límite 90 %)" in enviados


def test_ronda_escribe_la_linea_del_servidor(monkeypatch, caplog):
    preparar_servidor(monkeypatch, {"nombre": "VM"})

    with caplog.at_level(logging.INFO):
        programa.ronda("token", "chat")

    registro = next(r for r in caplog.records if r.getMessage().startswith("🖥️"))
    assert registro.getMessage() == "🖥️ VM: Disco / 93,5 %, RAM 40 %, Carga 10 %"
    assert registro.levelname == "WARNING"


def test_sin_servidor_no_se_mide(monkeypatch):
    preparar(monkeypatch)
    monkeypatch.setattr(programa, "guardar_resultados", lambda resultados, momento: None)
    llamadas = []
    monkeypatch.setattr(programa, "medir", lambda discos: llamadas.append(discos) or [])

    programa.ronda("token", "chat")

    assert llamadas == []


def test_un_fallo_al_medir_no_impide_el_aviso_de_la_web(monkeypatch):
    enviados, guardados = preparar_servidor(monkeypatch, {"nombre": "VM"})
    anterior = {"ok": False, "desde": "2026-10-15T08:00:00", "ultimo_aviso": "2026-10-15T08:00:00"}
    monkeypatch.setattr(programa, "cargar_estado", lambda: {"servidor:ram": anterior})

    def falla(discos):
        raise OSError("no se puede leer el disco")

    monkeypatch.setattr(programa, "medir", falla)

    programa.ronda("token", "chat")

    assert enviados == ["🔴 Caída: Web (ConnectionError)"]
    assert guardados["servidor:ram"] == anterior
