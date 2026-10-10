# -*- coding: utf-8 -*-
"""Генератор блога Gruzim.kz. Запуск: python3 -I build.py <корень сайта>"""
import os, re, sys, json, html, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from articles import ARTICLES, CATS, PUBLISHED

ROOT = sys.argv[1]
BASE = "https://www.gruzim.kz/"
PHONE = "77010120300"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
          "сентября", "октября", "ноября", "декабря"]


def rd(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


_HREF_INDEX = re.compile(r'href="((?:\.\./)*)((?:karaganda/)?)index\.html(#[^"]*)?"')
_ABS_INDEX = re.compile(r'https://www\.gruzim\.kz/((?:karaganda/)?)index\.html')


def dirlinks(s):
    """Ссылки на главную ведём на каталог (/, ../), а не на index.html —
    иначе Google видит /index.html как дубль главной."""
    s = _HREF_INDEX.sub(lambda m: f'href="{(m.group(1) + m.group(2)) or "./"}{m.group(3) or ""}"', s)
    return _ABS_INDEX.sub(lambda m: "https://www.gruzim.kz/" + m.group(1), s)


def wr(p, s):
    if p.endswith(".html"):
        s = dirlinks(s)
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(s)


def esc(s):
    return html.escape(s, quote=True)


def ru_date(iso):
    y, m, d = iso[:10].split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def mmss(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def thumb(vid):
    return f"https://i.ytimg.com/vi/{vid}/oar2.jpg"


# ---------------------------------------------------------------- shared blocks
INDEX = rd("index.html")
SAVE = rd("takelazh/save.html")
HEADER_SRC = re.search(r"<!-- GZ-UI:HEADER -->.*?<!-- /GZ-UI:HEADER -->", INDEX, re.S).group(0)
FOOTER_SRC = re.search(r"<!-- GZ-UI:FOOTER -->.*?<!-- /GZ-UI:FOOTER -->", INDEX, re.S).group(0)
ANALYTICS = re.search(r"    <script>\s*\(function \(\) \{\s*var GZ_CFG.*?</script>", SAVE, re.S).group(0)
TRACKER = re.search(r"<script>\s*\(function\(\)\{\s*function source\(\).*?</script>", SAVE, re.S).group(0)
NOSCRIPT = "\n".join(re.findall(r"    <noscript><(?:iframe|div).*?</noscript>", SAVE))
assert ANALYTICS and TRACKER and NOSCRIPT


def relink(block, P, self_href):
    # в шаблоне главной ссылки на неё — "./"; приводим к index.html, dirlinks() в wr() вернёт каталог
    block = block.replace('href="./#', 'href="index.html#').replace('href="./"', 'href="index.html"')

    def fix(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r"^(https?:|//|tel:|mailto:|/|data:|javascript:)", url):
            return m.group(0)
        if url.startswith("#"):
            return f'{attr}="{P}index.html{url}"'
        return f'{attr}="{P}{url}"'
    out = re.sub(r'\b(href|src)="([^"]*)"', fix, block)
    # Астана / РУС на странице блога ведут на саму страницу
    out = out.replace(f'<a href="{P}index.html" role="menuitem" class="is-active">', f'<a href="{self_href}" role="menuitem" class="is-active">')
    out = out.replace(f'<a href="{P}index.html" class="is-active" lang="ru">', f'<a href="{self_href}" class="is-active" lang="ru">')
    return out


NAV_ITEM = '<div class="gz-nav-item"><a class="gz-nav-top" href="{href}"{cur}>Блог</a></div>'
DRAWER_ITEM = '<a href="{href}" class="gz-d-link"{cur}>Блог</a>\n'
NAV_RE = re.compile(r'(<div class="gz-nav-item"><a class="gz-nav-top" href="[^"]*B2B\.html"[^>]*>Бизнесу</a></div>)')
DRAWER_RE = re.compile(r'(<a href="[^"]*" class="gz-d-link">О нас</a>)')


def add_blog_menu(block, P, current=False):
    if "blog.html\"" in block and ">Блог</a>" in block:
        return block
    cur = ' aria-current="page"' if current else ""
    block, n1 = NAV_RE.subn(lambda m: m.group(1) + "\n" + NAV_ITEM.format(href=P + "blog.html", cur=cur), block, count=1)
    block, n2 = DRAWER_RE.subn(lambda m: DRAWER_ITEM.format(href=P + "blog.html", cur=cur) + m.group(1), block, count=1)
    assert n1 == 1 and n2 == 1, "menu anchors not found"
    return block


def header(P, self_href):
    h = relink(HEADER_SRC, P, self_href)
    if f'href="{P}blog.html">Блог</a>' in h:  # пункт уже есть в шаблоне главной
        h = h.replace(f'href="{P}blog.html">Блог</a>', f'href="{P}blog.html" aria-current="page">Блог</a>')
        return h.replace(f'href="{P}blog.html" class="gz-d-link">Блог</a>', f'href="{P}blog.html" class="gz-d-link" aria-current="page">Блог</a>')
    return add_blog_menu(h, P, current=True)


def footer(P):
    return relink(FOOTER_SRC, P, P + "index.html")


WA_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.66 15L2 22l5.16-1.32A10 10 0 1 0 12 2zm5.47 14.14c-.23.65-1.35 1.24-1.86 1.28-.5.05-.97.23-3.27-.68-2.77-1.09-4.53-3.9-4.67-4.08-.13-.18-1.11-1.48-1.11-2.82 0-1.34.7-2 .95-2.27.25-.28.55-.35.73-.35.18 0 .37 0 .53.01.17.01.4-.06.62.48.23.55.78 1.9.85 2.04.07.14.11.3.02.48-.09.18-.14.3-.27.46-.14.16-.29.36-.41.48-.14.13-.28.28-.12.55.16.27.71 1.17 1.53 1.9 1.05.94 1.94 1.23 2.21 1.37.28.14.44.12.6-.07.16-.18.69-.8.87-1.08.18-.28.37-.23.62-.14.25.09 1.59.75 1.86.89.27.14.46.2.53.32.06.11.06.66-.18 1.31z"/></svg>'


def wa_link(text, label, extra=""):
    from urllib.parse import quote
    return f'<a class="bl-wa" href="https://wa.me/{PHONE}?text={quote(text)}" target="_blank" rel="noopener"{extra}>{WA_SVG}{label}</a>'


CONV_JS = """<script>
(function(){
  var t=false,s=false,done=false;
  setTimeout(function(){t=true;},30000);
  function onScroll(){var h=document.documentElement.scrollHeight-window.innerHeight;if(h>0&&(window.pageYOffset/h)>=0.5){s=true;window.removeEventListener('scroll',onScroll);}}
  window.addEventListener('scroll',onScroll,{passive:true});
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a');if(!a)return;
    var h=(a.getAttribute('href')||'').toLowerCase();
    if(!(h.indexOf('tel:')===0||h.indexOf('wa.me')>-1||h.indexOf('t.me')>-1))return;
    if(t&&s&&!done){done=true;if(window.GZ)GZ.conversion();}
  });
})();
</script>"""


def head(P, title, desc, canonical, og_type, ld_blocks, extra_meta=""):
    lds = "\n".join(f'<script type="application/ld+json">\n{json.dumps(b, ensure_ascii=False, indent=1)}\n</script>' for b in ld_blocks)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow, max-image-preview:large, max-video-preview:-1">
    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="ru" href="{canonical}">
    <link rel="alternate" hreflang="x-default" href="{canonical}">
    <meta property="og:title" content="{esc(title.replace(' | Gruzim.kz', ''))}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:type" content="{og_type}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="https://www.gruzim.kz/og-image.png">
    <meta property="og:locale" content="ru_KZ">
    <meta property="og:site_name" content="Gruzim.kz">{extra_meta}
{lds}
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-icon-180x180.png">
    <link rel="preconnect" href="https://fonts.googleapis.com" media="(min-width: 769px)">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin media="(min-width: 769px)">
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,600;14..32,700&display=swap" rel="stylesheet" media="(min-width: 769px)">
{ANALYTICS}
    <link rel="stylesheet" href="{P}assets/gz-ui.css?v=1">
    <link rel="stylesheet" href="{P}assets/gz-blog.css?v=1">
</head>
<body>
{NOSCRIPT}
"""


def tail(P):
    return f"""
{footer(P)}

<div class="bl-sticky">{wa_link("Здравствуйте! Пишу с сайта, из блога. Хочу рассчитать стоимость.", "Рассчитать в WhatsApp")}</div>

{CONV_JS}
{TRACKER}
<script src="/gz-crm.js" defer></script>
<script src="{P}assets/gz-ui.js?v=1" defer></script>
</body>
</html>
"""


ORG = {"@type": "Organization", "name": "Gruzim.kz", "url": "https://www.gruzim.kz/",
       "logo": {"@type": "ImageObject", "url": "https://www.gruzim.kz/Logo.png"}}


def words(s):
    return len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", s)))


def sort_key(a):
    return a["videos"][-1]["pub"] if a["videos"] else a.get("date", PUBLISHED) + "T00:00:00+05:00"


def blog_order():
    """Лента блога: кейсы с видео (свежие сверху) вперемешку с советами —
    советы равномерно распределены между видео, лента начинается с видео."""
    vids = sorted([x for x in ARTICLES if x["videos"]], key=sort_key, reverse=True)
    tips = [x for x in ARTICLES if not x["videos"]]
    if not vids or not tips:
        return vids + tips
    after = {(k + 1) * len(vids) // (len(tips) + 1): [] for k in range(len(tips))}
    for k, t in enumerate(tips):
        after[(k + 1) * len(vids) // (len(tips) + 1)].append(t)
    out = []
    for i, v in enumerate(vids, 1):
        out.append(v)
        out.extend(after.get(i, []))
    return out


def cover_id(a):
    return a["videos"][0]["id"] if a["videos"] else a["cover"]


COVER = "assets/blog-cover.jpg"  # единая обложка (логотип) для статей-советов без видео


def cover_src(a, P):
    return thumb(a["videos"][0]["id"]) if a["videos"] else P + COVER


def cover_abs(a):
    return cover_src(a, "https://www.gruzim.kz/")


def card(a, P, heading="h3"):
    url = f'{P}blog/{a["cat"]}/{a["slug"]}.html'
    if a["videos"]:
        v = a["videos"][0]
        dur = sum(x["sec"] for x in a["videos"])
        nvid = len(a["videos"])
        badge = f'<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2 1l7 4-7 4z"/></svg>' + (f"{nvid} видео" if nvid > 1 else mmss(dur))
        alt, more = v["name"], "Читать и смотреть →"
    else:
        badge, alt, more = "Советы", a["h1"], "Читать →"
    return f"""<a class="bl-card" href="{url}" data-cat="{a['cat']}">
<span class="bl-card-img"><img src="{cover_src(a, P)}" alt="{esc(alt)}" width="{1080 if a["videos"] else 1200}" height="{1920 if a["videos"] else 900}" loading="lazy" decoding="async"><span class="bl-play">{badge}</span></span>
<span class="bl-card-body"><span class="bl-cat">{CATS[a['cat']]}</span><{heading}>{esc(a['h1'])}</{heading}><p>{esc(a['card'])}</p><span class="bl-card-more">{more}</span></span>
</a>"""


def article_page(a):
    P = "../../"
    path = f'blog/{a["cat"]}/{a["slug"]}.html'
    url = BASE + path
    self_href = a["slug"] + ".html"
    body = a["body"].replace("@/", P)
    total_words = words(a["lead"] + body + " ".join(q + x for q, x in a["faq"]))
    read_min = max(2, round(total_words / 170))
    vids = a["videos"]

    video_ld = [{
        "@type": "VideoObject", "name": v["name"],
        "description": f'{v["name"]}. Видео Gruzim.kz — {CATS[a["cat"]].lower()} в Астане.',
        "thumbnailUrl": [thumb(v["id"]), f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg'],
        "uploadDate": v["pub"], "duration": f'PT{v["sec"]}S',
        "embedUrl": f'https://www.youtube.com/embed/{v["id"]}',
        "url": f'https://www.youtube.com/shorts/{v["id"]}',
        "publisher": ORG,
    } for v in vids]
    posting = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a["h1"][:110], "description": a["desc"],
        "datePublished": PUBLISHED, "dateModified": PUBLISHED,
        "author": ORG, "publisher": ORG,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "image": [thumb(v["id"]) for v in vids] or [cover_abs(a)],
        "articleSection": CATS[a["cat"]], "inLanguage": "ru",
    }
    if video_ld:
        posting["video"] = video_ld if len(video_ld) > 1 else video_ld[0]
    crumbs_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Блог", "item": BASE + "blog.html"},
        {"@type": "ListItem", "position": 3, "name": CATS[a["cat"]], "item": BASE + "blog.html#" + a["cat"]},
        {"@type": "ListItem", "position": 4, "name": a["h1"], "item": url}]}
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in a["faq"]]}

    meta = f'\n    <meta property="article:published_time" content="{PUBLISHED}">\n    <meta property="article:section" content="{CATS[a["cat"]]}">'
    out = head(P, a["title"], a["desc"], url, "article", [posting, crumbs_ld, faq_ld], meta)
    out += header(P, self_href)

    # видео
    figs = []
    for i, v in enumerate(vids):
        cap = v["name"] if len(vids) > 1 else "Видео с объекта"
        figs.append(f"""<figure class="bl-video">
<div class="bl-frame"><iframe src="https://www.youtube-nocookie.com/embed/{v['id']}?rel=0&amp;modestbranding=1&amp;playsinline=1" title="{esc(v['name'])}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>
<figcaption>{esc(cap)} · {mmss(v['sec'])} · <a href="https://www.youtube.com/shorts/{v['id']}" target="_blank" rel="noopener">смотреть на YouTube</a></figcaption>
</figure>""")

    facts = "\n".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in a["facts"])
    wa_text = f"Здравствуйте! Прочитал(а) статью «{a['h1']}». Хочу рассчитать похожий заказ."
    facts_box = f"""<aside class="bl-facts">
<h2>Коротко о заказе</h2>
<dl>
{facts}
</dl>
<p>Пришлите фото и адреса — назовём цену до выезда и не будем менять её в процессе.</p>
{wa_link(wa_text, "Рассчитать похожий заказ")}
</aside>"""

    if not figs:
        top = ""
    elif len(figs) == 1:
        top = f'<div class="bl-top">\n{figs[0]}\n{facts_box}\n</div>'
    else:
        top = f'<div class="bl-top">\n<div>{figs[0]}</div>\n{facts_box}\n</div>'
        # второе видео ставим в тело статьи после первого раздела
        anchor = "<h2>Результат</h2>"
        assert anchor in body
        body = body.replace(anchor, anchor + f'\n<div class="bl-top" style="grid-template-columns:minmax(0,340px)">{figs[1]}</div>', 1)

    links = "\n".join(f'<a href="{h.replace("@/", P)}">{esc(t)}{f"<span>{esc(pr)}</span>" if pr else ""}</a>' for h, t, pr in a["links"])
    faq = "\n".join(f"<details><summary>{esc(q)}</summary><p>{esc(x)}</p></details>" for q, x in a["faq"])

    same = [b for b in ARTICLES if b is not a and b["cat"] == a["cat"]]
    i = ARTICLES.index(a)
    rot = ARTICLES[i + 1:] + ARTICLES[:i]
    other = [b for b in rot if b["cat"] != a["cat"]]
    more = (same[:1] + other)[:3]
    more_html = "\n".join(card(b, P) for b in more)

    dates = f'<span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg><time datetime="{PUBLISHED}">{ru_date(PUBLISHED)}</time></span>'
    rt = f'<span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>{read_min} мин чтения</span>'
    vd = "" if not vids else f'<span><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>{"видео " + ", ".join(mmss(v["sec"]) for v in vids)}</span>'

    out += f"""
<main class="bl-wrap">
<nav class="bl-crumbs" aria-label="Хлебные крошки"><ol>
<li><a href="{P}index.html">Главная</a></li>
<li><a href="{P}blog.html">Блог</a></li>
<li><a href="{P}blog.html#{a['cat']}">{CATS[a['cat']]}</a></li>
<li aria-current="page">{esc(a['h1'] if len(a['h1']) < 60 else a['h1'][:57].rsplit(' ', 1)[0] + '…')}</li>
</ol></nav>

<article>
<header class="bl-head">
<a class="bl-cat" href="{P}blog.html#{a['cat']}">{CATS[a['cat']]}</a>
<h1>{esc(a['h1'])}</h1>
<p class="bl-lead">{esc(a['lead'])}</p>
<p class="bl-meta">{dates}{rt}{vd}</p>
</header>

{top}

<div class="bl-body">
{body.strip()}
</div>

<section class="bl-cta">
<div><h2>Нужно так же?</h2><p>Пришлите фото и адреса в WhatsApp — рассчитаем стоимость за 5 минут. Звонки и WhatsApp: 8:00–20:00, заказы выполняем 24/7.</p></div>
{wa_link(wa_text, "Написать в WhatsApp")}
</section>

<section class="bl-section">
<h2>Услуги по теме</h2>
<div class="bl-links">
{links}
</div>
</section>

<section class="bl-section bl-faq">
<h2>Вопросы и ответы</h2>
{faq}
</section>
</article>

<section class="bl-section" style="max-width:none">
<h2>Другие наши работы</h2>
<div class="bl-grid">
{more_html}
</div>
</section>
<div class="bl-end"></div>
</main>
"""
    out += tail(P)
    wr(path, out)
    return path


def hub_page():
    P = ""
    url = BASE + "blog.html"
    title = "Блог Gruzim.kz — наши работы на видео: переезды, такелаж, вывоз"
    desc = "Кейсы Gruzim.kz с видео: переезды домов и офисов, перевозка сейфов и оборудования, такелаж, упаковка, сборка мебели и вывоз мусора в Астане. Задача, техника, бригада, сроки."
    counts = {c: sum(1 for a in ARTICLES if a["cat"] == c) for c in CATS}
    order = blog_order()
    blog_ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Блог Gruzim.kz", "url": url,
               "description": desc, "inLanguage": "ru", "publisher": ORG,
               "blogPost": [{"@type": "BlogPosting", "headline": a["h1"][:110],
                             "url": f'{BASE}blog/{a["cat"]}/{a["slug"]}.html', "datePublished": PUBLISHED,
                             "image": cover_abs(a)} for a in order]}
    crumbs_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Главная", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Блог", "item": url}]}
    out = head(P, title + " | Gruzim.kz" if len(title) < 60 else title, desc, url, "website", [blog_ld, crumbs_ld])
    out += header(P, "blog.html")
    btns = [f'<button type="button" data-f="all" aria-pressed="true">Все<span>{len(ARTICLES)}</span></button>']
    btns += [f'<button type="button" data-f="{c}" aria-pressed="false">{n}<span>{counts[c]}</span></button>' for c, n in CATS.items() if counts[c]]
    cards = "\n".join(card(a, P, "h2") for a in order)
    out += f"""
<main class="bl-wrap">
<nav class="bl-crumbs" aria-label="Хлебные крошки"><ol>
<li><a href="index.html">Главная</a></li>
<li aria-current="page">Блог</li>
</ol></nav>

<header class="bl-hero">
<h1>Блог Gruzim.kz: наши работы на видео</h1>
<p>Реальные заказы в Астане — от сейфов весом в тонну до переезда целого офиса за выходные. Рассказываем, какой была задача, что пошло не по плану и как мы это решили.</p>
</header>

<div class="bl-filter" role="group" aria-label="Рубрики">
{"".join(btns)}
</div>

<div class="bl-grid" id="bl-list">
{cards}
</div>

<section class="bl-intro">
<h2>О чём этот блог</h2>
<p>Мы снимаем короткие видео на объектах и разбираем каждый заказ в статье: какая была задача, какая понадобилась техника и бригада, что могло пойти не так и как к такой работе подготовиться заказчику. Стоимость вашего заказа рассчитаем по фото в WhatsApp и зафиксируем до начала работ.</p>
<p>Все видео — на нашем <a href="https://www.youtube.com/@gruzimkz" target="_blank" rel="noopener">YouTube-канале</a>. Основные услуги: <a href="pereezdkay.html">переезд под ключ</a>, <a href="gruz/centr.html">грузоперевозки</a>, <a href="takelazh.html">такелажные работы</a>, <a href="upakovka.html">упаковка вещей</a>, <a href="mebel.html">сборка мебели</a> и <a href="musor.html">вывоз мусора</a>.</p>
</section>
<div class="bl-end"></div>
</main>

<script>
(function(){{
  var btns=[].slice.call(document.querySelectorAll('.bl-filter button')),
      cards=[].slice.call(document.querySelectorAll('#bl-list .bl-card'));
  function apply(f){{
    btns.forEach(function(b){{b.setAttribute('aria-pressed',b.getAttribute('data-f')===f?'true':'false');}});
    cards.forEach(function(c){{c.hidden=!(f==='all'||c.getAttribute('data-cat')===f);}});
  }}
  btns.forEach(function(b){{b.addEventListener('click',function(){{
    var f=b.getAttribute('data-f'); apply(f);
    try{{history.replaceState(null,'',f==='all'?location.pathname:'#'+f);}}catch(e){{}}
  }});}});
  var h=location.hash.slice(1);
  if(h&&btns.some(function(b){{return b.getAttribute('data-f')===h;}}))apply(h);
}})();
</script>
"""
    out += tail(P)
    wr("blog.html", out)


def home_block():
    s = rd("index.html")
    s = re.sub(r'<section class="section" id="blog">.*?</section>\s*', '', s, count=1, flags=re.S)
    latest = sorted([a for a in ARTICLES if a["videos"]], key=sort_key, reverse=True)[:3]
    items = "\n".join(f"""<a class="hb-card" href="blog/{a['cat']}/{a['slug']}.html"><span class="hb-img"><img src="{thumb(a['videos'][0]['id'])}" alt="{esc(a['videos'][0]['name'])}" width="1080" height="1920" loading="lazy" decoding="async"></span><span class="hb-body"><span class="hb-cat">{CATS[a['cat']]}</span><span class="hb-title">{esc(a['h1'])}</span></span></a>""" for a in latest)
    block = f"""<section class="section" id="blog">
        <style>
        #blog .hb-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;text-align:left}}
        #blog .hb-card{{display:flex;flex-direction:column;overflow:hidden;border:1px solid #e2e8f0;border-radius:16px;background:#fff;color:inherit;text-decoration:none;transition:border-color .2s}}
        #blog .hb-card:hover{{border-color:#2563eb}}
        #blog .hb-img{{position:relative;aspect-ratio:4/3;overflow:hidden;background:#0b1220}}
        #blog .hb-img img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
        #blog .hb-body{{display:flex;flex-direction:column;gap:8px;padding:16px 18px 20px}}
        #blog .hb-cat{{color:#2563eb;font-size:13px;font-weight:600}}
        #blog .hb-title{{color:#0f172a;font-size:17px;font-weight:700;line-height:1.35}}
        #blog .hb-sub{{max-width:640px;margin:-30px auto 32px;text-align:center;color:#475569}}
        #blog .hb-more{{text-align:center;margin-top:28px}}
        @media(max-width:900px){{#blog .hb-grid{{grid-template-columns:1fr 1fr}}#blog .hb-card:nth-child(3){{display:none}}}}
        @media(max-width:560px){{#blog .hb-grid{{grid-template-columns:1fr}}#blog .hb-card:nth-child(3){{display:flex}}#blog .hb-sub{{margin-top:-20px}}}}
        </style>
        <h2>Наши работы на видео</h2>
        <p class="hb-sub">Реальные заказы в Астане: какой была задача и как мы её решили.</p>
        <div class="hb-grid">
{items}
        </div>
        <div class="hb-more"><a href="blog.html" class="cta-button">Все статьи блога</a></div>
    </section>


    """
    anchor = '<section class="section" id="b2b">'
    assert s.count(anchor) == 1
    s = s.replace(anchor, block + anchor)
    wr("index.html", s)


def inject_menus():
    n = 0
    for full in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        if rel.startswith("blog/") or rel == "blog.html":
            continue
        s = open(full, encoding="utf-8").read()
        if "<!-- GZ-UI:HEADER -->" not in s or ">Бизнесу</a></div>" not in s:
            continue
        P = "../" * rel.count("/")
        m = re.search(r"<!-- GZ-UI:HEADER -->.*?<!-- /GZ-UI:HEADER -->", s, re.S)
        new = add_blog_menu(m.group(0), P)
        if new != m.group(0):
            s = s[:m.start()] + new + s[m.end():]
            open(full, "w", encoding="utf-8").write(s)
            n += 1
    return n


def sitemap(paths):
    s = rd("sitemap.xml")
    add = []
    for p, pr, cf in [("blog.html", "0.6", "weekly")] + [(x, "0.5", "monthly") for x in paths]:
        loc = BASE + p
        if f"<loc>{loc}</loc>" in s:
            continue
        add.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{PUBLISHED}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>\n")
    s = s.replace("</urlset>", "".join(add) + "</urlset>")
    wr("sitemap.xml", s)


def llms():
    s = rd("llms.txt")
    s = re.sub(r"## Блог\n.*?(?=\n## )", "", s, count=1, flags=re.S)
    s = re.sub(r"\n{3,}(?=## Полное)", "\n\n", s)
    lines = ["## Блог", "", "Кейсы с видео с реальных заказов в Астане: задача, техника, бригада, ориентиры цен.", "",
             f"- [Все статьи блога]({BASE}blog.html)"]
    for a in ARTICLES:
        lines.append(f'- [{a["h1"]}]({BASE}blog/{a["cat"]}/{a["slug"]}.html)')
    s = s.replace("## Полное содержимое сайта", "\n".join(lines) + "\n\n## Полное содержимое сайта", 1)
    wr("llms.txt", s)



# ---------------------------------------------------------------- кейсы на страницах услуг
CASES = {
    "takelazh.html": ["stoimost-takelazhnyh-rabot", "perevozka-dvuh-sejfov-1-tonna", "pereezd-prachechnoj-3-5-tonny"],
    "takelazh/save.html": ["perevozka-dvuh-sejfov-1-tonna"],
    "takelazh/oborud.html": ["pereezd-prachechnoj-3-5-tonny", "perevozka-metallicheskogo-resepshena"],
    "gruz/centr.html": ["razbor-perevozka-i-sborka-mebeli-pod-klyuch", "perevozka-metallicheskogo-resepshena"],
    "pereezdkay.html": ["organizaciya-pereezda-chek-list", "pereezd-dvuhurovnevogo-kottedzha", "pereezd-ofisa-kazaid"],
    "kay/kvartira.html": ["organizaciya-pereezda-chek-list", "razbor-perevozka-i-sborka-mebeli-pod-klyuch", "pereezd-dvuhurovnevogo-kottedzha"],
    "kay/ofice.html": ["pereezd-ofisa-kazaid", "organizaciya-pereezda-chek-list"],
    "B2B.html": ["pereezd-ofisa-kazaid", "vyvoz-ulichnyh-vazonov", "demontazh-i-vyvoz-torgovoj-mebeli-iz-magazina"],
    "upakovka.html": ["razborka-i-upakovka-kvartiry-pered-remontom"],
    "upakovka/posuda.html": ["razborka-i-upakovka-kvartiry-pered-remontom"],
    "upakovka/mebel.html": ["razborka-i-upakovka-kvartiry-pered-remontom", "razbor-perevozka-i-sborka-mebeli-pod-klyuch"],
    "mebel.html": ["sborka-shkafa-ot-chego-zavisit-cena", "sborka-mebeli-bez-hozyaina", "razbor-perevozka-i-sborka-mebeli-pod-klyuch"],
    "musor.html": ["vyvoz-ulichnyh-vazonov", "demontazh-i-vyvoz-torgovoj-mebeli-iz-magazina", "demontazh-shkafa-kupe-i-vyvoz-mebeli"],
    "musor/mebel.html": ["razbor-vyvoz-i-utilizaciya-ofisnoj-mebeli", "demontazh-shkafa-kupe-i-vyvoz-mebeli", "vyvoz-ulichnyh-vazonov"],
    "musor/mebel/shkaf-kupe.html": ["demontazh-shkafa-kupe-i-vyvoz-mebeli"],
    "musor/stroy/krupnogabarit.html": ["vyvoz-ulichnyh-vazonov", "demontazh-i-vyvoz-torgovoj-mebeli-iz-magazina"],
}

CASES_CSS = """<style>
#gz-cases{max-width:1200px;margin:0 auto;padding:56px 20px;font-family:var(--gz-font,Inter,system-ui,sans-serif);text-align:left}
#gz-cases h2{margin:0 0 8px;color:#0f172a;font-size:30px;line-height:1.2;font-weight:800;text-align:left}
#gz-cases .gc-sub{margin:0 0 24px;color:#475569;font-size:16px;line-height:1.5}
#gz-cases .gc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
#gz-cases .gc-card{display:flex;gap:16px;align-items:stretch;padding:12px;border:1px solid #e2e8f0;border-radius:16px;background:#fff;color:inherit;text-decoration:none;transition:border-color .2s,box-shadow .2s}
#gz-cases .gc-card:hover{border-color:#2563eb;box-shadow:0 6px 24px rgba(15,23,42,.10)}
#gz-cases .gc-img{position:relative;flex:none;width:96px;aspect-ratio:3/4;border-radius:10px;overflow:hidden;background:#0b1220}
#gz-cases .gc-img img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;margin:0;border-radius:0}
#gz-cases .gc-body{display:flex;flex-direction:column;gap:6px;min-width:0;padding:2px 0}
#gz-cases .gc-cat{color:#2563eb;font-size:12.5px;font-weight:600}
#gz-cases .gc-title{color:#0f172a;font-size:16px;line-height:1.35;font-weight:700}
#gz-cases .gc-more{margin-top:auto;color:#2563eb;font-size:14px;font-weight:600}
@media(max-width:640px){#gz-cases{padding:40px 16px}#gz-cases h2{font-size:24px}#gz-cases .gc-grid{grid-template-columns:1fr}}
</style>"""


def cases_block(rel, slugs):
    P = "../" * rel.count("/")
    by = {a["slug"]: a for a in ARTICLES}
    items = []
    for sl in slugs:
        a = by.get(sl)
        if not a:
            continue
        more = "Смотреть кейс →" if a["videos"] else "Читать →"
        items.append(f'''<a class="gc-card" href="{P}blog/{a['cat']}/{a['slug']}.html"><span class="gc-img"><img src="{cover_src(a, P)}" alt="{esc(a['h1'])}" width="{1080 if a['videos'] else 1200}" height="{1920 if a['videos'] else 900}" loading="lazy" decoding="async"></span><span class="gc-body"><span class="gc-cat">{'Кейс с видео' if a['videos'] else 'Советы'}</span><span class="gc-title">{esc(a['h1'])}</span><span class="gc-more">{more}</span></span></a>''')
    if not items:
        return ""
    title = "Наши работы по этой услуге" if any(by[x]["videos"] for x in slugs if x in by) else "Полезно знать"
    return f"""<!-- GZ-CASES -->
<section id="gz-cases" aria-label="{title}">
{CASES_CSS}
<h2>{title}</h2>
<p class="gc-sub">Реальные заказы в Астане: какой была задача и как мы её решили.</p>
<div class="gc-grid">
{chr(10).join(items)}
</div>
</section>
<!-- /GZ-CASES -->
"""


def inject_cases():
    n = 0
    for rel, slugs in CASES.items():
        s = rd(rel)
        blk = cases_block(rel, slugs)
        if "<!-- GZ-CASES -->" in s:
            s = re.sub(r"<!-- GZ-CASES -->.*?<!-- /GZ-CASES -->\n?", lambda m: blk, s, count=1, flags=re.S)
        else:
            m = (re.search(r'<section[^>]*id="related"', s) or re.search(r'<section class="contact-form-section"', s)
                 or re.search(r"<!-- GZ-UI:FOOTER -->", s))
            assert m, rel
            s = s[:m.start()] + blk + "\n" + s[m.start():]
        wr(rel, s)
        n += 1
    return n


if __name__ == "__main__":
    for stub in glob.glob(os.path.join(ROOT, "blog", "*", "1.html")):
        os.remove(stub)
    # удалить статьи, которых больше нет в articles.py (например, после смены slug)
    keep = {f'blog/{a["cat"]}/{a["slug"]}.html' for a in ARTICLES}
    for f in glob.glob(os.path.join(ROOT, "blog", "*", "*.html")):
        if os.path.relpath(f, ROOT).replace(os.sep, "/") not in keep:
            os.remove(f)
    paths = [article_page(a) for a in ARTICLES]
    hub_page()
    home_block()
    print("menus injected:", inject_menus())
    print("cases blocks:", inject_cases())
    sitemap(paths)
    llms()
    print("articles:", len(paths))
