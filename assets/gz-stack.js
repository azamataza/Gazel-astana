(function () {
  var mq = window.matchMedia('(max-width:768px)');
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var grids = [].slice.call(document.querySelectorAll('[data-gz-stack]'));
  if (!grids.length) return;

  var st = document.createElement('style');
  st.textContent = '@media(max-width:768px){' +
    '.gz-stack{display:block!important}' +
    '.gz-stack>*{position:sticky!important;top:var(--gz-top,68px);' +
    'transform-origin:50% 0;transform:scale(calc(1 - var(--gz-p,0) * .06))!important;' +
    'box-shadow:0 -6px 22px rgba(15,23,42,.07)}}';
  document.head.appendChild(st);

  var active = [], ticking = false;

  function stickTop() {
    var v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gz-header-h'));
    var top = isNaN(v) ? 56 : v;
    [].forEach.call(document.querySelectorAll('.breadcrumbs, nav[aria-label="Breadcrumb"]'), function (el) {
      var cs = getComputedStyle(el);
      if ((cs.position === 'sticky' || cs.position === 'fixed') && el.offsetHeight) {
        top = Math.max(top, (parseFloat(cs.top) || 0) + el.offsetHeight);
      }
    });
    return top + 12;
  }

  function setup() {
    active = [];
    grids.forEach(function (g) {
      var cards = [].slice.call(g.children);
      g.classList.remove('gz-stack');
      cards.forEach(function (c) {
        ['--gz-p', '--gz-top', 'margin-top', 'margin-bottom'].forEach(function (p) { c.style.removeProperty(p); });
      });
      if (!mq.matches || cards.length < 3) return;
      var T = stickTop(), vh = window.innerHeight;
      var gb = g.getBoundingClientRect().bottom;
      var gaps = cards.map(function (c, i) {
        return (i < cards.length - 1 ? cards[i + 1].getBoundingClientRect().top : gb) - c.getBoundingClientRect().bottom;
      });
      cards.forEach(function (c, i) {
        var want = T + Math.min(i, 3) * 10;
        var fit = vh - c.offsetHeight - 12;
        c.style.setProperty('--gz-top', Math.round(Math.min(want, fit)) + 'px');
        c.style.marginTop = '0px';
        c.style.marginBottom = Math.max(0, gaps[i]) + 'px';
        var bg = getComputedStyle(c).backgroundColor;
        if (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') c.style.backgroundColor = '#fff';
      });
      g.classList.add('gz-stack');
      active.push(cards);
    });
    update();
  }

  function update() {
    ticking = false;
    active.forEach(function (cards) {
      for (var i = 0; i < cards.length - 1; i++) {
        var a = cards[i].getBoundingClientRect(), b = cards[i + 1].getBoundingClientRect();
        var p = (a.bottom - b.top) / a.height; p = p < 0 ? 0 : p > 1 ? 1 : p;
        cards[i].style.setProperty('--gz-p', p.toFixed(3));
      }
    });
  }

  window.addEventListener('scroll', function () {
    if (active.length && !ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  var rt, lastW = window.innerWidth;
  window.addEventListener('resize', function () {
    if (window.innerWidth === lastW) return;
    lastW = window.innerWidth;
    clearTimeout(rt); rt = setTimeout(setup, 200);
  }, { passive: true });
  if (document.readyState === 'complete') setup(); else window.addEventListener('load', setup);
})();
