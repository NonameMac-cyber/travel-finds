"""Basic SEO audit for the generated static site (stdlib only)."""
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

SITE = "https://nonamemac-cyber.github.io/travel-finds"

def txt(pattern, s):
    m = re.search(pattern, s, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

def expected(rel, site=SITE):
    b = site.rstrip("/")
    if rel == "index.html": return b + "/"
    if rel.endswith("/index.html"): return b + "/" + rel[:-10]
    return b + "/" + rel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default="_src/build")
    ap.add_argument("--site-url", default=SITE)
    ap.add_argument("--report", default="_src/reports/seo-report.json")
    args = ap.parse_args()
    site = args.site_url.rstrip("/")
    build = Path(args.build)
    if not (build / "index.html").exists():
        print("ERROR: run build_site.py first", file=sys.stderr)
        return 2
    pages = sorted(build.rglob("*.html"))
    errors, warnings, titles, descs = [], [], {}, {}
    for p in pages:
        rel = p.relative_to(build).as_posix()
        s = p.read_text(encoding="utf-8")
        title = txt(r"<title>(.*?)</title>", s)
        desc = txt(r"<meta\s+name=[\"\x27]description[\"\x27]\s+content=[\"\x27](.*?)[\"\x27]", s)
        canonical = txt(r"<link\s+rel=[\"\x27]canonical[\"\x27]\s+href=[\"\x27](.*?)[\"\x27]", s)
        h1 = re.findall(r"<h1\b[^>]*>", s, re.I)
        lang = txt(r"<html\s+lang=[\"\x27](.*?)[\"\x27]", s)
        def add(kind, msg):
            (warnings if kind.startswith("warn") else errors).append({"page": rel, "type": kind, "message": msg})
        if not title: add("title", "missing title")
        elif not 15 <= len(title) <= 65: add("warn-title", f"title length {len(title)}")
        if not desc: add("description", "missing meta description")
        elif not 50 <= len(desc) <= 160: add("warn-description", f"description length {len(desc)}")
        if not canonical: add("canonical", "missing canonical")
        elif canonical.rstrip("/") != expected(rel, site).rstrip("/"): add("canonical", f"expected {expected(rel, site)}")
        if len(h1) != 1: add("h1", f"found {len(h1)} h1 tags")
        if not lang: add("lang", "missing html lang")
        if not re.search(r"<meta\s+name=[\"\x27]viewport[\"\x27]", s, re.I): add("viewport", "missing viewport meta")
        for key in ("og:title", "og:description", "og:image", "twitter:card"):
            if not re.search(r"<meta\s+(?:property|name)=[\"\x27]" + re.escape(key) + r"[\"\x27]", s, re.I):
                add("social", "missing " + key)
        for img in re.findall(r"<img\b[^>]*>", s, re.I):
            if not re.search(r"\balt\s*=", img, re.I): add("image-alt", "img without alt: " + img[:70])
        for block in re.findall(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", s, re.I | re.S):
            try:
                d = json.loads(block)
                if "@context" not in d: raise ValueError("missing @context")
            except Exception as e: add("jsonld", f"invalid JSON-LD: {e}")
        titles.setdefault(title, []).append(rel)
        descs.setdefault(desc, []).append(rel)
    for label, mapping in (("title", titles), ("description", descs)):
        for value, rels in mapping.items():
            if value and len(rels) > 1:
                warnings.append({"page": ", ".join(rels), "type": "warn-duplicate", "message": f"duplicate {label}: {value[:60]}"})
    sitemap = (build / "sitemap.xml").read_text(encoding="utf-8") if (build / "sitemap.xml").exists() else ""
    for p in pages:
        rel = p.relative_to(build).as_posix()
        if expected(rel) not in sitemap:
            warnings.append({"page": rel, "type": "warn-sitemap", "message": "URL missing from sitemap.xml"})
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "site_url": site,
              "pages_checked": len(pages), "errors": errors, "warnings": warnings}
    rp = Path(args.report); rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for e in errors: print(f"ERROR [{e['type']}] {e['page']} — {e['message']}")
    for w in warnings: print(f"WARN  [{w['type']}] {w['page']} — {w['message']}")
    print(f"SEO audit: {len(pages)} pages, {len(errors)} errors, {len(warnings)} warnings. Report: {rp}")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
