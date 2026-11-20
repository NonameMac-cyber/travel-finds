#!/usr/bin/env python3
"""Build static deploy bundle for Travel Finds (EN/ES landing + blog) — stdlib only.

Usage:  python3 tools/build_site.py
Output: travel-affiliate/build/  (ready to push to the `travel-finds` GitHub repo)
"""
import json, os, re, shutil, sys, tempfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build'
SITE_URL = 'https://nonamemac-cyber.github.io/travel-finds'
INDEXNOW_KEY = (ROOT / 'site' / 'indexnow-key.txt').read_text(encoding='utf-8').strip()
LINKS = json.load(open(ROOT / 'config/links.generated.json', encoding='utf-8'))

NAMES = {'kiwi':'Kiwi.com','klook':'Klook','saily':'Saily','gocity':'Go City','yesim':'Yesim','airalo':'Airalo',
 'drimsim':'Drimsim','gigsky':'GigSky','kiwitaxi':'Kiwitaxi','localrent':'Localrent','gettransfer':'GetTransfer',
 'welcomepickups':'Welcome Pickups','intui':'intui.travel','wegotrip':'WeGoTrip','tiqets':'Tiqets','kkday':'KKday',
 'radicalstorage':'Radical Storage','airhelp':'AirHelp','compensair':'Compensair','economybookings':'Economybookings',
 'getrentacar':'GetRentacar','qeeq':'QEEQ','bikesbooking':'BikesBooking','tripcom':'Trip.com','getyourguide':'GetYourGuide',
 'omio':'Omio','discovercars':'DiscoverCars','12go':'12Go','booking':'Booking.com','agoda':'Agoda','expedia':'Expedia',
 'hotelscom':'Hotels.com','viator':'Viator','traveloka':'Traveloka','hostelworld':'Hostelworld','vrbo':'Vrbo',
 'ticketmaster':'Ticketmaster','vio':'Vio.com','rakuten_jp':'Rakuten Travel','rakuten_intl':'Rakuten Travel'}

def resolve_tokens(text, lang):
    ch = 'seo_en' if lang == 'en' else 'seo_es'
    programs = LINKS['channels'][ch]['programs']

    def program_url(key):
        return programs.get(key, {}).get('url', '')

    # A token used as a Markdown destination must become a normal Markdown link.
    # Replacing it with raw HTML first creates nested anchors after inline_md().
    def md_link(m):
        label, key = m.group(1), m.group(2)
        url = program_url(key)
        return f'[{label}]({url})' if url else label

    text = re.sub(r'\[([^\]]+)\]\(\{\{TP:([a-z0-9_]+)(?:\|[^}]*)?\}\}\)', md_link, text)

    def repl(m):
        key = m.group(1)
        url = program_url(key)
        name = NAMES.get(key, key)
        if url:
            return f'<a href="{url}">{name}</a>'
        return name

    return re.sub(r'\{\{TP:([a-z0-9_]+)(?:\|[^}]*)?\}\}', repl, text)

def inline_md(s):
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s

def md_to_html(md):
    lines = md.splitlines()
    html, i = [], 0
    list_tag = None
    def close_list():
        nonlocal list_tag
        if list_tag:
            html.append(f'</{list_tag}>')
            list_tag = None
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            close_list(); i += 1; continue
        if re.match(r'^#{1,4} ', line):
            close_list(); level = len(re.match(r'^(#+) ', line).group(1)); text = line[level+1:].strip()
            if level == 1:
                i += 1; continue
            html.append(f'<h{level}>{inline_md(text)}</h{level}>'); i += 1; continue
        if line.strip() in ('---', '***'):
            close_list(); html.append('<hr>'); i += 1; continue
        if line.startswith('> '):
            close_list(); html.append(f'<blockquote>{inline_md(line[2:].strip())}</blockquote>'); i += 1; continue
        m = re.match(r'^[-*] (.+)$', line.strip())
        if m:
            if list_tag != 'ul': close_list(); html.append('<ul>'); list_tag = 'ul'
            html.append(f'<li>{inline_md(m.group(1))}</li>'); i += 1; continue
        m = re.match(r'^\d+\. (.+)$', line.strip())
        if m:
            if list_tag != 'ol': close_list(); html.append('<ol>'); list_tag = 'ol'
            html.append(f'<li>{inline_md(m.group(1))}</li>'); i += 1; continue
        close_list(); html.append(f'<p>{inline_md(line.strip())}</p>'); i += 1
    close_list()
    return '\n'.join(html)

