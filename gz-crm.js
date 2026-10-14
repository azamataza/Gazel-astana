/* Gruzim CRM: запоминает рекламный клик Google Ads (gclid), добавляет код #ЧЧММ первой строкой сообщения WhatsApp
   и отправляет в таблицу клики по WhatsApp, телефону и Telegram.
   На компьютере номер скрыт: нажатие на телефон считается звонком и открывает карточку с номером. */
(function () {
  if (window.__gzCrm) return;
  window.__gzCrm = true;
  var EP = 'https://script.google.com/macros/s/AKfycbzyJOy5cS94DVno0ELNf1ULpIRbJO9mrGuoZs4BbbgEQXaq-sizIJhQQ6uxKo45sMbO8g/exec';
  var KEY = 'gz_click', CKEY = 'gz_code', TTL = 90 * 864e5, CODE_TTL = 30 * 60 * 1000;
  try {
    var q = new URLSearchParams(location.search), id = q.get('gclid'), b;
    if (!id && (b = q.get('gbraid'))) id = 'gbraid:' + b;
    if (!id && (b = q.get('wbraid'))) id = 'wbraid:' + b;
    if (id) localStorage.setItem(KEY, JSON.stringify({ id: id, t: Date.now() }));
  } catch (e) {}
  function saved() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (s && s.id && Date.now() - s.t < TTL) return s.id;
    } catch (e) {}
    return null;
  }
  /* Код = время клика по Астане (UTC+5) ЧЧММ; повторные клики в течение 30 минут получают тот же код. */
  function code() {
    var now = Date.now();
    try {
      var s = JSON.parse(localStorage.getItem(CKEY) || 'null');
      if (s && s.c && now - s.t < CODE_TTL) return s.c;
    } catch (e) {}
    var d = new Date(now + 5 * 3600 * 1000);
    var c = ('0' + d.getUTCHours()).slice(-2) + ('0' + d.getUTCMinutes()).slice(-2);
    try { localStorage.setItem(CKEY, JSON.stringify({ c: c, t: now })); } catch (e) {}
    return c;
  }
  function withCode(u, c) {
    try {
      var i = u.indexOf('?'), base = i < 0 ? u : u.slice(0, i), rest = i < 0 ? [] : u.slice(i + 1).split('&');
      var text = 'Здравствуйте!', other = [];
      rest.forEach(function (p) {
        if (p.indexOf('text=') === 0) text = decodeURIComponent(p.slice(5).replace(/\+/g, ' '));
        else if (p) other.push(p);
      });
      text = '#' + c + '\n' + text.replace(/^\s*#\d{4}\s*/, '').replace(/\s*#\d{4}\s*$/, '');
      return base + '?' + other.concat('text=' + encodeURIComponent(text)).join('&');
    } catch (e) { return u; }
  }
  /* sendBeacon переживает уход страницы в звонилку/WhatsApp; fetch — запасной путь. */
  function post(body) {
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(EP, new Blob([body], { type: 'text/plain;charset=utf-8' }))) return;
    } catch (e) {}
    try {
      fetch(EP, { method: 'POST', mode: 'no-cors', keepalive: true, headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: body });
    } catch (e) {}
  }
  var last = {};
  function send(t, c) {
    var id = saved();
    if (!id) return;
    var now = Date.now();
    if (last[t] && now - last[t] < 3000) return;
    last[t] = now;
    post(JSON.stringify({ t: t, g: id, p: location.pathname, c: c }));
  }
  function kind(u) {
    u = String(u || '');
    if (u.indexOf('tel:') === 0) return 'call';
    if (/wa\.me\/|(api|web)\.whatsapp\.com|^whatsapp:/.test(u)) return 'wa';
    if (/^https?:\/\/(t\.me|telegram\.me)\/|^tg:/.test(u)) return 'tg';
    return null;
  }

  /* ---------- Компьютер: скрытый номер и карточка звонка ---------- */
  var mqDesk = window.matchMedia ? window.matchMedia('(min-width: 769px) and (hover: hover) and (pointer: fine)') : null;
  function isDesk() { return !!(mqDesk && mqDesk.matches); }
  var NUM_RE = /(\+?7[\s (-]*7\d{2}[\s )-]*\d{3}[\s -]*)(\d{2})([\s -]*)(\d{2})/;
  var revealed = false, css = false;

  function addCss() {
    if (css) return; css = true;
    var s = document.createElement('style');
    s.textContent =
      'a[data-gz-mask]{white-space:nowrap}.gz-ph-mask{white-space:nowrap}' +
      '.gz-ph-show{display:inline-block;margin-left:8px;padding:2px 8px;border-radius:999px;background:#eff6ff;color:#2563eb;font-size:.72em;font-weight:600;line-height:1.5;vertical-align:middle;letter-spacing:0;text-transform:none}' +
      '.gz-callcard{position:fixed;z-index:2147483000;width:300px;max-width:calc(100vw - 32px);box-sizing:border-box;padding:20px 20px 18px;border-radius:16px;background:#fff;color:#0f172a;' +
      'box-shadow:0 20px 50px rgba(15,23,42,.18),0 0 0 1px rgba(15,23,42,.06);font-family:inherit;text-align:left;opacity:0;transform:translateY(6px) scale(.98);transition:opacity .18s ease,transform .18s ease}' +
      '.gz-callcard.is-open{opacity:1;transform:none}' +
      '.gz-callcard *{box-sizing:border-box}' +
      '.gz-cc-x{position:absolute;top:10px;right:10px;width:30px;height:30px;border:0;border-radius:50%;background:transparent;color:#94a3b8;font-size:20px;line-height:30px;cursor:pointer;padding:0}' +
      '.gz-cc-x:hover{background:#f1f5f9;color:#0f172a}' +
      '.gz-cc-label{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:#64748b;margin:0 0 10px}' +
      '.gz-cc-ic{width:28px;height:28px;border-radius:50%;background:#eff6ff;color:#2563eb;display:inline-flex;align-items:center;justify-content:center}' +
      '.gz-cc-ic svg{width:15px;height:15px;fill:currentColor}' +
      '.gz-cc-num{display:block;font-size:26px;font-weight:800;letter-spacing:.01em;color:#0f172a;white-space:nowrap;user-select:all;margin:0 0 6px}' +
      '.gz-cc-hint{font-size:13px;color:#64748b;margin:0 0 16px;line-height:1.45}' +
      '.gz-cc-row{display:flex;gap:8px}' +
      '.gz-cc-btn{flex:1;height:40px;border-radius:12px;border:0;font:inherit;font-size:14px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;text-decoration:none}' +
      '.gz-cc-copy{background:#2563eb;color:#fff}.gz-cc-copy:hover{background:#1d4ed8}' +
      '.gz-cc-wa{background:#eafaf0;color:#15803d}.gz-cc-wa:hover{background:#d9f5e3}';
    document.head.appendChild(s);
  }

  function fmt(href) {
    var d = String(href || '').replace(/\D/g, '');
    if (d.length === 11) return '+' + d[0] + ' ' + d.slice(1, 4) + ' ' + d.slice(4, 7) + ' ' + d.slice(7, 9) + ' ' + d.slice(9);
    return String(href || '').replace(/^tel:/, '');
  }

  function maskAll() {
    if (!isDesk() || revealed) return;
    addCss();
    var links = document.querySelectorAll('a[href^="tel:"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      if (a.hasAttribute('data-gz-mask') || a.closest('.gz-callcard')) continue;
      var walker = document.createTreeWalker(a, NodeFilter.SHOW_TEXT, null), n, hit = null;
      while ((n = walker.nextNode())) { if (NUM_RE.test(n.nodeValue)) { hit = n; break; } }
      if (!hit) continue;
      a.setAttribute('data-gz-mask', a.innerHTML);
      var m = hit.nodeValue.match(NUM_RE);
      var before = hit.nodeValue.slice(0, m.index), after = hit.nodeValue.slice(m.index + m[0].length);
      var span = document.createElement('span');
      span.className = 'gz-ph-mask';
      span.textContent = m[1] + '••' + m[3] + '••';
      var chip = document.createElement('span');
      chip.className = 'gz-ph-show';
      chip.textContent = 'показать';
      var frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      frag.appendChild(span);
      frag.appendChild(chip);
      if (after) frag.appendChild(document.createTextNode(after));
      hit.parentNode.replaceChild(frag, hit);
    }
  }
  function unmaskAll() {
    var links = document.querySelectorAll('a[data-gz-mask]');
    for (var i = 0; i < links.length; i++) {
      links[i].innerHTML = links[i].getAttribute('data-gz-mask');
      links[i].removeAttribute('data-gz-mask');
    }
  }

  var card = null, cardAnchor = null;
  function closeCard() {
    if (!card) return;
    var c = card; card = null; cardAnchor = null;
    c.classList.remove('is-open');
    setTimeout(function () { if (c.parentNode) c.parentNode.removeChild(c); }, 200);
  }
  function place(el, anchor) {
    var r = anchor.getBoundingClientRect(), w = el.offsetWidth, h = el.offsetHeight, vw = window.innerWidth, vh = window.innerHeight, g = 10;
    var fixedAnchor = false;
    for (var p = anchor; p && p !== document.body; p = p.parentElement) {
      if (getComputedStyle(p).position === 'fixed') { fixedAnchor = true; break; }
    }
    var left, top;
    if (fixedAnchor && r.left > vw / 2) {
      left = r.left - w - 14; top = r.top + r.height / 2 - h / 2;   /* плавающая кнопка: карточка слева от неё */
      if (left < 16) { left = vw - w - 16; top = r.top - h - 14; }
    } else {
      left = r.left + r.width / 2 - w / 2;
      top = r.bottom + g;
      if (top + h > vh - 16) top = r.top - h - g;
    }
    left = Math.max(16, Math.min(left, vw - w - 16));
    top = Math.max(16, Math.min(top, vh - h - 16));
    el.style.left = Math.round(left) + 'px';
    el.style.top = Math.round(top) + 'px';
  }
  function openCard(anchor, href) {
    addCss();
    closeCard();
    var num = fmt(href), digits = String(href).replace(/\D/g, '');
    var el = document.createElement('div');
    el.className = 'gz-callcard';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Телефон для звонка');
    el.innerHTML =
      '<button type="button" class="gz-cc-x" aria-label="Закрыть">&times;</button>' +
      '<div class="gz-cc-label"><span class="gz-cc-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.6a1 1 0 0 1-.25 1z"/></svg></span>Позвоните нам</div>' +
      '<span class="gz-cc-num"></span>' +
      '<p class="gz-cc-hint">Звонки и WhatsApp 8:00–20:00<br>Заказы выполняем 24/7</p>' +
      '<div class="gz-cc-row"><button type="button" class="gz-cc-btn gz-cc-copy">Скопировать</button>' +
      '<a class="gz-cc-btn gz-cc-wa" target="_blank" rel="noopener">WhatsApp</a></div>';
    el.querySelector('.gz-cc-num').textContent = num;
    el.querySelector('.gz-cc-wa').setAttribute('href', 'https://wa.me/' + digits);
    el.querySelector('.gz-cc-x').addEventListener('click', closeCard);
    var cp = el.querySelector('.gz-cc-copy');
    cp.addEventListener('click', function () {
      function done() { cp.textContent = 'Скопировано ✓'; setTimeout(function () { cp.textContent = 'Скопировать'; }, 1800); }
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(num).then(done, done); return; }
      } catch (e) {}
      try {
        var r = document.createRange(); r.selectNodeContents(el.querySelector('.gz-cc-num'));
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); document.execCommand('copy'); done();
      } catch (e) {}
    });
    document.body.appendChild(el);
    place(el, anchor);
    card = el; cardAnchor = anchor;
    requestAnimationFrame(function () { el.classList.add('is-open'); });
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeCard(); });
  document.addEventListener('mousedown', function (e) {
    if (card && !card.contains(e.target) && !(cardAnchor && cardAnchor.contains(e.target))) closeCard();
  }, true);
  window.addEventListener('resize', function () { if (card && cardAnchor) place(card, cardAnchor); });
  window.addEventListener('scroll', function () { if (card && cardAnchor && getComputedStyle(cardAnchor).position !== 'fixed') closeCard(); }, { passive: true });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', maskAll); else maskAll();
  if (mqDesk) {
    var onMq = function () { if (isDesk()) maskAll(); else { unmaskAll(); closeCard(); } };
    if (mqDesk.addEventListener) mqDesk.addEventListener('change', onMq); else if (mqDesk.addListener) mqDesk.addListener(onMq);
  }

  /* ---------- Перехват кликов ---------- */
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest && ev.target.closest('a[href]');
    if (!a || a.closest('.gz-callcard .gz-cc-num')) return;
    var href = a.getAttribute('href'), t = kind(href);
    if (!t) return;
    if (t === 'call' && isDesk()) {
      ev.preventDefault();          /* на компьютере tel: бесполезен — показываем номер */
      var anchor = a;
      revealed = true;
      unmaskAll();
      openCard(anchor, href);
    }
    if (!saved()) return;
    var c = code();
    if (t === 'wa') a.setAttribute('href', withCode(href, c));
    send(t, c);
  }, true);
  var wo = window.open;
  window.open = function (u) {
    var args = Array.prototype.slice.call(arguments);
    try {
      var t = kind(u);
      if (t && saved()) {
        var c = code();
        if (t === 'wa') args[0] = withCode(u, c);
        send(t, c);
      }
    } catch (e) {}
    return wo.apply(window, args);
  };
})();
