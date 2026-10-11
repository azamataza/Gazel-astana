/* Gruzim CRM: запоминает рекламный клик Google Ads (gclid), добавляет код #ЧЧММ в сообщение WhatsApp
   и отправляет в таблицу клики по WhatsApp, телефону и Telegram. */
(function () {
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
      text = text.replace(/\s*#\d{4}\s*$/, '') + '\n\n#' + c;
      return base + '?' + other.concat('text=' + encodeURIComponent(text)).join('&');
    } catch (e) { return u; }
  }
  var last = {};
  function send(t, c) {
    var id = saved();
    if (!id || EP.indexOf('https://') !== 0) return;
    var now = Date.now();
    if (last[t] && now - last[t] < 3000) return;
    last[t] = now;
    var body = JSON.stringify({ t: t, g: id, p: location.pathname, c: c });
    try {
      fetch(EP, { method: 'POST', mode: 'no-cors', keepalive: true, headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: body });
    } catch (e) {
      try { navigator.sendBeacon(EP, body); } catch (e2) {}
    }
  }
  function kind(u) {
    u = String(u || '');
    if (u.indexOf('tel:') === 0) return 'call';
    if (/wa\.me\/|api\.whatsapp\.com|^whatsapp:/.test(u)) return 'wa';
    if (/^https?:\/\/(t\.me|telegram\.me)\//.test(u)) return 'tg';
    return null;
  }
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest && ev.target.closest('a[href]');
    var t = a && kind(a.getAttribute('href'));
    if (!t || !saved()) return;
    var c = code();
    if (t === 'wa') a.setAttribute('href', withCode(a.getAttribute('href'), c));
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
