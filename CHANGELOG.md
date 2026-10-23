# Cambios

Todos los cambios importantes de Centinela, de la versión más nueva a la más antigua. Las versiones siguen el [versionado semántico](https://semver.org/lang/es/): el tercer número cambia con los arreglos, el segundo con las funciones nuevas y el primero con los cambios que obligan a tocar la configuración.

## [1.0.0] - sin publicar

### Añadido

- `--comprobar` revisa `config.toml` y `.env` sin enviar nada: claves desconocidas (con la más parecida como pista), valores fuera de rango, URLs, canales inexistentes, variables que faltan y permisos de los archivos. Nunca muestra un secreto.
- `--version` y este archivo de cambios.
- Guía "Empieza en 5 minutos" en el README.
- `--salud` y un `HEALTHCHECK` en la imagen: `docker compose ps` muestra `healthy` si la última ronda fue reciente.

### Cambiado

- Los ejemplos de configuración usan `TZ=UTC` y direcciones `example.com`.
- El contenedor se ejecuta con el sistema de archivos de solo lectura, sin capacidades de Linux, sin poder ganar privilegios y con límites de memoria, CPU y procesos.
- La imagen base se fija por su resumen `sha256`, además de por su etiqueta.
- El CI solo tiene permiso de lectura, usa acciones fijadas por el hash de su commit y comprueba que la imagen de Docker se construye.
- Dependabot propone cada semana las actualizaciones de las dependencias de Python, la imagen base y las acciones del CI.

## [0.9.0] - 2026-10-23

### Añadido

- El informe semanal incluye el disco, la RAM y la carga del servidor: media, máximo y rondas por encima del límite.
- Las medidas del servidor se guardan en `historial.db` en cada ronda.

## [0.8.0] - 2026-10-18

### Añadido

- Avisos por Discord (webhook) y por correo (SMTP con STARTTLS).
- Canales con nombre en `[canales]` y destinos propios para cada web y para el servidor con `avisos`.
- `--prueba` envía un mensaje por cada canal y dice cuál falla.

## [0.7.0] - 2026-10-17

### Añadido

- Clave `texto` en cada web: si responde pero no muestra ese texto, cuenta como caída.
- Vigilancia del disco, la RAM y la carga del servidor en `[servidor]`, con avisos al pasar el límite y al volver a la normalidad.

## [0.6.0] - 2026-10-16

### Añadido

- Historial de cada ronda en SQLite e informe semanal de disponibilidad los lunes a las 9:00 (`--informe` para enviarlo en el momento).
- `TZ` en `.env` para la hora de los avisos y del informe.

## [0.5.0] - 2026-10-16

### Añadido

- Imagen de Docker con un usuario sin privilegios y `compose.yaml`.
- Modo `--bucle` para ejecutarse sin systemd.
- Tests con pytest, linter ruff y CI en GitHub Actions.

## [0.4.0] - 2026-10-15

### Añadido

- Ejecución automática cada 5 minutos con un servicio y un timer de systemd.
- Registro con niveles y prioridades del journal.

## [0.3.0] - 2026-10-15

### Añadido

- Configuración en `config.toml`.
- Aviso de certificados HTTPS a punto de caducar.
- Estado entre rondas: avisa al caer y al recuperarse, con un recordatorio si sigue caída.

## [0.2.0] - 2026-10-15

### Añadido

- Avisos por Telegram con el token y el chat en `.env`, y `--prueba`.

## [0.1.0] - 2026-10-14

### Añadido

- Revisión de webs desde la terminal: si responden, su código HTTP y cuánto tardan.