def parse_articles(text, lang):
    parts = re.split(r'<!--\s*=+\s*[^>]*?=+\s*-->', text)
    arts = []
    for part in parts:
        part = part.strip()
        if '---' not in part or 'title:' not in part:
            continue
        m = re.search(r'^---\s*\n(.*?)\n---\s*\n(.*)$', part, re.S)
        if not m: continue
        fm_raw, body = m.group(1), m.group(2)
        fm = {}
        for line in fm_raw.splitlines():
            mm = re.match(r'^([a-zA-Z_]+):\s*(.*)$', line)
            if mm: fm[mm.group(1)] = mm.group(2).strip().strip('"')
        if 'slug' not in fm: continue
        arts.append({'fm': fm, 'body': resolve_tokens(body, lang), 'lang': lang})
    return arts

CSS = """
:root{--blue:#1857e6;--ink:#14181f;--muted:#5c6470;--bg:#f5f7fb;--card:#fff;--line:#e4e8f0}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--card);line-height:1.6}
.wrap{max-width:920px;margin:0 auto;padding:0 20px}
.header{border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:10}
.header__row{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{display:flex;gap:10px;align-items:center;font-weight:700;color:var(--ink);text-decoration:none;font-size:18px}
.logo__mark{display:inline-flex;width:34px;height:34px;border-radius:50%;background:var(--blue);color:#fff;align-items:center;justify-content:center}
.header__nav{display:flex;gap:18px;align-items:center}.header__nav a{color:var(--muted);text-decoration:none;font-size:14px}.header__nav a:hover{color:var(--ink)}
main{padding:32px 0 56px}
article .hero{margin:0 0 24px}article .hero img{width:100%;height:auto;border-radius:14px;display:block;background:#e9edf4;object-fit:cover}article h1{font-size:34px;line-height:1.2;margin:0 0 16px;letter-spacing:-.5px}
article h2{font-size:24px;margin:34px 0 12px}article h3{font-size:19px;margin:26px 0 10px}
article p{margin:0 0 16px;font-size:17px;color:#242a33}article li{font-size:17px;margin-bottom:8px}
article a{color:var(--blue)}article blockquote{margin:18px 0;padding:12px 18px;border-left:3px solid var(--blue);background:var(--bg);border-radius:0 10px 10px 0;color:var(--muted)}
article hr{border:0;border-top:1px solid var(--line);margin:28px 0}
.meta{color:var(--muted);font-size:14px;margin-bottom:24px}
.disclosure{margin:32px 0;padding:16px 18px;background:var(--bg);border:1px solid var(--line);border-radius:12px;font-size:13px;color:var(--muted)}
.cta{display:inline-block;background:var(--blue);color:#fff!important;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600;margin:8px 0 4px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin:20px 0}
.card{border:1px solid var(--line);border-radius:14px;padding:20px;background:var(--card);text-decoration:none;color:var(--ink);transition:.15s}
.card:hover{border-color:var(--blue);transform:translateY(-1px)}.card h3{margin:0 0 8px;font-size:18px}.card p{margin:0;color:var(--muted);font-size:14px}
.footer{border-top:1px solid var(--line);padding:24px 0;color:var(--muted);font-size:13px;background:var(--bg)}
.footer a{color:var(--muted)}.lang-switch{border:1px solid var(--line);padding:4px 10px;border-radius:999px;font-size:13px}
"""

HEADER = """<header class="header"><div class="wrap header__row">
<a class="logo" href="{home}"><span class="logo__mark" aria-hidden="true">✈</span>Travel Finds</a>
<nav class="header__nav"><a href="{home}{guide}">Guides</a><a href="{other}">{other_label}</a></nav>
</div></header>"""

