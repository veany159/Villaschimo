/* Villas Chimo — comentarios de huéspedes.
   Se publican al instante usando Supabase (plan gratuito).
   Si todavía no hay Supabase configurado en contenido/config.json,
   la lista y el formulario se muestran con un aviso y el resto del sitio sigue igual. */
(function () {
  'use strict';

  var raiz = document.querySelector('[data-comentarios]');
  if (!raiz) return;

  var T = (window.VC_TEXTOS_COM) || {};
  var SB = (window.VC_CONFIG && window.VC_CONFIG.supabase) || {};
  var TABLA = 'comentarios';
  var LIMITE_CARACTERES = 800;
  var ESPERA_MS = 60000;

  var lista = raiz.querySelector('[data-com-lista]');
  var form = raiz.querySelector('[data-com-form]');
  var aviso = raiz.querySelector('[data-com-aviso]');
  var estrellas = raiz.querySelector('[data-estrellas]');
  var calificacion = 5;

  var activo = !!(SB.url && SB.clave_publica);

  /* ------------------------------------------------------------ utilidades */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function decirAviso(texto, clase) {
    if (!aviso) return;
    aviso.textContent = texto;
    aviso.className = 'aviso-form ' + (clase || '');
  }

  function pintarEstrellas(n) {
    return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n);
  }

  function fechaCorta(s) {
    try {
      var d = new Date(s);
      return d.toLocaleDateString(document.documentElement.lang || 'es-MX', { year: 'numeric', month: 'long' });
    } catch (e) { return ''; }
  }

  /* ------------------------------------------------------------- pintar */
  function pintarLista(filas) {
    if (!lista) return;
    if (!filas || !filas.length) {
      lista.innerHTML = '<div class="com-vacio">' + esc(T.vacio || '') + '</div>';
      return;
    }
    lista.innerHTML = filas.map(function (c) {
      var quien = '<b>' + esc(c.nombre) + '</b>';
      if (c.lugar) quien += ' · ' + esc(c.lugar);
      if (c.casa) quien += ' · ' + esc(c.casa);
      if (c.creado_en) quien += ' · ' + esc(fechaCorta(c.creado_en));
      return '<article class="com">' +
        '<div class="estrellas" aria-label="' + (c.calificacion || 5) + '/5">' + pintarEstrellas(c.calificacion || 5) + '</div>' +
        '<blockquote>' + esc(c.texto) + '</blockquote>' +
        '<p class="quien">' + quien + '</p>' +
        '</article>';
    }).join('');
  }

  /* -------------------------------------------------------------- cargar */
  function cargar() {
    if (!activo) {
      pintarLista([]);
      return;
    }
    var url = SB.url.replace(/\/+$/, '') +
      '/rest/v1/' + TABLA +
      '?select=nombre,lugar,casa,texto,calificacion,creado_en' +
      '&visible=eq.true&order=creado_en.desc&limit=30';

    fetch(url, {
      headers: { apikey: SB.clave_publica, Authorization: 'Bearer ' + SB.clave_publica }
    })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(pintarLista)
      .catch(function () { pintarLista([]); });
  }

  /* ------------------------------------------------------------- enviar */
  function enviar(e) {
    e.preventDefault();
    if (!activo) return;

    var datos = new FormData(form);
    if ((datos.get('sitio_web') || '').trim() !== '') return; // trampa anti-robots

    var nombre = (datos.get('nombre') || '').trim();
    var texto = (datos.get('texto') || '').trim();

    if (!nombre || !texto) { decirAviso(T.faltan_campos || '', 'mal'); return; }
    if (texto.length > LIMITE_CARACTERES) { decirAviso(T.muy_largo || '', 'mal'); return; }

    var ultimo = 0;
    try { ultimo = +(localStorage.getItem('vc_com_ultimo') || 0); } catch (err) { ultimo = 0; }
    if (Date.now() - ultimo < ESPERA_MS) { decirAviso(T.muy_seguido || '', 'mal'); return; }

    var btn = form.querySelector('button[type="submit"]');
    var etiquetaOriginal = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = T.enviando || ''; }
    decirAviso('', '');

    fetch(SB.url.replace(/\/+$/, '') + '/rest/v1/' + TABLA, {
      method: 'POST',
      headers: {
        apikey: SB.clave_publica,
        Authorization: 'Bearer ' + SB.clave_publica,
        'Content-Type': 'application/json',
        Prefer: 'return=minimal'
      },
      body: JSON.stringify({
        nombre: nombre.slice(0, 80),
        lugar: (datos.get('lugar') || '').trim().slice(0, 80),
        casa: (datos.get('casa') || '').trim().slice(0, 40),
        texto: texto,
        calificacion: calificacion,
        idioma: document.documentElement.lang || 'es'
      })
    })
      .then(function (r) {
        if (!r.ok) throw new Error('rechazado');
        try { localStorage.setItem('vc_com_ultimo', String(Date.now())); } catch (err) { /* sin almacenamiento */ }
        form.reset();
        calificacion = 5;
        marcarEstrellas();
        decirAviso(T.gracias || '', 'ok');
        cargar();
      })
      .catch(function () { decirAviso(T.error || '', 'mal'); })
      .finally(function () {
        if (btn) { btn.disabled = false; btn.textContent = etiquetaOriginal; }
      });
  }

  /* --------------------------------------------------------- estrellas */
  function marcarEstrellas() {
    if (!estrellas) return;
    Array.prototype.forEach.call(estrellas.querySelectorAll('button'), function (b, i) {
      b.classList.toggle('on', i < calificacion);
      b.textContent = i < calificacion ? '★' : '☆';
      b.setAttribute('aria-pressed', i < calificacion ? 'true' : 'false');
    });
  }

  if (estrellas) {
    estrellas.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      calificacion = +b.dataset.valor || 5;
      marcarEstrellas();
    });
    marcarEstrellas();
  }

  /* ---------------------------------------------------------- arranque */
  if (!activo) {
    if (form) {
      Array.prototype.forEach.call(form.querySelectorAll('input,textarea,select,button'), function (el) { el.disabled = true; });
    }
    decirAviso(T.sin_configurar || '', '');
  } else if (form) {
    form.addEventListener('submit', enviar);
  }

  cargar();
})();
