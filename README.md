# Travel Finds — EN/ES travel deals

Статический сайт Travel Finds: лендинги EN/ES, блог, партнёрские ссылки TravelPayouts.

- Live: https://nonamemac-cyber.github.io/travel-finds
- EN: `index.html`
- ES: `es.html`
- Гайды: `blog/*.html`, `es/blog/*.html`
- Стили/скрипты: `assets/`

## Автодеплой

Проект Vercel `valdislavn-1094/travel-finds` подключён к этому репозиторию.
Пуш в ветку `main` запускает автоматический production-деплой.
Pull request создаёт preview-деплой.

Vercel сам запускает `python3 _src/tools/build_site.py` и публикует
готовую статику из `_src/build/`.

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


## Резервный хостинг

В репозитории есть workflow `.github/workflows/pages.yml` для GitHub Pages.
Чтобы включить его, один раз открой:

https://github.com/NonameMac-cyber/travel-finds/settings/pages

и выбери **Source: GitHub Actions**. После этого workflow будет публиковать
сайт на `https://nonamemac-cyber.github.io/travel-finds/`.

Vercel при этом остаётся основным production-хостингом.

## GitHub Actions

Workflow `.github/workflows/pages.yml` собирает сайт и публикует готовую статику
в ветку `gh-pages` при каждом пуше в `main`.

Чтобы включить GitHub Pages:

1. Открой `Settings -> Pages`.
2. В **Build and deployment** выбери **Deploy from a branch**.
3. Branch: `gh-pages`, folder: `/ (root)`.
4. Нажми **Save**.

После этого сайт будет доступен по адресу
`https://nonamemac-cyber.github.io/travel-finds/`.
