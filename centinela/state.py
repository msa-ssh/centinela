"""Estado de Centinela entre ejecuciones: estado.json."""
import json
import sys
from pathlib import Path


def cargar_estado(ruta="estado.json"):
    """Devuelve el último estado guardado, o un diccionario vacío si no hay."""
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"{ruta} está dañado; se empieza de cero", file=sys.stderr)
        return {}


def guardar_estado(estado, ruta="estado.json"):
    """Escribe el estado en estado.json."""
    texto = json.dumps(estado, indent=2, ensure_ascii=False)
    Path(ruta).write_text(texto + "\n", encoding="utf-8")
