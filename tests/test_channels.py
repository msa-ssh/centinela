from centinela import channels

SMTP = {"servidor": "smtp.example.com", "puerto": 587, "usuario": "c@example.com", "clave": "x"}
WEBHOOK = "https://discord.example/webhook"


def preparar(monkeypatch, smtp=SMTP):
    enviados = []

    def telegram(token, chat_id, texto):
        enviados.append(("telegram", chat_id, texto))

    def discord(webhook, texto):
        enviados.append(("discord", webhook, texto))

    def correo(smtp, para, texto):
        enviados.append(("correo", para, texto))

    monkeypatch.setattr(channels, "enviar_telegram", telegram)
    monkeypatch.setattr(channels, "enviar_discord", discord)
    monkeypatch.setattr(channels, "enviar_correo", correo)
    monkeypatch.setattr(channels, "cargar_smtp", lambda: smtp)
    return enviados


def test_sin_canales_solo_existe_telegram(monkeypatch):
    enviados = preparar(monkeypatch)

    canales = channels.crear_canales({}, "token", "chat")
    canales["telegram"]("Hola")

    assert list(canales) == ["telegram"]
    assert enviados == [("telegram", "chat", "Hola")]


def test_cada_tipo_de_canal(monkeypatch):
    enviados = preparar(monkeypatch)
    monkeypatch.setenv("DISCORD_WEBHOOK_EQUIPO", WEBHOOK)
    monkeypatch.setenv("TELEGRAM_CHAT_ID_SOCIO", "chat-socio")
    config = {
        "canales": {
            "equipo": {"tipo": "discord", "variable": "DISCORD_WEBHOOK_EQUIPO"},
            "tienda": {"tipo": "correo", "para": "dueno@tienda.example"},
            "socio": {"tipo": "telegram", "variable": "TELEGRAM_CHAT_ID_SOCIO"},
        }
    }

    canales = channels.crear_canales(config, "token", "chat")
    for nombre in ["equipo", "tienda", "socio"]:
        canales[nombre]("Hola")

    assert enviados == [
        ("discord", WEBHOOK, "Hola"),
        ("correo", "dueno@tienda.example", "Hola"),
        ("telegram", "chat-socio", "Hola"),
    ]


def test_canal_sin_su_variable_no_se_crea(monkeypatch, caplog):
    preparar(monkeypatch)
    monkeypatch.delenv("DISCORD_WEBHOOK_NO_EXISTE", raising=False)
    config = {"canales": {"equipo": {"tipo": "discord", "variable": "DISCORD_WEBHOOK_NO_EXISTE"}}}

    canales = channels.crear_canales(config, "token", "chat")

    assert "equipo" not in canales
    assert "Canal equipo: falta DISCORD_WEBHOOK_NO_EXISTE en .env" in caplog.text


def test_canal_de_tipo_desconocido_no_se_crea(monkeypatch, caplog):
    preparar(monkeypatch)
    config = {"canales": {"movil": {"tipo": "whatsapp"}}}

    canales = channels.crear_canales(config, "token", "chat")

    assert list(canales) == ["telegram"]
    assert "Canal movil: tipo desconocido «whatsapp»" in caplog.text


def test_correo_sin_datos_smtp_no_se_crea(monkeypatch, caplog):
    preparar(monkeypatch, smtp=None)
    config = {"canales": {"tienda": {"tipo": "correo", "para": "dueno@tienda.example"}}}

    canales = channels.crear_canales(config, "token", "chat")

    assert "tienda" not in canales
    assert "Canal tienda: faltan los datos SMTP en .env" in caplog.text


def test_sin_canales_de_correo_no_se_lee_smtp(monkeypatch):
    preparar(monkeypatch)
    lecturas = []
    monkeypatch.setattr(channels, "cargar_smtp", lambda: lecturas.append("leído"))
    monkeypatch.setenv("DISCORD_WEBHOOK_EQUIPO", WEBHOOK)
    config = {"canales": {"equipo": {"tipo": "discord", "variable": "DISCORD_WEBHOOK_EQUIPO"}}}

    channels.crear_canales(config, "token", "chat")

    assert lecturas == []


def test_destinos_de_la_web_por_defecto_y_telegram():
    config = {"avisos": ["telegram", "equipo"]}

    assert channels.destinos({"avisos": ["tienda"]}, config) == ["tienda"]
    assert channels.destinos({}, config) == ["telegram", "equipo"]
    assert channels.destinos({}, {}) == ["telegram"]


def canales_falsos(enviados, falla=()):
    def canal(nombre):
        def enviar(texto):
            enviados.append((nombre, texto))
            return nombre not in falla

        return enviar

    return {nombre: canal(nombre) for nombre in ["telegram", "equipo", "tienda"]}


def test_avisar_envia_a_cada_canal_de_la_lista():
    enviados = []

    assert channels.avisar(canales_falsos(enviados), ["equipo", "tienda"], "🔴 Caída") is True
    assert enviados == [("equipo", "🔴 Caída"), ("tienda", "🔴 Caída")]


def test_un_canal_desconocido_no_impide_los_demas(caplog):
    enviados = []

    channels.avisar(canales_falsos(enviados), ["tiendaa", "equipo"], "🔴 Caída")

    assert enviados == [("equipo", "🔴 Caída")]
    assert "Canal desconocido en avisos: tiendaa" in caplog.text


def test_sin_canales_validos_avisa_por_telegram():
    enviados = []

    channels.avisar(canales_falsos(enviados), ["tiendaa"], "🔴 Caída")

    assert enviados == [("telegram", "🔴 Caída")]


def test_un_canal_que_falla_no_bloquea_al_siguiente():
    enviados = []
    canales = canales_falsos(enviados, falla=["equipo"])

    assert channels.avisar(canales, ["equipo", "tienda"], "🔴 Caída") is False
    assert enviados == [("equipo", "🔴 Caída"), ("tienda", "🔴 Caída")]
