#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Villas Chimo — generador del sitio.

Lee todo de la carpeta contenido/ y de diario/, y escribe las páginas HTML
en la raíz (español) y en en/ (inglés). No necesita instalar nada: solo Python.

Para correrlo a mano:   python3 build.py
En GitHub se corre solo cada vez que guardas un cambio.
"""

import json
import os
import re
import shutil
import html as _html
from datetime import date, datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
CONTENIDO = os.path.join(RAIZ, "contenido")
DIARIO = os.path.join(RAIZ, "diario")

# páginas generadas (se borran y se vuelven a escribir en cada corrida)
PAGINAS = ["index.html", "villa-chimo.html", "depa-vallarta.html",
           "chimo.html", "experiencias.html", "diario.html", "reservar.html"]


# --------------------------------------------------------------- utilidades
def leer_json(nombre):
    with open(os.path.join(CONTENIDO, nombre), encoding="utf-8") as f:
        return json.load(f)


def e(s):
    """Escapa texto para meterlo en HTML."""
    return _html.escape(str("" if s is None else s), quote=True)


def parrafos(texto, clase="lead"):
    """Convierte un texto con renglones en blanco en varios párrafos."""
    trozos = [t.strip() for t in str(texto or "").split("\n\n") if t.strip()]
    return "".join('<p class="%s">%s</p>' % (clase, e(t)) for t in trozos)


def slugificar(s):
    s = re.sub(r"[^\w\s-]", "", str(s).lower(), flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", s).strip("-")


# ------------------------------------------------------------ markdown mini
def markdown(texto):
    """Convertidor mínimo: encabezados, párrafos, listas, tablas, citas, enlaces."""
    def en_linea(t):
        t = e(t)
        t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1" loading="lazy">', t)
        t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        return t

    salida, buffer_p, lista, tipo_lista, tabla = [], [], [], None, []

    def cerrar_parrafo():
        if buffer_p:
            salida.append("<p>" + en_linea(" ".join(buffer_p)) + "</p>")
            buffer_p.clear()

    def cerrar_lista():
        nonlocal tipo_lista
        if lista:
            etq = "ol" if tipo_lista == "ol" else "ul"
            salida.append("<%s>%s</%s>" % (etq, "".join("<li>%s</li>" % en_linea(x) for x in lista), etq))
            lista.clear()
            tipo_lista = None

    def cerrar_tabla():
        if not tabla:
            return
        filas = [f for f in tabla if not re.match(r"^\s*\|[\s:|-]+\|\s*$", f)]
        if filas:
            celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas]
            cab = "".join("<th>%s</th>" % en_linea(c) for c in celdas[0])
            cuerpo = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % en_linea(c) for c in fila)
                for fila in celdas[1:])
            salida.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (cab, cuerpo))
        tabla.clear()

    for linea in texto.split("\n"):
        cruda = linea.rstrip()

        if cruda.strip().startswith("|"):
            cerrar_parrafo(); cerrar_lista()
            tabla.append(cruda)
            continue
        cerrar_tabla()

        if not cruda.strip():
            cerrar_parrafo(); cerrar_lista()
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", cruda)
        if m:
            cerrar_parrafo(); cerrar_lista()
            n = min(len(m.group(1)) + 1, 4)  # el h1 lo pone la plantilla
            salida.append("<h%d>%s</h%d>" % (n, en_linea(m.group(2)), n))
            continue

        if re.match(r"^\s*>\s?", cruda):
            cerrar_parrafo(); cerrar_lista()
            salida.append("<blockquote>%s</blockquote>" % en_linea(re.sub(r"^\s*>\s?", "", cruda)))
            continue

        if re.match(r"^\s*(---|\*\*\*)\s*$", cruda):
            cerrar_parrafo(); cerrar_lista()
            salida.append("<hr>")
            continue

        m = re.match(r"^\s*[-*]\s+(.*)$", cruda)
        if m:
            cerrar_parrafo()
            if tipo_lista == "ol":
                cerrar_lista()
            tipo_lista = "ul"
            lista.append(m.group(1))
            continue

        m = re.match(r"^\s*\d+[.)]\s+(.*)$", cruda)
        if m:
            cerrar_parrafo()
            if tipo_lista == "ul":
                cerrar_lista()
            tipo_lista = "ol"
            lista.append(m.group(1))
            continue

        buffer_p.append(cruda.strip())

    cerrar_parrafo(); cerrar_lista(); cerrar_tabla()
    return "\n".join(salida)


def leer_entradas(idioma):
    carpeta = os.path.join(DIARIO, idioma)
    if not os.path.isdir(carpeta):
        return []
    entradas = []
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".md"):
            continue
        with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
            crudo = f.read()
        meta, cuerpo = {}, crudo
        if crudo.startswith("---"):
            partes = crudo.split("---", 2)
            if len(partes) >= 3:
                for linea in partes[1].strip().split("\n"):
                    if ":" in linea:
                        k, v = linea.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
                cuerpo = partes[2]
        if meta.get("publicada", "si").lower() in ("no", "false", "0"):
            continue
        meta["slug"] = meta.get("slug") or slugificar(meta.get("titulo", nombre[:-3]))
        meta["html"] = markdown(cuerpo)
        meta["minutos"] = max(1, round(len(re.findall(r"\w+", cuerpo)) / 200))
        entradas.append(meta)
    entradas.sort(key=lambda x: x.get("fecha", ""), reverse=True)
    return entradas


def url_limpia(ruta):
    """index.html sobra en una dirección: la gente enlaza a villaschimo.com/
    y a villaschimo.com/en/, no al archivo. Quitarlo evita que Google vea
    dos direcciones para la misma página."""
    r = str(ruta or "").lstrip("/")
    if r == "index.html":
        return ""
    if r.endswith("/index.html"):
        return r[: -len("index.html")]
    return r


# ---------------------------------------------------------------- plantilla
def cabeza(ctx, titulo, descripcion, imagen=None, canonica=""):
    cfg, L, base = ctx["cfg"], ctx["L"], ctx["base"]
    sitio = (cfg.get("sitio_url") or "").rstrip("/")
    img = imagen or "assets/img/og-villas-chimo.jpg"
    img_abs = (sitio + "/" + img) if sitio else (base + img)

    alterna = ""
    if ctx["alterna"] is not None:
        otro = L["otro_idioma"]
        ruta_alt = ctx.get("alterna_ruta")
        if sitio and ruta_alt and canonica:
            # Google solo lee hreflang con la direccion completa; las relativas las ignora.
            # Cada pagina se apunta a si misma y a su gemela, y el espanol queda de x-default.
            propia = "%s/%s" % (sitio, url_limpia(canonica))
            otra = "%s/%s" % (sitio, url_limpia(ruta_alt))
            predeterminada = propia if L["codigo"] == "es" else otra
            alterna = ('<link rel="alternate" hreflang="%s" href="%s">'
                       '<link rel="alternate" hreflang="%s" href="%s">'
                       '<link rel="alternate" hreflang="x-default" href="%s">') % (
                L["codigo"], e(propia), otro["codigo"], e(otra), e(predeterminada))
        else:
            alterna = '<link rel="alternate" hreflang="%s" href="%s">' % (otro["codigo"], e(ctx["alterna"]))

    plausible = ""
    if cfg.get("analytics", {}).get("plausible_dominio"):
        plausible = '<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>' % \
                    e(cfg["analytics"]["plausible_dominio"])

    canon = ""
    if sitio and canonica:
        canon = '<link rel="canonical" href="%s/%s">' % (sitio, url_limpia(canonica))

    return f"""<!DOCTYPE html>
<html lang="{L['codigo']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descripcion)}">
{canon}
{alterna}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:image" content="{e(img_abs)}">
<meta property="og:locale" content="{'es_MX' if L['codigo'] == 'es' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="{base}assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300..700;1,300..600&family=Karla:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{base}assets/css/site.css">
{plausible}
</head>
<body>
<a class="saltar" href="#contenido">{e(L['ui']['saltar'])}</a>
"""


def encabezado(ctx, activa=""):
    L, base, cfg = ctx["L"], ctx["base"], ctx["cfg"]
    pre = ctx.get("pre", "")
    otro = L["otro_idioma"]
    enlaces = ""
    for it in L["menu"]:
        actual = ' aria-current="page"' if it["url"] == activa else ""
        enlaces += '<a href="%s%s"%s>%s</a>' % (pre, it["url"], actual, e(it["texto"]))

    if ctx["alterna"] is not None:
        idioma_html = '<a class="idioma" href="%s" hreflang="%s">%s</a>' % (
            e(ctx["alterna"]), otro["codigo"], e(otro["nombre"]))
    else:
        idioma_html = ""

    return f"""<header class="head">
