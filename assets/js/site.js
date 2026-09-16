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

  /* ------------------------------------------------------ visor galería */
  var galeria = document.querySelector('.galeria');
  var visor = document.querySelector('.visor');
  if (galeria && visor) {
    var botones = Array.prototype.slice.call(galeria.querySelectorAll('button'));
    var img = visor.querySelector('img');
    var pie = visor.querySelector('.pie-v');
    var indice = 0;
    var previo = null;

    function mostrar(i) {
      if (!botones.length) return;
      indice = (i + botones.length) % botones.length;
      var fuente = botones[indice].querySelector('img');
      img.src = fuente.dataset.grande || fuente.src;
      img.alt = fuente.alt;
      if (pie) pie.textContent = fuente.alt;
    }

    function abrir(i) {
      previo = document.activeElement;
      mostrar(i);
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

    botones.forEach(function (b, i) {
      b.addEventListener('click', function () { abrir(i); });
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
      if (e.target === visor) cerrar();
    });

    document.addEventListener('keydown', function (e) {
      if (!visor.classList.contains('abierto')) return;
      if (e.key === 'Escape') cerrar();
      if (e.key === 'ArrowLeft') mostrar(indice - 1);
      if (e.key === 'ArrowRight') mostrar(indice + 1);
    });
  }
})();
