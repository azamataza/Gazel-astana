(function () {
  var mq = window.matchMedia('(max-width:768px)');
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var grids = [].slice.call(document.querySelectorAll('[data-gz-stack]'));
  if (!grids.length) return;

  var css = '@media(max-width:768px){' +
    '.gz-stack{display:block!important}' +
    '.gz-stack>*{position:sticky!important;top:calc(var(--gz-stk-top,68px) + var(--gz-i,0) * 10px);' +
    'transform-origin:50% 0;transform:scale(calc(1 - var(--gz-p,0) * .06))!important;' +
    'box-shadow:0 -6px 22px rgba(15,23,42,.07);will-change:transform}' +
    '}';
  var st = document.createElement('style');
  st.textContent = css;
  document.head.appendChild(st);

  var active = [], ticking = false;

  function headerH() {
    var v = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gz-header-h'));
    var top = isNaN(v) ? 56 : v;
    [].forEach.call(document.querySelectorAll('.breadcrumbs, nav[aria-label="Breadcrumb"]'), function (el) {
      var cs = getComputedStyle(el);
      if ((cs.position === 'sticky' || cs.position === 'fixed') && el.offsetHeight) {
        top = Math.max(top, (parseFloat(cs.top) || 0) + el.offsetHeight);
      }
    });
    return top;
  }

  function setup() {
    active = [];
    grids.forEach(function (g) {
      var cards = [].slice.call(g.children);
      g.classList.remove('gz-stack');
      cards.forEach(function (c) { c.style.removeProperty('--gz-p'); c.style.removeProperty('--gz-i'); c.style.removeProperty('margin-bottom'); c.style.removeProperty('margin-top'); });
      if (!mq.matches || cards.length < 3) return;
      var top = headerH() + 12;
      g.style.setProperty('--gz-stk-top', top + 'px');
      var room = window.innerHeight - top - 12 - (cards.length - 1) * 10;
      for (var i = 0; i < cards.length; i++) if (cards[i].offsetHeight > room * 0.9) return;
      var gb = g.getBoundingClientRect().bottom;
      var gaps = cards.map(function (c, i) {
        var r = c.getBoundingClientRect();
        return (i < cards.length - 1 ? cards[i + 1].getBoundingClientRect().top : gb) - r.bottom;
      });
      cards.forEach(function (c, i) {
        c.style.setProperty('--gz-i', i);
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
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(setup, 200); }, { passive: true });
  if (document.readyState === 'complete') setup(); else window.addEventListener('load', setup);
})();