<div class="u">
  <a class="marca" href="{pre}index.html">{e(cfg['marca'])}<span>{e(cfg['bajada'])}</span></a>
  <button class="hamb" aria-expanded="false" aria-controls="nav-principal"
          aria-label="{e(L['ui']['menu_abrir'])}"
          data-abrir="{e(L['ui']['menu_abrir'])}" data-cerrar="{e(L['ui']['menu_cerrar'])}">
    <svg viewBox="0 0 18 14" aria-hidden="true"><g stroke="currentColor" stroke-width="1.5"><line x1="0" y1="1" x2="18" y2="1"/><line x1="0" y1="7" x2="18" y2="7"/><line x1="0" y1="13" x2="18" y2="13"/></g></svg>
  </button>
  <nav class="nav" id="nav-principal">{enlaces}</nav>
  {idioma_html}
  <a class="btn" href="{pre}{L['cta_url']}">{e(L['cta'])}</a>
</div>
</header>
"""


def otro_prefijo(ctx):
    """Prefijo de carpeta del idioma actual visto desde la raíz."""
    return "" if ctx["L"]["codigo"] == "es" else "en/"


def pie(ctx):
    L, base, cfg = ctx["L"], ctx["base"], ctx["cfg"]
    pre = ctx.get("pre", "")
    cols = ""
    for c in L["pie"]["columnas"]:
        items = "".join('<li><a href="%s%s">%s</a></li>' % (pre, u, e(t)) for t, u in c["enlaces"])
        cols += '<div><h4>%s</h4><ul>%s</ul></div>' % (e(c["titulo"]), items)

    wa = 'https://wa.me/%s' % e(cfg.get("whatsapp", ""))
    contacto = '<div><h4>%s</h4><ul>' % e(L["pie"]["contacto_titulo"])
    contacto += '<li><a href="%s" rel="noopener" target="_blank">WhatsApp</a></li>' % wa
    if cfg.get("correo"):
        contacto += '<li><a href="mailto:%s">%s</a></li>' % (e(cfg["correo"]), e(cfg["correo"]))
    if cfg.get("instagram"):
        contacto += '<li><a href="%s" rel="noopener" target="_blank">Instagram</a></li>' % e(cfg["instagram"])
    contacto += "</ul></div>"

    return f"""<footer class="pie">
<div class="u">
  <div class="cols">
    <div>
      <span class="marca">{e(cfg['marca'])}<span>{e(cfg['bajada'])}</span></span>
      <p class="desc">{e(L['pie']['descripcion'])}</p>
    </div>
    {cols}
    {contacto}
  </div>
  <div class="base">
    <span>© {date.today().year} {e(L['pie']['derechos'])}</span>
    <span>{' · '.join(e(x) for x in L['pie']['legal'])}</span>
    <span>Español · English</span>
  </div>
</div>
</footer>
"""


def scripts(ctx, con_calendario=False, con_comentarios=False):
    L, base, cfg, props = ctx["L"], ctx["base"], ctx["cfg"], ctx["props"]
    salida = ""

    if con_calendario or con_comentarios:
        conf = {
            "whatsapp": cfg.get("whatsapp", ""),
            "moneda": cfg.get("moneda", "MXN"),
            "supabase": {
                "url": cfg.get("supabase", {}).get("url", ""),
                "clave_publica": cfg.get("supabase", {}).get("clave_publica", ""),
            },
        }
        salida += '<script>window.VC_CONFIG=%s;</script>\n' % json.dumps(conf, ensure_ascii=False)

    if con_calendario:
        casas = {}
        for slug, p in props.items():
            if slug.startswith("_") or not p.get("activa"):
                continue
            t = p.get("tarifas", {})
            f = p.get("ficha", {})
            casas[slug] = {
                "nombre": p[L["codigo"]]["nombre"],
                "baja": t.get("baja", 0),
                "alta": t.get("alta", 0),
                "limpieza": t.get("limpieza", 0),
                "temporada_alta": t.get("temporada_alta", []),
                "min_baja": f.get("minimo_noches_baja", 1),
                "min_alta": f.get("minimo_noches_alta", 1),
            }
        textos = dict(L["ui"])
        textos["solicitud_saludo"] = ("Hola, quiero consultar disponibilidad en"
                                      if L["codigo"] == "es" else
                                      "Hello, I would like to check availability at")
        salida += '<script>window.VC_TEXTOS=%s;window.VC_CASAS=%s;</script>\n' % (
            json.dumps(textos, ensure_ascii=False), json.dumps(casas, ensure_ascii=False))
        salida += '<script src="%sassets/js/calendario.js" defer></script>\n' % base

    if con_comentarios:
        salida += '<script>window.VC_TEXTOS_COM=%s;</script>\n' % json.dumps(L["comentarios"], ensure_ascii=False)
        salida += '<script src="%sassets/js/comentarios.js" defer></script>\n' % base

    salida += '<script src="%sassets/js/site.js" defer></script>\n' % base
    return salida + "</body>\n</html>\n"


# ------------------------------------------------------------------ piezas
def img(ctx, nombre, alt, clase="", ancho=1600, lazy=True):
    base = ctx["base"]
    if not nombre:
        return ""
    return ('<img src="{b}assets/img/{n}.webp" '
            'srcset="{b}assets/img/{n}-800.webp 800w, {b}assets/img/{n}.webp 1600w" '
            'sizes="(max-width:860px) 100vw, {a}px" '
            'alt="{alt}" class="{c}" {l} decoding="async">').format(
        b=base, n=nombre, a=ancho, alt=e(alt), c=clase, l='loading="lazy"' if lazy else "")


ALT_CHIMO = {
    "es": {
        "chimo-bahia-pelicano": "Un pelícano sobre una baliza en la bahía de Chimo, con la sierra al fondo",
        "chimo-espuma-arena": "Espuma del mar deshaciéndose sobre la arena dorada de Chimo",
        "chimo-ola-verde": "Una ola verde rompiendo frente a la playa de Chimo",
        "chimo-playa-palapas": "La playa abierta de Chimo al amanecer, con palapas y la sierra al fondo",
        "chimo-velero": "Un velero navegando la costa sur de la Bahía de Banderas",
        "chimo-atardecer-aereo": "Vista aérea del atardecer sobre la playa, con una persona sola en el agua",
        "chimo-lancha-acantilado": "Una lancha rápida bordeando los acantilados de la costa sur",
        "chimo-pueblo-lanchas": "El pueblo de Chimo visto desde el mar, con las lanchas fondeadas frente a la playa",
    },
    "en": {
        "chimo-bahia-pelicano": "A pelican on a marker in Chimo bay, with the sierra behind",
        "chimo-espuma-arena": "Sea foam breaking over the golden sand of Chimo",
        "chimo-ola-verde": "A green wave breaking off Chimo beach",
        "chimo-playa-palapas": "The open beach at Chimo at dawn, with palapas and the sierra behind",
        "chimo-velero": "A sailboat working the south shore of Banderas Bay",
        "chimo-atardecer-aereo": "Aerial view of sunset over the beach, one person alone in the water",
        "chimo-lancha-acantilado": "A fast boat running the cliffs of the south shore",
        "chimo-pueblo-lanchas": "The village of Chimo seen from the sea, boats moored off the beach",
    },
}


def alt_chimo(ctx, nombre):
    return ALT_CHIMO.get(ctx["L"]["codigo"], {}).get(nombre, "Chimo, Cabo Corrientes")


def alt_de(ctx, slug_casa, nombre_img):
    p = ctx["props"].get(slug_casa, {})
    alts = p.get("es", {}).get("galeria_alt", {})
    return alts.get(nombre_img, p.get(ctx["L"]["codigo"], {}).get("nombre", ""))


def mapa_costa(ctx):
    etiquetas = {
        "es": ["Boca de Tomatlán", "Salida", "Las Ánimas", "10 min", "Quimixto", "15 min",
               "Yelapa", "30 min", "Chimo", "2 h 30 desde Vallarta"],
        "en": ["Boca de Tomatlán", "Start", "Las Ánimas", "10 min", "Quimixto", "15 min",
               "Yelapa", "30 min", "Chimo", "2 h 30 from Vallarta"],
    }[ctx["L"]["codigo"]]
    t = etiquetas
    titulo = ("Mapa de la costa sur de Bahía de Banderas, de Boca de Tomatlán a Chimo"
              if ctx["L"]["codigo"] == "es" else
              "Map of the south shore of Banderas Bay, from Boca de Tomatlán to Chimo")
    return f"""<div class="mapa">
