"""Informe semanal de Centinela: el porcentaje de disponibilidad de cada web."""
from datetime import timedelta

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
UMBRAL_BUENO = 99
DIA_INFORME = 0  # lunes
HORA_INFORME = 9


def fecha_corta(fecha):
    """Devuelve la fecha como '12 oct', sin depender del idioma del sistema."""
    return f"{fecha.day} {MESES[fecha.month - 1]}"


def porcentaje(buenas, total):
    """Porcentaje con un decimal, redondeado hacia abajo para no mostrar 100 si hubo fallos."""
    return buenas * 1000 // total / 10


def formatear_informe(filas, desde, hasta):
    """Convierte las filas de disponibilidad() en el texto del informe."""
    lineas = [f"📊 Informe semanal ({fecha_corta(desde)} – {fecha_corta(hasta)})"]
    if not filas:
        lineas.append("Sin datos en este periodo")
    for nombre, _url, total, buenas in filas:
        valor = porcentaje(buenas, total)
        icono = "✅" if valor >= UMBRAL_BUENO else "❌"
        texto = f"{valor:g}".replace(".", ",")
        lineas.append(f"{icono} {nombre}: {texto} % ({buenas} de {total} rondas)")
    return "\n".join(lineas)


def cita_mas_reciente(ahora):
    """Devuelve el último lunes a las 9:00 que no sea posterior a ahora."""
    dias_atras = (ahora.weekday() - DIA_INFORME) % 7
    cita = (ahora - timedelta(days=dias_atras)).replace(
        hour=HORA_INFORME, minute=0, second=0, microsecond=0
    )
    if cita > ahora:
        cita -= timedelta(days=7)
    return cita


def toca_informe(ultimo, ahora):
    """True si el último informe se envió antes de la cita más reciente."""
    return ultimo < cita_mas_reciente(ahora)
