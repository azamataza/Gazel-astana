/* Gruzim CRM: запоминает рекламный клик Google Ads (gclid) и отправляет в таблицу клики по WhatsApp и телефону. */
(function () {
  var EP = 'https://script.google.com/macros/s/AKfycbzyJOy5cS94DVno0ELNf1ULpIRbJO9mrGuoZs4BbbgEQXaq-sizIJhQQ6uxKo45sMbO8g/exec';
  var KEY = 'gz_click', TTL = 90 * 864e5;
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
  var last = {};
  function send(t) {
    var id = saved();
    if (!id || EP.indexOf('https://') !== 0) return;
    var now = Date.now();
    if (last[t] && now - last[t] < 3000) return;
    last[t] = now;
    var body = JSON.stringify({ t: t, g: id, p: location.pathname });
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
    return null;
  }
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest && ev.target.closest('a[href]');
    var t = a && kind(a.getAttribute('href'));
    if (t) send(t);
  }, true);
  var wo = window.open;
  window.open = function (u) {
    try { var t = kind(u); if (t) send(t); } catch (e) {}
    return wo.apply(window, arguments);
  };
})();
