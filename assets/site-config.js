/* ==========================================================================
   Партнёрские ID/ссылки для сайта (site/) — non-RU (EN/ES).
   Основная страница: site/en.html (seo_en-ссылки), site/es.html (seo_es).
   RU-страница site/index.html переведена в архив (noindex, не деплоится).
   Ссылки взяты из config/links.generated.json (website project 597672,
   seo_en / seo_es; могут отдавать 403 до заполнения формы ad law — тогда
   пользователь откладывает партнёрские кнопки; замените urls на новые).
   API-токен на сайте НЕ НУЖЕН и НЕ ДОЛЖЕН попадать в репозиторий.
   ========================================================================== */
window.TRAVEL_CONFIG = {
  marker: "674170",
  market: "non_ru",
  widget: {
    // TravelPayouts widget: Aviasales Flights Search Form.
    // Source project 597756 (Travel-finds), widget 7879, campaign 100.
    promoId: "7879",
    campaignId: "100",
    poweredBy: "true",
  },
  // У каждой программы своя короткая ссылка на язык (sub_id seo_en/seo_es
  // зашит при создании). fallback — url для остальных случаев.
  programs: {
    kiwi: {
      url: "",
      urls: {
        en: "https://kiwi.tpk.ro/RJINNJJm",
        es: "https://kiwi.tpk.ro/n2alia22",
      },
      landing: "https://www.kiwi.com/",
      label: "Kiwi.com",
    },
    kiwitaxi: {
      url: "",
      urls: {
        en: "https://kiwitaxi.tpk.ro/xmQYmqIl",
        es: "https://kiwitaxi.tpk.ro/8bXhqjhr",
      },
      landing: "https://kiwitaxi.com/",
      label: "Kiwitaxi",
    },
    yesim: {
      url: "",
      urls: {
        en: "https://yesim.tpk.ro/uzjpBpju",
        es: "https://yesim.tpk.ro/KqpvuYgm",
      },
      landing: "https://yesim.app/",
      label: "Yesim",
    },
    klook: {
      url: "",
      urls: {
        en: "https://klook.tpk.ro/2NhHWOSD",
        es: "https://klook.tpk.ro/RmERIKIk",
      },
      landing: "https://www.klook.com/",
      label: "Klook",
    },
    tripcom: {
      // Website-проект пока не подписан на Trip.com → pending (кнопка off).
      url: "",
      urls: { en: "", es: "" },
      landing: "https://www.trip.com/",
      label: "Trip.com",
    },
  },
  siteUrl: "https://nonamemac-cyber.github.io/travel-finds",
};

window.TRAVEL_PLACEHOLDER = !window.TRAVEL_CONFIG.programs.kiwi.urls.en;
