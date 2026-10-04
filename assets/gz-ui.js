/* Gruzim.kz — общая шапка: меню, выбор города, высота липкого блока. */
(function () {
  var root = document.documentElement;
  var header = document.getElementById('gz-header');
  var drawer = document.getElementById('gz-drawer');
  var overlay = document.getElementById('gz-overlay');
  var burger = document.getElementById('gz-burger');
  var closeBtn = document.getElementById('gz-close');
  var city = document.getElementById('gz-city');
  var cityBtn = document.getElementById('gz-city-btn');
  if (!header) return;

  /* --- меню --- */
  function setMenu(open) {
    root.classList.toggle('gz-menu-open', open);
    if (burger) burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (drawer) drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    if (open && closeBtn) closeBtn.focus();
    if (!open && burger && burger.offsetParent) burger.focus();
  }
  if (burger) burger.addEventListener('click', function (e) {
    e.stopPropagation();
    setMenu(!root.classList.contains('gz-menu-open'));
  });
  if (closeBtn) closeBtn.addEventListener('click', function () { setMenu(false); });
  if (overlay) overlay.addEventListener('click', function () { setMenu(false); });
  if (drawer) drawer.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('a')) setMenu(false);
  });

  /* --- город --- */
  function setCity(open) {
    if (!city) return;
    city.classList.toggle('is-open', open);
    cityBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (city && cityBtn) {
    cityBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      setCity(!city.classList.contains('is-open'));
    });
    document.addEventListener('click', function (e) {
      if (!city.contains(e.target)) setCity(false);
    });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (root.classList.contains('gz-menu-open')) setMenu(false);
    setCity(false);
  });

  /* --- высота шапки и хлебных крошек для отступа страницы --- */
  var crumb = document.querySelector('nav.breadcrumbs');
  function measure() {
    root.style.setProperty('--gz-header-h', header.offsetHeight + 'px');
    if (crumb && getComputedStyle(crumb).position === 'fixed') {
      root.style.setProperty('--gz-crumb-h', crumb.offsetHeight + 'px');
    }
  }
  measure();
  window.addEventListener('load', measure);
  window.addEventListener('resize', measure, { passive: true });

  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      root.classList.toggle('gz-scrolled', window.scrollY > 8);
      ticking = false;
    });
  }, { passive: true });
})();
