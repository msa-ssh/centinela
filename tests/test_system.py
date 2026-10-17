from types import SimpleNamespace

from centinela import system


def preparar(monkeypatch, discos=None, ram=60.1, carga=(0.5, 2.0, 1.0), nucleos=4):
    discos = discos or {"/": 45.2}
    monkeypatch.setattr(
        system.psutil, "disk_usage", lambda ruta: SimpleNamespace(percent=discos[ruta])
    )
    monkeypatch.setattr(system.psutil, "virtual_memory", lambda: SimpleNamespace(percent=ram))
    monkeypatch.setattr(system.psutil, "getloadavg", lambda: carga)
    monkeypatch.setattr(system.psutil, "cpu_count", lambda: nucleos)


def test_medir_disco_ram_y_carga(monkeypatch):
    preparar(monkeypatch)
    assert system.medir(["/"]) == [
        ("servidor:disco:/", "disco", "Disco /", 45.2),
        ("servidor:ram", "ram", "RAM", 60.1),
        ("servidor:carga", "carga", "Carga", 50.0),
    ]


def test_medir_varios_discos(monkeypatch):
    preparar(monkeypatch, discos={"/": 45.2, "/home": 91.0})
    medidas = system.medir(["/", "/home"])
    assert medidas[:2] == [
        ("servidor:disco:/", "disco", "Disco /", 45.2),
        ("servidor:disco:/home", "disco", "Disco /home", 91.0),
    ]


def test_medir_sin_discos(monkeypatch):
    preparar(monkeypatch)
    tipos = [tipo for _clave, tipo, _etiqueta, _valor in system.medir([])]
    assert tipos == ["ram", "carga"]


def test_la_carga_usa_la_media_de_5_minutos(monkeypatch):
    preparar(monkeypatch, carga=(9.0, 6.0, 0.1), nucleos=4)
    assert system.medir([])[-1] == ("servidor:carga", "carga", "Carga", 150.0)


def test_la_carga_sin_saber_los_nucleos(monkeypatch):
    preparar(monkeypatch, carga=(0.0, 0.5, 0.0), nucleos=None)
    assert system.medir([])[-1] == ("servidor:carga", "carga", "Carga", 50.0)
