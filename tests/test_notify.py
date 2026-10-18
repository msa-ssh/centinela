import requests

from centinela import notify

WEBHOOK = "https://discord.com/api/webhooks/123/token-secreto"


class RespuestaFalsa:
    def __init__(self, status_code):
        self.status_code = status_code
        self.ok = status_code < 400


def test_discord_envia_el_texto(monkeypatch):
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json))
        return RespuestaFalsa(204)

    monkeypatch.setattr(notify.requests, "post", post)

    assert notify.enviar_discord(WEBHOOK, "🔴 Caída: Web") is True
    assert llamadas == [(WEBHOOK, {"content": "🔴 Caída: Web"})]


def test_discord_recorta_los_mensajes_largos(monkeypatch):
    enviados = []

    def post(url, json, timeout):
        enviados.append(json["content"])
        return RespuestaFalsa(204)

    monkeypatch.setattr(notify.requests, "post", post)

    notify.enviar_discord(WEBHOOK, "a" * 2500)

    assert len(enviados[0]) == 2000


def test_discord_con_error_devuelve_false(monkeypatch, caplog):
    monkeypatch.setattr(notify.requests, "post", lambda url, json, timeout: RespuestaFalsa(404))

    assert notify.enviar_discord(WEBHOOK, "Hola") is False
    assert "Discord respondió 404" in caplog.text


def test_un_fallo_de_red_no_muestra_el_webhook(monkeypatch, caplog):
    def falla(url, json, timeout):
        raise requests.ConnectionError(f"No se pudo conectar con {url}")

    monkeypatch.setattr(notify.requests, "post", falla)

    assert notify.enviar_discord(WEBHOOK, "Hola") is False
    assert "ConnectionError" in caplog.text
    assert "token-secreto" not in caplog.text

    
SMTP = {
    "servidor": "smtp.example.com",
    "puerto": 587,
    "usuario": "centinela@example.com",
    "clave": "clave-secreta",
}


def preparar_smtp(monkeypatch, fallo=None):
    conexiones = []

    class SMTPFalso:
        def __init__(self, servidor, puerto, timeout):
            self.pasos = [("conectar", servidor, puerto)]
            self.mensaje = None
            conexiones.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *error):
            return False

        def starttls(self, context):
            self.pasos.append(("starttls", context.check_hostname))

        def login(self, usuario, clave):
            if fallo:
                raise fallo
            self.pasos.append(("login", usuario))

        def send_message(self, mensaje):
            self.pasos.append("enviar")
            self.mensaje = mensaje

    monkeypatch.setattr(notify.smtplib, "SMTP", SMTPFalso)
    return conexiones


def test_correo_cifra_antes_de_iniciar_sesion(monkeypatch):
    conexiones = preparar_smtp(monkeypatch)

    assert notify.enviar_correo(SMTP, "dueno@tienda.example", "🔴 Caída: Web") is True
    assert conexiones[0].pasos == [
        ("conectar", "smtp.example.com", 587),
        ("starttls", True),
        ("login", "centinela@example.com"),
        "enviar",
    ]


def test_correo_lleva_el_aviso_en_el_asunto_y_el_cuerpo(monkeypatch):
    conexiones = preparar_smtp(monkeypatch)
    texto = "📊 Informe semanal (12 oct – 19 oct)\n✅ Web: 100 % (2016 de 2016 rondas)"

    notify.enviar_correo(SMTP, "dueno@tienda.example", texto)

    mensaje = conexiones[0].mensaje
    assert mensaje["Subject"] == "Centinela: 📊 Informe semanal (12 oct – 19 oct)"
    assert mensaje["From"] == "centinela@example.com"
    assert mensaje["To"] == "dueno@tienda.example"
    assert mensaje.get_content().strip() == texto


def test_un_error_de_correo_no_muestra_la_clave(monkeypatch, caplog):
    fallo = notify.smtplib.SMTPAuthenticationError(535, b"clave-secreta rechazada")
    preparar_smtp(monkeypatch, fallo)

    assert notify.enviar_correo(SMTP, "dueno@tienda.example", "Hola") is False
    assert "SMTPAuthenticationError" in caplog.text
    assert "clave-secreta" not in caplog.text
