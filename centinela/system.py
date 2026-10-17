"""Recursos del servidor: disco, RAM y carga de CPU con psutil."""
import psutil


def medir(discos):
    """Devuelve [(clave, tipo, etiqueta, porcentaje)] de cada disco, la RAM y la carga."""
    medidas = []
    for ruta in discos:
        uso = psutil.disk_usage(ruta).percent
        medidas.append((f"servidor:disco:{ruta}", "disco", f"Disco {ruta}", uso))
    medidas.append(("servidor:ram", "ram", "RAM", psutil.virtual_memory().percent))
    _uno, cinco, _quince = psutil.getloadavg()
    carga = round(cinco / (psutil.cpu_count() or 1) * 100, 1)
    medidas.append(("servidor:carga", "carga", "Carga", carga))
    return medidas
