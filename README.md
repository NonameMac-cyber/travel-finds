# Travel Finds — EN/ES travel deals

Статический сайт Travel Finds: лендинги EN/ES, блог, партнёрские ссылки TravelPayouts.

- Live (GitHub Pages): https://nonamemac-cyber.github.io/travel-finds/
- Vercel: https://travel-finds.vercel.app
- EN: `index.html`
- ES: `es.html`
- Гайды: `blog/*.html`, `es/blog/*.html`
- Стили/скрипты: `assets/`

## Исходники и сборка

Исходники лежат в `_src/`:

- `_src/site/` — HTML-шаблоны и ассеты
- `_src/content/` — Markdown-статьи
- `_src/config/links.generated.json` — партнёрские ссылки
- `_src/tools/build_site.py` — генератор статического сайта

Пересборка:

```bash
python3 _src/tools/build_site.py
```

Скрипт собирает сайт в `_src/build/` и публикует готовые файлы в корень
репозитория для локального просмотра. На Vercel публикация в корень
отключается автоматически: Vercel забирает результат прямо из `_src/build/`.

## Автодеплой

Vercel-проект `valdislavn-1094/travel-finds` подключён к репозиторию.
Пуш в `main` запускает production-деплой Vercel.

GitHub Actions workflow `.github/workflows/pages.yml` при каждом пуше в `main`:

1. собирает сайт;
2. проверяет ключевые файлы;
3. публикует готовую статику в ветку `gh-pages`.

GitHub Pages настроен на ветку `gh-pages` (folder `/ (root)`), поэтому
`https://nonamemac-cyber.github.io/travel-finds/` обновляется автоматически.

## Правовое

Партнёрские ссылки раскрываются на странице. Цены и доступность меняются —
перед покупкой проверяйте у провайдера. Это не финансовая рекомендация.
Дизайн основан на MIT-шаблоне Trippi; лицензия лежит в
`assets/vendor/trippi-LICENSE.txt`.

## SEO и проверка ссылок

- `python3 _src/tools/seo_check.py --report _src/reports/seo-report.json` — проверяет title, description, canonical, h1, viewport, Open Graph, alt у изображений, JSON-LD и sitemap.
- `.github/workflows/seo-audit.yml` — GitHub Actions: сборка, SEO-аудит, проверка внутренних ссылок и якорей через `lycheeverse/lychee-action`, проверка внешних ссылок и отчёт-артефакт.
- `.github/workflows/lighthouse.yml` — Lighthouse CI для SEO, accessibility, best practices и performance после публикации GitHub Pages.
- `.github/workflows/pages.yml` — перед публикацией в `gh-pages` запускает SEO-аудит и проверку внутренних ссылок, поэтому битая внутренняя ссылка блокирует деплой.
- `feed.xml` генерируется автоматически; RSS подключён в `<head>` всех страниц.
- В статьях автоматически появляется блок «Related guides» с внутренними ссылками, а на лендингах — блок «Trusted resources» с внешними источниками.
