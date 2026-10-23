# Centinela

[![CI](https://github.com/msa-ssh/centinela/actions/workflows/ci.yml/badge.svg)](https://github.com/msa-ssh/centinela/actions/workflows/ci.yml)

Vigila tus webs y te avisa por Telegram, correo o Discord antes de que tus clientes noten que algo falla.

Centinela revisa cada pocos minutos que tus webs respondan, que muestren lo que deben (por ejemplo, el botón "Añadir al carrito") y que su certificado HTTPS no esté a punto de caducar. También vigila el disco, la RAM y la carga del servidor donde se ejecuta. Solo te escribe cuando algo cambia: cuando una web cae, cuando se recupera y, si sigue caída, con un recordatorio cada pocas horas. Y cada lunes te manda un informe con el porcentaje de tiempo que cada web estuvo disponible y cómo estuvieron el disco, la RAM y la carga del servidor durante la semana. Cada web puede avisar a sus propios destinos, así que con un solo Centinela cada cliente recibe solo lo suyo, por el canal que prefiera.

## Cómo se ve un aviso

![Avisos de Centinela en Telegram: caída, recuperación, certificado e informe semanal](docs/avisos.jpg)

```
🔴 Caída: Mi tienda (ConnectionError)
🔴 Caída: Mi tienda (falta el texto «Añadir al carrito»)
🔴 Sigue caída: Mi tienda desde 2026-10-15T08:00:00 (ConnectionError)
🟢 Recuperada: Mi tienda (estuvo caída 35 min)
🟡 Certificado de Mi tienda: caduca en 9 días
🟠 Disco / de Servidor web al 93,5 % (límite 90 %)
🟢 Disco / de Servidor web vuelve al 71 %
📊 Informe semanal (8 oct – 15 oct)
✅ Blog: 100 % (2016 de 2016 rondas)
✅ Mi tienda: 99,6 % (2009 de 2016 rondas)
🖥️ Servidor web
✅ Disco /: media 46,2 %, máximo 48 %
🟠 RAM: media 71,4 %, máximo 93,1 % (4 rondas por encima del límite)
✅ Carga: media 8,3 %, máximo 57 %
```

El porcentaje se redondea hacia abajo: una web con un solo fallo en la semana nunca aparece al 100 %.

## Instalación con Docker

Necesitas Docker con el plugin `compose` y un bot de Telegram (créalo con [@BotFather](https://t.me/BotFather)).

```bash
git clone https://github.com/msa-ssh/centinela.git
cd centinela
cp .env.example .env
cp config.example.toml config.toml
chmod 600 .env
```

Rellena `.env` y `config.toml` (ver [Configuración](#configuración)) y arranca:

```bash
docker compose up -d
docker compose logs -f
```

El contenedor se ejecuta con un usuario sin privilegios, se reinicia solo y guarda su estado y su historial en un volumen de Docker. El informe semanal lo envía el propio contenedor cada lunes a las 9:00, en la zona horaria de `TZ`.

`compose.yaml` entrega `.env` al contenedor al arrancar (`env_file`): los secretos nunca se copian dentro de la imagen.

Dentro de un contenedor, la RAM y la carga que se ven son las de la máquina anfitriona, y el disco `/` es el que usa Docker para sus datos. Para vigilar con precisión los discos de un servidor, usa la instalación con systemd.

## Alternativa con systemd

Sin Docker, en cualquier Linux con Python 3.11 o superior:

```bash
git clone https://github.com/msa-ssh/centinela.git ~/proyectos/centinela
cd ~/proyectos/centinela
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && cp config.example.toml config.toml && chmod 600 .env
.venv/bin/python -m centinela --prueba
```

Las plantillas de `deploy/systemd/` son unidades de usuario, sin `sudo`: `centinela.timer` ejecuta una revisión cada 5 minutos y `centinela-informe.timer` envía el informe semanal los lunes a las 9:00 (si el equipo estaba apagado, al arrancar):

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/centinela*.service deploy/systemd/centinela*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now centinela.timer centinela-informe.timer
loginctl enable-linger "$USER"
```

Los registros se leen con `journalctl --user -u centinela` y `journalctl --user -u centinela-informe`.

## Configuración

`.env` guarda las credenciales y la zona horaria, y nunca se sube a Git. Telegram es obligatorio; Discord y el correo, solo si los usas (ver [Canales de aviso](#canales-de-aviso)):

```
TELEGRAM_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
TZ=UTC
DISCORD_WEBHOOK_EQUIPO=https://discord.com/api/webhooks/...
SMTP_SERVIDOR=smtp.gmail.com
SMTP_PUERTO=587
SMTP_USUARIO=centinela@example.com
SMTP_CLAVE=contraseña-de-aplicación
```

`TZ` es la zona horaria de quien recibe los avisos (por ejemplo `Europe/Madrid`; ver la [lista de zonas](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)). Distingue mayúsculas: si está mal escrita, se usa UTC sin avisar.

`config.toml` define qué webs vigilar y cuándo avisar:

| Clave | Qué hace |
| --- | --- |
| `intervalo_minutos` | Minutos entre revisiones en modo `--bucle` (Docker) |
| `timeout_segundos` | Tiempo máximo de espera por web |
| `dias_aviso_certificado` | Avisa si el certificado caduca en menos días |
| `horas_entre_avisos_certificado` | Horas entre avisos del mismo certificado |
| `horas_recordatorio_caida` | Horas entre recordatorios de una web caída (0 los desactiva) |
| `dias_historial` | Días que se guardan en `historial.db` (webs y recursos del servidor) para el informe (90 si falta) |

Cada web es un bloque `[[sitio]]` con `nombre` y `url`. Con `texto`, además, la web cuenta como caída si responde pero su HTML no contiene ese texto (distingue mayúsculas; elige un texto que aparezca tal cual en el código fuente de la página):

```toml
[[sitio]]
nombre = "Mi tienda"
url = "https://mitienda.example"
texto = "Añadir al carrito"
```

Para vigilar el servidor donde corre Centinela, añade al final una tabla `[servidor]`. Sin ella, no se mide nada:

```toml
[servidor]
nombre = "Servidor web"
discos = ["/"]
disco_max = 90
ram_max = 90
carga_max = 100
```

| Clave | Qué hace |
| --- | --- |
| `nombre` | Nombre del servidor en los avisos |
| `discos` | Rutas cuyo disco se vigila (`["/"]` si falta) |
| `disco_max` | Porcentaje de disco usado a partir del cual avisa (90 si falta) |
| `ram_max` | Porcentaje de RAM usada a partir del cual avisa (90 si falta) |
| `carga_max` | Carga media de 5 minutos dividida entre los núcleos, en porcentaje (100 si falta) |

Avisa al pasar el límite, recuerda cada `horas_recordatorio_caida` si sigue alto y avisa cuando vuelve a la normalidad. Cada revisión deja en el registro una línea como `🖥️ Servidor web: Disco / 46,5 %, RAM 40,9 %, Carga 6,1 %` y guarda las medidas en `historial.db`. El informe semanal resume cada recurso: la media, el máximo y cuántas rondas pasó de su límite (🟠 si alguna lo pasó).

## Canales de aviso

Sin más configuración, todo llega al chat de Telegram de `.env`, que es el canal `telegram`. Para avisar también por Discord, por correo o a otro chat de Telegram, define cada canal en `config.toml` con un nombre y elige a quién avisa cada web con `avisos`:

```toml
avisos = ["telegram"]

[canales.discord_equipo]
tipo = "discord"
variable = "DISCORD_WEBHOOK_EQUIPO"

[canales.correo_tienda]
tipo = "correo"
para = "dueno@mitienda.example"

[canales.telegram_socio]
tipo = "telegram"
variable = "TELEGRAM_CHAT_ID_SOCIO"

[[sitio]]
nombre = "Mi tienda"
url = "https://mitienda.example"
avisos = ["telegram", "correo_tienda"]

[servidor]
nombre = "Servidor web"
avisos = ["telegram", "discord_equipo"]
```

- `avisos` arriba del todo (antes de cualquier tabla) son los destinos por defecto: los de las webs sin lista propia y los del informe semanal. Si falta, es `["telegram"]`.
- `avisos` dentro de un `[[sitio]]` o de `[servidor]` sustituye a la lista por defecto.
- `variable` es el **nombre** de una línea de `.env`, nunca el secreto: la URL de un webhook de Discord funciona como una contraseña.
- Un canal de `tipo = "telegram"` usa el mismo bot con otro `chat_id`, por ejemplo el grupo de un cliente.
- El correo sale por SMTP con STARTTLS (puerto 587), con los datos `SMTP_*` de `.env`.
- Si un canal está mal configurado, o una lista nombra uno que no existe, se registra un `ERROR` y el aviso llega igual: si no queda ningún destino válido, va a `telegram`. Un canal que falla no impide que los demás reciban el aviso.

**Webhook de Discord:** en el servidor de Discord, editar el canal → Integraciones → Webhooks → Nuevo webhook → Copiar URL del webhook, y pegarla en `.env`.

**Correo con Gmail:** usa una cuenta dedicada, activa la verificación en dos pasos (vale una app de autenticación) y crea una contraseña de aplicación en [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). Esa contraseña, sin espacios, va en `SMTP_CLAVE`; nunca la contraseña de la cuenta.

## Uso

```bash
python -m centinela            # una revisión
python -m centinela --bucle    # revisa cada intervalo_minutos, sin fin
python -m centinela --prueba   # envía un mensaje de prueba por cada canal
python -m centinela --informe  # envía ahora el informe de los últimos 7 días
```

## Desarrollo

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Hoja de ruta

- Vigilar varios servidores desde un solo Centinela.
- Zona horaria por web, para vigilar a clientes de varios países.
- Página de estado pública.

## Licencia

[MIT](LICENSE)
