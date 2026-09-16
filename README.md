# Villas Chimo

Sitio web de Villas Chimo — una villa en Chimo, Cabo Corrientes, Jalisco, y un
departamento en Puerto Vallarta. Bilingüe español/inglés, con calendario de
disponibilidad, comentarios de huéspedes y blog.

**👉 Para publicarlo y mantenerlo, lee [GUIA.md](GUIA.md).** Está en español y
paso a paso. Este archivo es la explicación técnica.

---

## Cómo está armado

HTML estático. Sin React, sin npm, sin nada que instalar. Un script de Python
que solo usa la librería estándar lee los archivos de `contenido/` y escribe las
páginas. GitHub Actions lo corre y GitHub Pages lo publica.

```
contenido/          Todo lo editable: textos, propiedades, experiencias, precios
  config.json         Contacto, Supabase, links de Airbnb, dominio
  es.json / en.json   Los textos del sitio en cada idioma
  propiedades.json    Las dos casas
  experiencias.json   Las actividades
  disponibilidad.json Fechas ocupadas (a mano o desde Airbnb)
diario/es/          Entradas del blog en Markdown
diario/en/          Lo mismo en inglés
assets/css/         Una hoja de estilo
assets/js/          Tres archivos: menú y galería, calendario, comentarios
assets/img/         Fotos en webp, dos tamaños
scripts/            sync_airbnb.py — lee los .ics y actualiza la disponibilidad
build.py            El generador
.github/workflows/  publicar.yml — construye y publica
```

Todo lo demás (los `.html` de la raíz y de `en/`) lo genera `build.py`.
No los edites a mano: se sobrescriben en cada publicación.

## Correrlo en local

```bash
python3 build.py
python3 -m http.server 8000
```

Y abre `http://localhost:8000`. No requiere dependencias.

## Decisiones

**HTML generado, no renderizado en el navegador.** Google indexa el contenido
real, que es lo que importa para "cómo llegar a Chimo" y para las entradas del
Diario.

**El HTML generado se versiona en el repositorio.** Redundante, y a propósito:
si el proceso automático falla algún día, el sitio publicado sigue en pie.

**Los precios en `0` se muestran como "Precio a confirmar".** El sitio nunca
inventa una cifra.

**Lo que no se sabe se dice.** Internet, señal y apagones aparecen como "por
confirmar" hasta que estén medidos. Es más barato perder una reserva que ganar
una reseña de tres estrellas.

**Sin cookies, sin rastreo, sin banner.** No hay analítica instalada.

## Calendario y Airbnb

`scripts/sync_airbnb.py` descarga los `.ics` que estén configurados, saca los
días ocupados (sin contar el día de salida, que ya está libre) y los escribe en
`contenido/disponibilidad.json`. Corre diario a las 12:00 UTC.

Si un link falla, no borra nada: conserva la última versión buena.
Si no hay links, respeta lo que esté escrito a mano.

Es sincronización **de entrada**. Las reservas directas hay que bloquearlas en
Airbnb manualmente.

## Comentarios

Supabase, tabla `comentarios`, con row level security: leer solo los visibles,
insertar uno nuevo. La llave `anon` es pública por diseño.

Anti-spam: campo trampa oculto, límite de 800 caracteres y un minuto de espera
entre envíos del mismo navegador. Para moderar, `visible = false` en la tabla.

Si no hay Supabase configurado, la lista y el formulario se muestran con un
aviso y el resto del sitio funciona igual.

## Accesibilidad

Un solo `h1` por página, foco visible, `aria-current` en el menú, texto
alternativo real en todas las imágenes, galería navegable con teclado y Escape,
`prefers-reduced-motion` respetado, y salto al contenido.

---

Hecho por [Estudio Raíz](https://github.com) para Villas Chimo.
