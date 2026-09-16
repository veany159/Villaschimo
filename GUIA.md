# Guía de Villas Chimo

Todo lo que hay que saber para publicar el sitio y mantenerlo, sin instalar nada
en tu computadora. Se hace desde la página de GitHub, en el navegador.

Lee los pasos en orden. El 1 y el 2 dejan el sitio en vivo. Los demás se pueden
hacer después, cuando tengas la información.

---

## Paso 1 · Subir el sitio a GitHub

1. Entra a [github.com](https://github.com) y crea una cuenta si no tienes.
   Anota el nombre de usuario que elijas; va a formar parte de la dirección del sitio.
2. Arriba a la derecha, botón **+** › **New repository**.
3. Llénalo así:
   - **Repository name:** `villaschimo`
   - **Public** (tiene que ser público para que Pages funcione gratis)
   - **No** marques "Add a README file"
4. Botón verde **Create repository**.
5. En la pantalla que sigue, haz clic en **uploading an existing file**.
6. Abre la carpeta `villaschimo` en tu computadora, selecciona **todo lo que hay
   adentro** (no la carpeta, su contenido) y arrástralo a la ventana de GitHub.

   > **Ojo con la carpeta `.github`.** Empieza con punto, y algunos navegadores
   > y el Finder de Mac la esconden. Es la que hace que el sitio se publique
   > solo, así que tiene que subir.
   >
   > En Mac, para verla: `Cmd + Shift + .` dentro de la carpeta.
   >
   > Si de plano no la puedes arrastrar, créala a mano: en tu repositorio,
   > **Add file** › **Create new file**, y en el nombre escribe exactamente
   > `.github/workflows/publicar.yml` — las diagonales van creando las
   > carpetas solas. Luego abre el archivo `publicar.yml` de tu computadora
   > con el Bloc de notas, copia todo y pégalo ahí.

7. Abajo, en el recuadro de mensaje, escribe `Primera versión` y dale a
   **Commit changes**.

---

## Paso 2 · Encender el sitio

1. En tu repositorio, pestaña **Settings** (arriba a la derecha).
2. En el menú de la izquierda, **Pages**.
3. En **Source**, elige **GitHub Actions**.
4. Listo. Ve a la pestaña **Actions** y verás el proceso corriendo. Tarda uno o
   dos minutos. Cuando aparezca la palomita verde, tu sitio está en vivo en:

   ```
   https://TU-USUARIO.github.io/villaschimo/
   ```

A partir de aquí, **cada vez que guardes un cambio el sitio se actualiza solo**.
No tienes que volver a hacer nada de esto.

---

## Paso 3 · Poner tus datos

Abre `contenido/config.json` en GitHub y dale al lápiz ✏️ para editar.

Lo que hay que cambiar:

| Renglón | Qué poner |
|---|---|
| `whatsapp` | Tu número completo, sin espacios ni signos. México: `52` + `1` + lada + número. Ejemplo: `5213221234567` |
| `correo` | El correo de contacto |
| `instagram` | El link de tu perfil |

Guarda con **Commit changes** y en un minuto ya está en el sitio.

> **Importante:** el archivo es un JSON. Respeta las comillas y las comas.
> Si te equivocas, GitHub te lo va a marcar y el sitio simplemente no se
> actualiza; no se rompe lo que ya estaba publicado.

---

## Paso 4 · Activar los comentarios

Los comentarios se publican al instante. Para eso hace falta una base de datos,
y usamos **Supabase**, que es gratis para este tamaño. Se hace una sola vez.

### 4.1 Crear la base

1. Entra a [supabase.com](https://supabase.com) y crea una cuenta.
2. **New project**. Nómbralo `villaschimo`, elige una contraseña cualquiera
   (guárdala) y la región **East US** o la más cercana.
3. Espera a que termine de crearse, un par de minutos.

### 4.2 Crear la tabla

En el menú de la izquierda, **SQL Editor** › **New query**. Pega esto tal cual
y dale a **Run**:

```sql
create table comentarios (
  id bigint generated always as identity primary key,
  creado_en timestamptz not null default now(),
  nombre text not null check (char_length(nombre) between 1 and 80),
  lugar text check (char_length(lugar) <= 80),
  casa text check (char_length(casa) <= 40),
  texto text not null check (char_length(texto) between 1 and 800),
  calificacion smallint not null default 5 check (calificacion between 1 and 5),
  idioma text default 'es',
  visible boolean not null default true
);

alter table comentarios enable row level security;

create policy "cualquiera puede leer los visibles"
  on comentarios for select to anon
  using (visible = true);

create policy "cualquiera puede escribir uno"
  on comentarios for insert to anon
  with check (visible is true);
```

### 4.3 Copiar las dos llaves

Menú izquierdo › **Project Settings** › **API**. Ahí vas a ver:

- **Project URL** — algo como `https://abcdefgh.supabase.co`
- **anon public** — una cadena larguísima que empieza con `eyJ...`

Cópialas a `contenido/config.json`:

```json
"supabase": {
  "url": "https://abcdefgh.supabase.co",
  "clave_publica": "eyJ..."
}
```

Guarda. En un minuto los comentarios están vivos.

> La llave `anon public` está hecha para ir en la página, a la vista. Con las
> reglas de arriba, lo único que permite es leer comentarios visibles y
> escribir uno nuevo. Nada más. **No pongas nunca la llave `service_role`.**

### 4.4 Borrar o esconder un comentario

Menú izquierdo › **Table Editor** › tabla `comentarios`. Cambia `visible` a
`false` y desaparece del sitio. Nadie se entera.

### 4.5 Si te llega spam

En el SQL Editor, corre esto y a partir de ahí los comentarios nuevos ya no
aparecen hasta que tú los apruebes desde el Table Editor:

```sql
alter table comentarios alter column visible set default false;
drop policy "cualquiera puede escribir uno" on comentarios;
create policy "cualquiera puede escribir uno"
  on comentarios for insert to anon with check (true);
```

---

## Paso 5 · Conectar el calendario de Airbnb

Hazlo cuando publiques los anuncios. Mientras tanto, la disponibilidad se
edita a mano (ver paso 6).

Por cada anuncio en Airbnb:

1. Entra al anuncio › **Calendario**.
2. Panel derecho › **Disponibilidad** › **Sincronizar calendarios**.
3. **Exportar calendario**. Te da un link que termina en `.ics`. Cópialo.

Pega los links en `contenido/config.json`:

```json
"airbnb": {
  "villa-chimo": "https://www.airbnb.mx/calendar/ical/XXXXX.ics?s=YYYYY",
  "depa-vallarta": "https://www.airbnb.mx/calendar/ical/ZZZZZ.ics?s=WWWWW"
}
```

Desde ese momento el sitio revisa Airbnb **una vez al día, a las 6 de la mañana**,
y bloquea en el calendario las fechas que ya estén ocupadas. No hay que tocar nada.

Si quieres forzar una actualización ahora mismo: pestaña **Actions** ›
**Publicar el sitio** › botón **Run workflow**.

> Esto trae la disponibilidad *desde* Airbnb. No manda tus reservas directas
> *hacia* Airbnb. Si alguien reserva por WhatsApp, bloquea esas fechas tú misma
> en el calendario de Airbnb para no venderlas dos veces.

---

## Paso 6 · Bloquear fechas a mano

Mientras no haya Airbnb, abre `contenido/disponibilidad.json` y escribe las
fechas ocupadas de cada casa, en formato **año-mes-día**:

```json
"villa-chimo": {
  "ocupadas": [
    "2026-12-24",
    "2026-12-25",
    "2026-12-26"
  ],
  "fuente": "manual"
}
```

Cada fecha entre comillas, separadas por comas, **y la última sin coma**.
Escribe también el día de llegada y todos los días de la estancia, excepto el
de salida (ese día la casa ya está libre otra vez).

---

## Paso 7 · Cambiar textos, precios y fotos

Todo vive en la carpeta `contenido/`. No hace falta tocar nada más.

| Archivo | Qué contiene |
|---|---|
| `config.json` | WhatsApp, correo, Instagram, Supabase, Airbnb, dominio |
| `es.json` | Todos los textos del sitio en español |
| `en.json` | Lo mismo en inglés |
| `propiedades.json` | Las dos casas: descripción, amenidades, precios, ficha |
| `experiencias.json` | Las actividades |
| `disponibilidad.json` | Fechas ocupadas |

### Cambiar los precios

En `propiedades.json`, busca `"tarifas"` de cada casa:

```json
"tarifas": {
  "baja": 150,
  "alta": 150,
  "limpieza": 0
}
```

Números sin comas, sin signo de pesos y sin centavos. La moneda se define aparte,
en `config.json`, renglón `"moneda"`. Hoy está en `USD`.

El sitio agrega solo la leyenda **"más impuestos"** al total, para que nadie se
lleve una sorpresa. **Si pones `0`, el sitio dice "Precio a confirmar"** en vez
de inventar una cifra.

La temporada alta va del 15 de diciembre al 30 de abril. Se cambia en
`"temporada_alta"`, con el formato `mes-día`. Hoy las dos temporadas cuestan lo
mismo; el día que quieras cobrar más en invierno, sube el número de `"alta"`.

Los descuentos por semana, por 15 noches y por mes se describen en `es.json` y
`en.json`, dentro de `"reservar"` › `"descuentos"`. No se calculan solos a
propósito: se cotizan al confirmar, que es como los estás manejando.

### Cambiar el aviso de la fauna y el de limpieza

Están en `es.json` y `en.json`, en el bloque `"avisos"`. Son las dos cajas que
aparecen en la portada y en la ficha de la villa. Cambia el texto ahí y se
actualiza en los dos lugares.

### Mover el mapa al punto exacto de la casa

En `config.json`, renglón `"consulta"` dentro de `"mapa"`. Hoy dice
`Chimo, Jalisco, México`. Cuando tengas las coordenadas exactas —las sacas
abriendo Google Maps en el punto de la casa, clic derecho, y copiando los dos
números que aparecen arriba— pega algo así:

```json
"mapa": { "consulta": "20.3140,-105.6730" }
```

El mapa no se carga hasta que el visitante le da clic a "Ver el mapa". Es a
propósito: así el sitio no le deja cookies de Google a nadie que no las pidió,
y no hace falta poner aviso de cookies.

### Agregar fotos

1. En GitHub, entra a `assets/img/` › **Add file** › **Upload files**.
2. Sube la foto. Nómbrala con palabras reales y sin acentos ni espacios:
   `depa-vallarta-sala.jpg`, no `IMG_4821.jpg`.
3. En `propiedades.json`, agrega el nombre **sin la extensión** a la lista de
   `"galeria"` de esa casa, y ponlo también en `"portada"` si quieres que sea
   la principal.

> Las fotos de la villa están optimizadas en dos tamaños (`.webp` y `-800.webp`).
> Si subes una foto normal en `.jpg` va a funcionar igual, solo pesa más.
> Antes de subir, bájale el peso a menos de 1 MB.

### Cambiar un texto

Búscalo en `es.json` o `en.json` con **Ctrl+F** dentro del editor de GitHub,
cámbialo, guarda. Cambia siempre los dos archivos para que el sitio no quede
cojo en un idioma.

---

## Paso 8 · Escribir en el Diario

Cada entrada es un archivo de texto en `diario/es/` (o `diario/en/` para inglés).

1. Entra a la carpeta › **Add file** › **Create new file**.
2. Ponle nombre terminado en `.md`, por ejemplo `que-llevar-a-chimo.md`.
3. Empieza el archivo exactamente con este bloque:

```
---
titulo: Qué llevar a Chimo
resumen: La lista que arman los que ya vinieron.
tema: Antes de venir
fecha: 2026-10-05
slug: que-llevar-a-chimo
publicada: si
---
```

4. Debajo, escribe normal. Para dar formato:

```
## Un subtítulo

Un párrafo normal.

- Un punto de lista
- Otro punto

**Negritas** y *cursivas*.

> Una frase destacada.

[Un enlace](https://ejemplo.com)
```

5. **Commit changes**. La entrada aparece sola en el Diario y en la portada.

Para despublicar sin borrar: cambia `publicada: si` por `publicada: no`.

---

## Paso 9 · Conectar tu dominio

Cuando lo compres:

1. En `contenido/config.json`, pon `"sitio_url": "https://villaschimo.com"`
   (sin diagonal al final). Esto activa el mapa del sitio para Google.
2. En GitHub: **Settings** › **Pages** › **Custom domain**, escribe el dominio
   y dale **Save**.
3. Donde compraste el dominio, en la zona de DNS, agrega:

   - Cuatro registros **A** para `@` apuntando a:
     `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - Un registro **CNAME** para `www` apuntando a `TU-USUARIO.github.io`

4. Regresa a Settings › Pages y marca **Enforce HTTPS** cuando se active
   (puede tardar unas horas).

---

## Preguntas que te van a salir

**¿Rompí algo?**
No se puede romper el sitio publicado desde el editor. Si un archivo queda mal
escrito, el proceso falla y el sitio se queda con la última versión buena. En la
pestaña **Actions**, una tacha roja significa "no se aplicó el último cambio".
Entra, lee el renglón en rojo y casi siempre es una coma o una comilla de más.

**¿Cómo veo cómo va a quedar antes de publicar?**
No hay vista previa. Guarda, espera el minuto y míralo en vivo. Si algo no te
gusta, cámbialo otra vez: es gratis y no deja rastro para el visitante.

**¿Y si quiero cobrar con tarjeta en el sitio?**
Hoy el flujo es: el huésped elige fechas, se va a WhatsApp, tú confirmas y
cobras por transferencia. Cuando haya volumen para justificarlo se puede meter
Stripe, y entonces sí hay que pagar comisión por transacción.

**¿Dónde veo cuánta gente entra?**
Todavía no hay medición. En `config.json` está lista la casilla para Plausible,
que cuesta pero no usa cookies y no obliga a poner aviso de cookies. Google
Analytics es gratis pero sí obliga.

---

## Lo que falta para que el sitio esté completo

- [ ] **Número de WhatsApp real** (hoy hay uno de ejemplo, y sin él no entra ninguna solicitud)
- [ ] Fotos, descripción, amenidades y precio del Depa Vallarta
- [ ] Horario y tarifa reales de la panga a Chimo
- [ ] Coordenadas exactas de la casa para el mapa
- [ ] Fotos de la gente del pueblo, con permiso y con su nombre
- [ ] Definir qué son las "motos" (acuáticas o cuatrimotos) en `experiencias.json`
- [ ] Dominio
- [ ] Activar los comentarios (paso 4)