<svg viewBox="0 0 1100 150" width="100%" height="150" role="img" aria-label="{e(titulo)}">
  <path d="M40 34 C 150 20, 210 62, 300 52 S 470 26, 560 60 S 720 96, 820 74 S 990 40, 1060 66"
        fill="none" stroke="#8FB0BF" stroke-width="1.2" stroke-linecap="round" stroke-dasharray="1 5" opacity=".85"/>
  <g font-family="Karla, sans-serif">
    <circle cx="40" cy="34" r="4.5" fill="#FBF9F4"/>
    <text x="40" y="20" font-size="11.5" fill="#FBF9F4">{e(t[0])}</text>
    <text x="40" y="56" font-size="10" fill="#8FB0BF">{e(t[1])}</text>
    <circle cx="300" cy="52" r="3" fill="#8FB0BF"/>
    <text x="300" y="76" font-size="11" fill="#C6D6DD" text-anchor="middle">{e(t[2])}</text>
    <text x="300" y="91" font-size="9.5" fill="#7FA1B1" text-anchor="middle">{e(t[3])}</text>
    <circle cx="560" cy="60" r="3" fill="#8FB0BF"/>
    <text x="560" y="84" font-size="11" fill="#C6D6DD" text-anchor="middle">{e(t[4])}</text>
    <text x="560" y="99" font-size="9.5" fill="#7FA1B1" text-anchor="middle">{e(t[5])}</text>
    <circle cx="820" cy="74" r="3" fill="#8FB0BF"/>
    <text x="820" y="98" font-size="11" fill="#C6D6DD" text-anchor="middle">{e(t[6])}</text>
    <text x="820" y="113" font-size="9.5" fill="#7FA1B1" text-anchor="middle">{e(t[7])}</text>
    <circle cx="1060" cy="66" r="6.5" fill="#A3502F"/>
    <text x="1060" y="46" font-size="14" fill="#FBF9F4" text-anchor="end" font-weight="600">{e(t[8])}</text>
    <text x="1060" y="92" font-size="10" fill="#D8A88E" text-anchor="end">{e(t[9])}</text>
  </g>
</svg>
</div>"""


def bloque_rutas(ctx):
    L = ctx["L"]
    rutas = ""
    for r in L["rutas"]:
        filas = "".join('<div class="fila"><span>%s</span><span>%s</span></div>' % (e(a), e(b))
                        for a, b in r["filas"])
        rutas += '<div class="ruta"><div class="n">%s</div><h3>%s</h3>%s</div>' % (
            e(r["n"]), e(r["titulo"]), filas)
    return f"""<section class="pad fondo-mar" id="como-llegar">
<div class="u">
  <p class="lbl">{e(L['inicio']['llegar']['etiqueta'])}</p>
  <h2 class="h2" style="margin-top:12px">{e(L['inicio']['llegar']['titulo'])}</h2>
  {mapa_costa(ctx)}
  <div class="rutas">{rutas}</div>
  <p class="aviso">{e(L['inicio']['llegar']['aviso'])}</p>
</div>
</section>"""


def bloque_ano(ctx):
    L = ctx["L"]
    c = L["calendario_ano"]
    encabezados = "".join('<td class="mo">%s</td>' % e(m) for m in c["meses_cortos"])
    filas = ""
    for f in c["filas"]:
        celdas, mes = "", 1
        for inicio, largo, texto in sorted(f["tramos"]):
            while mes < inicio:
                celdas += "<td></td>"
                mes += 1
            celdas += '<td colspan="%d"><div class="cb %s">%s</div></td>' % (largo, f["color"], e(texto))
            mes += largo
        while mes <= 12:
            celdas += "<td></td>"
            mes += 1
        filas += '<tr><td class="lb">%s</td>%s</tr>' % (e(f["nombre"]), celdas)

    return f"""<section class="pad pad-top0">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(L['inicio']['ano']['etiqueta'])}</p>
    <h2 class="h2">{e(L['inicio']['ano']['titulo'])}</h2>
  </div>
  <div class="anio">
    <table><tr><td class="lb"></td>{encabezados}</tr>{filas}</table>
  </div>
</div>
</section>"""


def bloque_mapa(ctx, fondo=""):
    L, cfg = ctx["L"], ctx["cfg"]
    U, M = L["ui"], L["mapa"]
    consulta = (cfg.get("mapa") or {}).get("consulta") or "Chimo, Jalisco"
    import urllib.parse as _u
    q = _u.quote_plus(consulta)
    return f"""<section class="pad {fondo}" id="mapa">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(M['etiqueta'])}</p>
    <h2 class="h2">{e(M['titulo'])}</h2>
    <p class="lead">{e(M['texto'])}</p>
  </div>
  <div class="mapa-google" data-mapa data-consulta="{e(q)}">
    <div class="previo">
      <p>{e(U['mapa_aviso'])}</p>
      <button type="button" class="btn claro" data-cargar-mapa>{e(U['ver_mapa'])}</button>
    </div>
    <div class="pie-mapa">
      <span>{e(consulta)}</span>
      <a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">{e(U['abrir_google'])}</a>
    </div>
  </div>
</div>
</section>"""


def bloque_avisos(ctx, fondo="fondo-cal2"):
    L = ctx["L"]
    A = L["avisos"]
    cajas = ""
    for it in A["items"]:
        parrafos = "".join("<p>%s</p>" % e(x) for x in it["parrafos"])
        clase = "verde" if it.get("tipo") == "verde" else ""
        cajas += '<div class="aviso-caja %s"><h3>%s</h3>%s</div>' % (clase, e(it["titulo"]), parrafos)
    return f"""<section class="pad {fondo}">
<div class="u">
  <div class="encabezado"><h2 class="h2">{e(A['titulo'])}</h2></div>
  <div class="avisos">{cajas}</div>
</div>
</section>"""


def bloque_alimentos(ctx, fondo=""):
    L = ctx["L"]
    A = L["alimentos"]
    items = "".join(
        '<div class="alimento"><p class="etq">%s</p><h3>%s</h3><p>%s</p></div>' % (
            e(x["etq"]), e(x["titulo"]), e(x["texto"])) for x in A["items"])
    return f"""<section class="pad {fondo}">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(A['etiqueta'])}</p>
    <h2 class="h2">{e(A['titulo'])}</h2>
    <p class="lead">{e(A['intro'])}</p>
  </div>
  <div class="alimentos">{items}</div>
</div>
</section>"""


def bloque_publico(ctx, fondo=""):
    L = ctx["L"]
    P = L["publico"]
    chips = "".join("<span>%s</span>" % e(x) for x in P["items"])
    return f"""<section class="pad {fondo}">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(P['etiqueta'])}</p>
    <h2 class="h2">{e(P['titulo'])}</h2>
    <p class="lead">{e(P['texto'])}</p>
  </div>
  <div class="publicos">{chips}</div>
</div>
</section>"""


def bloque_faq(ctx, fondo="fondo-cal2"):
    """Bloque citable. Escrito para que un buscador o un asistente de IA pueda
    tomar la respuesta completa y citar el sitio: pregunta literal como
    encabezado, dato numérico en la primera oración."""
    L = ctx["L"]
    F = L["faq"]
    items = "".join(
        '<div class="faq-item"><h3>%s</h3><p>%s</p></div>' % (e(x["p"]), e(x["r"]))
        for x in F["items"])
    datos = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": x["p"],
             "acceptedAnswer": {"@type": "Answer", "text": x["r"]}}
            for x in F["items"]
        ],
    }
    schema = '<script type="application/ld+json">%s</script>' % json.dumps(datos, ensure_ascii=False)
    return f"""<section class="pad {fondo}" id="preguntas">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(F['etiqueta'])}</p>
    <h2 class="h2">{e(F['titulo'])}</h2>
  </div>
  <div class="faqs">{items}</div>
</div>
{schema}
</section>"""


def bloque_precio(ctx):
    L, cfg, props = ctx["L"], ctx["cfg"], ctx["props"]
    R, U = L["reservar"], L["ui"]
    t = props["villa-chimo"].get("tarifas", {})
    precio = t.get("baja") or 0
    moneda = cfg.get("moneda", "MXN")
    if precio:
        cifra = '<b>$%s</b><span>%s · %s · %s</span>' % (
            format(precio, ",d"), e(moneda), e(U["por_noche"]), e(U["mas_impuestos"]))
    else:
        cifra = '<b>%s</b>' % e(U["precio_pendiente"])

    desc = "".join(
        '<div><dt>%s</dt><dd>%s</dd><p>%s</p></div>' % (e(x["dt"]), e(x["dd"]), e(x["p"]))
        for x in R["descuentos"])
    pagos = "".join("<span>%s</span>" % e(x) for x in R["pagos"])

    return f"""<section class="pad pad-top0">
<div class="u">
  <div class="encabezado">
    <p class="lbl">{e(R['precio_etiqueta'])}</p>
    <div class="precio-grande" style="margin-top:12px">{cifra}</div>
    <p class="nota" style="margin-top:12px">{e(R['precio_nota'])}</p>
  </div>

  <h3 class="h3" style="margin-bottom:18px">{e(R['descuentos_titulo'])}</h3>
  <dl class="descuentos">{desc}</dl>

  <h3 class="h3" style="margin:40px 0 12px">{e(R['pagos_titulo'])}</h3>
  <p class="lead">{e(R['pagos_texto'])}</p>
  <div class="pagos">{pagos}</div>
  <p class="nota" style="margin-top:14px">{e(R['pagos_saldo'])}</p>
