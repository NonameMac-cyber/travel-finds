#!/usr/bin/env python3
"""Build static deploy bundle for Travel Finds (EN/ES landing + blog) — stdlib only.

Usage:  python3 tools/build_site.py
Output: travel-affiliate/build/  (ready to push to the `travel-finds` GitHub repo)
"""
import json, os, re, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build'
SITE_URL = 'https://travel-finds-valdislavn-1094.vercel.app'
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

def page_html(*, lang, title, description, canonical, body, root, home_link, guide_href, lang_href, og_image=None):
    other_label = 'ES' if lang == 'en' else 'EN'
    css_href = root + 'assets/style.css'
    html = f"""<{chr(33)}DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css_href}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Ccircle cx=%2750%27 cy=%2750%27 r=%2748%27 fill=%27%23173c32%27/%3E%3Ctext x=%2750%27 y=%2765%27 font-size=%2746%27 text-anchor=%27middle%27 fill=%27%23f6f0e4%27%3E%E2%9C%88%3C/text%3E%3C/svg%3E">
<meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{og_image or SITE_URL + '/assets/og-cover.png'}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og_image or SITE_URL + '/assets/og-cover.png'}">
</head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-header><div class="container header-inner">
<a class="brand" href="{home_link}" aria-label="Travel Finds — home"><span class="brand-mark" aria-hidden="true">✈</span><span>Travel <em>Finds</em></span></a>
<nav class="site-nav" id="site-nav" aria-label="Navigation" data-nav><a href="{home_link}#finds">Finds</a><a href="{home_link}#how">How it works</a><a href="{guide_href}">Guides</a><a href="{home_link}#search">Search</a></nav>
<div class="header-actions"><a class="lang-pill" href="{lang_href}" hreflang="{'es' if lang == 'en' else 'en'}">{other_label}</a><a class="btn btn--primary btn--small" href="{home_link}#search">Find a trip</a><button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="site-nav" data-menu-toggle><span></span></button></div>
</div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="container"><div class="footer-grid">
<div class="footer-brand"><a class="brand" href="{home_link}"><span class="brand-mark" aria-hidden="true">✈</span><span>Travel <em>Finds</em></span></a><p>Independent travel media. We compare flight, stay and travel-essential options so you can spend less and go more often.</p></div>
<div class="footer-col"><h3>Explore</h3><a href="{home_link}#finds">Finds</a><a href="{home_link}#how">How it works</a><a href="{guide_href}">Guides</a></div>
<div class="footer-col"><h3>Language</h3><a href="{lang_href}" hreflang="{'es' if lang == 'en' else 'en'}">{other_label} version</a><a href="{home_link}#disclosure">Affiliate disclosure</a></div>
</div><div class="footer-bottom"><span>© 2026 Travel Finds.</span><span class="footer-credit">Design adapted from <a href="https://github.com/RSurya99/trippi" rel="noopener">Trippi</a> (MIT).</span></div></div></footer>
<script src="{root}assets/site-config.js"></script><script src="{root}assets/main.js"></script></body></html>"""
    return html

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
               'sub': 'Guías prácticas para viajar mejor y pagar menos.'},
    }
    sources = [('en', ROOT / 'content/seo-en.md', OUT / 'blog'), ('es', ROOT / 'content/seo-es.md', OUT / 'es' / 'blog')]
    for lang, src, base in sources:
        cfg = config[lang]
        arts = parse_articles(src.read_text(encoding='utf-8'), lang)
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
            head = f'<div class="container" style="padding:56px 0 80px"><article class="article-shell">{hero_html}<h1>{title}</h1><p class="article-meta">{meta}</p><div class="article-body">{body_html}</div></article></div>'
            html = page_html(lang=lang, title=title + ' | Travel Finds', description=desc, canonical=canonical, body=head,
                             root=cfg['root'], home_link=cfg['home'], guide_href='./', lang_href=cfg['lang_href'],
                             og_image=(SITE_URL + '/' + hero) if hero else None)
            (base / f'{slug}.html').write_text(html, encoding='utf-8')
            indexing[lang].append({'slug': slug, 'title': title, 'desc': desc, 'image': hero})

        cards = []
        for a in indexing[lang]:
            image = f'<img src="{cfg["root"]}{a["image"]}" alt="" loading="lazy" width="340" height="240">' if a['image'] else ''
            cards.append(f'<a class="blog-card" href="{a["slug"]}.html">{image}<div class="blog-card__body"><span class="blog-card__label">{cfg["guide"]}</span><h2>{a["title"]}</h2><p>{a["desc"]}</p></div></a>')
        body = f'<section class="page-hero"><div class="container"><p class="kicker">{cfg["guide"]}</p><h1>{cfg["h1"]}</h1><p>{cfg["sub"]}</p></div></section><section class="container" style="padding-top:46px"><div class="blog-list">{"".join(cards)}</div></section>'
        idx = page_html(lang=lang, title=('Guides | Travel Finds' if lang == 'en' else 'Guías | Travel Finds'),
                        description=cfg['sub'], canonical=f"{SITE_URL}/{'blog' if lang == 'en' else 'es/blog'}/", body=body,
                        root=cfg['root'], home_link=cfg['home'], guide_href='./', lang_href=cfg['lang_href'])
        (base / 'index.html').write_text(idx, encoding='utf-8')

    (OUT / 'robots.txt').write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding='utf-8')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    (OUT / '.vercelignore').write_text('.vercel\n.env*\n.gitignore\n', encoding='utf-8')
    urls = [f"{SITE_URL}/", f"{SITE_URL}/es.html", f"{SITE_URL}/blog/", f"{SITE_URL}/es/blog/"]
    urls += [f"{SITE_URL}/blog/{a['slug']}.html" for a in indexing['en']]
    urls += [f"{SITE_URL}/es/blog/{a['slug']}.html" for a in indexing['es']]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f'  <url><loc>{u}</loc></url>')
    sm.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sm), encoding='utf-8')
    print('built', len(indexing['en']), 'EN articles,', len(indexing['es']), 'ES articles ->', OUT)
    for u in urls:
        print(' ', u)


GENERATED = ['assets', 'blog', 'es', 'index.html', 'es.html', 'robots.txt', 'sitemap.xml', '.nojekyll']

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
