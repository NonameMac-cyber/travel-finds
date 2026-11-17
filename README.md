# Travel Finds — EN/ES travel deals

Статический сайт Travel Finds: лендинги EN/ES, блог, партнёрские ссылки TravelPayouts.

- Live: https://travel-finds.vercel.app
- EN: `index.html`
- ES: `es.html`
- Гайды: `blog/*.html`, `es/blog/*.html`
- Стили/скрипты: `assets/`

## Автодеплой

Проект Vercel `valdislavn-1094/travel-finds` подключён к этому репозиторию.
Пуш в ветку `main` запускает автоматический production-деплой.
Pull request создаёт preview-деплой.

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

Скрипт собирает сайт в `_src/build/` и публикует готовые файлы в корень репозитория.
Корень репозитория — то, что деплоит Vercel.

## Правовое

Партнёрские ссылки раскрываются на странице. Цены и доступность меняются —
перед покупкой проверяйте у провайдера. Это не финансовая рекомендация.
Дизайн основан на MIT-шаблоне Trippi; лицензия лежит в
`assets/vendor/trippi-LICENSE.txt`.