</div>
</section>"""


def tarjeta_casa(ctx, slug):
    L, props, base = ctx["L"], ctx["props"], ctx["base"]
    p = props[slug]
    d = p[L["codigo"]]
    pre = ctx.get("pre", "")
    t = p.get("tarifas", {})
    f = p.get("ficha", {})

    if p.get("portada"):
        imagen = '<div class="im">%s</div>' % img(ctx, p["portada"], alt_de(ctx, slug, p["portada"]), ancho=600)
    else:
        etiqueta = "Fotografía pendiente" if L["codigo"] == "es" else "Photography pending"
        imagen = '<div class="im sinfoto">%s</div>' % e(etiqueta)

    precio_min = min([x for x in (t.get("baja"), t.get("alta")) if x], default=0)
    if precio_min:
        precio = '<span class="precio">$%s<small>%s</small></span>' % (
            format(precio_min, ",d").replace(",", ","), e(L["ui"]["por_noche"]))
    else:
        precio = '<span class="precio" style="font-size:15px;font-family:var(--sans);color:var(--arena)">%s</span>' % \
                 e(L["ui"]["precio_pendiente"])

    meta = d["lugar"]
    if f.get("recamaras"):
        unidad = "recámaras" if L["codigo"] == "es" else "bedrooms"
        meta += " · %d %s" % (f["recamaras"], unidad)

    return f"""<article class="casa">
  {imagen}
  <div class="cuerpo">
    <h3>{e(d['nombre'])}</h3>
    <p class="meta">{e(meta)}</p>
    <p>{e(d['resumen'])}</p>
    <div class="pie">
      {precio}
      <a class="enlace" href="{pre}{slug}.html">{e(L['ui']['ver_mas'])}</a>
    </div>
  </div>
</article>"""


def bloque_comentarios(ctx):
    L = ctx["L"]
    C = L["comentarios"]
    props = ctx["props"]
    opciones = "".join('<option value="%s">%s</option>' % (e(props[s][L["codigo"]]["nombre"]),
                                                           e(props[s][L["codigo"]]["nombre"]))
                       for s in props if not s.startswith("_") and props[s].get("activa"))
    estrellas = "".join(
        '<button type="button" data-valor="%d" aria-label="%d/5">★</button>' % (i, i) for i in range(1, 6))

    return f"""<section class="pad fondo-cal2" id="comentarios" data-comentarios>
<div class="u">
  <div class="encabezado">
    <h2 class="h2">{e(C['titulo'])}</h2>
    <p class="lead">{e(C['intro'])}</p>
  </div>
  <div class="coms">
    <div class="com-lista" data-com-lista aria-live="polite"></div>
    <form class="form" data-com-form novalidate>
      <div class="dos">
        <div class="campo">
          <label for="c-nombre">{e(C['nombre'])}</label>
          <input id="c-nombre" name="nombre" type="text" maxlength="80" required autocomplete="name">
        </div>
        <div class="campo">
          <label for="c-lugar">{e(C['lugar'])}</label>
          <input id="c-lugar" name="lugar" type="text" maxlength="80" placeholder="{e(C['lugar_ph'])}">
        </div>
      </div>
      <div class="campo">
        <label for="c-casa">{e(C['casa'])}</label>
        <select id="c-casa" name="casa">{opciones}</select>
      </div>
      <div class="campo">
        <span class="label" style="display:block;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--arena);font-weight:700;margin-bottom:7px">{e(C['calificacion'])}</span>
        <div class="estrellas-input" data-estrellas>{estrellas}</div>
      </div>
      <div class="campo">
        <label for="c-texto">{e(C['mensaje'])}</label>
        <textarea id="c-texto" name="texto" maxlength="800" required placeholder="{e(C['mensaje_ph'])}"></textarea>
      </div>
      <div class="trampa" aria-hidden="true">
        <label for="c-web">No llenar</label>
        <input id="c-web" name="sitio_web" type="text" tabindex="-1" autocomplete="off">
      </div>
      <button type="submit" class="btn">{e(C['enviar'])}</button>
      <p class="aviso-form" data-com-aviso role="status"></p>
    </form>
  </div>
</div>
</section>"""


def bloque_calendario(ctx, casa_inicial="villa-chimo", con_selector=True):
    L, props, base = ctx["L"], ctx["props"], ctx["base"]
    U = L["ui"]
    activas = [s for s in props if not s.startswith("_") and props[s].get("activa")]

    selector = ""
    if con_selector and len(activas) > 1:
        etiqueta = "Casa" if L["codigo"] == "es" else "House"
        opciones = "".join('<option value="%s"%s>%s</option>' % (
            s, " selected" if s == casa_inicial else "", e(props[s][L["codigo"]]["nombre"])) for s in activas)
        selector = f"""<div class="campo">
        <span class="k">{e(etiqueta)}</span>
        <select class="v" data-selector-casa aria-label="{e(etiqueta)}">{opciones}</select>
      </div>"""

    maximo = max([props[s].get("ficha", {}).get("huespedes_max") or 4 for s in activas] or [4])
    op_hue = "".join('<option value="%d"%s>%d</option>' % (i, " selected" if i == 2 else "", i)
                     for i in range(1, max(maximo, 4) + 1))

    return f"""<section class="pad" id="calendario">
<div class="u">
  <div class="encabezado">
    <h2 class="h2">{e(U['elige_fechas'])}</h2>
    <p class="nota" data-actualizado></p>
  </div>
  <div class="barra" style="border:1px solid var(--linea-suave);margin-bottom:26px">
    <div class="u" style="padding-left:22px;padding-right:22px;max-width:none">
      {selector}
      <div class="campo">
        <span class="k">{e(U['llegada'])}</span>
        <button type="button" class="v vacio" data-barra-llegada data-ir-calendario>{e(U['elige_fechas'])}</button>
      </div>
      <div class="campo">
        <span class="k">{e(U['salida'])}</span>
        <button type="button" class="v vacio" data-barra-salida data-ir-calendario>{e(U['elige_fechas'])}</button>
      </div>
      <div class="campo">
        <span class="k">{e(U['huespedes'])}</span>
        <select class="v" data-selector-huespedes aria-label="{e(U['huespedes'])}">{op_hue}</select>
      </div>
    </div>
  </div>

  <div class="cal-wrap" data-calendario data-casa="{e(casa_inicial)}" data-base="{base}">
    <div class="cal-cab">
      <button type="button" data-mes="-1" aria-label="{e(U['mes_anterior'])}">&#8592;</button>
      <strong data-rango-meses style="font-family:var(--serif);font-size:19px;font-weight:400;text-transform:capitalize"></strong>
      <button type="button" data-mes="1" aria-label="{e(U['mes_siguiente'])}">&#8594;</button>
    </div>
    <div class="cal-meses" data-meses></div>
    <div class="cal-leyenda">
      <span><i class="l"></i>{e(U['libre'])}</span>
      <span><i class="o"></i>{e(U['ocupado'])}</span>
      <span><i class="s"></i>{e(U['elige_fechas'])}</span>
    </div>
    <div class="resumen" data-resumen></div>
  </div>
