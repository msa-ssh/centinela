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
