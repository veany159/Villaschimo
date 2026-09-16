/* Villas Chimo — calendario de disponibilidad.
   Lee contenido/disponibilidad.json y las tarifas incrustadas en la página.
   No reserva ni cobra: arma la solicitud y la manda por WhatsApp. */
(function () {
  'use strict';

  var raiz = document.querySelector('[data-calendario]');
  if (!raiz) return;

  var T = window.VC_TEXTOS || {};
  var CFG = window.VC_CONFIG || {};
  var CASAS = window.VC_CASAS || {};
  var BASE = raiz.dataset.base || '';
  var MESES_VISIBLES = window.matchMedia('(max-width:760px)').matches ? 1 : 2;

  var estado = {
    casa: raiz.dataset.casa || Object.keys(CASAS)[0],
    ancla: primerDia(new Date()),
    llegada: null,
    salida: null,
    huespedes: 2,
    ocupadas: {},
    actualizado: ''
  };

  /* ------------------------------------------------------------- fechas */
  function primerDia(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
  function iso(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function deIso(s) {
    var p = s.split('-');
    return new Date(+p[0], +p[1] - 1, +p[2]);
  }
  function masDias(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function noches(a, b) { return Math.round((b - a) / 86400000); }
  function mismoDia(a, b) { return a && b && iso(a) === iso(b); }

  var HOY = (function () { var h = new Date(); return new Date(h.getFullYear(), h.getMonth(), h.getDate()); })();

  function estaOcupada(fecha) {
    var lista = estado.ocupadas[estado.casa] || [];
    return lista.indexOf(iso(fecha)) !== -1;
  }

  /* --------------------------------------------------- temporada y precio */
  function enAlta(fecha) {
    var casa = CASAS[estado.casa];
    if (!casa || !casa.temporada_alta) return false;
    var md = String(fecha.getMonth() + 1).padStart(2, '0') + '-' + String(fecha.getDate()).padStart(2, '0');
    return casa.temporada_alta.some(function (r) {
      var ini = r[0], fin = r[1];
      return ini <= fin ? (md >= ini && md <= fin) : (md >= ini || md <= fin);
    });
  }

  function minimoNoches(fecha) {
    var casa = CASAS[estado.casa] || {};
    return enAlta(fecha) ? (casa.min_alta || 1) : (casa.min_baja || 1);
  }

  function precioNoche(fecha) {
    var casa = CASAS[estado.casa] || {};
    return enAlta(fecha) ? (casa.alta || 0) : (casa.baja || 0);
  }

  function dinero(n) {
    return '$' + n.toLocaleString('es-MX') + ' ' + (CFG.moneda || 'MXN');
  }

  /* ---------------------------------------------------------- disponible */
  function rangoLibre(a, b) {
    for (var d = new Date(a); d < b; d = masDias(d, 1)) {
      if (estaOcupada(d)) return false;
    }
    return true;
  }

  /* ------------------------------------------------------------- pintar */
  function pintar() {
    var meses = raiz.querySelector('[data-meses]');
    if (!meses) return;
    meses.innerHTML = '';
    for (var i = 0; i < MESES_VISIBLES; i++) {
      meses.appendChild(pintarMes(new Date(estado.ancla.getFullYear(), estado.ancla.getMonth() + i, 1)));
    }

    var etiqueta = raiz.querySelector('[data-rango-meses]');
    if (etiqueta) {
      var m = (T.meses || [])[estado.ancla.getMonth()] || '';
      etiqueta.textContent = m + ' ' + estado.ancla.getFullYear();
    }
    var atras = raiz.querySelector('[data-mes="-1"]');
    if (atras) atras.disabled = estado.ancla <= primerDia(HOY);

    pintarResumen();
  }

  function pintarMes(fecha) {
    var cont = document.createElement('div');
    cont.className = 'cal-mes';

    var h = document.createElement('h4');
    h.textContent = ((T.meses || [])[fecha.getMonth()] || '') + ' ' + fecha.getFullYear();
    cont.appendChild(h);

    var rej = document.createElement('div');
    rej.className = 'cal-rej';

    (T.dias || ['L', 'M', 'M', 'J', 'V', 'S', 'D']).forEach(function (d, i) {
      var s = document.createElement('span');
      s.className = 'dow';
      s.textContent = d;
      s.setAttribute('aria-hidden', 'true');
      rej.appendChild(s);
    });

    var primero = new Date(fecha.getFullYear(), fecha.getMonth(), 1);
    var offset = (primero.getDay() + 6) % 7; // lunes primero
    for (var i = 0; i < offset; i++) {
      var v = document.createElement('span');
      v.className = 'cal-vacio';
      rej.appendChild(v);
    }

    var ultimo = new Date(fecha.getFullYear(), fecha.getMonth() + 1, 0).getDate();
    for (var d = 1; d <= ultimo; d++) {
      rej.appendChild(pintarDia(new Date(fecha.getFullYear(), fecha.getMonth(), d)));
    }

    cont.appendChild(rej);
    return cont;
  }

  function pintarDia(fecha) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'cal-dia';
    b.textContent = fecha.getDate();
    b.dataset.fecha = iso(fecha);

    var pasada = fecha < HOY;
    var ocupada = estaOcupada(fecha);

    if (pasada) { b.disabled = true; }
    else if (ocupada) { b.classList.add('ocupado'); b.disabled = true; b.title = T.ocupado || ''; }

    if (mismoDia(fecha, HOY)) b.classList.add('hoy');
    if (mismoDia(fecha, estado.llegada) || mismoDia(fecha, estado.salida)) b.classList.add('sel');
    else if (estado.llegada && estado.salida && fecha > estado.llegada && fecha < estado.salida) b.classList.add('rango');

    b.setAttribute('aria-label', fecha.getDate() + ' ' + ((T.meses || [])[fecha.getMonth()] || '') + (ocupada ? ' — ' + (T.ocupado || '') : ''));

    if (!b.disabled) {
      b.addEventListener('click', function () { elegir(fecha); });
    }
    return b;
  }

  function elegir(fecha) {
    if (!estado.llegada || (estado.llegada && estado.salida)) {
      estado.llegada = fecha;
      estado.salida = null;
    } else if (fecha <= estado.llegada) {
      estado.llegada = fecha;
      estado.salida = null;
    } else if (!rangoLibre(estado.llegada, fecha)) {
      estado.llegada = fecha;
      estado.salida = null;
    } else {
      estado.salida = fecha;
    }
    pintar();
    sincronizarBarra();
  }

  /* ----------------------------------------------------------- resumen */
  function pintarResumen() {
    var caja = raiz.querySelector('[data-resumen]');
    if (!caja) return;

    var casa = CASAS[estado.casa] || {};
    var sinPrecio = !casa.baja && !casa.alta;

    if (!estado.llegada) {
      caja.innerHTML = '<p class="msj">' + esc(T.elige_llegada || '') + '</p>';
      return;
    }
    if (!estado.salida) {
      caja.innerHTML = '<p class="msj">' + esc(T.elige_salida || '') + '</p>';
      return;
    }

    var n = noches(estado.llegada, estado.salida);
    var min = minimoNoches(estado.llegada);
    var filas = '';

    filas += fila(T.llegada, fechaLarga(estado.llegada));
    filas += fila(T.salida, fechaLarga(estado.salida));
    filas += fila(T.huespedes, String(estado.huespedes));

    var etiquetaNoches = n + ' ' + (n === 1 ? (T.noche || '') : (T.noches || ''));
    var aviso = '';
    if (n < min) {
      aviso = '<p class="msj">' + esc((T.minimo_noches || '').replace('{n}', min)) + '</p>';
    }

    if (sinPrecio) {
      filas += fila(etiquetaNoches, '');
      filas += '<div class="r total"><span>' + esc(T.total || '') + '</span><span>' + esc(T.precio_pendiente || '') + '</span></div>';
    } else {
      var subtotal = 0;
      for (var d = new Date(estado.llegada); d < estado.salida; d = masDias(d, 1)) subtotal += precioNoche(d);
      var limpieza = casa.limpieza || 0;
      filas += '<div class="r"><span>' + esc(etiquetaNoches) + '</span><span>' + esc(dinero(subtotal)) + '</span></div>';
      if (limpieza) filas += fila(T.limpieza, dinero(limpieza));
      filas += '<div class="r total"><span>' + esc(T.total || '') + '</span><span>' + esc(dinero(subtotal + limpieza)) + '</span></div>';
    }

    var puede = n >= min;
    caja.innerHTML = filas + aviso +
      '<button type="button" class="btn ancho" data-solicitar ' + (puede ? '' : 'disabled') + '>' + esc(T.solicitar || '') + '</button>' +
      '<p style="margin-top:12px"><button type="button" class="enlace" data-limpiar style="border:none;border-bottom:1px solid var(--teja);background:none;cursor:pointer;padding:0 0 4px">' + esc(T.limpiar || '') + '</button></p>';

    var bs = caja.querySelector('[data-solicitar]');
    if (bs) bs.addEventListener('click', solicitar);
    var bl = caja.querySelector('[data-limpiar]');
    if (bl) bl.addEventListener('click', function () {
      estado.llegada = null; estado.salida = null; pintar(); sincronizarBarra();
    });
  }

  function fila(k, v) {
    return '<div class="r"><span>' + esc(k || '') + '</span><span>' + esc(v || '') + '</span></div>';
  }

  function fechaLarga(d) {
    return d.getDate() + ' ' + ((T.meses || [])[d.getMonth()] || '') + ' ' + d.getFullYear();
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* -------------------------------------------------------- WhatsApp */
  function solicitar() {
    var casa = CASAS[estado.casa] || {};
    var n = noches(estado.llegada, estado.salida);
    var lineas = [
      (T.solicitud_saludo || 'Hola, quiero consultar disponibilidad en') + ' ' + (casa.nombre || estado.casa) + '.',
      (T.llegada || 'Llegada') + ': ' + fechaLarga(estado.llegada),
      (T.salida || 'Salida') + ': ' + fechaLarga(estado.salida),
      (T.noches || 'noches') + ': ' + n,
      (T.huespedes || 'Huéspedes') + ': ' + estado.huespedes
    ];
    var url = 'https://wa.me/' + (CFG.whatsapp || '') + '?text=' + encodeURIComponent(lineas.join('\n'));
    window.open(url, '_blank', 'noopener');
  }

  /* -------------------------------------------------- barra superior */
  function sincronizarBarra() {
    var bl = document.querySelector('[data-barra-llegada]');
    var bs = document.querySelector('[data-barra-salida]');
    if (bl) {
      bl.textContent = estado.llegada ? fechaLarga(estado.llegada) : (T.elige_fechas || '');
      bl.classList.toggle('vacio', !estado.llegada);
    }
    if (bs) {
      bs.textContent = estado.salida ? fechaLarga(estado.salida) : (T.elige_fechas || '');
      bs.classList.toggle('vacio', !estado.salida);
    }
  }

  /* ------------------------------------------------------- controles */
  raiz.addEventListener('click', function (e) {
    var b = e.target.closest('[data-mes]');
    if (!b) return;
    estado.ancla = new Date(estado.ancla.getFullYear(), estado.ancla.getMonth() + (+b.dataset.mes), 1);
    pintar();
  });

  var selCasa = document.querySelector('[data-selector-casa]');
  if (selCasa) {
    selCasa.addEventListener('change', function () {
      estado.casa = selCasa.value;
      raiz.dataset.casa = selCasa.value;
      estado.llegada = null; estado.salida = null;
      pintar(); sincronizarBarra();
    });
  }

  var selHue = document.querySelector('[data-selector-huespedes]');
  if (selHue) {
    estado.huespedes = +selHue.value || 2;
    selHue.addEventListener('change', function () {
      estado.huespedes = +selHue.value || 2;
      pintarResumen();
    });
  }

  document.querySelectorAll('[data-ir-calendario]').forEach(function (b) {
    b.addEventListener('click', function () {
      raiz.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  /* ---------------------------------------------------------- arranque */
  pintar();
  sincronizarBarra();

  fetch(BASE + 'contenido/disponibilidad.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (!data || !data.casas) return;
      Object.keys(data.casas).forEach(function (k) {
        estado.ocupadas[k] = data.casas[k].ocupadas || [];
      });
      estado.actualizado = data.actualizado || '';
      var e = document.querySelector('[data-actualizado]');
      if (e && estado.actualizado) {
        e.textContent = (T.actualizado || '') + ' ' + estado.actualizado;
      }
      pintar();
    })
    .catch(function () { /* sin disponibilidad cargada, el calendario sigue usable */ });
})();