def page_html(*, lang, title, description, canonical, body, root, home_link, guide_href, lang_href, og_image=None, json_ld=None):
    other_label = 'ES' if lang == 'en' else 'EN'
    legal_base = root + ('es/' if lang == 'es' else '')
    css_href = root + 'assets/style.css'
    og_type = 'article' if json_ld else 'website'
    og_locale = 'en_US' if lang == 'en' else 'es_ES'
    jsonld_script = ('<script type="application/ld+json">' + json.dumps(json_ld, ensure_ascii=False, separators=(',', ':')) + '</script>') if json_ld else ''
    html = f"""<{chr(33)}DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="Travel Finds RSS" href="{SITE_URL}/feed.xml">
<meta name="author" content="Travel Finds">
<link rel="stylesheet" href="{css_href}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Ccircle cx=%2750%27 cy=%2750%27 r=%2748%27 fill=%27%23173c32%27/%3E%3Ctext x=%2750%27 y=%2765%27 font-size=%2746%27 text-anchor=%27middle%27 fill=%27%23f6f0e4%27%3E%E2%9C%88%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Travel Finds"><meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{og_image or SITE_URL + '/assets/og-cover.png'}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{description}"><meta name="twitter:image" content="{og_image or SITE_URL + '/assets/og-cover.png'}">
{jsonld_script}
</head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-header><div class="container header-inner">
<a class="brand" href="{home_link}" aria-label="Travel Finds — home"><span class="brand-mark" aria-hidden="true">✈</span><span>Travel <em>Finds</em></span></a>
<nav class="site-nav" id="site-nav" aria-label="Navigation" data-nav><a href="{home_link}#finds">Finds</a><a href="{home_link}#how">How it works</a><a href="{guide_href}">Guides</a><a href="{home_link}#resources">Resources</a><a href="{home_link}#search">Search</a></nav>
<div class="header-actions"><a class="lang-pill" href="{lang_href}" hreflang="{'es' if lang == 'en' else 'en'}">{other_label}</a><a class="btn btn--primary btn--small" href="{home_link}#search">Find a trip</a><button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-nav" data-menu-toggle><span></span></button></div>
</div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="container"><div class="footer-grid">
<div class="footer-brand"><a class="brand" href="{home_link}"><span class="brand-mark" aria-hidden="true">✈</span><span>Travel <em>Finds</em></span></a><p>Independent travel media. We compare flight, stay and travel-essential options so you can spend less and go more often.</p></div>
<div class="footer-col"><h3>Explore</h3><a href="{home_link}#finds">Finds</a><a href="{home_link}#how">How it works</a><a href="{guide_href}">Guides</a><a href="{home_link}#resources">Resources</a></div>
<div class="footer-col"><h3>Useful links</h3><a href="https://europa.eu/youreurope/citizens/travel/passenger-rights/air/index_en.htm" target="_blank" rel="noopener">EU passenger rights</a><a href="https://www.caa.co.uk/passengers/" target="_blank" rel="noopener">UK CAA advice</a><a href="https://www.seat61.com/" target="_blank" rel="noopener">Seat61 rail guide</a><a href="https://wwwnc.cdc.gov/travel" target="_blank" rel="noopener">CDC travel health</a></div>
<div class="footer-col"><h3>Language</h3><a href="{lang_href}" hreflang="{'es' if lang == 'en' else 'en'}">{other_label} version</a><a href="{home_link}#disclosure">Affiliate disclosure</a><a href="{legal_base}privacy.html" data-legal="privacy">Privacy</a><a href="{legal_base}cookies.html" data-legal="cookies">Cookies</a><a href="{legal_base}about.html" data-legal="about">About &amp; contact</a><button type="button" class="link-button" data-cookie-reset>Cookie settings</button></div>
</div><div class="footer-bottom"><span>© 2026 Travel Finds.</span><span class="footer-credit">Design adapted from <a href="https://github.com/RSurya99/trippi" rel="noopener">Trippi</a> (MIT).</span></div></div></footer>
<script src="{root}assets/site-config.js"></script><script src="{root}assets/main.js"></script></body></html>"""
    return html


