"""Reglas de aviso de Centinela: deciden qué mensajes enviar."""
from datetime import datetime, timedelta


def ha_pasado(marca, horas, ahora):
    """True si nunca se avisó o si desde la marca han pasado al menos esas horas."""
    if marca is None:
        return True
    return ahora - datetime.fromisoformat(marca) >= timedelta(hours=horas)


def decidir_avisos(nombre, antes, ok, detalle, dias, ahora, config):
    """Compara el estado anterior de una web con el actual. Devuelve (avisos, nuevo)."""
    avisos = []
    nuevo = dict(antes)
    marca = ahora.isoformat(timespec="seconds")

    if not antes or antes["ok"] != ok:
        nuevo["ok"] = ok
        nuevo["desde"] = marca
        if not ok:
            avisos.append(f"🔴 Caída: {nombre} ({detalle})")
            nuevo["ultimo_aviso"] = marca
        elif antes:
            minutos = int((ahora - datetime.fromisoformat(antes["desde"])).total_seconds() // 60)
            avisos.append(f"🟢 Recuperada: {nombre} (estuvo caída {minutos} min)")
    elif not ok:
        horas = config["horas_recordatorio_caida"]
        if horas > 0 and ha_pasado(antes.get("ultimo_aviso"), horas, ahora):
            avisos.append(f"🔴 Sigue caída: {nombre} desde {antes['desde']} ({detalle})")
            nuevo["ultimo_aviso"] = marca

    if dias is not None and dias < config["dias_aviso_certificado"]:
        horas = config["horas_entre_avisos_certificado"]
        if ha_pasado(antes.get("aviso_certificado"), horas, ahora):
            avisos.append(f"🟡 Certificado de {nombre}: caduca en {dias} días")
            nuevo["aviso_certificado"] = marca

    return avisos, nuevo


def con_coma(valor):
    """Escribe un número con coma decimal y sin ceros sobrantes: 93.5 -> '93,5', 90.0 -> '90'."""
    return f"{valor:g}".replace(".", ",")


def decidir_avisos_recurso(servidor, etiqueta, antes, valor, limite, ahora, config):
    """Compara un recurso del servidor con su límite. Devuelve (avisos, nuevo)."""
    avisos = []
    nuevo = dict(antes)
    marca = ahora.isoformat(timespec="seconds")
    ok = valor <= limite
    texto = f"{etiqueta} de {servidor} al {con_coma(valor)} % (límite {con_coma(limite)} %)"

    if not antes or antes["ok"] != ok:
        nuevo["ok"] = ok
        nuevo["desde"] = marca
        if not ok:
            avisos.append(f"🟠 {texto}")
            nuevo["ultimo_aviso"] = marca
        elif antes:
            avisos.append(f"🟢 {etiqueta} de {servidor} vuelve al {con_coma(valor)} %")
    elif not ok:
        horas = config["horas_recordatorio_caida"]
        if horas > 0 and ha_pasado(antes.get("ultimo_aviso"), horas, ahora):
            avisos.append(f"🟠 Sigue alto: {texto}")
            nuevo["ultimo_aviso"] = marca

    return avisos, nuevo
