"""Informe semanal de Centinela: el porcentaje de disponibilidad de cada web."""

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
UMBRAL_BUENO = 99


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
