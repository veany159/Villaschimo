#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Villas Chimo — sincronización del calendario de Airbnb.

Lee los links .ics que estén puestos en contenido/config.json (sección "airbnb"),
los descarga, saca las fechas ocupadas y las escribe en contenido/disponibilidad.json.

Se ejecuta solo una vez al día desde GitHub. También se puede correr a mano:
    python3 scripts/sync_airbnb.py

Si un link está vacío, esa casa se deja como está y se respeta lo que hayas
escrito a mano. Si un link falla, no se borra nada: se conserva lo último bueno.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(RAIZ, "contenido", "config.json")
DISPO = os.path.join(RAIZ, "contenido", "disponibilidad.json")

TIEMPO_ESPERA = 30
AGENTE = "VillasChimo-CalendarSync/1.0"


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def descargar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=TIEMPO_ESPERA) as r:
        return r.read().decode("utf-8", "replace")


def desdoblar(texto):
    """Las líneas de un .ics se parten; las que empiezan con espacio continúan la anterior."""
    lineas = []
    for linea in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if linea[:1] in (" ", "\t") and lineas:
            lineas[-1] += linea[1:]
        else:
            lineas.append(linea)
    return lineas


def a_fecha(valor):
    valor = valor.strip()
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", valor)
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def fechas_ocupadas(ics):
    """Devuelve el conjunto de días ocupados. DTEND en Airbnb es el día de salida,
    y ese día la casa vuelve a estar libre, así que no se cuenta."""
    ocupadas = set()
    inicio = fin = None
    dentro = False

    for linea in desdoblar(ics):
        arriba = linea.upper()
        if arriba.startswith("BEGIN:VEVENT"):
            dentro, inicio, fin = True, None, None
        elif arriba.startswith("END:VEVENT"):
            if inicio and fin:
                d = inicio
                while d < fin:
                    ocupadas.add(d)
                    d += timedelta(days=1)
            elif inicio:
                ocupadas.add(inicio)
            dentro = False
        elif dentro:
            if arriba.startswith("DTSTART"):
                inicio = a_fecha(linea.split(":", 1)[-1])
            elif arriba.startswith("DTEND"):
                fin = a_fecha(linea.split(":", 1)[-1])
    return ocupadas


def main():
    cfg = leer(CONFIG)
    dispo = leer(DISPO)
    enlaces = {k: v for k, v in (cfg.get("airbnb") or {}).items() if not k.startswith("_")}

    if not any(enlaces.values()):
        print("No hay links de Airbnb en config.json. La disponibilidad se queda como está.")
        return 0

    hoy = date.today()
    limite = hoy + timedelta(days=550)
    cambios = 0

    for casa, url in enlaces.items():
        if not url:
            print("· %s: sin link, se respeta lo que esté a mano." % casa)
            continue
        try:
            ics = descargar(url)
        except Exception as err:                       # noqa: BLE001
            print("· %s: no se pudo descargar (%s). Se conserva lo anterior." % (casa, err),
                  file=sys.stderr)
            continue

        dias = sorted(d for d in fechas_ocupadas(ics) if hoy <= d <= limite)
        dispo.setdefault("casas", {}).setdefault(casa, {})
        dispo["casas"][casa]["ocupadas"] = [d.isoformat() for d in dias]
        dispo["casas"][casa]["fuente"] = "airbnb"
        cambios += 1
        print("· %s: %d días ocupados." % (casa, len(dias)))

    if cambios:
        dispo["fuente"] = "airbnb"
        dispo["actualizado"] = datetime.now().strftime("%d/%m/%Y")
        guardar(DISPO, dispo)
        print("Disponibilidad actualizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