</div>
</section>"""


def json_ld(ctx, slug=None, extra=None):
    """Datos estructurados. Es lo que leen Google y los asistentes de IA antes
    que el texto, y lo que decide si te citan a ti o a otro."""
    cfg, L, props = ctx["cfg"], ctx["L"], ctx["props"]
    sitio = (cfg.get("sitio_url") or "").rstrip("/")
    # el numero de wa.me lleva un 1 extra que no es parte del numero real;
    # para Google y los asistentes va el internacional de verdad
    tel = cfg.get("telefono") or (("+" + cfg["whatsapp"]) if cfg.get("whatsapp") else None)
    bloques = []

    if slug:
        p = props[slug]
        d = p[L["codigo"]]
        f = p.get("ficha", {})
        t = p.get("tarifas", {})
        amen = []
        for g in d.get("amenidades", []):
            for x in g["items"]:
                if "confirmar" in x.lower() or "confirmed" in x.lower():
                    continue
                amen.append({"@type": "LocationFeatureSpecification", "name": x, "value": True})

        casa = {
            "@context": "https://schema.org",
            "@type": "VacationRental",
            "name": d["nombre"],
            "description": d["resumen"],
            "address": {"@type": "PostalAddress", "addressLocality": d["lugar"].split(",")[0].strip(),
                        "addressRegion": "Jalisco", "addressCountry": "MX"},
            "containsPlace": {
                "@type": "Accommodation",
                "occupancy": {"@type": "QuantitativeValue", "value": f.get("huespedes") or None},
                "numberOfBedrooms": f.get("recamaras") or None,
                "numberOfBathroomsTotal": f.get("banos") or None,
            },
            "amenityFeature": amen or None,
            "petsAllowed": True if slug == "villa-chimo" else None,
            "telephone": tel,
        }
        if t.get("baja"):
            casa["priceRange"] = "$%s %s" % (t["baja"], cfg.get("moneda", "MXN"))
            casa["offers"] = {
                "@type": "Offer",
                "price": t["baja"],
                "priceCurrency": cfg.get("moneda", "MXN"),
                "availability": "https://schema.org/InStock",
                "priceSpecification": {
                    "@type": "UnitPriceSpecification",
                    "price": t["baja"],
                    "priceCurrency": cfg.get("moneda", "MXN"),
                    "unitCode": "DAY",
                    "valueAddedTaxIncluded": False,
                },
            }
        if sitio:
            casa["url"] = sitio + "/" + otro_prefijo(ctx) + slug + ".html"
            casa["image"] = sitio + "/assets/img/og-villas-chimo.jpg"
        bloques.append(casa)
    else:
        org = {
            "@context": "https://schema.org",
            "@type": "LodgingBusiness",
            "name": cfg["marca"],
            "description": L["inicio"]["descripcion_seo"],
            "address": {"@type": "PostalAddress", "addressLocality": "Chimo",
                        "addressRegion": "Jalisco", "addressCountry": "MX"},
            "areaServed": "Cabo Corrientes, Jalisco, México",
            "telephone": tel,
            "email": cfg.get("correo") or None,
            "sameAs": [cfg.get("instagram")] if cfg.get("instagram") else None,
            "currenciesAccepted": cfg.get("moneda", "MXN"),
            "paymentAccepted": "Transferencia bancaria, tarjeta de crédito, Zelle, PayPal, efectivo",
        }
        if sitio:
            org["url"] = sitio
            org["image"] = sitio + "/assets/img/og-villas-chimo.jpg"
        bloques.append(org)

    if extra:
        bloques.append(extra)

    def limpiar(o):
        if isinstance(o, dict):
            return {k: limpiar(v) for k, v in o.items() if v is not None and limpiar(v) not in ({}, [], None)}
        if isinstance(o, list):
            return [limpiar(x) for x in o if x is not None]
        return o

    return "".join('<script type="application/ld+json">%s</script>' % json.dumps(limpiar(b), ensure_ascii=False)
                   for b in bloques)


# ------------------------------------------------------------------ páginas
def pagina_inicio(ctx):
    L, base, props = ctx["L"], ctx["base"], ctx["props"]
    I = L["inicio"]
    pre = ctx.get("pre", "")
    villa = props["villa-chimo"]
    dv = villa[L["codigo"]]

    datos = "".join('<div><b>%s</b><span>%s</span></div>' % (e(x["n"]), e(x["t"])) for x in I["datos"])
    casas = "".join(tarjeta_casa(ctx, s) for s in props
                    if not s.startswith("_") and props[s].get("activa"))

    destacadas = [x for x in ctx["exps"]["experiencias"] if x.get("destacada")][:3]
    exps = ""
    for x in destacadas:
        d = x[L["codigo"]]
        exps += f"""<article class="exp">
      <p class="temporada">{e(d['cuando'])}</p>
      <h3>{e(d['nombre'])}</h3>
      <p>{e(d['texto'])}</p>
      <dl>
        <dt>{'Duración' if L['codigo'] == 'es' else 'Duration'}</dt><dd>{e(d['duracion'])}</dd>
        <dt>{'Opera' if L['codigo'] == 'es' else 'Run by'}</dt><dd>{e(d['opera'])}</dd>
      </dl>
    </article>"""

    tira_nombres = ["chimo-pueblo-lanchas", "chimo-bahia-pelicano",
                    "chimo-playa-palapas", "chimo-atardecer-aereo"]
    pies = {
        "es": ["El pueblo desde el mar", "La bahía", "La playa al amanecer", "El atardecer"],
        "en": ["The village from the sea", "The bay", "The beach at dawn", "Sunset"],
    }[L["codigo"]]
    tira = "".join('<figure>%s<figcaption>%s</figcaption></figure>' % (
        img(ctx, n, alt_chimo(ctx, n), ancho=400), e(p))
        for n, p in zip(tira_nombres, pies))

    entradas = ctx["entradas"][:3]
    posts = ""
    for x in entradas:
        posts += f"""<a class="post" href="{pre}diario/{e(x['slug'])}.html">
      <span class="k">{e(x.get('tema', ''))}</span>
      <h3>{e(x.get('titulo', ''))}</h3>
      <p>{e(x.get('resumen', ''))}</p>
      <span class="d">{x['minutos']} {'min de lectura' if L['codigo'] == 'es' else 'min read'}</span>
    </a>"""
    if not posts:
        posts = '<p class="nota">%s</p>' % e(L["diario_pagina"]["vacio"])

    wa = "https://wa.me/" + e(ctx["cfg"].get("whatsapp", ""))

    cuerpo = f"""<main id="contenido">

<section class="hero">
  {img(ctx, 'villa-fachada-terraza', alt_de(ctx, 'villa-chimo', 'villa-fachada-terraza'), lazy=False, ancho=1600)}
  <span class="velo"></span>
  <div class="sello"><b>{e(I['hero']['sello_numero'])}</b><span>{e(I['hero']['sello_texto'])}</span></div>
  <div class="u">
    <p class="ubica">{e(I['hero']['ubica'])}</p>
    <h1>{e(I['hero']['titulo'])}</h1>
    <p class="sub">{e(I['hero']['texto'])}</p>
    <div class="acciones">
      <a class="btn" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a>
      <a class="btn fantasma" href="#como-llegar">{e(L['ui']['como_se_llega'])}</a>
    </div>
  </div>
</section>

<section class="datos">{datos}</section>

<section class="pad">
  <div class="u split">
    {img(ctx, 'villa-alberca-piedra-playa', alt_de(ctx, 'villa-chimo', 'villa-alberca-piedra-playa'), ancho=640)}
    <div>
      <p class="lbl">{e(I['casa']['etiqueta'])}</p>
      <h2 class="h2" style="margin-top:12px">{e(I['casa']['titulo'])}</h2>
      {parrafos(dv['historia'])}
      <p class="sig">{e(I['casa']['firma'])}</p>
      <p style="margin-top:26px"><a class="enlace" href="{pre}villa-chimo.html">{e(L['ui']['ver_casa'])}</a></p>
    </div>
  </div>
</section>

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(I['casas']['etiqueta'])}</p>
      <h2 class="h2">{e(I['casas']['titulo'])}</h2>
    </div>
    <div class="casas">{casas}</div>
  </div>
</section>

{bloque_rutas(ctx)}

<section class="pad">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(I['pueblo']['etiqueta'])}</p>
      <h2 class="h2">{e(I['pueblo']['titulo'])}</h2>
      <p class="lead" style="max-width:58ch">{e(I['pueblo']['texto'])}</p>
    </div>
    <div class="tira">{tira}</div>
    <p style="margin-top:28px"><a class="enlace" href="{pre}chimo.html">{e(I['pueblo']['enlace'])}</a></p>
  </div>
</section>

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(I['experiencias']['etiqueta'])}</p>
      <h2 class="h2">{e(I['experiencias']['titulo'])}</h2>
    </div>
    <div class="exps">{exps}</div>
    <p style="margin-top:28px"><a class="enlace" href="{pre}experiencias.html">{e(I['experiencias']['enlace'])}</a></p>
  </div>
</section>

{bloque_alimentos(ctx, "fondo-cal2")}

{bloque_ano(ctx)}

{bloque_publico(ctx, "pad-top0")}

{bloque_avisos(ctx)}

{bloque_mapa(ctx)}

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(I['diario']['etiqueta'])}</p>
      <h2 class="h2">{e(I['diario']['titulo'])}</h2>
    </div>
    <div class="posts">{posts}</div>
    <p style="margin-top:28px"><a class="enlace" href="{pre}diario.html">{e(I['diario']['enlace'])}</a></p>
  </div>
</section>

{bloque_comentarios(ctx)}

<section class="pad cierre">
  <div class="u">
    <h2 class="h2">{e(I['cierre']['titulo'])}</h2>
    <p>{e(I['cierre']['texto'])}</p>
    <div class="acciones">
      <a class="btn" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a>
      <a class="btn claro" href="{wa}" target="_blank" rel="noopener">{e(L['ui']['escribir_whatsapp'])}</a>
    </div>
  </div>
</section>

</main>
"""
    return (cabeza(ctx, I["titulo_seo"], I["descripcion_seo"], canonica=otro_prefijo(ctx) + "index.html")
            + json_ld(ctx) + encabezado(ctx, "index.html") + cuerpo + pie(ctx)
            + scripts(ctx, con_comentarios=True))


def pagina_casa(ctx, slug):
    L, base, props = ctx["L"], ctx["base"], ctx["props"]
    p = props[slug]
    d = p[L["codigo"]]
    f = p.get("ficha", {})
    pre = ctx.get("pre", "")
    es = L["codigo"] == "es"

    if p.get("galeria"):
        botones = "".join(
            '<button type="button">%s</button>' % img(ctx, n, alt_de(ctx, slug, n), ancho=800)
            for n in p["galeria"])
        galeria = f"""<section class="pad pad-top0">
  <div class="u">
    <div class="galeria">{botones}</div>
  </div>
</section>
<div class="visor" role="dialog" aria-modal="true" aria-label="{e(L['ui']['galeria'])}">
  <button class="cerrar" data-accion="cerrar" aria-label="{e(L['ui']['cerrar'])}">&#10005;</button>
  <button class="nav-v prev" data-accion="prev" aria-label="{e(L['ui']['imagen_anterior'])}">&#8592;</button>
  <img src="" alt="">
  <button class="nav-v sig" data-accion="sig" aria-label="{e(L['ui']['imagen_siguiente'])}">&#8594;</button>
  <p class="pie-v"></p>
</div>"""
    else:
        texto = "Las fotografías de este departamento están pendientes." if es else \
                "Photographs of this apartment are pending."
        galeria = f"""<section class="pad pad-top0"><div class="u">
  <div class="casa"><div class="im sinfoto" style="aspect-ratio:21/9">{e(texto)}</div></div>
