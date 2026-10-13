(function () {
  var PIXEL = '3664506947019736';
  if (window.__gzMeta) return;
  window.__gzMeta = true;

  !function (f, b, e, v, n, t, s) {
    if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
    if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
  }(window, document);

  fbq('init', PIXEL);
  fbq('track', 'PageView');

  var loaded = false;
  function load() {
    if (loaded) return; loaded = true;
    var s = document.createElement('script');
    s.async = true; s.src = 'https://connect.facebook.net/en_US/fbevents.js';
    document.head.appendChild(s);
  }
  var evts = ['scroll', 'touchstart', 'click', 'keydown', 'mousemove'];
  function trig() { evts.forEach(function (e) { window.removeEventListener(e, trig); }); load(); }
  evts.forEach(function (e) { window.addEventListener(e, trig, { passive: true }); });
  setTimeout(load, 3500);

  var page = location.pathname;

  var shown = 0, last = Date.now(), engaged = false;
  var timer = setInterval(function () {
    var now = Date.now();
    if (document.visibilityState === 'visible') shown += now - last;
    last = now;
    if (!engaged && shown >= 10000) {
      engaged = true; clearInterval(timer);
      fbq('trackCustom', 'Engaged10s', { page: page });
    }
  }, 1000);

  var prices = false;
  function viewPrices(how) {
    if (prices) return; prices = true;
    fbq('trackCustom', 'ViewPrices', { page: page, how: how });
  }
  var SEL = '#price-table,#tariffs,#calculator,#price,.price-table,.price-table-wrap,.tariff-grid,.tariff-card,' +
            '.calculator-section,.calculator-wrapper,.hub-price,.al-price,.service-price,.tariff-price,.price,table';
  function watch() {
    var els = document.querySelectorAll(SEL);
    if (!els.length || !('IntersectionObserver' in window)) return;
    var timers = new Map();
    var io = new IntersectionObserver(function (list) {
      list.forEach(function (en) {
        if (en.isIntersecting) {
          timers.set(en.target, setTimeout(function () { viewPrices('view'); io.disconnect(); }, 1500));
        } else if (timers.has(en.target)) {
          clearTimeout(timers.get(en.target)); timers.delete(en.target);
        }
      });
    }, { threshold: 0.4 });
    els.forEach(function (el) { io.observe(el); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', watch); else watch();
  document.addEventListener('change', function (e) {
    if (e.target.closest && e.target.closest('#calculator,.calculator-section,.calculator-wrapper,.calc-select,.calc-check,[class*="calc"]')) viewPrices('calc');
  }, true);

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href*="wa.me"], a[href*="api.whatsapp.com"]');
    if (!a) return;
    load();
    fbq('track', 'Contact', { method: /^tel:/.test(a.getAttribute('href')) ? 'phone' : 'whatsapp', page: page });
  }, true);
})();