LEGAL_PAGES = {
    'privacy': {
        'en': {
            'title': 'Privacy Policy | Travel Finds',
            'desc': 'What data Travel Finds processes, why we use it, and how to exercise your privacy rights.',
            'h1': 'Privacy Policy',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">Legal</p><h1>Privacy Policy</h1><p>Last updated: 19 November 2026</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<p>Travel Finds is an independent travel media project. It is not an airline, hotel, travel agency or financial adviser.</p>
<h2>Who is responsible</h2><p>Travel Finds is responsible for the editorial content on this website. You can contact us through the public GitHub issue tracker linked at the bottom of this page.</p>
<h2>What we process</h2><ul>
<li>Technical data from our hosting providers: IP address, browser type, requested page, time and status code. This is needed to deliver and secure the site.</li>
<li>Aggregate analytics: page views, referrers, country and device type through Cloudflare Web Analytics. It is cookieless and does not create a cross-site profile of you.</li>
<li>Affiliate attribution: when you click a partner link or use the flight search widget, TravelPayouts or the travel partner may set cookies and record a referral. See our <a href="cookies.html">Cookie Policy</a>.</li>
<li>Messages you send us voluntarily through GitHub. Please do not include sensitive personal data.</li>
</ul>
<h2>Why we use it</h2><p>To run the site, understand which guides are useful, measure affiliate referrals, prevent abuse and answer messages.</p>
<h2>Legal bases</h2><p>Where GDPR applies, we rely on legitimate interests for hosting, security and aggregate analytics; consent where required for partner cookies; and the steps you request when you contact us.</p>
<h2>Third parties</h2><p>Our hosting and infrastructure providers include GitHub Pages, Vercel and Cloudflare. Affiliate services include TravelPayouts and its travel partners. We do not sell personal data. Partner websites are governed by their own privacy policies.</p>
<h2>Retention</h2><p>Hosting logs are kept according to each provider's retention settings. Analytics data is aggregate. Messages posted in GitHub remain public unless you contact us through another channel.</p>
<h2>Your rights</h2><p>You may request access, correction, deletion, restriction, objection or portability where applicable. You may also complain to your local data protection authority. To exercise a right, contact us through GitHub Issues.</p>
<h2>Changes</h2><p>We will update this page when our practices change. The date at the top shows the latest revision.</p>
</article></section>''',
        },
        'es': {
            'title': 'Privacidad | Travel Finds',
            'desc': 'Qué datos procesa Travel Finds, para qué los usamos y cómo ejercer tus derechos de privacidad.',
            'h1': 'Política de privacidad',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">Legal</p><h1>Política de privacidad</h1><p>Última actualización: 19 de noviembre de 2026</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<p>Travel Finds es un proyecto independiente de medios de viaje. No somos una aerolínea, hotel, agencia de viajes ni asesor financiero.</p>
<h2>Quién es responsable</h2><p>Travel Finds es responsable del contenido editorial de este sitio. Puedes contactarnos mediante el repositorio público de GitHub enlazado al final de esta página.</p>
<h2>Qué datos tratamos</h2><ul>
<li>Datos técnicos de nuestros proveedores de alojamiento: dirección IP, tipo de navegador, página solicitada, hora y código de estado. Son necesarios para entregar y proteger el sitio.</li>
<li>Analítica agregada: páginas vistas, referencias, país y tipo de dispositivo mediante Cloudflare Web Analytics. No usa cookies ni crea un perfil entre sitios.</li>
<li>Atribución de afiliados: cuando haces clic en un enlace de socio o usas el buscador de vuelos, TravelPayouts o el socio pueden instalar cookies y registrar una referencia. Consulta nuestra <a href="cookies.html">Política de cookies</a>.</li>
<li>Mensajes que nos envías voluntariamente a través de GitHub. No incluyas datos personales sensibles.</li>
</ul>
<h2>Para qué lo usamos</h2><p>Para operar el sitio, entender qué guías son útiles, medir referencias de afiliados, prevenir abusos y responder mensajes.</p>
<h2>Bases legales</h2><p>Cuando se aplica el RGPD, nos basamos en intereses legítimos para el alojamiento, la seguridad y la analítica agregada; en el consentimiento cuando sea necesario para cookies de socios; y en los pasos que solicitas cuando nos contactas.</p>
<h2>Terceros</h2><p>Nuestros proveedores de infraestructura incluyen GitHub Pages, Vercel y Cloudflare. Los servicios de afiliación incluyen TravelPayouts y sus socios de viaje. No vendemos datos personales. Los sitios de los socios se rigen por sus propias políticas.</p>
<h2>Conservación</h2><p>Los registros de alojamiento se conservan según la configuración de cada proveedor. La analítica es agregada. Los mensajes publicados en GitHub son públicos salvo que nos contactes por otro canal.</p>
<h2>Tus derechos</h2><p>Puedes solicitar acceso, rectificación, supresión, limitación, oposición o portabilidad cuando corresponda. También puedes reclamar ante tu autoridad de protección de datos. Para ejercer un derecho, contáctanos mediante GitHub Issues.</p>
<h2>Cambios</h2><p>Actualizaremos esta página cuando cambien nuestras prácticas. La fecha superior muestra la última revisión.</p>
</article></section>''',
        },
    },
    'cookies': {
        'en': {
            'title': 'Cookie Policy | Travel Finds',
            'desc': 'How Travel Finds uses essential storage, Cloudflare analytics and partner affiliate cookies.',
            'h1': 'Cookie Policy',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">Legal</p><h1>Cookie Policy</h1><p>Last updated: 19 November 2026</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<p>This page explains the storage and cookies used by Travel Finds and by the partner services connected to it.</p>
<h2>What we store</h2><p>We do not use first-party advertising cookies. We store your cookie choice in your browser's local storage under the key <code>tf-consent-v1</code>. This is essential to remember your choice.</p>
<h2>Cloudflare Web Analytics</h2><p>We use Cloudflare Web Analytics to count page views and understand aggregate traffic. It is cookieless, does not create a cross-site profile and does not identify individual visitors.</p>
<h2>Affiliate cookies</h2><p>TravelPayouts and travel partners may set cookies when you use the flight search widget or click a partner link. These cookies help attribute a booking to this site and usually last up to 30 days. They are controlled by the partner and are subject to the partner's own cookie and privacy policies.</p>
<h2>Flight search widget</h2><p>The TravelPayouts flight search widget is loaded only after you choose <strong>Accept all</strong>. If you choose <strong>Essential only</strong>, we show direct partner links instead. The widget may set cookies or local storage when it loads.</p>
<h2>Managing cookies</h2><p>Use the <strong>Cookie settings</strong> link in the footer to reset your choice, or clear site data in your browser. Blocking partner cookies may affect search and booking features.</p>
<h2>Contact</h2><p>Questions about this policy can be sent through the public GitHub issue tracker linked in the footer.</p>
</article></section>''',
        },
        'es': {
            'title': 'Cookies | Travel Finds',
            'desc': 'Cómo Travel Finds usa almacenamiento esencial, analítica de Cloudflare y cookies de afiliados.',
            'h1': 'Política de cookies',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">Legal</p><h1>Política de cookies</h1><p>Última actualización: 19 de noviembre de 2026</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<p>Esta página explica el almacenamiento y las cookies que usa Travel Finds y los servicios de socios conectados al sitio.</p>
<h2>Qué almacenamos</h2><p>No usamos cookies publicitarias propias. Guardamos tu elección en el almacenamiento local del navegador con la clave <code>tf-consent-v1</code>. Es esencial para recordar tu decisión.</p>
<h2>Cloudflare Web Analytics</h2><p>Usamos Cloudflare Web Analytics para contar páginas vistas y entender el tráfico agregado. No usa cookies, no crea un perfil entre sitios y no identifica a visitantes individuales.</p>
<h2>Cookies de afiliados</h2><p>TravelPayouts y los socios de viaje pueden instalar cookies cuando usas el buscador de vuelos o haces clic en un enlace de socio. Estas cookies ayudan a atribuir una reserva a este sitio y suelen durar hasta 30 días. Las controla el socio y se rigen por sus propias políticas.</p>
<h2>Buscador de vuelos</h2><p>El buscador de TravelPayouts se carga solo después de elegir <strong>Aceptar todo</strong>. Si eliges <strong>Solo esencial</strong>, mostramos enlaces directos a los socios. El buscador puede instalar cookies o almacenamiento local al cargarse.</p>
<h2>Gestión</h2><p>Usa el enlace <strong>Configuración de cookies</strong> del pie de página para reiniciar tu elección o borra los datos del sitio en el navegador. Bloquear cookies de socios puede afectar la búsqueda y la reserva.</p>
<h2>Contacto</h2><p>Las preguntas sobre esta política se pueden enviar mediante el repositorio público de GitHub enlazado en el pie de página.</p>
</article></section>''',
        },
    },
    'about': {
        'en': {
            'title': 'About & Contact | Travel Finds',
            'desc': 'About Travel Finds, how we make money, how we label sample prices and how to contact us.',
            'h1': 'About Travel Finds',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">About</p><h1>About Travel Finds</h1><p>Independent travel media. No hype, no fake urgency.</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<h2>What this site is</h2><p>Travel Finds publishes practical guides about cheaper flights, city breaks, flexible dates and travel essentials. We focus on decisions travellers can actually use, not on inventing prices or pressure tactics.</p>
<h2>How we make money</h2><p>Some links are affiliate links. If you click one and book with a partner, we may earn a commission at no extra cost to you. This never changes the editorial rules: we do not invent live prices, fake discounts or availability.</p>
<h2>Editorial rules</h2><ul>
<li>Sample prices and deal cards are clearly labelled as illustrative.</li>
<li>Affiliate links are marked with a sponsored link relationship.</li>
<li>We link to official sources for passenger rights, health and transport information where possible.</li>
<li>We correct material errors when they are found.</li>
</ul>
<h2>Corrections</h2><p>If you spot an error, open an issue in the public repository. Please include the page URL and the exact statement that needs checking.</p>
<h2>Contact</h2><p>The best public contact channel is <a href="https://github.com/NonameMac-cyber/travel-finds/issues" rel="noopener">GitHub Issues</a>. Do not send sensitive personal data.</p>
</article></section>''',
        },
        'es': {
            'title': 'Acerca de y contacto | Travel Finds',
            'desc': 'Quiénes somos, cómo ganamos dinero, cómo etiquetamos los precios de ejemplo y cómo contactarnos.',
            'h1': 'Acerca de Travel Finds',
            'body': '''<section class="page-hero"><div class="container"><p class="kicker">Acerca de</p><h1>Acerca de Travel Finds</h1><p>Medio de viajes independiente. Sin exageraciones ni urgencia falsa.</p></div></section>
<section class="container legal-page"><article class="article-shell article-body">
<h2>Qué es este sitio</h2><p>Travel Finds publica guías prácticas sobre vuelos baratos, escapadas urbanas, fechas flexibles y esenciales de viaje. Nos centramos en decisiones útiles para el viajero, no en inventar precios ni presionar para reservar.</p>
<h2>Cómo ganamos dinero</h2><p>Algunos enlaces son de afiliado. Si haces clic y reservas con un socio, podemos recibir una comisión sin coste adicional para ti. Esto no cambia nuestras reglas editoriales: no inventamos precios en vivo, descuentos falsos ni disponibilidad.</p>
<h2>Reglas editoriales</h2><ul>
<li>Los precios de ejemplo y las ofertas están marcados como ilustrativos.</li>
<li>Los enlaces de afiliado se identifican como enlaces patrocinados.</li>
<li>Enlazamos a fuentes oficiales sobre derechos de pasajeros, salud y transporte cuando es posible.</li>
<li>Corregimos errores materiales cuando los detectamos.</li>
</ul>
<h2>Correcciones</h2><p>Si ves un error, abre un issue en el repositorio público. Incluye la URL de la página y la frase exacta que debe revisarse.</p>
<h2>Contacto</h2><p>El canal público principal es <a href="https://github.com/NonameMac-cyber/travel-finds/issues" rel="noopener">GitHub Issues</a>. No envíes datos personales sensibles.</p>
</article></section>''',
        },
    },
}


def build_legal_pages():
    for slug, translations in LEGAL_PAGES.items():
        for lang, page in translations.items():
            if lang == 'en':
                root = ''
                home = 'index.html'
                guide = 'blog/'
                lang_href = f'es/{slug}.html'
                target = OUT / f'{slug}.html'
                canonical = f'{SITE_URL}/{slug}.html'
            else:
                root = '../'
                home = '../es.html'
                guide = 'blog/'
                lang_href = f'../{slug}.html'
                target = OUT / 'es' / f'{slug}.html'
                canonical = f'{SITE_URL}/es/{slug}.html'
            html = page_html(lang=lang, title=page['title'], description=page['desc'], canonical=canonical,
                             body=page['body'], root=root, home_link=home, guide_href=guide,
                             lang_href=lang_href)
            target.write_text(html, encoding='utf-8')


def build():
    preserved = ['.vercel', '.env.local', '.gitignore', '.vercelignore']
    stash = Path(tempfile.mkdtemp(prefix='tf-build-'))
    for name in preserved:
        src = OUT / name
        if src.exists():
            shutil.move(str(src), str(stash / name))
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in preserved:
        src = stash / name
        if src.exists():
            shutil.move(str(src), str(OUT / name))
    shutil.rmtree(stash, ignore_errors=True)

    shutil.copytree(ROOT / 'site/assets', OUT / 'assets', dirs_exist_ok=True)
    (OUT / f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY, encoding='utf-8')
    (OUT / 'blog').mkdir(parents=True, exist_ok=True)
    (OUT / 'es' / 'blog').mkdir(parents=True, exist_ok=True)

    # landing pages: source files already use the correct relative links.
    for src_name, dst_name in [('en.html', 'index.html'), ('es.html', 'es.html')]:
        html = (ROOT / 'site' / src_name).read_text(encoding='utf-8')
        html = html.replace('https://YOUR-DOMAIN.example', SITE_URL)
        (OUT / dst_name).write_text(html, encoding='utf-8')

    indexing = {'en': [], 'es': []}
    config = {
        'en': {'root': '../', 'home': '../index.html', 'lang_href': '../es/blog/', 'label': 'EN',
               'guide': 'Travel guides', 'h1': 'Travel guides and money-saving playbooks',
               'sub': 'Practical, no-hype guides to cheaper flights, city breaks and travel essentials.'},
        'es': {'root': '../../', 'home': '../../es.html', 'lang_href': '../blog/', 'label': 'ES',
               'guide': 'Guías de viaje', 'h1': 'Guías de viaje y trucos para ahorrar',
               'sub': 'Guías prácticas para viajar mejor, pagar menos y evitar trampas al reservar.'},
    }
    sources = [('en', ROOT / 'content/seo-en.md', OUT / 'blog'), ('es', ROOT / 'content/seo-es.md', OUT / 'es' / 'blog')]
    for lang, src, base in sources:
        cfg = config[lang]
        arts = parse_articles(src.read_text(encoding='utf-8'), lang)
        indexing[lang] = []
        for art in arts:
            fm = art['fm']
            indexing[lang].append({'slug': fm['slug'], 'title': fm.get('title', fm['slug']),
                                   'desc': fm.get('description', ''), 'image': str(fm.get('image', '')).strip()})
        for art in arts:
            fm = art['fm']; slug = fm['slug']
            body_html = md_to_html(art['body'])
            title = fm.get('title', slug); desc = fm.get('description', '')
            prefix = 'blog' if lang == 'en' else 'es/blog'
            canonical = f"{SITE_URL}/{prefix}/{slug}.html"
            hero = str(fm.get('image', '')).strip()
            hero_html = ''
            if hero:
                hero_html = f'<figure class="article-hero"><img src="{cfg["root"]}{hero}" alt="{title}" loading="eager" width="1200" height="675"></figure>'
            meta = f'{fm.get("lang", lang).upper()} · Travel Finds guides'
            related = [a for a in indexing[lang] if a['slug'] != slug][:3]
            related_title = 'Related guides' if lang == 'en' else 'Guías relacionadas'
            related_cards = ''.join(
                f'<a class="related-card" href="{a["slug"]}.html"><strong>{a["title"]}</strong><span>{a["desc"]}</span></a>'
                for a in related
            )
            related_html = f'<aside class="related-guides"><h2>{related_title}</h2><div class="related-list">{related_cards}</div></aside>' if related_cards else ''
            image_url = (SITE_URL + '/' + hero) if hero else (SITE_URL + '/assets/og-cover.png')
            home_name = 'Home' if lang == 'en' else 'Inicio'
            guides_name = 'Guides' if lang == 'en' else 'Guías'
            article_ld = {
                '@context': 'https://schema.org',
                '@graph': [
                    {'@type': 'Article', '@id': canonical + '#article', 'headline': title, 'description': desc,
                     'image': [image_url], 'inLanguage': lang,
                     'author': {'@type': 'Organization', 'name': 'Travel Finds'},
                     'publisher': {'@type': 'Organization', 'name': 'Travel Finds', 'url': SITE_URL + '/'},
                     'mainEntityOfPage': {'@type': 'WebPage', '@id': canonical}},
                    {'@type': 'BreadcrumbList', 'itemListElement': [
                        {'@type': 'ListItem', 'position': 1, 'name': home_name, 'item': SITE_URL + '/'},
                        {'@type': 'ListItem', 'position': 2, 'name': guides_name, 'item': f"{SITE_URL}/{prefix}/"},
                        {'@type': 'ListItem', 'position': 3, 'name': title, 'item': canonical},
                    ]},
                ],
            }
            head = f'<div class="container" style="padding:56px 0 80px"><article class="article-shell">{hero_html}<h1>{title}</h1><p class="article-meta">{meta}</p><div class="article-body">{body_html}</div>{related_html}</article></div>'
            html = page_html(lang=lang, title=title, description=desc, canonical=canonical, body=head,
                             root=cfg['root'], home_link=cfg['home'], guide_href='./', lang_href=cfg['lang_href'],
                             og_image=image_url, json_ld=article_ld)
            (base / f'{slug}.html').write_text(html, encoding='utf-8')

        cards = []
        for a in indexing[lang]:
            image = f'<img src="{cfg["root"]}{a["image"]}" alt="" loading="lazy" width="340" height="240">' if a['image'] else ''
            cards.append(f'<a class="blog-card" href="{a["slug"]}.html">{image}<div class="blog-card__body"><span class="blog-card__label">{cfg["guide"]}</span><h2>{a["title"]}</h2><p>{a["desc"]}</p></div></a>')
        body = f'<section class="page-hero"><div class="container"><p class="kicker">{cfg["guide"]}</p><h1>{cfg["h1"]}</h1><p>{cfg["sub"]}</p></div></section><section class="container" style="padding-top:46px"><div class="blog-list">{"".join(cards)}</div></section>'
        idx = page_html(lang=lang, title=('Guides | Travel Finds' if lang == 'en' else 'Guías | Travel Finds'),
                        description=cfg['sub'], canonical=f"{SITE_URL}/{'blog' if lang == 'en' else 'es/blog'}/", body=body,
                        root=cfg['root'], home_link=cfg['home'], guide_href='./', lang_href=cfg['lang_href'])
        (base / 'index.html').write_text(idx, encoding='utf-8')

    build_legal_pages()
    (OUT / 'robots.txt').write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding='utf-8')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    (OUT / '.vercelignore').write_text('.vercel\n.env*\n.gitignore\n', encoding='utf-8')
    urls = [f"{SITE_URL}/", f"{SITE_URL}/es.html", f"{SITE_URL}/blog/", f"{SITE_URL}/es/blog/"]
    urls += [f"{SITE_URL}/{slug}.html" for slug in LEGAL_PAGES]
    urls += [f"{SITE_URL}/es/{slug}.html" for slug in LEGAL_PAGES]
    urls += [f"{SITE_URL}/blog/{a['slug']}.html" for a in indexing['en']]
    urls += [f"{SITE_URL}/es/blog/{a['slug']}.html" for a in indexing['es']]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f'  <url><loc>{u}</loc></url>')
    sm.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sm), encoding='utf-8')
    rss_items = []
    for lang in ('en', 'es'):
        prefix = 'blog' if lang == 'en' else 'es/blog'
        for a in indexing[lang]:
            link = f"{SITE_URL}/{prefix}/{a['slug']}.html"
            rss_items.append(f"<item><title>{xml_escape(a['title'])}</title><link>{link}</link><guid>{link}</guid><description>{xml_escape(a['desc'])}</description></item>")
    rss = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
           f'<title>Travel Finds</title><link>{SITE_URL}/</link><description>Independent travel finds and money-saving guides.</description>'
           f'<language>en</language>{"".join(rss_items)}</channel></rss>')
    (OUT / 'feed.xml').write_text(rss, encoding='utf-8')
    print('built', len(indexing['en']), 'EN articles,', len(indexing['es']), 'ES articles ->', OUT)
    for u in urls:
        print(' ', u)


GENERATED = ['assets', 'blog', 'es', 'index.html', 'es.html', 'privacy.html', 'cookies.html', 'about.html', 'robots.txt', 'sitemap.xml', 'feed.xml', '.nojekyll', f'{INDEXNOW_KEY}.txt']

def publish():
    """Copy the generated static site from _src/build to the repository root."""
    repo = ROOT.parent
    for name in GENERATED:
        target = repo / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    shutil.copytree(OUT, repo, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.vercel', '.env.local', '.gitignore', '.vercelignore'))
    print('published ->', repo)


if __name__ == '__main__':
    build()
    if os.environ.get('VERCEL') == '1':
        print('Vercel build: skipped publishing to repository root')
    else:
        publish()