</div></section>"""

    filas_ficha = []
    if f.get("recamaras"):
        filas_ficha.append(("Recámaras" if es else "Bedrooms", str(f["recamaras"])))
    if f.get("banos") and f["banos"] != "0":
        filas_ficha.append(("Baños" if es else "Bathrooms", f["banos"]))
    if f.get("huespedes"):
        filas_ficha.append(("Huéspedes" if es else "Guests", str(f["huespedes"])))
    filas_ficha.append(("Mínimo de noches" if es else "Minimum stay",
                        ("%d en baja · %d en alta" if es else "%d low season · %d high season") %
                        (f.get("minimo_noches_baja", 1), f.get("minimo_noches_alta", 1))))
    filas_ficha.append(("Ubicación" if es else "Location", d["lugar"]))
    t = p.get("tarifas", {})
    precio_min = min([x for x in (t.get("baja"), t.get("alta")) if x], default=0)
    filas_ficha.append((("Desde" if es else "From"),
                        ("$%s %s %s" % (format(precio_min, ",d"), ctx["cfg"].get("moneda", "MXN"),
                                        L["ui"]["por_noche"])) if precio_min else L["ui"]["precio_pendiente"]))
    ficha = "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(a), e(b)) for a, b in filas_ficha)

    amen = ""
    for g in d["amenidades"]:
        items = "".join("<li>%s</li>" % e(x) for x in g["items"])
        amen += '<div><h3>%s</h3><ul>%s</ul></div>' % (e(g["grupo"]), items)

    ex = d["expectativas"]
    hay = "".join("<li>%s</li>" % e(x) for x in ex["hay"])
    no_hay = "".join("<li>%s</li>" % e(x) for x in ex["no_hay"])
    pend = ""
    if ex.get("pendientes"):
        etiqueta = "Por confirmar" if es else "To be confirmed"
        pend = '<p style="margin-top:22px"><span class="pendiente">%s</span> <span class="nota">%s</span></p>' % (
            e(etiqueta), e(" · ".join(ex["pendientes"])))

    portada = p.get("portada") or "villa-fachada-terraza"

    diferenciador = ""
    if d.get("diferenciador"):
        dif = "".join('<p class="lead">%s</p>' % e(x) for x in d["diferenciador"])
        diferenciador = f"""<section class="pad pad-top0">
  <div class="u split invertido">
    {img(ctx, 'chimo-atardecer-aereo', alt_chimo(ctx, 'chimo-atardecer-aereo'), ancho=640)}
    <div>
      <p class="lbl">{'Por qué aquí' if es else 'Why here'}</p>
      <h2 class="h2" style="margin-top:12px;margin-bottom:20px">{e(d.get('diferenciador_titulo', ''))}</h2>
      {dif}
    </div>
  </div>
</section>"""

    alimentos = bloque_alimentos(ctx) if slug == "villa-chimo" else ""
    avisos = bloque_avisos(ctx) if slug == "villa-chimo" else ""
    mapa = bloque_mapa(ctx, "pad-top0") if slug == "villa-chimo" else ""

    proximamente = ""
    if p.get("proximamente"):
        proximamente = '<p style="margin-top:26px"><span class="pendiente">%s</span> <span class="nota">%s</span></p>' % (
            e(L["ui"]["proximamente"]), e(p["proximamente"][L["codigo"]]))

    cuerpo = f"""<main id="contenido">

<section class="hero chico">
  {img(ctx, portada, alt_de(ctx, slug, portada), lazy=False)}
  <span class="velo"></span>
  <div class="u">
    <h1>{e(d['nombre'])}</h1>
    <p class="sub">{e(d['resumen'])}</p>
    <div class="acciones">
      <a class="btn" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a>
    </div>
  </div>
</section>

{galeria}

<section class="pad pad-top0">
  <div class="u split">
    <div>
      <p class="lbl">{'La casa' if es else 'The house'}</p>
      <h2 class="h2" style="margin-top:12px">{e(d['nombre'])}</h2>
      {parrafos(d['historia'])}
    </div>
    <table class="ficha">{ficha}</table>
  </div>
</section>

{diferenciador}

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{'Qué incluye' if es else 'What is included'}</p>
      <h2 class="h2">{'Amenidades' if es else 'Amenities'}</h2>
    </div>
    <div class="amen">{amen}</div>
    {proximamente}
  </div>
</section>

<section class="pad fondo-cal2">
  <div class="u">
    <div class="encabezado">
      <h2 class="h2">{e(ex['titulo'])}</h2>
      <p class="lead">{e(ex['intro'])}</p>
    </div>
    <div class="hay-no">
      <div><h3>{e(L['chimo']['hay_no_hay']['hay_titulo'])}</h3><ul>{hay}</ul></div>
      <div><h3>{e(L['chimo']['hay_no_hay']['no_hay_titulo'])}</h3><ul class="no">{no_hay}</ul></div>
    </div>
    {pend}
  </div>
</section>

{alimentos}

{avisos}

{mapa}

{bloque_calendario(ctx, casa_inicial=slug, con_selector=False)}

</main>
"""
    titulo = d.get("titulo_seo") or ("%s · %s" % (d["nombre"], ctx["cfg"]["marca"]))
    return (cabeza(ctx, titulo, d["resumen"], canonica=otro_prefijo(ctx) + slug + ".html")
            + json_ld(ctx, slug) + encabezado(ctx, slug + ".html") + cuerpo + pie(ctx)
            + scripts(ctx, con_calendario=True))


def pagina_chimo(ctx):
    L, base = ctx["L"], ctx["base"]
    C = L["chimo"]
    pre = ctx.get("pre", "")
    villa = ctx["props"]["villa-chimo"][L["codigo"]]

    secciones = ""
    for s in C["secciones"]:
        cuerpo_sec = "".join('<p class="lead">%s</p>' % e(x) for x in s["parrafos"])
        secciones += f"""<section class="pad">
  <div class="u">
    <p class="lbl">{e(s['etiqueta'])}</p>
    <h2 class="h2" style="margin-top:12px;margin-bottom:22px">{e(s['titulo'])}</h2>
    {cuerpo_sec}
  </div>
</section>"""

    hay = "".join("<li>%s</li>" % e(x) for x in villa["expectativas"]["hay"])
    no_hay = "".join("<li>%s</li>" % e(x) for x in villa["expectativas"]["no_hay"])

    alrededores = "".join(
        '<div class="alrededor"><h3>%s</h3><p>%s</p></div>' % (e(x["nombre"]), e(x["texto"]))
        for x in C["alrededores"]["items"])

    llevar = "".join("<li>%s</li>" % e(x) for x in C["llevar"]["items"])

    tira_nombres = ["chimo-espuma-arena", "chimo-ola-verde",
                    "chimo-velero", "chimo-lancha-acantilado"]
    tira = "".join('<figure>%s</figure>' % img(ctx, n, alt_chimo(ctx, n), ancho=400)
                   for n in tira_nombres)

    cuerpo = f"""<main id="contenido">

<section class="hero chico">
  {img(ctx, 'chimo-bahia-pelicano', alt_chimo(ctx, 'chimo-bahia-pelicano'), lazy=False)}
  <span class="velo"></span>
  <div class="u">
    <h1>{e(C['hero_titulo'])}</h1>
    <p class="sub">{e(C['hero_texto'])}</p>
  </div>
</section>

{secciones}

<section class="pad pad-top0">
  <div class="u"><div class="tira">{tira}</div></div>
</section>

{bloque_rutas(ctx)}

<section class="pad">
  <div class="u">
    <div class="encabezado">
      <h2 class="h2">{e(C['hay_no_hay']['titulo'])}</h2>
      <p class="lead">{e(C['hay_no_hay']['intro'])}</p>
    </div>
    <div class="hay-no">
      <div><h3>{e(C['hay_no_hay']['hay_titulo'])}</h3><ul>{hay}</ul></div>
      <div><h3>{e(C['hay_no_hay']['no_hay_titulo'])}</h3><ul class="no">{no_hay}</ul></div>
    </div>
  </div>
</section>

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(C['gente']['etiqueta'])}</p>
      <h2 class="h2">{e(C['gente']['titulo'])}</h2>
    </div>
    <p class="lead">{e(C['gente']['texto'])}</p>
    <p style="margin-top:18px"><span class="pendiente">{e(C['gente']['pendiente'])}</span></p>
  </div>
</section>

<section class="pad fondo-cal2">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(C['alrededores']['etiqueta'])}</p>
      <h2 class="h2">{e(C['alrededores']['titulo'])}</h2>
    </div>
    <div class="rejilla2">{alrededores}</div>
  </div>
</section>

<section class="pad">
  <div class="u">
    <div class="encabezado">
      <p class="lbl">{e(C['llevar']['etiqueta'])}</p>
      <h2 class="h2">{e(C['llevar']['titulo'])}</h2>
    </div>
    <ul class="lista" style="max-width:56ch">{llevar}</ul>
    <p style="margin-top:30px"><a class="enlace" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a></p>
  </div>
</section>

{bloque_mapa(ctx, "pad-top0")}

