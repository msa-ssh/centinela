# Centinela

[![CI](https://github.com/msa-ssh/centinela/actions/workflows/ci.yml/badge.svg)](https://github.com/msa-ssh/centinela/actions/workflows/ci.yml)

Vigila tus webs y te avisa por Telegram antes de que tus clientes noten que algo falla.

Centinela revisa cada pocos minutos que tus webs respondan y que su certificado HTTPS no esté a punto de caducar. Solo te escribe cuando algo cambia: cuando una web cae, cuando se recupera y, si sigue caída, con un recordatorio cada pocas horas.

## Cómo se ve un aviso

```
🔴 Caída: Mi tienda (ConnectionError)
🔴 Sigue caída: Mi tienda desde 2026-10-15T08:00:00 (ConnectionError)
🟢 Recuperada: Mi tienda (estuvo caída 35 min)
🟡 Certificado de Mi tienda: caduca en 9 días
```

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

El contenedor se ejecuta con un usuario sin privilegios, se reinicia solo y guarda su estado en un volumen de Docker.

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

Las plantillas de `deploy/systemd/` ejecutan una revisión cada 5 minutos como unidades de usuario, sin `sudo`:

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/centinela.service deploy/systemd/centinela.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now centinela.timer
loginctl enable-linger "$USER"
```

Los registros se leen con `journalctl --user -u centinela`.

## Configuración

`.env` guarda las credenciales de Telegram y nunca se sube a Git:

```
TELEGRAM_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
```

`config.toml` define qué webs vigilar y cuándo avisar:

| Clave | Qué hace |
| --- | --- |
| `intervalo_minutos` | Minutos entre revisiones en modo `--bucle` (Docker) |
| `timeout_segundos` | Tiempo máximo de espera por web |
| `dias_aviso_certificado` | Avisa si el certificado caduca en menos días |
| `horas_entre_avisos_certificado` | Horas entre avisos del mismo certificado |
| `horas_recordatorio_caida` | Horas entre recordatorios de una web caída (0 los desactiva) |

Cada web es un bloque `[[sitio]]` con `nombre` y `url`.

## Uso

```bash
python -m centinela            # una revisión
python -m centinela --bucle    # revisa cada intervalo_minutos, sin fin
python -m centinela --prueba   # envía un mensaje de prueba
```

## Desarrollo

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## Hoja de ruta

- Vigilar disco, RAM y CPU de un servidor.
- Comprobar que una página contiene un texto concreto.
- Más canales de aviso: correo y Discord.
- Resumen semanal con el porcentaje de disponibilidad.
- Página de estado pública.

## Licencia

[MIT](LICENSE)
