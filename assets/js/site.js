/* Villas Chimo — menú móvil y visor de galería. Sin librerías. */
(function () {
  'use strict';

  /* ---------------------------------------------------------- menú móvil */
  var hamb = document.querySelector('.hamb');
  var nav = document.querySelector('.nav');
  if (hamb && nav) {
    hamb.addEventListener('click', function () {
      var abierto = nav.classList.toggle('abierto');
      hamb.setAttribute('aria-expanded', abierto ? 'true' : 'false');
      hamb.setAttribute('aria-label', hamb.dataset[abierto ? 'cerrar' : 'abrir'] || '');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('abierto');
        hamb.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------------------------------------------- mapa a petición */
  document.querySelectorAll('[data-cargar-mapa]').forEach(function (b) {
    b.addEventListener('click', function () {
      var caja = b.closest('[data-mapa]');
      if (!caja) return;
      var previo = caja.querySelector('.previo');
      var marco = document.createElement('iframe');
      marco.src = 'https://www.google.com/maps?q=' + caja.dataset.consulta + '&z=11&output=embed';
      marco.loading = 'lazy';
      marco.title = caja.querySelector('.pie-mapa span').textContent;
      marco.referrerPolicy = 'no-referrer-when-downgrade';
      marco.setAttribute('allowfullscreen', '');
      if (previo) previo.replaceWith(marco); else caja.prepend(marco);
    });
  });

  /* ------------------------------------------------- galería por estancia */
  var galeria = document.querySelector('.galeria');
  var visor = document.querySelector('.visor');
  if (galeria && visor) {
    var celdas = Array.prototype.slice.call(galeria.querySelectorAll('.gal-celda'));
    var pestanas = Array.prototype.slice.call(document.querySelectorAll('.gal-tab'));
    var marco = visor.querySelector('img');
    var pie = visor.querySelector('.pie-v');
    var cuenta = visor.querySelector('.cuenta-v');
    var deTexto = (cuenta && cuenta.dataset.de) || 'de';
    var indice = 0;
    var previo = null;

    /* las visibles son las que manda la pestaña activa */
    function visibles() {
      return celdas.filter(function (c) { return !c.hidden; });
    }

    function filtrar(grupo) {
      celdas.forEach(function (c) {
        c.hidden = !(grupo === 'todo' || c.dataset.grupo === grupo);
      });
      pestanas.forEach(function (b) {
        var activa = b.dataset.grupo === grupo;
        b.classList.toggle('activa', activa);
        b.setAttribute('aria-pressed', activa ? 'true' : 'false');
      });
    }

    pestanas.forEach(function (b) {
      b.addEventListener('click', function () { filtrar(b.dataset.grupo); });
    });
    function precargar(ruta) {
      if (!ruta) return;
      var p = new Image();
      p.src = ruta;
    }

    function mostrar(i) {
      var v = visibles();
      if (!v.length) return;
      indice = (i + v.length) % v.length;
      var fuente = v[indice].querySelector('img');
      marco.src = fuente.dataset.grande || fuente.src;
      marco.alt = fuente.alt;
      if (pie) pie.textContent = fuente.alt;
      if (cuenta) {
        var etiqueta = v[indice].dataset.etiqueta;
        cuenta.textContent = (etiqueta ? etiqueta + ' · ' : '') +
          (indice + 1) + ' ' + deTexto + ' ' + v.length;
      }
      /* la siguiente y la anterior se bajan antes de que las pidas */
      var sig = v[(indice + 1) % v.length].querySelector('img');
      var ant = v[(indice - 1 + v.length) % v.length].querySelector('img');
      precargar(sig && sig.src);
      precargar(ant && ant.src);
    }

    function abrir(celda) {
      var v = visibles();
      previo = document.activeElement;
      mostrar(v.indexOf(celda));
      visor.classList.add('abierto');
      document.body.style.overflow = 'hidden';
      var cerrarBtn = visor.querySelector('.cerrar');
      if (cerrarBtn) cerrarBtn.focus();
    }

    function cerrar() {
      visor.classList.remove('abierto');
      document.body.style.overflow = '';
      if (previo && previo.focus) previo.focus();
    }

    celdas.forEach(function (c) {
      c.addEventListener('click', function () { abrir(c); });
    });

    visor.addEventListener('click', function (e) {
      var accion = e.target.closest('[data-accion]');
      if (accion) {
        var a = accion.dataset.accion;
        if (a === 'cerrar') cerrar();
        if (a === 'prev') mostrar(indice - 1);
        if (a === 'sig') mostrar(indice + 1);
        return;
      }
      if (e.target === visor || e.target.classList.contains('visor-marco')) cerrar();
    });

    document.addEventListener('keydown', function (e) {
      if (!visor.classList.contains('abierto')) return;
      if (e.key === 'Escape') cerrar();
      if (e.key === 'ArrowLeft') mostrar(indice - 1);
      if (e.key === 'ArrowRight') mostrar(indice + 1);
    });

    /* deslizar con el dedo */
    var x0 = null, y0 = null;
    visor.addEventListener('touchstart', function (e) {
      x0 = e.changedTouches[0].clientX;
      y0 = e.changedTouches[0].clientY;
    }, { passive: true });
    visor.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      var dy = e.changedTouches[0].clientY - y0;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) {
        mostrar(indice + (dx < 0 ? 1 : -1));
      }
      x0 = null; y0 = null;
    }, { passive: true });
  }
})();