{bloque_ano(ctx)}

{bloque_faq(ctx)}

</main>
"""
    return (cabeza(ctx, C["titulo_seo"], C["descripcion_seo"], canonica=otro_prefijo(ctx) + "chimo.html")
            + encabezado(ctx, "chimo.html") + cuerpo + pie(ctx) + scripts(ctx))


def pagina_experiencias(ctx):
    L, base = ctx["L"], ctx["base"]
    E = L["experiencias_pagina"]
    pre = ctx.get("pre", "")
    es = L["codigo"] == "es"

    tarjetas = ""
    for x in ctx["exps"]["experiencias"]:
        d = x[L["codigo"]]
        precio = ""
        if x.get("precio_desde"):
            precio = "<dt>%s</dt><dd>$%s</dd>" % (e(L["ui"]["desde"]), format(x["precio_desde"], ",d"))
        tarjetas += f"""<article class="exp">
      <p class="temporada">{e(d['cuando'])}</p>
      <h3>{e(d['nombre'])}</h3>
      <p>{e(d['texto'])}</p>
      <dl>
        <dt>{'Duración' if es else 'Duration'}</dt><dd>{e(d['duracion'])}</dd>
        <dt>{'Opera' if es else 'Run by'}</dt><dd>{e(d['opera'])}</dd>
        {precio}
      </dl>
    </article>"""

    horario = "".join('<div class="h"><time>%s</time><p>%s</p></div>' % (e(a), e(b)) for a, b in E["dia"])
    wa = "https://wa.me/" + e(ctx["cfg"].get("whatsapp", ""))

    cuerpo = f"""<main id="contenido">

<section class="hero chico">
  {img(ctx, 'chimo-ola-verde', alt_chimo(ctx, 'chimo-ola-verde'), lazy=False)}
  <span class="velo"></span>
  <div class="u">
    <h1>{e(E['hero_titulo'])}</h1>
    <p class="sub">{e(E['hero_texto'])}</p>
  </div>
</section>

<section class="pad">
  <div class="u"><div class="exps">{tarjetas}</div></div>
</section>

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado"><h2 class="h2">{e(E['dia_titulo'])}</h2></div>
    <div class="horario" style="max-width:62ch">{horario}</div>
  </div>
</section>

{bloque_ano(ctx)}

<section class="pad pad-top0 cierre">
  <div class="u">
    <h2 class="h2">{e(L['inicio']['cierre']['titulo'])}</h2>
    <p>{e(L['inicio']['cierre']['texto'])}</p>
    <div class="acciones">
      <a class="btn" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a>
      <a class="btn claro" href="{wa}" target="_blank" rel="noopener">{e(L['ui']['escribir_whatsapp'])}</a>
    </div>
  </div>
</section>

</main>
"""
    return (cabeza(ctx, E["titulo_seo"], E["descripcion_seo"], canonica=otro_prefijo(ctx) + "experiencias.html")
            + encabezado(ctx, "experiencias.html") + cuerpo + pie(ctx) + scripts(ctx))


def pagina_diario(ctx):
    L, base = ctx["L"], ctx["base"]
    D = L["diario_pagina"]
    pre = ctx.get("pre", "")

    posts = ""
    for x in ctx["entradas"]:
        posts += f"""<a class="post" href="{pre}diario/{e(x['slug'])}.html">
      <span class="k">{e(x.get('tema', ''))}</span>
      <h3>{e(x.get('titulo', ''))}</h3>
      <p>{e(x.get('resumen', ''))}</p>
      <span class="d">{x['minutos']} {'min de lectura' if L['codigo'] == 'es' else 'min read'}</span>
    </a>"""
    if not posts:
        posts = '<p class="nota">%s</p>' % e(D["vacio"])

    cuerpo = f"""<main id="contenido">
<section class="hero chico">
  {img(ctx, 'chimo-lancha-acantilado', alt_chimo(ctx, 'chimo-lancha-acantilado'), lazy=False)}
  <span class="velo"></span>
  <div class="u">
    <h1>{e(D['hero_titulo'])}</h1>
    <p class="sub">{e(D['hero_texto'])}</p>
  </div>
</section>
<section class="pad">
  <div class="u"><div class="posts">{posts}</div></div>
</section>
</main>
"""
    return (cabeza(ctx, D["titulo_seo"], D["descripcion_seo"], canonica=otro_prefijo(ctx) + "diario.html")
            + encabezado(ctx, "diario.html") + cuerpo + pie(ctx) + scripts(ctx))


def pagina_entrada(ctx, entrada):
    L = ctx["L"]
    ctx = dict(ctx)
    base = ctx["base"]
    pre = ctx.get("pre", "")

    cuerpo = f"""<main id="contenido">
<section class="pad">
  <div class="u">
    <div class="entrada">
      <p class="lbl">{e(entrada.get('tema', ''))}</p>
      <h1 class="h2" style="margin:14px 0 18px">{e(entrada.get('titulo', ''))}</h1>
      <p class="nota">{e(entrada.get('fecha', ''))} · {entrada['minutos']} {'min de lectura' if L['codigo'] == 'es' else 'min read'}</p>
      <hr style="border:none;border-top:1px solid var(--linea);margin:28px 0">
      {entrada['html']}
      <p style="margin-top:44px">
        <a class="enlace" href="{pre}diario.html">{e(L['ui']['volver'])}</a>
      </p>
    </div>
  </div>
</section>
<section class="pad pad-top0 cierre">
  <div class="u">
    <h2 class="h2">{e(L['inicio']['cierre']['titulo'])}</h2>
    <p>{e(L['inicio']['cierre']['texto'])}</p>
    <div class="acciones"><a class="btn" href="{pre}reservar.html">{e(L['ui']['ver_disponibilidad'])}</a></div>
  </div>
</section>
</main>
"""
    canon = otro_prefijo(ctx) + "diario/" + entrada["slug"] + ".html"
    sitio = (ctx["cfg"].get("sitio_url") or "").rstrip("/")
    articulo = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": entrada.get("titulo", ""),
        "description": entrada.get("resumen", ""),
        "datePublished": entrada.get("fecha", ""),
        "inLanguage": L["codigo"],
        "author": {"@type": "Organization", "name": ctx["cfg"]["marca"]},
        "publisher": {"@type": "Organization", "name": ctx["cfg"]["marca"]},
    }
    if sitio:
        articulo["url"] = sitio + "/" + canon
    # el nombre de la marca solo cabe si el título de la entrada es corto
    t_entrada = entrada.get("titulo", "")
    titulo_pag = t_entrada if len(t_entrada) > 45 else (t_entrada + " · " + ctx["cfg"]["marca"])
    return (cabeza(ctx, titulo_pag, entrada.get("resumen", ""), canonica=canon)
            + json_ld(ctx, extra=articulo)
            + encabezado(ctx, "diario.html") + cuerpo + pie(ctx) + scripts(ctx))


def pagina_reservar(ctx):
    L, base = ctx["L"], ctx["base"]
    R = L["reservar"]
    wa = "https://wa.me/" + e(ctx["cfg"].get("whatsapp", ""))

    politicas = "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(a), e(b)) for a, b in R["politicas"])

    cuerpo = f"""<main id="contenido">
<section class="hero chico">
  {img(ctx, 'villa-alberca-piedra-playa', alt_de(ctx, 'villa-chimo', 'villa-alberca-piedra-playa'), lazy=False)}
  <span class="velo"></span>
  <div class="u">
    <h1>{e(R['hero_titulo'])}</h1>
    <p class="sub">{e(R['hero_texto'])}</p>
  </div>
</section>

{bloque_precio(ctx)}

{bloque_calendario(ctx)}

<section class="pad pad-top0">
  <div class="u">
    <div class="encabezado"><h2 class="h2">{e(R['politicas_titulo'])}</h2></div>
    <table class="ficha">{politicas}</table>
    <p class="lead" style="margin-top:26px">{e(R['nota_pago'])}</p>
    <p style="margin-top:26px">
      <a class="btn claro" href="{wa}" target="_blank" rel="noopener">{e(L['ui']['escribir_whatsapp'])}</a>
    </p>
  </div>
</section>

{bloque_comentarios(ctx)}

</main>
"""
    return (cabeza(ctx, R["titulo_seo"], R["descripcion_seo"], canonica=otro_prefijo(ctx) + "reservar.html")
            + encabezado(ctx, "reservar.html") + cuerpo + pie(ctx)
            + scripts(ctx, con_calendario=True, con_comentarios=True))


# --------------------------------------------------------------------- main
def escribir(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)


def limpiar():
    for p in PAGINAS:
        ruta = os.path.join(RAIZ, p)
        if os.path.exists(ruta):
            os.remove(ruta)
    for carpeta in (os.path.join(RAIZ, "en"), os.path.join(RAIZ, "diario_html")):
        if os.path.isdir(carpeta):
            shutil.rmtree(carpeta)
    salida_diario = os.path.join(RAIZ, "diario")
    if os.path.isdir(salida_diario):
        for n in os.listdir(salida_diario):
            if n.endswith(".html"):
                os.remove(os.path.join(salida_diario, n))


def favicon():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" fill="#EFEAE0"/>'
           '<path d="M6 44 L22 24 L34 38 L44 28 L58 44 Z" fill="#3C4F33"/>'
           '<path d="M0 46 h64 v18 H0 z" fill="#173F52"/>'
           '<circle cx="47" cy="17" r="6" fill="#A3502F"/></svg>')
    escribir(os.path.join(RAIZ, "assets", "img", "favicon.svg"), svg)


def llms_txt(cfg, props, urls):
    """Resumen del sitio para los rastreadores de asistentes de IA.
    Convención emergente: hechos duros, en texto plano, sin adornos."""
    sitio = (cfg.get("sitio_url") or "").rstrip("/")
    base = sitio + "/" if sitio else ""
    v = props["villa-chimo"]
    t = v.get("tarifas", {})
    f = v.get("ficha", {})
    precio = ("%s %s por noche más impuestos" % (t.get("baja"), cfg.get("moneda", "MXN"))
              if t.get("baja") else "por confirmar")
    return f"""# {cfg['marca']}

> Renta vacacional de casa completa en Chimo, Cabo Corrientes, Jalisco, México.
> Reserva directa, sin intermediarios. Sitio bilingüe español e inglés.

## Hechos verificables

- Chimo es una localidad del municipio de Cabo Corrientes, Jalisco, México.
- Viven alrededor de 280 personas. La cifra fluctúa entre 180 y 300 según la temporada de pesca.
- Está a unos 30 kilómetros al sur de Puerto Vallarta siguiendo la línea de costa.
- Se llega en lancha (unas 2 horas 30 minutos desde Puerto Vallarta), en panga desde Boca de Tomatlán, o por terracería desde El Tuito (unas 3 horas). No hay carretera pavimentada hasta el pueblo.
- La economía del pueblo es la pesca, principalmente pulpo y pescado.
- El muelle del pueblo lleva más de veinte años sin terminarse.
- Hay centro de salud, pero casi nunca hay médico de planta. No hay cajero automático, farmacia ni supermercado.
- La temporada oficial de avistamiento de ballena jorobada en Bahía de Banderas va del 8 de diciembre al 23 de marzo, según fechas publicadas en el Diario Oficial de la Federación.

## Villa Chimo

- Casa completa frente al mar en Chimo. Se renta entera, una sola reserva a la vez.
- {f.get('recamaras', 2)} recámaras ({f.get('camas', '')}), {f.get('banos', '2.5')} baños, recomendada para {f.get('huespedes', 4)} personas.
- Alberca privada, vista al océano, terraza, chimenea exterior, acceso a playa, cocina equipada, área de asador.
- Wifi, aire acondicionado, planta generadora de luz, seguridad, servicio de limpieza al tercer día. Pet friendly.
- Desayuno americano incluido. Comida y cena bajo solicitud. Servicio de compra de despensa.
- Tarifa: {precio}. Descuentos por semana, a partir de 15 noches y por mes.
- Cancelación: reembolso parcial, con 20 días de anticipación, reteniendo el 20 %.
- La zona es selvática y hay fauna, incluidos alacranes ocasionalmente. Se pide avisar si hay alergia a la picadura de alacrán.

## Depa Vallarta

- Departamento en Puerto Vallarta, pensado como escala antes y después de Chimo, porque la última lancha sale por la tarde.
- Ficha en preparación: capacidad, amenidades y precio por confirmar.

## Páginas

- [Inicio]({base})
- [Villa Chimo]({base}villa-chimo.html)
- [Depa Vallarta]({base}depa-vallarta.html)
- [Chimo, el pueblo]({base}chimo.html) — cómo llegar, qué hay y qué no, alrededores, preguntas frecuentes
- [Experiencias]({base}experiencias.html)
- [Diario]({base}diario.html)
- [Reservar]({base}reservar.html)
- Versión en inglés: {base}en/

## Contacto

- WhatsApp: {cfg.get('telefono') or ('+' + cfg.get('whatsapp', ''))}
- Correo: {cfg.get('correo', '')}
"""


def revisar_etiquetas():
    """Avisa si algún título o descripción se sale del largo que Google muestra.
    No detiene nada: solo lo dice, para que se pueda corregir en contenido/."""
    problemas = []
    for carpeta, _, archivos in os.walk(RAIZ):
        if any(x in carpeta for x in (".git", "contenido", "scripts", "assets")):
            continue
        for a in archivos:
            if not a.endswith(".html"):
                continue
            h = open(os.path.join(carpeta, a), encoding="utf-8").read()
            rel = os.path.relpath(os.path.join(carpeta, a), RAIZ)
            t = re.search(r"<title>(.*?)</title>", h, re.S)
            d = re.search(r'name="description" content="(.*?)"', h, re.S)
            if t and len(t.group(1)) > 62:
                problemas.append("  %s · título de %d caracteres (Google corta en ~60)" % (rel, len(t.group(1))))
            if d and len(d.group(1)) > 160:
                problemas.append("  %s · descripción de %d caracteres (Google corta en ~158)" % (rel, len(d.group(1))))
    if problemas:
        print("Etiquetas largas:")
        for x in sorted(problemas):
            print(x)


def main():
    cfg = leer_json("config.json")
    props = leer_json("propiedades.json")
    exps = leer_json("experiencias.json")

    limpiar()
    favicon()

    urls = []
    for codigo in ("es", "en"):
        L = leer_json("%s.json" % codigo)
        base = "" if codigo == "es" else "../"
        carpeta = RAIZ if codigo == "es" else os.path.join(RAIZ, "en")

        ctx = {
            "cfg": cfg, "L": L, "props": props, "exps": exps,
            "entradas": leer_entradas(codigo), "base": base, "alterna": None,
        }

        def con_alterna(archivo, profundidad=0):
            """profundidad = cuántas carpetas hay que subir para llegar a la
            raíz del idioma actual. 0 para las páginas principales, 1 para el diario."""
            c = dict(ctx)
            subir = "../" * profundidad
            c["pre"] = subir                       # hacia la raíz de este idioma
            c["base"] = subir + ("" if codigo == "es" else "../")   # hacia la raíz del sitio
            if codigo == "es":
                c["alterna"] = subir + "en/" + archivo
                c["alterna_ruta"] = "en/" + archivo      # desde la raiz del sitio
            else:
                c["alterna"] = subir + "../" + archivo
                c["alterna_ruta"] = archivo
            return c

        paginas = {
            "index.html": pagina_inicio,
            "villa-chimo.html": lambda c: pagina_casa(c, "villa-chimo"),
            "depa-vallarta.html": lambda c: pagina_casa(c, "depa-vallarta"),
            "chimo.html": pagina_chimo,
            "experiencias.html": pagina_experiencias,
            "diario.html": pagina_diario,
            "reservar.html": pagina_reservar,
        }
        for archivo, fn in paginas.items():
            c = con_alterna(archivo)
            escribir(os.path.join(carpeta, archivo), fn(c))
            urls.append(("" if codigo == "es" else "en/") + archivo)

        for entrada in ctx["entradas"]:
            c = con_alterna("diario/" + entrada["slug"] + ".html", profundidad=1)
            c["alterna"] = None  # las entradas no siempre existen en los dos idiomas
            c["alterna_ruta"] = None
            escribir(os.path.join(carpeta, "diario", entrada["slug"] + ".html"),
                     pagina_entrada(c, entrada))
            urls.append(("" if codigo == "es" else "en/") + "diario/" + entrada["slug"] + ".html")

    # 404
    L = leer_json("es.json")
    ctx = {"cfg": cfg, "L": L, "props": props, "exps": exps, "entradas": [],
           "base": "/", "pre": "/", "alterna": None}
    cuerpo404 = """<main id="contenido"><section class="pad" style="text-align:center">
<div class="u"><h1 class="h2">404</h1>
<p class="lead" style="margin:18px auto">Esta página no existe. / This page does not exist.</p>
<p><a class="btn" href="/index.html">Inicio · Home</a></p></div></section></main>"""
    escribir(os.path.join(RAIZ, "404.html"),
             cabeza(ctx, "404 · " + cfg["marca"], "Página no encontrada") +
             encabezado(ctx) + cuerpo404 + pie(ctx) + scripts(ctx))

    # sitemap y robots
    sitio = (cfg.get("sitio_url") or "").rstrip("/")
    if sitio:
        hoy = date.today().isoformat()
        entradas_xml = "".join(
            "<url><loc>%s/%s</loc><lastmod>%s</lastmod></url>" % (sitio, url_limpia(u), hoy) for u in urls)
        escribir(os.path.join(RAIZ, "sitemap.xml"),
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % entradas_xml)
        escribir(os.path.join(RAIZ, "robots.txt"),
                 "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % sitio)
    else:
        escribir(os.path.join(RAIZ, "robots.txt"), "User-agent: *\nAllow: /\n")

    escribir(os.path.join(RAIZ, ".nojekyll"), "")
    escribir(os.path.join(RAIZ, "llms.txt"), llms_txt(cfg, props, urls))
    revisar_etiquetas()
    print("Listo: %d páginas generadas." % len(urls))


if __name__ == "__main__":
    main()
